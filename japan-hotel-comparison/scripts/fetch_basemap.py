#!/usr/bin/env python3
"""Download a quiet background map for the comparison page and record it in data.json.

Usage:
    python3 fetch_basemap.py data.json [--max-tiles 30]

Uses OpenStreetMap's standard tiles. The page fades them to a calm gray in light theme
and inverts them in dark theme with CSS, so one download works for both. Tiles are saved
next to data.json in tiles/ and embedded by build_page.py, because the published page
can't load images from other sites. The page shows "© OpenStreetMap contributors" as
the attribution, which is required.

Only a handful of tiles are fetched (one area, one zoom level, ≤30 by default) with an
identifying User-Agent, as OpenStreetMap's tile usage policy asks. Don't raise the limit
much or run this in a loop. (CARTO's basemaps returned blank placeholders when tested in
Oct 2026, so they aren't used.)
"""
import json, math, pathlib, sys, time, urllib.request

URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

def tile_xy(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def main():
    path = pathlib.Path(sys.argv[1])
    max_tiles = int(sys.argv[sys.argv.index("--max-tiles") + 1]) if "--max-tiles" in sys.argv else 30
    d = json.loads(path.read_text())
    pts = [(h["lat"], h["lon"]) for h in d["hotels"] if h.get("lat")]
    pts += [(s[1], s[2]) for s in d.get("stations", [])]
    pts += [(p["lat"], p["lon"]) for p in d.get("places", [])]
    if not pts:
        sys.exit("no coordinates in data.json")
    la0, la1 = min(p[0] for p in pts), max(p[0] for p in pts)
    lo0, lo1 = min(p[1] for p in pts), max(p[1] for p in pts)
    # pick the most detailed zoom that still fits in max_tiles (with a margin of ~1 tile)
    for z in range(17, 9, -1):
        x0, y0 = tile_xy(la1, lo0, z); x1, y1 = tile_xy(la0, lo1, z)
        tx0, tx1, ty0, ty1 = int(x0 - 0.3), int(x1 + 0.3), int(y0 - 0.3), int(y1 + 0.3)
        if (tx1 - tx0 + 1) * (ty1 - ty0 + 1) <= max_tiles:
            break
    out = path.parent / "tiles"; out.mkdir(exist_ok=True)
    tiles = []
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            f = out / f"osm_{z}_{tx}_{ty}.png"
            if not f.exists():
                req = urllib.request.Request(URL.format(z=z, x=tx, y=ty), headers={
                    "User-Agent": "japan-hotel-comparison/1.0 (+https://github.com/intruder04/claude_rank_hotels_jp)"})
                data = urllib.request.urlopen(req, timeout=30).read()
                if len(data) < 3000:
                    print("warning: tile", tx, ty, "looks blank (", len(data), "bytes)")
                f.write_bytes(data); time.sleep(0.3)
            tiles.append({"x": tx, "y": ty, "img": str(f.relative_to(path.parent))})
    d["basemap"] = {"z": z, "tiles": tiles, "attribution": "© OpenStreetMap contributors"}
    path.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(f"zoom {z}: {len(tiles)} tiles saved to {out}")

if __name__ == "__main__":
    main()
