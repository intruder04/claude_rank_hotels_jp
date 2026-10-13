#!/usr/bin/env python3
"""Count places to eat, shops, konbini, supermarkets (500 m) and big shopping (800 m)
around each hotel using OpenStreetMap's Overpass API, and write them into data.json.

Usage:
    python3 osm_counts.py data.json [--force]

Saves after every hotel, and skips hotels that already have counts, so if the servers
are busy you can just run it again to fill in the rest (--force recounts everything).

Only hotel coordinates are sent (public places, no personal data). Overpass is a free,
shared service: the script goes slowly, retries on 429/504 and switches mirrors, and
never reuses a previous hotel's result when a request fails (that bug happened once).
"""
import json, sys, time, urllib.parse, urllib.request, pathlib

ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
Q = """[out:json][timeout:60];
(nwr(around:500,{la},{lo})["amenity"~"^(restaurant|cafe|fast_food|bar|pub|izakaya)$"];)->.food;
(nwr(around:500,{la},{lo})["shop"];)->.shops;
(nwr(around:500,{la},{lo})["shop"="convenience"];)->.conv;
(nwr(around:500,{la},{lo})["shop"="supermarket"];)->.sup;
(nwr(around:800,{la},{lo})["shop"~"^(department_store|mall)$"];)->.malls;
.food out count; .shops out count; .conv out count; .sup out count; .malls out tags;"""

def query(la, lo):
    data = urllib.parse.urlencode({"data": Q.format(la=la, lo=lo)}).encode()
    for attempt in range(6):
        ep = ENDPOINTS[attempt % len(ENDPOINTS)]
        try:
            req = urllib.request.Request(ep, data=data, headers={"User-Agent": "japan-hotel-comparison/1.0"})
            return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception as e:
            print("  retry", attempt + 1, e, file=sys.stderr, flush=True); time.sleep(10 + 5 * attempt)
    return None

def main():
    path = pathlib.Path(sys.argv[1]); d = json.loads(path.read_text())
    for h in d["hotels"]:
        if h.get("lat") is None: continue
        if h.get("food") is not None and "--force" not in sys.argv: continue
        j = query(h["lat"], h["lon"])
        if j is None:
            print(h["name"], "FAILED — left blank"); continue
        els = j["elements"]; c = [int(e["tags"]["total"]) for e in els if e["type"] == "count"]
        h.update(food=c[0], shops=c[1], konbini=c[2], supermarkets=c[3])
        malls = sorted({e["tags"].get("name:en") or e["tags"].get("name") for e in els if e["type"] != "count"} - {None})
        if malls and not h.get("big_shopping"): h["big_shopping"] = ", ".join(malls[:6])
        path.write_text(json.dumps(d, ensure_ascii=False, indent=1))
        print(h["name"], c, flush=True); time.sleep(6)

if __name__ == "__main__":
    main()
