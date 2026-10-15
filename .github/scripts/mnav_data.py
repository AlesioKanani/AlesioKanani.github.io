#!/usr/bin/env python3
"""Build the data file behind https://alesiokanani.github.io/mnav/

Pulls Strategy's public dashboard API (the one strategy.com itself uses), turns its
daily MSTR series into three mNAV multiples, and writes one compact JSON file.

  Basic mNAV          = market cap / BTC NAV
  Enterprise mNAV     = (market cap + debt + preferred - USD reserve and cash) / BTC NAV
  Equity Premium mNAV = market cap / (BTC NAV - debt - preferred)
                        the "residual equity" view: what common holders own once every
                        senior claim is paid in BTC terms. Cash is left out on purpose
                        (Strategy earmarks it for dividends and coupons).

Market cap uses basic shares outstanding. BTC NAV is holdings x BTC price at the
4:00 pm ET close, as Strategy reports it. Debt is principal and preferred is notional
(par), both as Strategy reports them.

Strategy's series carries debt and preferred (as % of BTC NAV) from 2024-12-31 on.
Before that the company had no preferred stock, and debt comes from DEBT_EVENTS below.

Standard library only, so the GitHub Actions job needs no installs.

  python3 mnav_data.py --out mnav.json                    # fetch live
  python3 mnav_data.py --out mnav.json --from-dir DIR     # use saved API responses
"""
import argparse
import datetime as dt
import gzip
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

API = "https://api.strategy.com"
UA = "alesiokanani.github.io-mnav/1.0 (+https://github.com/AlesioKanani/alesiokanani.github.io)"
ET = ZoneInfo("America/New_York")

# Debt principal changes before 2024-12-31, in $M, dated by closing / extinguishment.
# Sources: the company's press releases and 8-K filings for each instrument.
DEBT_EVENTS = [
    ("2020-12-11", +650.00, "0.750% convertible notes due 2025 issued"),
    ("2021-02-19", +1050.00, "0% convertible notes due 2027 issued"),
    ("2021-06-14", +500.00, "6.125% senior secured notes due 2028 issued"),
    ("2022-03-23", +205.00, "Silvergate term loan drawn"),
    ("2023-03-24", -205.00, "Silvergate term loan repaid"),
    ("2024-03-11", +800.00, "0.625% convertible notes due 2030 issued"),
    ("2024-03-19", +603.75, "0.875% convertible notes due 2031 issued"),
    ("2024-06-20", +800.00, "2.25% convertible notes due 2032 issued"),
    ("2024-07-15", -650.00, "2025 notes called and converted into shares"),
    ("2024-09-20", +1010.00, "0.625% convertible notes due 2028 issued"),
    ("2024-09-26", -500.00, "2028 senior secured notes redeemed"),
    ("2024-11-21", +3000.00, "0% convertible notes due 2029 issued"),
]  # running total on 2024-12-31: 7,263.75, which matches Strategy's own figure that day


def fetch_json(path, from_dir=None, attempts=4):
    """GET a JSON endpoint from Strategy's API (or a saved copy of it)."""
    if from_dir:
        name = path.rstrip("/").rsplit("/", 1)[-1] + ".json"
        with open(os.path.join(from_dir, name), encoding="utf-8") as f:
            return json.load(f)
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(API + path, headers={
                "User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            last = e
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"could not fetch {path}: {last}")


def num(v):
    """Strategy sends some numbers as strings with thousands separators."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(",", "").replace("$", "").replace("%", "").strip()
    return float(s) if s not in ("", "-", "NA", "N/A") else None


def schedule_debt(date):
    return sum(amount for d, amount, _ in DEBT_EVENTS if d <= date)


def multiples(mc, nav, debt, pref, usd):
    """The three mNAV views. Returns None where a view is undefined."""
    if not (mc and nav and nav > 0):
        return None, None, None
    basic = mc / nav
    ent = (mc + debt + pref - usd) / nav
    residual = nav - debt - pref
    # Below ~5% of NAV the residual is a rounding error away from zero and the ratio is
    # meaningless (2022: debt briefly exceeded the BTC stack), so leave a gap instead.
    eq = mc / residual if residual > 0.05 * nav else None
    return basic, ent, eq


def r4(x):
    return None if x is None or not math.isfinite(x) else round(x, 4)


def r1(x):
    return None if x is None or not math.isfinite(x) else round(x, 1)


def build_history(ts):
    series = ts if isinstance(ts, list) else list(ts.values())
    mstr = next(e for e in series if e.get("ticker") == "MSTR")["values"]
    rows = sorted(mstr, key=lambda r: r["date"])
    # A row for today before the 4:00 pm close would be an intraday figure, not a close.
    # The page adds its own live point, so leave today out until the close is in.
    now = dt.datetime.now(ET)
    if rows and rows[-1]["date"][:10] == now.date().isoformat() and now.time() < dt.time(16, 20):
        rows = rows[:-1]
    out = {k: [] for k in ("d", "px", "mc", "nav", "btc", "debt", "pref", "usd", "basic", "ent", "eq")}
    for r in rows:
        date = r["date"][:10]
        px, mc, nav, btc = num(r.get("price")), num(r.get("marketCap")), num(r.get("btcNav")), num(r.get("btcHoldings"))
        if not (px and mc and nav and btc):
            continue
        dp = num(r.get("debtPrefByBN"))
        if dp is not None:
            debt_pref = dp / 100 * nav
            pref = (num(r.get("prefBtcNav")) or 0.0) / 100 * nav
            debt = max(debt_pref - pref, 0.0)
        else:
            debt, pref = schedule_debt(date), 0.0
        usd = num(r.get("usdAssets")) or 0.0
        basic, ent, eq = multiples(mc, nav, debt, pref, usd)
        for k, v in (("d", date), ("px", round(px, 4)), ("mc", round(mc)), ("nav", round(nav)), ("btc", round(btc)),
                     ("debt", r1(debt)), ("pref", r1(pref)), ("usd", r1(usd)),
                     ("basic", r4(basic)), ("ent", r4(ent)), ("eq", r4(eq))):
            out[k].append(v)
    return out


def et_iso(stamp):
    """'10/15/2026 08:51 AM' (New York time) -> ISO 8601 with offset."""
    try:
        return dt.datetime.strptime(stamp, "%m/%d/%Y %I:%M %p").replace(tzinfo=ET).isoformat()
    except (TypeError, ValueError):
        return None


def build_latest(btc_kpis, mstr_kpis):
    """Snapshot of right now, computed the same way the page computes its live point."""
    b = btc_kpis.get("results", btc_kpis)
    m = mstr_kpis[0] if isinstance(mstr_kpis, list) else mstr_kpis
    close_px, close_mc = num(m["ufPrice"]), num(m["marketCap"])
    shares = close_mc * 1e6 / close_px
    px, session, px_time = close_px, "close", et_iso(m.get("timeStamp"))
    ext = m.get("extendedSession") or {}
    ext_time = et_iso(ext.get("timeStamp"))
    if num(ext.get("ufPrice")) and ext_time and px_time and ext_time > px_time:
        px, session, px_time = num(ext["ufPrice"]), ext.get("sessionType") or "extended", ext_time
    btc_price, holdings = num(b["ufPrice"]), num(b["btcHoldings"])
    nav = holdings * btc_price / 1e6
    usd = num(b.get("totalReserve")) / 1e6 - nav if b.get("totalReserve") is not None else 0.0
    debt, pref = num(m["debt"]), num(m["pref"])
    mc = shares * px / 1e6
    basic, ent, eq = multiples(mc, nav, debt, pref, usd)
    return {
        "mstr": {"price": px, "session": session, "time": px_time, "close": close_px},
        "btc": {"price": btc_price, "time": dt.datetime.fromtimestamp(b["msTimestamp"] / 1000, dt.timezone.utc).isoformat()
                if b.get("msTimestamp") else None},
        "holdings": holdings, "shares": round(shares), "mc": round(mc, 1), "nav": round(nav, 1),
        "debt": debt, "pref": pref, "usd": round(usd, 1),
        "basic": r4(basic), "ent": r4(ent), "eq": r4(eq),
        "strategyMnav": num(b.get("mNav")),
    }


def check(hist, latest):
    """Refuse to publish anything that looks broken, so the last good file stays up."""
    n = len(hist["d"])
    assert n >= 1000, f"only {n} rows"
    last = dt.date.fromisoformat(hist["d"][-1])
    assert (dt.date.today() - last).days <= 10, f"stale series, last row {last}"
    assert all(x is None or 0.05 < x < 60 for x in hist["eq"]), "equity premium out of range"
    assert all(0.05 < x < 20 for x in hist["ent"]), "enterprise mNAV out of range"
    assert 0.05 < latest["ent"] < 20, "latest enterprise mNAV out of range"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--from-dir", help="read saved API responses instead of fetching")
    a = ap.parse_args()

    ts = fetch_json("/btc/timeSeries", a.from_dir)
    hist = build_history(ts)
    latest = build_latest(fetch_json("/btc/bitcoinKpis", a.from_dir), fetch_json("/btc/mstrKpiData", a.from_dir))
    check(hist, latest)

    doc = {
        "v": 1,
        "generated": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "units": {"px": "USD", "mc,nav,debt,pref,usd": "USD millions", "btc": "BTC"},
        "notes": "Daily at the 4:00 pm ET close. Source: Strategy's public dashboard API (api.strategy.com); "
                 "debt before 2024-12-31 from company filings. Not affiliated with Strategy.",
        "debtEvents": [{"date": d, "change": c, "what": w} for d, c, w in DEBT_EVENTS],
        "latest": latest,
        "rows": hist,
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, separators=(",", ":"), allow_nan=False)
    print(f"{len(hist['d'])} rows, {hist['d'][0]} to {hist['d'][-1]}; latest eq {latest['eq']} "
          f"ent {latest['ent']} basic {latest['basic']} ({latest['mstr']['session']})")


if __name__ == "__main__":
    sys.exit(main())
