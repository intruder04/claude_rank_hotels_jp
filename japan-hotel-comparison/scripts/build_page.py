#!/usr/bin/env python3
"""Build the hotel comparison page (one self-contained HTML file) from a data JSON.

Usage:
    python3 build_page.py data.json out.html

Paths to photos in the JSON are relative to the JSON file. See references/data-format.md
for every field. Missing optional fields are fine; the page leaves those cells blank.
"""
import base64, html, json, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from scoring import overall_scores, WEIGHTS

esc = html.escape
DATA = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
D = json.loads(DATA.read_text())
BASE = DATA.parent
trip = D["trip"]; dests = D.get("destinations", [])
H = list(D["hotels"])

BK = ("https://www.booking.com/hotel/jp/{slug}.html?checkin={ci}&checkout={co}"
      "&group_adults={ad}&no_rooms=1&group_children=0")

for h in H:
    h.setdefault("status", "new")
    p = BASE / h["photo"] if h.get("photo") else None
    h["img"] = ("data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()) if p and p.exists() else ""
    if h.get("url"):
        pass
    elif h.get("booking_slug"):
        h["url"] = BK.format(slug=h["booking_slug"], ci=trip["checkin"], co=trip["checkout"], ad=trip.get("adults", 2))
    else:
        h["url"] = "#"
    tr, tx = h.get("train", []), h.get("taxi", [])
    h["tt_total"] = (sum(tr) + sum(tx)) if tr and tx and None not in tr + tx else None
    h["fs_total"] = (h.get("food") or 0) + (h.get("shops") or 0)
    cats = [h.get(k) for k in ("cleanliness", "comfort", "location", "value")]
    h["rv_avg"] = round(sum(cats) / 4, 2) if None not in cats else None

# ---------- overall score → rank (always computed, so every hotel is ranked the same way) ----------
def _g(h, part):
    price = h.get("total_usd") if h.get("total_usd") is not None else h.get("score_price_usd")
    heat_ok = h.get("hotel_confirmed_ac") or h.get("heat_risk", "low") == "low"
    return {"reviews": h["rv_avg"], "price": price, "travel": h["tt_total"], "room": h.get("twin_ft2"),
            "heat": None if h.get("heat_risk") == "unknown" and not h.get("hotel_confirmed_ac") else (1 if heat_ok else 0),
            "food": h["fs_total"] if (h.get("food") is not None) else None, "bath": None if h.get("bath") is None else (1 if h["bath"] else 0)}[part]
overall_scores(H, _g)
H.sort(key=lambda x: -x["overall"])
for i, h in enumerate(H, 1):
    h["rank"] = i; h["tag"] = str(i)

def getv(h, key):
    if isinstance(key, tuple):
        arr = h.get(key[0]) or []
        return arr[key[1]] if len(arr) > key[1] else None
    return h.get(key)
def best(key, mode):
    vals = [getv(h, key) for h in H if getv(h, key) is not None]
    if not vals: return None
    return max(vals) if mode == "max" else min(vals)
def cell(h, key, mode, text, sub=""):
    v = getv(h, key)
    if v is None:
        return f'<td><span class="sub">{sub or "—"}</span></td>'
    win = v == best(key, mode)
    s = f'<span class="sub">{sub}</span>' if sub else ""
    medal = '<span aria-label="best">🥇</span> ' if win else ""
    return f'<td{" class=\"win\"" if win else ""}>{medal}<span class="num">{text}</span>{s}</td>'

CHIP = {"booked": '<span class="chip booked">📌 Booked</span>',
        "new": '<span class="chip new">✨ New option</span>',
        "unavailable": '<span class="chip exp">🔎 Not on Booking.com right now</span>'}
def name_cell(h, thumb=False):
    img = f'<img class="thumb" src="{h["img"]}" alt="{esc(h["name"])} building">' if (thumb and h["img"]) else ""
    return (f'<th scope="row"><div class="hname">{img}<div><span class="tag t-{h["status"]}">{h["tag"]}</span> '
            f'<a href="{h["url"]}" target="_blank" rel="noopener">{esc(h["name"])}</a><br>{CHIP.get(h["status"], "")}</div></div></th>')

GROUPS = [("📌 Your bookings", "booked"), ("🔎 Not on Booking.com right now", "unavailable"), ("✨ New options, ranked", "new")]
def group_rows(fn):
    out = []
    for label, st in GROUPS:
        rows = [h for h in H if h["status"] == st]
        if not rows: continue
        out.append(f'<tr class="grp"><td colspan="30">{label}</td></tr>')
        out += [fn(h) for h in rows]
    return "\n".join(out)
def sorted_rows(fn, key, reverse):
    have = [h for h in H if h.get(key) is not None]; miss = [h for h in H if h.get(key) is None]
    return "\n".join(fn(h) for h in sorted(have, key=lambda x: x[key], reverse=reverse) + miss)

def heat_cell(h):
    if h.get("hotel_confirmed_ac"):
        return '<td class="win"><span class="pill good">✅ Hotel confirmed AC works in winter</span></td>'
    r = h.get("heat_risk", "low")
    if r == "low": return '<td class="win"><span class="pill good">✅ Low</span></td>'
    if r == "unknown": return '<td><span class="pill">❔ Not checked</span></td>'
    return '<td class="warncell"><span class="pill warn">⚠️ Moderate</span></td>'
def bath_cell(h):
    b = h.get("bath")
    if b is None: return '<td><span class="sub">unknown</span></td>'
    return '<td class="win"><span class="num">🛁 Yes</span></td>' if b else '<td><span class="num">🚿 Shower only</span></td>'
def price_cell(h):
    if h.get("total_usd") is None:
        return f'<td><span class="num">{esc(h.get("price_label") or "—")}</span><span class="sub">{esc(h.get("price_note",""))}</span></td>'
    return cell(h, "total_usd", "min", f'${h["total_usd"]:,}', esc(h.get("price_note", "")))

# ---------- tables ----------
def verdict_row(h):
    cls = ' class="top"' if h.get("rank") == 1 else ""
    if h.get("total_usd") is not None: price = f'${h["total_usd"]:,}'
    elif h.get("score_price_usd") is not None: price = f'~${h["score_price_usd"]:,} (last seen)'
    else: price = h.get("price_label") or ""
    sp = h["score_parts"]
    brk = f'⭐{sp["reviews"]:g} 💰{sp["price"]:g} 🚆{sp["travel"]:g} 🛏️{sp["room"]:g} 🌡️{sp["heat"]:g} 🍜{sp["food"]:g} 🛁{sp["bath"]:g}'
    if h.get("total_usd") is None and h.get("score_price_usd") is None: brk += " · price unknown → half points"
    lab = ("🏆 Highest overall score · " if h["rank"] == 1 else "") + h.get("verdict_label", "")
    btn = {"booked": ("View 🔗", " alt"), "unavailable": ("Check 🔗", " alt")}.get(h["status"], ("Book 🔗", ""))
    room = f'{h.get("twin_ft2","?")} ft² · {"🛁" if h.get("bath") else "🚿"} · {price}'
    return (f'<tr{cls}><td class="rank">{h.get("rank","")}</td>{name_cell(h, True)}'
            + cell(h, "overall", "max", f'🏅 {h["overall"]:g}', brk) +
            f'<td><strong>{esc(lab)}</strong><span class="sub">{esc(h.get("verdict_text",""))}</span></td>'
            f'<td><span class="num">⭐ {h.get("rating","")}</span><span class="sub">{room}</span></td>'
            f'<td><a class="book{btn[1]}" href="{h["url"]}" target="_blank" rel="noopener">{btn[0]}</a></td></tr>')
t_verdict = "\n".join(verdict_row(h) for h in H)

t_facts = group_rows(lambda h: "<tr>" + name_cell(h)
    + cell(h, "rating", "max", f'⭐ {h.get("rating")}', f'{h.get("review_count",0):,} reviews')
    + cell(h, "twin_ft2", "max", f'{h.get("twin_ft2")} ft²', f'{esc(h.get("room_name",""))} · {round((h.get("twin_ft2") or 0)*0.0929)} m²')
    + bath_cell(h) + price_cell(h) + heat_cell(h) + "</tr>")

t_access = group_rows(lambda h: "<tr>" + name_cell(h)
    + cell(h, "walk_jr_min", "min", f'{h.get("walk_jr_min")} min', f'{esc(h.get("nearest_jr",""))} · {h.get("walk_jr_m","?")} m')
    + f'<td><span class="sub">{esc(h.get("other_stations",""))}</span></td>'
    + cell(h, "shinkansen_min", "min", f'~{h.get("shinkansen_min")} min', esc(h.get("shinkansen_route","")))
    + cell(h, "shinkansen_taxi_min", "min", f'{h.get("shinkansen_taxi_min")} min', "") + "</tr>")

def tt(h):
    out = [cell(h, "tt_total", "min", f'⏱️ {h["tt_total"]} min' if h["tt_total"] is not None else "", "all trips added up")]
    notes = h.get("train_note") or [""] * len(dests)
    for i in range(len(dests)):
        ic = "🚶" if (len(notes) > i and notes[i] == "walk") else "🚆"
        out.append(cell(h, ("train", i), "min", f'{ic} {getv(h, ("train", i))} min', "walk" if ic == "🚶" else ""))
        out.append(cell(h, ("taxi", i), "min", f'🚕 {getv(h, ("taxi", i))} min'))
    return "<tr>" + name_cell(h) + "".join(out) + "</tr>"
t_travel = sorted_rows(tt, "tt_total", False)
travel_head = ('<tr><th scope="col" rowspan="2">Hotel</th><th scope="col" rowspan="2">⏱️ Total score</th>'
               + "".join(f'<th scope="colgroup" colspan="2">{esc(d)}</th>' for d in dests) + "</tr><tr>"
               + "".join('<th scope="col">Train</th><th scope="col">Taxi</th>' for _ in dests) + "</tr>")

t_food = sorted_rows(lambda h: "<tr>" + name_cell(h)
    + cell(h, "fs_total", "max", f'🧮 {h["fs_total"]}', "places to eat + shops")
    + cell(h, "food", "max", f'{h.get("food")}', "restaurants, cafés, bars")
    + cell(h, "shops", "max", f'{h.get("shops")}', "shops")
    + cell(h, "konbini", "max", f'{h.get("konbini")}', f'konbini · {h.get("supermarkets","?")} supermarkets')
    + f'<td><span class="sub">🏬 {esc(h.get("big_shopping",""))}</span></td>'
    + f'<td><span class="sub">⭐ {esc(h.get("top_restaurants",""))}</span></td></tr>', "fs_total", True)

t_heat = group_rows(lambda h: "<tr>" + name_cell(h) + heat_cell(h)
    + f'<td><span class="sub">{"🏨 The hotel confirmed the AC works in winter. From reviews: " if h.get("hotel_confirmed_ac") else ""}{esc(h.get("heat_note",""))}</span></td></tr>')

t_scores = sorted_rows(lambda h: "<tr>" + name_cell(h)
    + cell(h, "rv_avg", "max", f'📊 {h["rv_avg"]:.2f}' if h["rv_avg"] is not None else "", "average of the 4 scores")
    + cell(h, "cleanliness", "max", f'{h.get("cleanliness")}') + cell(h, "comfort", "max", f'{h.get("comfort")}')
    + cell(h, "location", "max", f'{h.get("location")}') + cell(h, "value", "max", f'{h.get("value")}')
    + f'<td><span class="sub">👍 {esc(h.get("pros",""))}<br>👎 {esc(h.get("cons",""))}</span></td></tr>', "rv_avg", True)

t_out = "\n".join(f'<tr><th scope="row">{esc(r["name"])}</th><td>{esc(r["reason"])}</td></tr>' for r in D.get("ruled_out", []))

# ---------- map (hand-drawn SVG, no map tiles) ----------
PRESETS = {
 "tokyo_yamanote": [("Tokyo",35.6812,139.7671),("Yurakucho",35.6750,139.7630),("Shimbashi",35.6663,139.7583),("Hamamatsucho",35.6553,139.7570),("Tamachi",35.6457,139.7476),("Takanawa Gateway",35.6355,139.7407),("Shinagawa",35.6285,139.7388),("Osaki",35.6197,139.7286),("Gotanda",35.6262,139.7236),("Meguro",35.6340,139.7158),("Ebisu",35.6467,139.7101),("Shibuya",35.6580,139.7016),("Harajuku",35.6702,139.7027),("Yoyogi",35.6830,139.7020),("Shinjuku",35.6896,139.7006),("Shin-Okubo",35.7012,139.7000),("Takadanobaba",35.7127,139.7038),("Mejiro",35.7212,139.7065),("Ikebukuro",35.7295,139.7109),("Otsuka",35.7318,139.7286),("Sugamo",35.7334,139.7393),("Komagome",35.7365,139.7470),("Tabata",35.7381,139.7608),("Nishi-Nippori",35.7320,139.7668),("Nippori",35.7278,139.7710),("Uguisudani",35.7213,139.7781),("Ueno",35.7138,139.7773),("Okachimachi",35.7075,139.7748),("Akihabara",35.6984,139.7731),("Kanda",35.6918,139.7709)],
}
stations = [tuple(s) for s in D.get("stations", [])] or PRESETS.get(D.get("rail_preset", ""), [])
def svgmap(pad=28, r=10):
    pts = [(h["lat"], h["lon"]) for h in H if h.get("lat")] + [(a, b) for _, a, b in stations]
    if not pts: return ""
    la0, la1 = min(p[0] for p in pts) - .004, max(p[0] for p in pts) + .004
    lo0, lo1 = min(p[1] for p in pts) - .004, max(p[1] for p in pts) + .004
    c = math.cos(math.radians((la0 + la1) / 2)); kmw = (lo1 - lo0) * 111.32 * c; kmh = (la1 - la0) * 110.57
    ppk = 520 / max(kmw, kmh * 0.75)
    P = lambda la, lo: ((lo - lo0) * 111.32 * c * ppk + pad, (la1 - la) * 110.57 * ppk + pad)
    W, Hh = kmw * ppk + 2 * pad, kmh * ppk + 2 * pad
    o = [f'<svg viewBox="0 0 {W:.0f} {Hh:.0f}" role="img" aria-label="Hotel locations" xmlns="http://www.w3.org/2000/svg"><rect width="{W:.0f}" height="{Hh:.0f}" class="m-bg"/>']
    if stations:
        loop = D.get("rail_preset", "").endswith(("yamanote", "loop"))
        tagname = "polygon" if loop else "polyline"
        o.append(f'<{tagname} class="m-line" points="' + " ".join(f"{P(a,b)[0]:.1f},{P(a,b)[1]:.1f}" for _, a, b in stations) + '"/>')
        labels = set(D.get("station_labels", [d for d in dests]))
        for n, a, b in stations:
            x, y = P(a, b); big = n in labels
            o.append(f'<circle class="m-stn{" big" if big else ""}" cx="{x:.1f}" cy="{y:.1f}" r="{5 if big else 3}"/>')
            if big: o.append(f'<text class="m-stn-l" x="{x+9:.1f}" y="{y+4:.1f}">{esc(n)}</text>')
    for h in H:
        if not h.get("lat"): continue
        x, y = P(h["lat"], h["lon"])
        o.append(f'<g class="m-h {h["status"]}"><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}"/><text x="{x:.1f}" y="{y+r*0.36:.1f}" text-anchor="middle" font-size="{r*1.05:.0f}">{h["tag"]}</text></g>')
    o.append("</svg>"); return "".join(o)
mapsvg = svgmap()
legend = "".join(f'<li><span class="dot {h["status"]}">{h["tag"]}</span>{esc(h["name"])}</li>' for h in H)
hr = lambda *c: "<tr>" + "".join(f'<th scope="col">{x}</th>' for x in c) + "</tr>"

eyebrow = f'🗾 {esc(trip.get("city","Japan"))} · {trip["checkin"]} → {trip["checkout"]} · {trip.get("adults",2)} adults · {esc(trip.get("room","twin"))} room' + (f' · under ${trip["budget_usd_total"]:,}' if trip.get("budget_usd_total") else "")
lede = esc(D.get("intro", "Hotels compared on price, room size, bathtub, station access, travel times, food and shops nearby, and what guests say about winter heating and AC."))

LBL = {"reviews":"⭐ review average","price":"💰 total price","travel":"🚆 travel total","room":"🛏️ room size","heat":"🌡️ no hot-room risk","food":"🍜 food & shops","bath":"🛁 bathtub"}
WLINE = esc(" · ".join(f"{LBL[k]} {w}" for k, w in WEIGHTS.items()))
CSS = (pathlib.Path(__file__).with_name("page.css")).read_text()
page = f"""<title>{esc(D.get("title","Japan Hotel Shortlist"))}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@500;700&family=Source+Sans+3:wght@400;600;700&display=swap">
<style>{CSS}</style>
<div class="wrap">
  <header>
    <div class="eyebrow">{eyebrow}</div>
    <h1>{esc(D.get("title","Japan Hotel Shortlist"))}</h1>
    <p class="lede">{lede} Data collected {esc(trip.get("collected",""))}.</p>
    <div class="key"><span><i class="sw"></i>🥇 Green = best in that column</span><span>📌 Booked</span><span>🔎 Not on Booking.com</span><span>✨ New option</span><span>🛁 Bathtub</span><span>Click a hotel name to open it with your dates</span></div>
  </header>
  <section><h2>🏆 All hotels ranked</h2>
    <p class="lede">Ranked by a 🏅 <strong>Overall score</strong> out of 100: {WLINE}. Each number part is scaled from the worst hotel here (0) to the best (full points). Yes/no parts (no hot-room risk, bathtub) give full points or none. Unknown values get half points. Hotels that failed the heat check are removed before scoring.</p>
    <div class="table-wrap"><table><thead>{hr("#","Hotel","🏅 Overall score","Why","Rating · room · total","")}</thead><tbody>{t_verdict}</tbody></table></div></section>
  <section><h2>📋 Key facts</h2>
    <div class="table-wrap"><table><thead>{hr("Hotel","⭐ Rating","🛏️ Room","🛁 Bathtub","💰 Total incl. VAT","🌡️ Hot-room risk")}</thead><tbody>{t_facts}</tbody></table></div></section>
  <section><h2>🚉 Station access</h2>
    <p class="lede">{esc(trip.get("arrival",""))}</p>
    <div class="table-wrap"><table><thead>{hr("Hotel", esc(D.get("station_label","🚶 Walk to JR")), "🚇 Other stations", esc(D.get("arrival_label","🚄 Arrival → hotel")), "🚕 Or by taxi")}</thead><tbody>{t_access}</tbody></table></div></section>
  <section><h2>🚆 Travel times</h2>
    <p class="lede">Door to door from Google Maps. <strong>Total score</strong> adds up every train and taxi time. Lower is better, sorted best first.</p>
    <div class="table-wrap"><table><thead>{travel_head}</thead><tbody>{t_travel}</tbody></table></div></section>
  <section><h2>🍜 Restaurants & shops nearby</h2>
    <p class="lede">The counts are places within 500 m (about a 6 min walk) from OpenStreetMap. The ⭐ picks are the highest-rated restaurants Google Maps shows. <strong>Total score</strong> = places to eat + shops. Sorted most first.</p>
    <div class="table-wrap"><table><thead>{hr("Hotel","🧮 Total score","🍽️ Places to eat","🛍️ Shops","🏪 Konbini","🏬 Big shopping","⭐ Top-rated restaurants")}</thead><tbody>{t_food}</tbody></table></div></section>
  <section><h2>🌡️ Heating & AC in winter</h2>
    <p class="lede">From English reviews of winter stays plus the lowest-scored reviews. ✅ Low = nobody said the room got too hot. ⚠️ Moderate = guests struggled to control the temperature.</p>
    <div class="table-wrap"><table><thead>{hr("Hotel","Risk","What guests said")}</thead><tbody>{t_heat}</tbody></table></div></section>
  <section><h2>⭐ Review scores</h2>
    <p class="lede">Booking.com category scores. <strong>Total score</strong> = average of cleanliness, comfort, location and value. Sorted best first.</p>
    <div class="table-wrap"><table><thead>{hr("Hotel","📊 Total score","🧼 Clean","😴 Comfort","📍 Location","💵 Value","Liked / disliked")}</thead><tbody>{t_scores}</tbody></table></div></section>
  {"<section><h2>🗺️ Where they are</h2><figure class='map'>" + mapsvg + "<figcaption>Drawn from coordinates: hotel positions from Google Maps, station positions approximate.</figcaption></figure><ul class='legend'>" + legend + "</ul></section>" if mapsvg else ""}
  {"<section><h2>❌ Checked and ruled out</h2><div class='table-wrap'><table><thead>" + hr("Hotel","Why it's out") + "</thead><tbody>" + t_out + "</tbody></table></div></section>" if t_out else ""}
  <section class="notes"><h3>Notes</h3><ul>
    <li>Booking.com prices exclude Japan's 10% consumption tax (added here) and the local accommodation tax paid at the hotel. Prices change.</li>
    <li>Photos are from each hotel's Booking.com listing. Restaurant and shop counts from OpenStreetMap are approximate.</li>
    {"".join(f"<li>{esc(n)}</li>" for n in D.get("notes", []))}
  </ul></section>
</div>
"""
OUT.write_text(page)
print("written", OUT, len(page) // 1024, "KB")
