"""Throwaway probe: can a GitHub Actions runner reach Strive's dashboard API?"""
import json, os, urllib.request, urllib.error, gzip
OUT = "probe-out"; os.makedirs(OUT, exist_ok=True)
UA = "alesiokanani.github.io-mnav/1.0 (+https://github.com/AlesioKanani/alesiokanani.github.io)"
B = "https://strive.com"
eps = {
  "base": "/treasury/api/dashboard/base-data",
  "agg": "/treasury/api/dashboard/aggregates?fromDate=2025-09-01&toDate=2026-10-15&currency=USD&stockSymbol=ASST",
  "calc": "/treasury/api/dashboard/calculated?fromDate=2026-10-01&toDate=2026-10-15&currency=USD&stockSymbol=ASST",
  "header": "/treasury/api/header-market",
  "quotes": "/api/quotes",
  "treasury": "/api/treasury",
}
log = {}
for k, p in eps.items():
    req = urllib.request.Request(B + p, headers={"User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read(); body = gzip.decompress(raw) if r.headers.get("Content-Encoding") == "gzip" else raw
            log[k] = {"status": r.status, "bytes": len(body), "wire": len(raw), "server": r.headers.get("Server"), "cf": r.headers.get("CF-Cache-Status"), "acao": r.headers.get("Access-Control-Allow-Origin")}
            open(os.path.join(OUT, k + ".json"), "wb").write(body if k != "calc" else body[:200000])
    except urllib.error.HTTPError as e:
        log[k] = {"status": e.code, "server": e.headers.get("Server"), "body": e.read()[:500].decode("utf-8", "replace")}
    except Exception as e:
        log[k] = {"error": repr(e)}
json.dump(log, open(os.path.join(OUT, "log.json"), "w"), indent=1)
print(json.dumps(log, indent=1))
