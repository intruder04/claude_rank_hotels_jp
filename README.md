# 🗾 Japan Hotel Comparison: a Claude skill

A [Claude](https://claude.ai) skill that researches and ranks **hotels in Japan** (Tokyo,
Osaka, Kyoto or anywhere in Japan) and builds one color-coded comparison page, so you can
see at a glance which hotel fits your trip.

It was built during a real trip-planning session and covers the things that are easy to
miss when booking in Japan:

- 🌡️ **Winter heating trap.** Many Japanese hotels switch the building to heating-only in winter, so you can't cool your room. The skill reads every winter review and the lowest-scored reviews, and rules out hotels where guests say the room got too hot.
- 🛏️ **Real twin room size** in ft² and m², and whether there's a 🛁 **bathtub**. It checks the room's facility data *and* the room photos, because listings often miss the tub.
- 🚉 **Walk to the nearest JR station**, plus the main subway when there's no JR nearby, and how to get from the Shinkansen to the hotel.
- 🚆🚕 **Train and taxi times** to the places you'll actually go, added up into a travel score.
- 🍜 **Restaurants, shops and konbini** within a 6-minute walk (OpenStreetMap), plus the top-rated everyday restaurants nearby (Tabelog first, Google Maps as a fallback).
- 💰 **Real total price** with Japan's 10% consumption tax, compared against your budget.
- ⭐ **Booking.com review scores**, with a short pros/cons summary.
- 🏅 **Overall score (0–100)** that ranks every hotel the same way, including ones you've already booked.

## What you get

A single self-contained HTML page with:
- A ranked list.
- Key-facts, station, travel-time, food & shops, heating and review-score tables.
- 🥇 Green highlighting for the best value in every column.
- Building photos, a map (a calm OpenStreetMap background with your hotels, train line and destinations) and booking links with your dates.

See [`examples/tokyo-example.html`](examples/tokyo-example.html) (download it and open it in a browser). It was built from
[`assets/example_tokyo.json`](japan-hotel-comparison/assets/example_tokyo.json) without photos.

## How it works

When you ask Claude to compare or find hotels in Japan, the skill first asks:

1. **Compare hotels you've booked**, or **find the top hotels in an area** (which city or neighborhood?)
2. Dates, guests, twin or double room, total budget
3. The places you'll visit most, and how you arrive (e.g. Shinkansen from Osaka)
4. Areas to avoid, and priorities: JR walking distance, heating and AC, bathtub, minimum rating

Then it researches with a browser (Booking.com, Google Maps and Tabelog), scores the hotels and publishes the page.
It works **only for hotels in Japan**.

## Install

**Claude.ai / Claude desktop app:** download [`japan-hotel-comparison.skill`](japan-hotel-comparison.skill),
open it in Claude and click **Save skill**. Or go to *Settings → Capabilities → Skills* and upload the file.

**Claude Code:** copy the skill folder into your skills directory:

```bash
git clone https://github.com/intruder04/claude_rank_hotels_jp.git
cp -R claude_rank_hotels_jp/japan-hotel-comparison ~/.claude/skills/
```

Then just ask, for example:

> Compare the hotels I booked in Tokyo for Dec 1–6: Hotel A and Hotel B. We'll mostly go to Shibuya and Asakusa.

> Find the 5 best hotels near Kyoto Station for March 10–14, 2 adults, twin room, under $900 total.

### Requirements

- A Claude environment with **browser access** (Claude in Chrome, the desktop app's built-in browser, or similar). The research happens on Booking.com, Google Maps and Tabelog.
- **Python 3** for the helper scripts: page builder, OpenStreetMap counter and map downloader. They use only the standard library.

## What's inside

```
japan-hotel-comparison/
├── SKILL.md                     # the workflow Claude follows
├── references/
│   ├── browser-snippets.md      # tested JavaScript for Booking.com search, reviews, bathtubs, Google Maps, Tabelog
│   └── data-format.md           # the data.json format the page builder reads
├── scripts/
│   ├── build_page.py            # data.json → comparison page (HTML)
│   ├── scoring.py               # overall score weights (edit WEIGHTS to change priorities)
│   ├── osm_counts.py            # restaurants / shops / konbini within 500 m
│   ├── fetch_basemap.py         # downloads a few OpenStreetMap tiles for the background map
│   └── page.css
└── assets/example_tokyo.json    # real example data (anonymized)
```

### Overall score

| Part | Points |
|---|---|
| ⭐ Review average (clean, comfort, location, value) | 25 |
| 💰 Total price | 20 |
| 🚆 Travel time total | 20 |
| 🛏️ Room size | 15 |
| 🌡️ No hot-room risk | 10 |
| 🍜 Food & shops nearby | 5 |
| 🛁 Bathtub | 5 |

Number parts are scaled from the worst hotel in the comparison (0) to the best (full points).
Hotels that fail the winter-heat check are removed before scoring. Change the weights in
[`scripts/scoring.py`](japan-hotel-comparison/scripts/scoring.py).

## Limits

- **Search coverage:** Booking.com limits search results, so a city-wide search can miss a few hotels.
- **Changing data:** prices, availability and reviews change all the time. The page shows when the data was collected.
- **Approximate counts:** OpenStreetMap restaurant and shop counts are approximate. The skill also checks that the nearest konbini is a short walk.
- **No CAPTCHAs:** the skill won't try to get past bot checks. If Tabelog shows one, it uses Google Maps for restaurants instead.
- **Your own photos only:** hotel photos come from Booking.com listings and are only downloaded for your own page.

## License

[MIT](LICENSE)
