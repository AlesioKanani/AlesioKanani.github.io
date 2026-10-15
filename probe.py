"""Throwaway probe #2: is Strategy's public dashboard API reachable from a GitHub Actions runner?"""
import json, os, urllib.request, urllib.error, gzip

OUT = "probe-out"
os.makedirs(OUT, exist_ok=True)
HONEST_UA = "alesiokanani.github.io-mnav/1.0 (+https://github.com/AlesioKanani/alesiokanani.github.io)"
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
log = []


def get(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json, text/plain, */*",
                                               "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            return r.status, dict(r.headers), body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()[:3000]
    except Exception as e:  # noqa
        return -1, {}, repr(e).encode()


def probe(name, url, ua=HONEST_UA, keep=3000):
    code, hdr, body = get(url, ua)
    log.append({"name": name, "ua": "honest" if ua == HONEST_UA else "browser", "url": url, "status": code,
                "bytes": len(body), "ctype": hdr.get("Content-Type"),
                "cors": hdr.get("Access-Control-Allow-Origin")})
    with open(os.path.join(OUT, name + ".txt"), "wb") as f:
        f.write(body[:keep] if keep else body)
    print(code, len(body), name, flush=True)
    return code, body


S = "https://api.strategy.com"
for ep in ["btc/bitcoinKpis", "btc/mstrKpiData", "btc/kpiData", "btc/getPreferreds", "v2/btc/credit"]:
    probe("strat_" + ep.replace("/", "_"), f"{S}/{ep}")
code, body = probe("strat_timeSeries", f"{S}/btc/timeSeries", keep=1500)
if code != 200:
    probe("strat_bitcoinKpis_browserUA", f"{S}/btc/bitcoinKpis", ua=BROWSER_UA)

# Nasdaq daily history for MSTR (split-adjusted?) and a preferred
probe("nasdaq_hist_mstr", "https://api.nasdaq.com/api/quote/MSTR/historical?assetclass=stocks&fromdate=2024-08-01&todate=2024-08-20&limit=50", ua=BROWSER_UA, keep=0)
probe("nasdaq_hist_mstr_honest", "https://api.nasdaq.com/api/quote/MSTR/historical?assetclass=stocks&fromdate=2026-10-01&todate=2026-10-15&limit=50", keep=0)
# Coinbase daily candles (historical window)
probe("coinbase_hist", "https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start=2023-01-01T00:00:00Z&end=2023-03-01T00:00:00Z", keep=0)
# CoinGecko treasury entity endpoints (free tier?)
probe("cg_entity", "https://api.coingecko.com/api/v3/public_treasury/strategy")
probe("cg_holding_chart", "https://api.coingecko.com/api/v3/public_treasury/strategy/bitcoin/holding_chart?days=max")

with open(os.path.join(OUT, "log.json"), "w") as f:
    json.dump(log, f, indent=1)
print("done")
