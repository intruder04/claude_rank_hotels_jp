---
name: japan-hotel-comparison
description: Research and compare hotels in Japan (Tokyo, Osaka, Kyoto or anywhere in Japan) on Booking.com, Google Maps and Tabelog, then publish one comparison page with color-coded tables. It covers twin/double room size and bathtub, total price with Japan's 10% tax, walking time to the nearest JR station, train and taxi times to the places the traveler cares about, Shinkansen arrival, restaurants and shops nearby, review scores, and whether winter reviews complain the room gets too hot (central heating, AC you can't cool). Use this whenever someone wants to compare, shortlist, choose or double-check hotels in Japan, whether they've already booked some and want them compared, or want the best hotels in a Japanese city or neighborhood for their dates, even if they don't say "compare". Japan only. For hotels outside Japan, say this skill doesn't cover them.
---

# Japan hotel comparison

This skill turns a long, careful hotel hunt into a repeatable process. The first version
came from a real trip: a couple choosing Tokyo hotels for December. They cared about a
twin room, JR access, a budget, and above all **not being stuck in an overheated room**.
Many Japanese hotels switch the building to heating-only in winter, so you can't cool
your room. Everything below exists because it mattered on that trip. Adjust the details
for each new traveler, but keep the rigor.

## 0. Check it's Japan

The method depends on things specific to Japan: JR lines, the Shinkansen, konbini,
Japan's 10% consumption tax, and Booking.com's `/hotel/jp/` pages. If the hotels or area
are outside Japan, say so and stop.

## 1. Ask before researching

Ask in one short message, and offer sensible defaults so the user can just say "yes":

1. **Mode**:
   - **A. Compare hotels I've booked or picked.** Get the exact hotel names.
   - **B. Find the top hotels in an area.** Which city, and which neighborhood or station? It can be "anywhere in Tokyo".
   - Both modes can be combined: their bookings, plus the best alternatives.
2. **Dates and guests**: check-in, check-out, number of adults (and children with ages).
3. **Room**: twin (two beds) or double, and the minimum size if they care.
4. **Budget**: total for the whole stay, including tax.
5. **Where they'll go**: the 2–4 places they'll visit most (e.g. Shibuya, Tokyo Station, Ikebukuro), and how they arrive (Shinkansen from where, or which airport). Don't add airport travel times unless they ask. One traveler said "we'll take a taxi" and didn't want them.
6. **Areas to avoid**: any neighborhoods they don't want to stay in, and whether a hotel's look matters to them. Show building photos early so they can veto hotels before the deep research.
7. **Priorities**: walk to a **JR** station (default: under ~10 min, and JR beats subway), heating and AC in their season, bathtub (a plus, not a must, unless they say so), minimum rating (default 8.5+ for new options).

Things travelers mentioned later, which you can ask up front:
- Do they want photos of the buildings? Downloading needs their OK.
- Should restaurant and shop density count?
- Which booking site? Default Booking.com. A hotel can be missing there and still be on Expedia.

## 2. Research

`references/browser-snippets.md` has tested, copy-paste code for every step below.
Read it before starting the browser work. Use whatever browser tool the session has
(the built-in browser, or Claude in Chrome).

**Mode B: find candidates.** Run a city-wide Booking.com search: hotels only, twin beds,
8+ rating, nightly price under budget ÷ nights ÷ 1.1. The results page only returns ~20
hotels, so split it into price bands (snippet 1). Also run quick searches around the
user's key stations. The city-wide pass still misses some hotels, and on the first trip
two of the best only turned up in the station searches. Then filter:
- At least ~300 reviews.
- Total with VAT under budget.
- Real hotel rooms, not capsules, dorms or apartments.
- Not at an airport or outside the city.
- Near JR. Subway-only areas count against a hotel.

**For every hotel (both modes):**

1. **Rooms and price** (snippet 2): twin rooms for the exact dates, size in ft², bathtub (from the room's own facility data, and if that says no, from the room photos' descriptions; it's often missing), cheapest total, and free-cancellation option. Multiply by 1.1 for VAT. If no twin room is listed, it's sold out on Booking.com for those dates. Say that plainly, and keep the hotel in the comparison if the user wants it. Mark it "not on Booking.com right now", because it may be on Expedia or elsewhere.
2. **Winter heat check** (snippet 3): scan every English review from the stay's season (Dec–Feb for winter), then the ~140 lowest-scored reviews from any season. Read each match yourself:
   - **Rule out** hotels where guests say the AC is turned off or heating-only in winter, the minimum is 25°C, the heating turns itself on, "too hot at night", the window can't open when the room is hot, or the temperature is "centrally controlled" and hot.
   - **Not a problem**: hot water, summer corridors, or a single vague mention.
   - **A good sign**: "individual aircon/heating controls", or windows that open.

   Record a short quote for the ruled-out table, because users trust the guest's own words. If the user says a hotel confirmed the AC works in winter, mark it (`hotel_confirmed_ac`) and keep the review notes beside it.
3. **Station access** (Google Maps, snippet 5): walking time to the nearest JR station, plus the nearest subway. Some central areas have no JR within walking distance; Osaka's Shinsaibashi is 20+ min from JR Namba. There, the main subway line (e.g. Midosuji) is the station that matters. Show it as the main station (`station_label`), list the JR distance next to it, and tell the user. Check suspicious results: big stations have one map point, often far from the closest gate.
4. **Travel times**: fastest train and taxi (driving) time from the hotel to each destination, and from the arrival station (Shinkansen stop) to the hotel. Always measure at **10:00 Japan time on a weekday** (snippet 5), never "leave now", and re-measure booked hotels the same way so every hotel is compared at the same hour. Say on the page which time was used.
5. **Food and shops**: once you have coordinates, run `scripts/osm_counts.py data.json` for counts within 500 m. Also check that the nearest konbini is a short walk on Google Maps, because OpenStreetMap counts can be out of date or sit across a canal or highway. Add the 3 best-rated everyday restaurants near the hotel's station as "top picks" (snippet 6). Use **Tabelog's English site first**, because it is Japan's main restaurant review site. Fall back to Google Maps only if Tabelog shows a bot check or fails, and set `restaurant_source` to match. Don't present a site's list length as a count.
6. **Review scores**: Booking.com category scores, plus a few pros and cons from the reviews.
7. **Photo**: one building exterior per hotel from its Booking.com gallery (snippet 4), only after the user agrees to downloads. Say where the photos came from.

**Things not to do:**
- Don't get around bot checks or CAPTCHAs. If Tabelog or any site shows one, switch to the fallback (Google Maps for restaurants), tell the user and move on.
- Don't screenshot Google Maps for the page, because the map tiles are copyrighted. The build script draws its own map from coordinates.
- Don't book anything or enter personal details.

## 3. Rank

First remove anything that fails a dealbreaker:
- A hot-room or AC problem in the user's season.
- Over budget.
- Too far from JR.
- Anything the user rules out. Travelers know things the data misses: one removed a hotel because there was "not even a konbini nearby", even though OpenStreetMap listed some within 500 m.

Then rank **every remaining hotel together, including the user's bookings**, by the
🏅 **Overall score** (0–100). `scripts/build_page.py` computes it with `scripts/scoring.py`,
so the ranking can be traced and repeated:

| Part | Points | How |
|---|---|---|
| ⭐ Review average (clean, comfort, location, value) | 25 | scaled worst → best among these hotels |
| 💰 Total price incl. VAT | 20 | cheapest gets full points |
| 🚆 Travel total (all train + taxi times) | 20 | lowest total gets full points |
| 🛏️ Room size | 15 | biggest gets full points |
| 🌡️ No hot-room risk (or hotel confirmed AC) | 10 | yes / no |
| 🍜 Food & shops within 500 m | 5 | most gets full points |
| 🛁 Bathtub | 5 | yes / no |

Unknown values get half points, for example a hotel with no current price. When a booked
hotel has sold out since the user booked it, put the last price you saw in
`score_price_usd`, so price still counts. Show the score and its breakdown in the ranked
table, and say plainly when a booked hotel scores low. If the user wants different
priorities, change `WEIGHTS` in `scripts/scoring.py` and rebuild.

Write one sentence per hotel in `verdict_text`. If the user corrects a fact ("it does
have a bathtub", "I didn't book that one"), fix it right away, rebuild, and say whether the
rank changed.

## 4. Build and publish the page

1. Put the data in `data.json` (format: `references/data-format.md`; real example: `assets/example_tokyo.json`) and the photos next to it.
2. `python3 scripts/osm_counts.py data.json` fills in food and shop counts. Add the traveler's destinations as `places` (name, lat, lon) so they show as ◆ on the map, then run `python3 scripts/fetch_basemap.py data.json`. It downloads ≤30 OpenStreetMap tiles for a real background map, which the page dims to gray, or inverts for dark theme, so it stays calm.
3. `python3 scripts/build_page.py data.json out.html` builds one self-contained page with the photos embedded. It contains:
   - A ranked verdict table.
   - Key facts: rating, room, 🛁, total price, 🌡️ heat risk.
   - Station access.
   - Travel times with a total score.
   - Restaurants and shops with a total score.
   - Heating and AC notes.
   - Review scores with an average.
   - The map.
   - The ruled-out table.

   🥇 green cells mark the best value in each column. Booked, unavailable and new hotels each get their own chip.
4. Publish it as an artifact if the session can (load the artifact skill first), otherwise send the HTML file. If the page might be shared, mention that the photos come from Booking.com.

## 5. Report back

Lead with the answer: the top pick and why, how the user's bookings rank, and what was
ruled out and why. Also be clear about the limits:
- The search can miss hotels.
- Prices are from today and will change.
- Restaurant counts are approximate.
- Any station times you estimated rather than measured.
