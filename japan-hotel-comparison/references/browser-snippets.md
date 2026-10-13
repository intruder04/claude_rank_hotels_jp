# Browser snippets (tested on Booking.com and Google Maps, Oct 2026)

Run these with the browser tool's "execute JavaScript in page" action while a
`booking.com` (or `google.com/maps`) tab is open. Page-level helpers are lost on every
navigation, so re-define them after you navigate. Most browser tools time out a single
script after ~45 s: for long loops, start the work as a background promise stored on
`window`, return immediately, then poll.

Sites change their markup. If a selector returns nothing, take one screenshot, find the
new selector, and adapt — don't retry the same failing call.

## Contents
1. Booking.com search across a whole city (price-band splitting)
2. Hotel page: twin rooms, size, price, cancellation, bathtub
3. Review scan for winter heat / AC complaints
4. Photo gallery IDs (pick a building exterior)
5. Google Maps: walking, transit, taxi times and coordinates
6. Google Maps: top-rated restaurants near a point

---

## 1. Whole-city search (price-band splitting)

Booking.com's server-rendered search page returns only ~20 cards no matter the
`offset`, so paging doesn't work. Split by nightly price bands instead and recurse
until each band's count fits on one page. `ht_id=204` = hotels only, `tdb=2` = twin
beds, `review_score=80` = 8+.

```js
window.__st = {all: new Map(), log: [], done: false};
const CI='2026-12-01', CO='2026-12-06', ADULTS=2, CITY='Tokyo';   // ← fill in
const mk=(lo,hi,rs,ord='review_score_and_price')=>`/searchresults.html?ss=${encodeURIComponent(CITY)}&dest_type=city&checkin=${CI}&checkout=${CO}&group_adults=${ADULTS}&no_rooms=1&group_children=0&nflt=${encodeURIComponent(`ht_id=204;review_score=${rs};tdb=2;price=USD-${lo}-${hi}-1`)}&order=${ord}&lang=en-us&selected_currency=USD`;
const grab=async(lo,hi,rs,depth=0)=>{const S=window.__st; const h=await (await fetch(mk(lo,hi,rs))).text(); const d=new DOMParser().parseFromString(h,'text/html');
 const cnt=parseInt((((d.querySelector('h1')||{}).textContent||'').replace(/,/g,'').match(/(\d+) propert/)||[0,'0'])[1]);
 const cards=[...d.querySelectorAll('[data-testid="property-card"]')]; S.log.push(`${rs} $${lo}-${hi}: ${cnt} (got ${cards.length})`);
 for(const c of cards){const g=s=>((c.querySelector(s)||{}).textContent||'').replace(/\s+/g,' ').trim(); const sc=g('[data-testid="review-score"]');
  const slug=((c.querySelector('a[data-testid="title-link"]')||{}).href||'').split('?')[0].split('/').pop();
  const p=parseInt((g('[data-testid="price-and-discounted-price"]').match(/[\d,]+/)||['0'])[0].replace(/,/g,''));
  S.all.set(slug,{t:g('[data-testid="title"]'),score:parseFloat((sc.match(/[\d.]+/)||['0'])[0]),n:parseInt((sc.match(/([\d,]+) reviews?/)||['','0'])[1].replace(/,/g,'')),dist:g('[data-testid="distance"]'),p,unit:g('[data-testid="recommended-units"]').slice(0,70),slug});}
 if(cnt>cards.length && hi-lo>=4 && depth<7){const mid=Math.floor((lo+hi)/2); await grab(lo,mid,rs,depth+1); await grab(mid,hi,rs,depth+1);}
};
const MAXN = 220;   // ← max nightly price before tax = budget / nights / 1.1, rounded up
window.__job=(async()=>{await grab(0,MAXN,90); await grab(0,MAXN,80); window.__st.done=true;})(); 'started'
```
Poll with `await new Promise(r=>setTimeout(r,40000)); JSON.stringify({done:__st.done,n:__st.all.size})`.

`p` on the card is the **nightly** price before tax. Band counts can exceed 20 even at
$2 wide; for those, re-fetch with other `order=` values (`bayesian_review_score`,
`price`, `popularity`) to pick up stragglers. Even so, some hotels get missed. Keep
any good hotel you already found by other means (searches around specific stations)
in the pool.

Search around one station instead (useful for a first pass or a fixed area):
`ss=Shinagawa+Station` with `distance=1000` added to `nflt`.

## 2. Hotel page: twin rooms, bathtub, price

The room table's short facility list is unreliable for bathtubs. Each room's full
facility list is in the page's embedded data as
`"CategorizedFacilitiesForAllRooms","roomId":<id>` → `"BATHROOM_PRIVATE"` →
`SimpleFacility:5` (= "Bath"). `SimpleFacility:4` is "Shower".

```js
window.bathCheck=async(slug)=>{const h=await (await fetch(`/hotel/jp/${slug}.html?checkin=${CI}&checkout=${CO}&group_adults=${ADULTS}&no_rooms=1&group_children=0&lang=en-us&selected_currency=USD`)).text();
 const bath={}; const re=/"CategorizedFacilitiesForAllRooms","roomId":(\d+)/g; let m; const idx=[]; while((m=re.exec(h))) idx.push([m[1],m.index]);
 idx.forEach(([id,i],k)=>{const seg=h.slice(i,k+1<idx.length?idx[k+1][1]:i+6000); bath[id]=/"BATHROOM_PRIVATE","facilities":\[[^\]]*SimpleFacility:5"/.test(seg);});
 const d=new DOMParser().parseFromString(h,'text/html'); const rooms=[]; let cur=null;
 for(const r of d.querySelectorAll('.hprt-table tbody tr')){const a=r.querySelector('a.hprt-roomtype-link'); const txt=r.textContent.replace(/\s+/g,' ');
  if(a){cur={id:a.getAttribute('data-room-id'),name:a.textContent.trim(),twin:/twin/i.test(txt),ft:+((txt.match(/([\d,]+) feet²/)||['','0'])[1].replace(/,/g,'')),bath:null,offers:[]}; cur.bath=bath[cur.id]??null; rooms.push(cur);}
  if(cur){const p=txt.match(/Current price \$([\d,]+)|Price \$([\d,]+)/); if(p) cur.offers.push({v:+(p[1]||p[2]).replace(/,/g,''),fc:/Free cancellation/.test(txt)});}}
 const t=h.replace(/<[^>]+>/g,' ').replace(/\s+/g,' '); const g=re=>(t.match(re)||['',''])[1];
 return {slug, rating:g(/Rated: [A-Za-z ]+?([\d.]+ – based on [\d,]+) reviews/),
  cats:['Cleanliness','Comfort','Location','Value for money'].map(c=>g(new RegExp(c+', ([\\d.]+), Average'))).join('/'),
  freeCancelUntil:[...new Set([...t.matchAll(/Free cancellation before ([A-Za-z]+ \d+), \d{4}/g)].map(m=>m[1]))].join(';'),
  twins:rooms.filter(r=>r.twin&&!/single|family|quad|triple|extra/i.test(r.name)).map(r=>({n:r.name,ft:r.ft,bath:r.bath,min:Math.min(...r.offers.map(o=>o.v)),minFreeCancel:Math.min(...r.offers.filter(o=>o.fc).map(o=>o.v))}))};};
```
`min` is the **total for the stay before 10% VAT**. Multiply by 1.1 for the
comparison. If a twin room is missing from the result, it's sold out for those dates.
Say so in the page, and don't guess a price.

The facility data often misses bathtubs. Hotels in Japan usually have a tub, and three
hotels in a row were listed without one when they had one. So when a room shows
`bath: false` or `null`, **check the room photos**. Each gallery photo has an
auto-generated description and the rooms it belongs to:

```js
const h=await (await fetch('/hotel/jp/<slug>.html?lang=en-us')).text();
[...h.matchAll(/alt: "([^"]*)"[^}]*?associated_rooms: \[([^\]]*)\]/g)]
  .filter(m=>/\btub\b|bathtub|bath tub/i.test(m[1])).map(m=>m[1].slice(0,70)+' → rooms '+m[2].replace(/\s+/g,''))
```
A match like "a bathroom with a toilet and a sink and a tub", tied to the twin room's ID,
counts as a bathtub. If nothing matches, look at the bathroom photos yourself before
writing "no bathtub". If the user tells you otherwise, trust the user.

## 3. Review scan (winter heat / AC)

Open `https://www.booking.com/hotel/jp/<slug>.html?lang=en-us#tab-reviews`. The hash
opens the reviews panel. The panel slides in and loads slowly, and if you scan too early
you get "n: 1". So wait for cards before each pass, and read `textContent` rather than
`innerText`, which is empty while the panel is still sliding in. Set the selects with the
native setter so React notices:

```js
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
window.setSel=async(n,v)=>{const s=document.querySelector(`select[name="${n}"]`); if(!s) return; Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(s,v); s.dispatchEvent(new Event('change',{bubbles:true})); await sleep(2500);};
window.waitCards=async()=>{for(let i=0;i<20;i++){if(document.querySelectorAll('[data-testid="review-card"]').length>=5) return true; await sleep(700);} return false;};
window.acc={seen:new Set(),hits:[]};
window.step=async(pages)=>{const kw=/(too hot|very hot|so hot|extremely hot|quite hot|bit hot|hot room|room (?:was|is|got|gets) (?:very |too |so |quite |a bit )?(?:hot|warm|stuffy)|too warm|very warm|overheat|stuffy|stifling|heating|heater|air ?con|\bA\/?C\b|aircon|temperature|thermostat|couldn'?t (?:cool|turn))/i;
 const a=window.acc; let done=false;
 for(let p=0;p<pages;p++){for(const c of document.querySelectorAll('[data-testid="review-card"]')){const s=c.textContent.replace(/\s+/g,' ').replace(/Hotel response:.*$/,'').replace(/Helpful Not helpful.*$/,''); const k=s.slice(0,150); if(a.seen.has(k)) continue; a.seen.add(k); const hit=s.match(kw); if(hit){const i=s.search(kw); a.hits.push((s.match(/nights? · [A-Za-z]+ \d{4}/)||[''])[0]+' … '+s.slice(Math.max(0,i-130),i+120));}}
  const next=document.querySelector('button[aria-label="Next page"]'); if(!next||next.disabled){done=true;break;} next.click(); await sleep(2100);}
 return {done,n:a.seen.size};};
// pass 1: English, Dec–Feb (all pages, ~13 per call)
await waitCards(); await setSel('languages','en'); await setSel('timeOfYear','_12_02'); await waitCards(); JSON.stringify(await step(13))+'\n'+acc.hits.join('\n---\n')
```
Pass 2, all seasons, lowest scores first:
`await setSel('timeOfYear','ALL'); await setSel('reviewListSorters','SCORE_ASC'); await waitCards(); acc={seen:new Set(),hits:[]}; JSON.stringify(await step(14))+'\n'+acc.hits.join('\n---\n')`

Other `timeOfYear` values are `_03_05`, `_06_08` and `_09_11`. Use the season of the user's stay.
Matches print with their context, and you read them yourself. Regex hits include praise ("AC
works great"), hot water and summer corridors, so judge each one by its meaning.

## 4. Photo IDs

```js
const h=await (await fetch('/hotel/jp/<slug>.html?lang=en-us')).text();
window.__imgs=[...new Set([...h.matchAll(/xdata\/images\/hotel\/[a-z0-9x]+\/(\d+\.jpg\?k=[0-9a-f]+)/g)].map(x=>x[1]))];
```
To pick the building exterior, overlay a numbered grid of thumbnails
(`https://cf.bstatic.com/xdata/images/hotel/max300/<id>&o=`) on the page, take one
screenshot, and choose by eye. The first photo is often a room, not the building.
Download the chosen one at `max500` with `curl` into its own folder, after the user
has agreed to downloads.

## 5. Google Maps times

```
https://www.google.com/maps/dir/?api=1&origin=<Hotel name>&destination=<Place>&travelmode=walking|transit|driving&hl=en
```
After ~3 s:
```js
const t=document.body.innerText; const i=t.indexOf('Copy link'); document.title.split(' - ')[0]+' :: '+t.slice(i+9,i+120).replace(/\s+/g,' ')
```
The first number is the fastest route: walking `7 min 500 m`, transit `23 min … Yamanote
Line … ¥210`, driving `18 min 6.5 km` (use that as the taxi time). Coordinates of both
ends are in the URL once it has settled (wait ~5 s):
`location.href.match(/!1d[\d.]+!2d[\d.]+/g)` → `!1d<lon>!2d<lat>`.

Large stations have one map point, often far from the gate the hotel is near. If a
walk looks long, route to a landmark beside the right gate (e.g. a mall next to a
ticket gate) and say the estimate is approximate. A user once caught Takanawa Gateway
showing as 10 min when the south gate was about 5 min away.

## 6. Top-rated restaurants near a point

```
https://www.google.com/maps/search/restaurants/@<lat>,<lon>,17z?hl=en
```
```js
[...document.querySelectorAll('div[role=feed] > div')].filter(d=>d.querySelector('a.hfpxzc')).map(d=>({n:d.querySelector('a.hfpxzc').getAttribute('aria-label'),r:parseFloat((d.querySelector('.MW4etd')||{}).innerText||'0'),c:parseInt(((d.querySelector('.UY7F9')||{}).innerText||'0').replace(/[^\d]/g,''))})).filter(x=>x.c>=100).sort((a,b)=>b.r-a.r).slice(0,3).map(x=>x.n+' '+x.r).join(' · ')
```
The list only loads ~20 places, so don't use its length as a count. Use it only
for "top picks". If it comes back empty, retry once with `restaurants+near+<Station>`.
