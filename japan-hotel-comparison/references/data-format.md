# data.json format (input to scripts/build_page.py)

`assets/example_tokyo.json` is a complete real example (12 Tokyo hotels, Dec 2026). Copy it
and replace the values. Photo paths are relative to the JSON file. Any optional field can
be left out, and the page shows "—" for it.

```jsonc
{
  "title": "Tokyo Hotel Shortlist",            // 2–4 word name for the page
  "intro": "One-sentence description shown under the title",   // optional
  "trip": {
    "city": "Tokyo", "checkin": "2026-12-01", "checkout": "2026-12-06", "nights": 5,
    "adults": 2, "room": "twin", "budget_usd_total": 1200,
    "arrival": "Tōkaidō Shinkansen from Osaka (stops Shinagawa, ends Tokyo)",  // shown above station table
    "collected": "2026-10-12"
  },
  "destinations": ["Shibuya", "Tokyo Station", "Ikebukuro"],   // order matches train[]/taxi[]
  "rail_preset": "tokyo_yamanote",       // optional; only Tokyo's loop is built in
  "station_label": "🚶 Walk to main station",          // optional column title (default "🚶 Walk to JR")
  "arrival_label": "🚄 Hotel → Shin-Osaka (departure day)",   // optional column title (default "🚄 Arrival → hotel")
  "stations": [["Osaka", 34.7025, 135.4959], ...],  // optional, overrides preset (name, lat, lon); drawn in order
  "station_labels": ["Shibuya", "Tokyo"],           // optional; which stations get text labels
  "places": [{"name": "Dotonbori", "lat": 34.6687, "lon": 135.5013}],   // optional; destinations, drawn as ◆ on the map
  "basemap": { ... },                                // written by scripts/fetch_basemap.py (zoom + tile files)
  "hotels": [ { ...hotel... } ],
  "ruled_out": [ {"name": "Tokyo Prince Hotel (8.5)", "reason": "🌡️ ...short quote..."} ],
  "notes": ["Extra footnote lines"]
}
```

## Hotel fields

| Field | Example | Notes |
|---|---|---|
| `id` | `"tokyu"` | short unique key |
| `name` | `"Tokyu Stay Takanawa"` | |
| `status` | `"booked"` · `"new"` · `"unavailable"` | unavailable = not bookable on Booking.com right now |
| `score_price_usd` | `965` | optional: last price seen, used for scoring when `total_usd` is null (e.g. a booked hotel that has since sold out) |
| `verdict_label` | `"🏆 Best overall"` | short label in the ranked table |
| `verdict_text` | `"8.9, 248 ft², bathtub…"` | one or two sentences |
| `booking_slug` | `"villa-fontaine-tamachi"` | from `booking.com/hotel/jp/<slug>.html`; builds a link with the trip dates |
| `url` | `"https://www.expedia.com/..."` | optional; overrides the Booking link (e.g. for unavailable hotels) |
| `photo` | `"photos/vf-tamachi.jpg"` | building exterior, ~500 px wide |
| `lat`, `lon` | `35.64286, 139.74492` | from the Google Maps URL |
| `rating`, `review_count` | `8.7`, `2162` | Booking.com |
| `cleanliness`, `comfort`, `location`, `value` | `9.1` … | Booking.com category scores |
| `room_name`, `twin_ft2`, `bath` | `"Standard Twin"`, `205`, `true` | bath: true / false / null (unknown) |
| `total_usd` | `902` | whole stay **including** 10% VAT; `null` if not bookable |
| `price_label`, `price_note` | `"📌 Your booking"`, `"free cancellation until Dec 20"` | label is used when total_usd is null |
| `heat_risk` | `"low"` · `"mod"` · `"unknown"` | |
| `heat_note` | short paraphrase / quote of what guests said | |
| `hotel_confirmed_ac` | `true` | set only when the user says the hotel confirmed it |
| `nearest_jr`, `walk_jr_min`, `walk_jr_m` | `"Tamachi"`, `8`, `550` | |
| `other_stations` | `"Mita subway (Asakusa, Mita)"` | |
| `shinkansen_route`, `shinkansen_min`, `shinkansen_taxi_min` | `"Shinagawa → JR 1 stop"`, `13`, `8` | or whatever the arrival point is |
| `train`, `taxi` | `[27,17,40]`, `[20,21,31]` | minutes, one per destination |
| `train_note` | `["","","walk"]` | `"walk"` shows 🚶 instead of 🚆 |
| `food`, `shops`, `konbini`, `supermarkets` | `117, 57, 22, 4` | filled by `scripts/osm_counts.py` |
| `big_shopping`, `top_restaurants` | `"Tamachi station shops"`, `"KASA 4.2 · …"` | |
| `pros`, `cons` | short phrases | from reviews |

## Computed by the script

- **🏅 Overall score and rank**: `scripts/scoring.py` (weights in `WEIGHTS`). Hotels are sorted by it, and the rank number is also the map marker.

- **Travel total score**: sum of all train and taxi minutes (lower is better). The travel table is sorted by it.
- **Food & shops total score**: `food + shops` (konbini are already counted in shops). Sorted descending.
- **Review total score**: average of the 4 category scores. Sorted descending.
- **🥇 Best cell**: the max or min in each numeric column across all hotels, highlighted green.
