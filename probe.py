"""Throwaway probe: which free data endpoints answer from a GitHub Actions runner."""
import json, os, re, sys, time, urllib.request, urllib.error

OUT = "probe-out"
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
SEC_UA = "alesiokanani.github.io mNAV chart (github.com/AlesioKanani)"
log = []


def get(url, ua=UA, accept="*/*", limit=None):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": accept, "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            return r.status, dict(r.headers), body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()[:4000]
    except Exception as e:  # noqa
        return -1, {}, repr(e).encode()


def save(name, body):
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(body if isinstance(body, bytes) else body.encode())


def probe(name, url, ua=UA, accept="*/*", keep=6000):
    code, hdr, body = get(url, ua, accept)
    ct = hdr.get("Content-Type", hdr.get("content-type", ""))
    log.append({"name": name, "url": url, "status": code, "ctype": ct, "bytes": len(body),
                "cors": hdr.get("Access-Control-Allow-Origin", hdr.get("access-control-allow-origin"))})
    save(name + ".txt", body[:keep] if keep else body)
    print(code, len(body), url, flush=True)
    return code, body


# 1) strategy.com pages + JS bundles -> look for API endpoints
pages = ["", "charts", "bitcoin", "debt", "shares", "ledger", "credit/risk", "strc", "strf"]
script_urls = set()
for p in pages:
    code, body = probe("strategy_page_" + (p.replace("/", "_") or "home"), "https://www.strategy.com/" + p, keep=0)
    html = body.decode("utf-8", "replace")
    for m in re.findall(r'<script[^>]+src="([^"]+)"', html):
        script_urls.add(m if m.startswith("http") else "https://www.strategy.com" + m)
    # inline JSON blobs (Next.js / Nuxt)
    for tag in ("__NEXT_DATA__", "__NUXT__", "self.__next_f"):
        if tag in html:
            log.append({"name": "inline_" + tag, "page": p, "present": True})

api_hits = {}
for su in sorted(script_urls):
    code, hdr, body = get(su)
    txt = body.decode("utf-8", "replace")
    for m in re.findall(r'["\'`](https?://[a-zA-Z0-9.\-]+(?:/[^"\'`\s]*)?)["\'`]', txt):
        if any(k in m for k in ("api", "data", "json", "csv", "kpi", "graphql", "supabase", "firebase", "contentstack")):
            api_hits.setdefault(m, set()).add(su.rsplit("/", 1)[-1])
    for m in re.findall(r'["\'`](/api/[^"\'`\s]+)["\'`]', txt):
        api_hits.setdefault(m, set()).add(su.rsplit("/", 1)[-1])
    for m in re.findall(r'["\'`]((?:/|https?://)[^"\'`\s]*(?:bitcoinKpis|mnav|mNAV|kpi|Kpi|history|History|timeseries|chart-data|chartData)[^"\'`\s]*)["\'`]', txt):
        api_hits.setdefault(m, set()).add(su.rsplit("/", 1)[-1])
save("strategy_scripts.json", json.dumps(sorted(script_urls), indent=1))
save("strategy_api_hits.json", json.dumps({k: sorted(v) for k, v in sorted(api_hits.items())}, indent=1))

# 2) price + reference data candidates
cands = {
    "yahoo_mstr": "https://query1.finance.yahoo.com/v8/finance/chart/MSTR?range=5d&interval=1d",
    "yahoo_mstr_q2": "https://query2.finance.yahoo.com/v8/finance/chart/MSTR?range=5d&interval=1d",
    "yahoo_btc": "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD?range=5d&interval=1d",
    "stooq_mstr": "https://stooq.com/q/d/l/?s=mstr.us&i=d",
    "coingecko_ping": "https://api.coingecko.com/api/v3/ping",
    "coingecko_treasury": "https://api.coingecko.com/api/v3/companies/public_treasury/bitcoin",
    "coinbase_candles": "https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400",
    "kraken_ohlc": "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1440",
    "bitstamp_ohlc": "https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=86400&limit=10",
    "bitcointreasuries_page": "https://bitcointreasuries.net/public-companies/strategy",
    "nasdaq_mstr": "https://api.nasdaq.com/api/quote/MSTR/info?assetclass=stocks",
}
for k, u in cands.items():
    probe(k, u)

for k, u in {
    "sec_submissions": "https://data.sec.gov/submissions/CIK0001050446.json",
    "sec_companyfacts": "https://data.sec.gov/api/xbrl/companyfacts/CIK0001050446.json",
}.items():
    probe(k, u, ua=SEC_UA, keep=0)

save("log.json", json.dumps(log, indent=1))
print("done")
