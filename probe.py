"""Throwaway probe #3: save Strategy API payloads so the pipeline can be designed against real data."""
import json, os, urllib.request, urllib.error, gzip

OUT = "probe-out"
os.makedirs(OUT, exist_ok=True)
UA = "alesiokanani.github.io-mnav/1.0 (+https://github.com/AlesioKanani/alesiokanani.github.io)"
S = "https://api.strategy.com"
meta = {}


def get(path):
    req = urllib.request.Request(S + path, headers={"User-Agent": UA, "Accept": "application/json",
                                                    "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
        hdr = {k: v for k, v in r.headers.items()}
        body = gzip.decompress(raw) if hdr.get("Content-Encoding") == "gzip" else raw
        meta[path] = {"status": r.status, "wire_bytes": len(raw), "bytes": len(body),
                      **{k: hdr.get(k) for k in ("Content-Encoding", "Cache-Control", "Last-Modified", "ETag",
                                                 "Access-Control-Allow-Origin", "Age", "Expires")}}
        return json.loads(body)


for ep in ["bitcoinKpis", "mstrKpiData", "kpiData", "getPreferreds"]:
    with open(os.path.join(OUT, ep + ".json"), "w") as f:
        json.dump(get("/btc/" + ep), f, indent=1)
with open(os.path.join(OUT, "credit.json"), "w") as f:
    json.dump(get("/v2/btc/credit"), f, indent=1)

ts = get("/btc/timeSeries")
keep = {e["ticker"]: e for e in ts if e["ticker"] in ("MSTR", "BTC", "STRK", "STRF", "STRD", "STRC", "STRE")}
with open(os.path.join(OUT, "timeSeries_subset.json"), "w") as f:
    json.dump(keep, f, separators=(",", ":"))
with open(os.path.join(OUT, "meta.json"), "w") as f:
    json.dump(meta, f, indent=1)
print(json.dumps(meta, indent=1))
