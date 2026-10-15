#!/usr/bin/env python3
"""Build the data file behind https://alesiokanani.github.io/mnav/

Two bitcoin treasury companies, each turned into three daily mNAV multiples:

  Basic mNAV          = market cap / BTC NAV
  Enterprise mNAV     = (market cap + debt + preferred - cash and similar) / BTC NAV
  Equity Premium mNAV = market cap / (BTC NAV - debt - preferred)
                        the "residual equity" view: what common holders own once every
                        senior claim is paid in BTC terms. Cash is left out on purpose.

Market cap uses basic shares outstanding, BTC NAV uses the bitcoin price at the
4:00 pm ET close, debt is principal and preferred is notional (par / stated amount).

  MSTR  Strategy's public dashboard API (api.strategy.com, the data behind strategy.com).
        It carries debt and preferred from 2024-12-31 on; earlier debt is DEBT_EVENTS.
  ASST  Strive's public dashboard API (strive.com/treasury): bitcoin purchases, weekly
        share counts, cash and debt. It only reports the current preferred (SATA)
        count, so the history before that comes from Strive's 8-K and 10-Q filings
        (ASST_* below) and each run adds the latest count to the file it publishes.

Standard library only, so the GitHub Actions job needs no installs.

  python3 mnav_data.py --out mnav.json [--previous LAST_PUBLISHED.json]
  python3 mnav_data.py --out mnav.json --from-dir DIR      # saved API responses
"""
import argparse
import bisect
import datetime as dt
import gzip
import http.client
import json
import math
import os
import sys
import time
import traceback
import urllib.request
from zoneinfo import ZoneInfo

UA = "alesiokanani.github.io-mnav/1.0 (+https://github.com/AlesioKanani/alesiokanani.github.io)"
ET = ZoneInfo("America/New_York")
STRATEGY = "https://api.strategy.com"
STRIVE = "https://strive.com/treasury/api"

# ---------------------------------------------------------------------------------------
# MSTR: debt principal changes before 2024-12-31, in $M, dated by closing / extinguishment.
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

# ---------------------------------------------------------------------------------------
# ASST history before Strive's dashboard reports it weekly (from its 8-K and 10-Q filings).
# Share counts are split-adjusted (1-for-20 reverse split, February 2026) and are Class A +
# Class B + pre-funded warrants. Two points on consecutive days mark a one-off jump.
ASST_START = "2025-09-15"   # first trading day after the 5,816 BTC buy that followed the merger

ASST_SHARES = [
    ("2025-09-12", 42_204_977), ("2025-09-30", 42_204_977), ("2025-12-31", 44_766_899),
    ("2026-01-15", 44_766_899), ("2026-01-16", 60_857_685),       # Semler merger: +16,090,786
    ("2026-03-09", 66_777_785), ("2026-03-31", 69_158_785), ("2026-04-02", 69_209_119),
    ("2026-04-13", 69_718_831), ("2026-04-24", 72_782_431), ("2026-05-01", 73_023_431),
    ("2026-05-12", 73_082_631), ("2026-05-18", 73_537_163), ("2026-05-22", 75_769_163),
    ("2026-06-01", 78_869_163), ("2026-06-05", 79_190_663), ("2026-06-12", 79_674_063),
    ("2026-06-18", 81_567_885),
]
ASST_SATA = [  # SATA shares outstanding; notional is $100 a share
    ("2025-09-12", 0), ("2025-11-09", 0), ("2025-11-10", 2_000_000),  # IPO
    ("2025-12-31", 2_012_729), ("2026-01-26", 2_012_729),
    ("2026-01-27", 4_262_728),   # follow-on (1,320,000) + Semler notes exchange (929,999)
    ("2026-03-09", 4_275_118), ("2026-03-31", 4_373_194), ("2026-04-13", 4_373_194),
    ("2026-04-24", 4_573_194), ("2026-05-01", 4_959_536), ("2026-05-12", 4_959_536),
    ("2026-05-18", 5_244_421), ("2026-05-22", 5_759_719), ("2026-06-01", 7_513_907),
    ("2026-06-12", 7_513_907), ("2026-06-18", 7_829_502), ("2026-08-14", 7_829_502),
    ("2026-08-21", 8_270_815), ("2026-08-28", 9_073_914), ("2026-09-04", 9_995_425),
    ("2026-09-11", 10_397_966), ("2026-09-18", 11_184_160), ("2026-09-25", 12_193_180),
    ("2026-09-30", 12_940_621), ("2026-10-02", 13_498_082), ("2026-10-09", 14_030_176),
]
ASST_DEBT = [  # $M, holds until the next entry
    ("2025-09-12", 0.0),
    ("2026-01-16", 120.0),   # assumed with Semler: $100M convertible notes + $20M Coinbase loan
    ("2026-01-27", 10.0),    # $90M of notes swapped into SATA, the loan repaid
    ("2026-05-12", 0.0),     # the last $10M of notes repurchased by May 12
]
ASST_USD = [  # cash + marketable securities (Strategy's STRC preferred), $M
    ("2025-09-30", 109.1), ("2025-12-31", 67.6), ("2026-03-09", 143.4), ("2026-03-16", 137.4),
    ("2026-03-31", 145.6), ("2026-04-02", 137.4), ("2026-04-13", 140.2), ("2026-04-24", 140.8),
    ("2026-05-01", 148.3), ("2026-05-12", 138.1), ("2026-05-18", 137.1), ("2026-05-22", 143.4),
    ("2026-06-01", 186.8), ("2026-06-05", 186.4), ("2026-06-12", 189.3), ("2026-06-18", 189.2),
]


# ---------------------------------------------------------------------------------------
# plumbing

class Source:
    """Fetches JSON from the APIs, or reads saved copies of them for testing."""

    def __init__(self, from_dir=None):
        self.from_dir = from_dir

    def get(self, url, name, attempts=3):
        if self.from_dir:
            with open(os.path.join(self.from_dir, name + ".json"), encoding="utf-8") as f:
                return json.load(f)
        last = None
        for i in range(attempts):   # at most about 3 minutes per source, well inside the job's limit
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"})
                with urllib.request.urlopen(req, timeout=55) as r:
                    raw = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    return json.loads(raw)
            except (OSError, http.client.HTTPException, ValueError) as e:   # OSError covers URLError, timeouts, resets
                last = e
                if i + 1 < attempts:
                    time.sleep(5 * (i + 1))
        raise RuntimeError(f"could not fetch {url}: {last}")


def load_previous(path):
    """The file the last run published. It carries the SATA counts recorded since the seed,
    so when one is named but can't be read, stop rather than publish a file without them."""
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"could not read the previous file {path} ({e}); nothing published") from e


def no_lost_history(name, rows, prev_rows):
    """A source that suddenly starts later or returns fewer days is broken or trimmed;
    keep the last good history instead of publishing the shorter one."""
    if not prev_rows or not prev_rows.get("d"):
        return
    if rows["d"][0] > prev_rows["d"][0] or len(rows["d"]) < len(prev_rows["d"]) - 2:
        raise RuntimeError(f"{name}: source returned less history than last time "
                           f"({rows['d'][0]}..{rows['d'][-1]}, {len(rows['d'])} days vs "
                           f"{prev_rows['d'][0]}..{prev_rows['d'][-1]}, {len(prev_rows['d'])} days)")


def num(v):
    """Some numbers arrive as strings with thousands separators."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(",", "").replace("$", "").replace("%", "").strip()
    return float(s) if s not in ("", "-", "NA", "N/A") else None


def r4(x):
    return None if x is None or not math.isfinite(x) else round(x, 4)


def r1(x):
    return None if x is None or not math.isfinite(x) else round(x, 1)


def multiples(mc, nav, debt, pref, usd):
    """The three mNAV views. Returns None where a view is undefined."""
    if not (mc and nav and nav > 0):
        return None, None, None
    basic = mc / nav
    ent = (mc + debt + pref - usd) / nav
    residual = nav - debt - pref
    # Below ~5% of NAV the residual is a rounding error away from zero and the ratio is
    # meaningless (MSTR in 2022: debt briefly exceeded the BTC stack), so leave a gap.
    eq = mc / residual if residual > 0.05 * nav else None
    return basic, ent, eq


def now_et():
    return dt.datetime.now(ET)


def provisional_today(date):
    """True for today's row before the close is in: an intraday figure, not a close."""
    n = now_et()
    return date == n.date().isoformat() and n.time() < dt.time(16, 20)


def at(points, date, mode="linear"):
    """Value of a dated series on `date`: held flat ('step') or interpolated ('linear')."""
    dates = [p[0] for p in points]
    i = bisect.bisect_right(dates, date)
    if i == 0:
        return points[0][1]
    if mode == "step" or i == len(points) or points[i - 1][0] == date:
        return points[i - 1][1]
    (d0, v0), (d1, v1) = points[i - 1], points[i]
    a, b, x = (dt.date.fromisoformat(s).toordinal() for s in (d0, d1, date))
    return v0 + (v1 - v0) * (x - a) / (b - a)


def merged(seed, extra):
    """Seed points, then any newer points from the live API; one value per date."""
    last = seed[-1][0] if seed else ""
    pts = dict(seed)
    pts.update({d: v for d, v in extra if d > last})
    return sorted(pts.items())


def blank_rows():
    return {k: [] for k in ("d", "px", "mc", "nav", "btc", "debt", "pref", "usd", "basic", "ent", "eq")}


def add_row(out, date, px, mc, nav, btc, debt, pref, usd):
    basic, ent, eq = multiples(mc, nav, debt, pref, usd)
    for k, v in (("d", date), ("px", round(px, 4)), ("mc", round(mc, 1)), ("nav", round(nav, 1)), ("btc", round(btc, 2)),
                 ("debt", r1(debt)), ("pref", r1(pref)), ("usd", r1(usd)),
                 ("basic", r4(basic)), ("ent", r4(ent)), ("eq", r4(eq))):
        out[k].append(v)


def et_iso(stamp):
    """'10/15/2026 08:51 AM' (New York time) -> ISO 8601 with offset."""
    try:
        return dt.datetime.strptime(stamp, "%m/%d/%Y %I:%M %p").replace(tzinfo=ET).isoformat()
    except (TypeError, ValueError):
        return None


def latest_block(stock, btc_price, btc_time, holdings, shares, debt, pref, usd, company_mnav):
    nav = holdings * btc_price / 1e6
    mc = shares * stock["price"] / 1e6
    basic, ent, eq = multiples(mc, nav, debt, pref, usd)
    return {
        "stock": stock, "btc": {"price": btc_price, "time": btc_time},
        "holdings": holdings, "shares": round(shares), "mc": round(mc, 1), "nav": round(nav, 1),
        "debt": r1(debt), "pref": r1(pref), "usd": r1(usd),
        "basic": r4(basic), "ent": r4(ent), "eq": r4(eq), "companyMnav": company_mnav,
    }


# ---------------------------------------------------------------------------------------
# MSTR

def schedule_debt(date):
    return sum(amount for d, amount, _ in DEBT_EVENTS if d <= date)


def build_mstr(src):
    ts = src.get(STRATEGY + "/btc/timeSeries", "timeSeries")
    series = ts if isinstance(ts, list) else list(ts.values())
    rows = sorted(next(e for e in series if e.get("ticker") == "MSTR")["values"], key=lambda r: r["date"])
    if rows and provisional_today(rows[-1]["date"][:10]):
        rows = rows[:-1]
    out = blank_rows()
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
        add_row(out, date, px, mc, nav, btc, debt, pref, num(r.get("usdAssets")) or 0.0)

    b = src.get(STRATEGY + "/btc/bitcoinKpis", "bitcoinKpis")
    b = b.get("results", b)
    m = src.get(STRATEGY + "/btc/mstrKpiData", "mstrKpiData")
    m = m[0] if isinstance(m, list) else m
    close_px, close_mc = num(m["ufPrice"]), num(m["marketCap"])
    stamp_txt = m.get("timeStamp") or ""
    px, px_time = close_px, et_iso(stamp_txt)
    session = "close" if stamp_txt.endswith("04:00 PM") else "market hours"
    ext = m.get("extendedSession") or {}
    ext_time = et_iso(ext.get("timeStamp"))
    if num(ext.get("ufPrice")) and ext_time and px_time and ext_time > px_time:
        px, session, px_time = num(ext["ufPrice"]), ext.get("sessionType") or "extended", ext_time
    btc_price, holdings = num(b["ufPrice"]), num(b["btcHoldings"])
    btc_time = (dt.datetime.fromtimestamp(b["msTimestamp"] / 1000, dt.timezone.utc).isoformat()
                if b.get("msTimestamp") else None)
    nav = holdings * btc_price / 1e6
    usd = num(b.get("totalReserve")) / 1e6 - nav if b.get("totalReserve") is not None else 0.0
    stock = {"price": px, "session": session, "time": px_time, "close": close_px}
    latest = latest_block(stock, btc_price, btc_time, holdings, close_mc * 1e6 / close_px,
                          num(m["debt"]), num(m["pref"]), usd, num(b.get("mNav")))
    latest["mstr"], latest["strategyMnav"] = stock, latest["companyMnav"]   # names the first page used

    n = len(out["d"])
    assert n >= 1000, f"MSTR: only {n} rows"
    assert (dt.date.today() - dt.date.fromisoformat(out["d"][-1])).days <= 10, "MSTR: stale series"
    assert all(x is None or 0.05 < x < 60 for x in out["eq"]), "MSTR: equity premium out of range"
    assert all(0.05 < x < 20 for x in out["ent"]), "MSTR: enterprise mNAV out of range"
    assert 0.05 < latest["ent"] < 20, "MSTR: latest enterprise mNAV out of range"
    return out, latest, (btc_price, btc_time)


# ---------------------------------------------------------------------------------------
# ASST

def build_asst(src, btc_at_close, live_btc, prev_pref):
    base = src.get(STRIVE + "/dashboard/base-data", "base")["data"]
    today = now_et().date().isoformat()
    agg = src.get(f"{STRIVE}/dashboard/aggregates?fromDate=2025-09-01&toDate={today}&currency=USD&stockSymbol=ASST",
                  "agg")["data"]
    since = (now_et().date() - dt.timedelta(days=5)).isoformat()
    calc = src.get(f"{STRIVE}/dashboard/calculated?fromDate={since}&toDate={today}&currency=USD&stockSymbol=ASST",
                   "calc")
    header = src.get(STRIVE + "/header-market", "header")["data"]
    try:   # Strive's official closing price; the day's bar can keep moving with after-hours trades
        q = next(x for x in src.get("https://strive.com/api/quotes", "quotes")["quotes"] if x.get("symbol") == "ASST")
        official = {q["officialCloseDate"]: num(q["officialClose"])} if num(q.get("officialClose")) else {}
    except Exception as e:  # noqa: BLE001
        print(f"note: no official close ({e})")
        official = {}

    def et_day(ms):
        return dt.datetime.fromtimestamp(ms / 1000, ET).date().isoformat()

    # bitcoin held: running total after each purchase, by transaction date
    tx = sorted(((t["transaction_date"], num(t["total_btc_holdings"])) for t in base["transactions"]))
    shares = merged(ASST_SHARES, [(s["date"], num(s["issued_shares"])) for s in base["shares"]])
    debt_pts = merged(ASST_DEBT, [(c["date"], num(c["debt"]) / 1e6) for c in base["cashDebt"]])
    usd_pts = merged(ASST_USD, [(c["date"], (num(c["cash"]) + (num(c.get("marketable_securities")) or 0)) / 1e6)
                                for c in base["cashDebt"]])

    # preferred: seed + what earlier runs recorded + today's count, per ticker
    pref_hist = {("SATA", d): n * 100 for d, n in ASST_SATA}
    for p in prev_pref or []:
        pref_hist.setdefault((p["ticker"], p["date"]), p["notional"])
    for p in calc.get("preferredStocks") or []:
        if p.get("use_in_calculations", True) and p.get("date"):
            pref_hist[(p["ticker"], p["date"])] = num(p["notional_value"])
    by_ticker = {}
    for (tk, d), v in sorted(pref_hist.items()):
        by_ticker.setdefault(tk, []).append((d, v))
    for tk, pts in by_ticker.items():   # a new series is zero until its first count
        if pts[0][1]:
            day_before = (dt.date.fromisoformat(pts[0][0]) - dt.timedelta(days=1)).isoformat()
            pts.insert(0, (day_before, 0.0))

    def pref_at(date):
        return sum(at(pts, date) for pts in by_ticker.values()) / 1e6

    # bitcoin bars are UTC days; only a fallback for days missing from Strategy's 4:00 pm prices
    btc_bars = {dt.datetime.fromtimestamp(b["t"] / 1000, dt.timezone.utc).date().isoformat(): b["c"]
                for b in agg["btcAggregates"]}
    # stock bars start at midnight ET; today's only counts as a close once the official close is out
    bars = sorted((et_day(b["t"]), official.get(et_day(b["t"]), b["c"])) for b in agg["stockAggregates"])
    if bars and bars[-1][0] == today and (provisional_today(today) or today not in official):
        live_bar = bars.pop()
    else:
        live_bar = None

    out = blank_rows()
    for date, px in bars:
        if date < ASST_START:
            continue
        held = at(tx, date, "step") if tx and tx[0][0] <= date else 0
        btc_px = btc_at_close.get(date) or btc_bars.get(date)
        if not (held and btc_px and px):
            continue
        sh = at(shares, date)
        add_row(out, date, px, sh * px / 1e6, held * btc_px / 1e6, held,
                at(debt_pts, date, "step"), pref_at(date), at(usd_pts, date))

    # right now: today's bar if trading has started, else the last close
    label = (header.get("marketStatusLabel") or "").strip().lower()
    pulled = header.get("pulledAtTimestamp")
    if live_bar and live_bar[1]:
        stock = {"price": live_bar[1], "session": label or "market hours",
                 "time": dt.datetime.fromtimestamp(pulled / 1000, ET).isoformat() if pulled else None,
                 "close": bars[-1][1] if bars else None}
    else:
        stock = {"price": bars[-1][1], "session": "close",
                 "time": dt.datetime.combine(dt.date.fromisoformat(bars[-1][0]), dt.time(16, 0), ET).isoformat(),
                 "close": bars[-1][1]}
    btc_price, btc_time = live_btc
    if not btc_price:
        t = next((x for x in header.get("tickers", []) if x.get("symbol") == "BTC"), {})
        btc_price, btc_time = num(t.get("price")), dt.datetime.now(dt.timezone.utc).isoformat()
    last_day = today
    company_mnav = None
    rows_calc = (calc.get("data") or {}).get("btcNav") or []
    if rows_calc and rows_calc[-1].get("evMnav"):
        company_mnav = round(num(rows_calc[-1]["evMnav"]), 4)
    latest = latest_block(stock, btc_price, btc_time, at(tx, last_day, "step"), at(shares, last_day),
                          at(debt_pts, last_day, "step"), pref_at(last_day), at(usd_pts, last_day), company_mnav)

    n = len(out["d"])
    assert n >= 200, f"ASST: only {n} rows"
    assert (dt.date.today() - dt.date.fromisoformat(out["d"][-1])).days <= 10, "ASST: stale series"
    assert all(x is None or 0.05 < x < 60 for x in out["eq"]), "ASST: equity premium out of range"
    assert all(0.05 < x < 30 for x in out["ent"]), "ASST: enterprise mNAV out of range"
    assert 0.05 < latest["ent"] < 30, "ASST: latest enterprise mNAV out of range"
    pref_list = [{"ticker": tk, "date": d, "notional": v} for (tk, d), v in sorted(pref_hist.items())
                 if not (tk == "SATA" and d <= ASST_SATA[-1][0])]
    return out, latest, pref_list


# ---------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--from-dir", help="read saved API responses instead of fetching")
    ap.add_argument("--previous", help="path of the last published file (required once one exists)")
    ap.add_argument("--problems", help="write any partial-failure notes here (for the workflow)")
    a = ap.parse_args()
    src = Source(a.from_dir)
    prev = load_previous(a.previous)
    problems = []
    stamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    as_of = dict((prev or {}).get("asOf") or {})

    mstr = None
    live_btc = (None, None)
    try:
        rows, latest, live_btc = build_mstr(src)
        no_lost_history("MSTR", rows, (prev or {}).get("rows"))
        mstr = {"rows": rows, "latest": latest}
        as_of["MSTR"] = stamp
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        problems.append(str(e) if str(e).startswith("MSTR") else f"MSTR: {e}")
        if prev and prev.get("rows"):
            mstr = {"rows": prev["rows"], "latest": prev["latest"]}

    btc_at_close = {}
    if mstr:
        r = mstr["rows"]
        btc_at_close = {d: nav * 1e6 / btc for d, nav, btc in zip(r["d"], r["nav"], r["btc"]) if btc}

    asst = None
    try:
        prev_pref = ((prev or {}).get("asst") or {}).get("prefHistory")
        rows, latest, pref_list = build_asst(src, btc_at_close, live_btc, prev_pref)
        no_lost_history("ASST", rows, ((prev or {}).get("asst") or {}).get("rows"))
        asst = {"rows": rows, "latest": latest, "prefHistory": pref_list}
        as_of["ASST"] = stamp
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        problems.append(str(e) if str(e).startswith("ASST") else f"ASST: {e}")
        if prev and prev.get("asst"):
            asst = prev["asst"]

    if not mstr:
        raise SystemExit("no MSTR data, fresh or previous; nothing published")

    doc = {
        "v": 2,
        "generated": stamp,
        "asOf": as_of,
        "units": {"px": "USD", "mc,nav,debt,pref,usd": "USD millions", "btc": "BTC"},
        "notes": "Daily at the 4:00 pm ET close. MSTR from Strategy's public dashboard API (api.strategy.com); "
                 "ASST from Strive's (strive.com/treasury) and its SEC filings. Not affiliated with either company.",
        "debtEvents": [{"date": d, "change": c, "what": w} for d, c, w in DEBT_EVENTS],
        # MSTR stays at the top level so a page cached from before ASST was added keeps working
        "latest": mstr["latest"],
        "rows": mstr["rows"],
        "asst": asst,
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, separators=(",", ":"), allow_nan=False)
    if a.problems:
        with open(a.problems, "w", encoding="utf-8") as f:
            f.write("\n".join(problems))
    for name, part in (("MSTR", mstr), ("ASST", asst)):
        if part:
            r, l = part["rows"], part["latest"]
            print(f"{name}: {len(r['d'])} rows, {r['d'][0]} to {r['d'][-1]}; now eq {l['eq']} ent {l['ent']} "
                  f"basic {l['basic']} ({l['stock']['session'] if 'stock' in l else l['mstr']['session']})")
    for p in problems:
        print("PROBLEM", p)


if __name__ == "__main__":
    sys.exit(main())
