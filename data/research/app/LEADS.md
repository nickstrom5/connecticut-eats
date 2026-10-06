# Leads the October 2026 research couldn't verify

Left out of the guides until someone finds a 2025–26 source (the place's own current site or menu, a dated news story, or a dated tourism listing). Merged from the four regional researchers; each section is theirs.

---

## Leads: Capitol region, Quiet Corner, Northwest Hills (checked 2026-10-05)

These places probably belong in a guide but could not be verified under the README rules (no dated 2025-26 source showing them open, site blocked, or Facebook/Yelp only). Each line gives the reason and what would settle it.

Notes on `capitol_north.json`:
- `evidence_date` is `YYYY-MM` when the source gives a month, and plain `YYYY` when the only 2025-26 date is a season label or a site copyright year (Belvedere, Tulmeadow, A.C. Petersen, Hopkins Inn, Old Riverton Inn, Henry's Diner, We-Li-Kit).
- `seasonal: null` means the season wasn't confirmed (Tulmeadow, Gooseboro).
- Weakest records, worth a recheck first: A.C. Petersen Farms (site copyright 2026 plus a June 2025 blog guide), Old Riverton Inn (Riverton merchants page dated 2026), Henry's Diner (Discover Putnam page dated 2026), Patty's and Gooseboro (Visit Litchfield page with 2025 openings on it), Doogie's (WFSB 2025 plus a blog for the address).

## Capitol region

### Burger, hot dog, diner
- **Rein's New York Style Deli**, 435 Hartford Tpke, Vernon (Rockville area). Its site returns 403 (blocked), and the only dated listings found are Yelp or Google-derived. Could take `grinder`. Needs a dated news story.
- **Frankie's**, Plainville. A Plainville branch was named in WFSB's 2025 hot dog series, but the chain site (frankieshotdogs.com, copyright 2023) has no locations page or address. Needs the address and a dated page. If it's a branch: `branch_of: "Frankie's, Waterbury"`.
- **Saint's Restaurant & Catering**, Southington (a blog gives 1248 Queen St, 1967, and the "John's Way" dog). WFSB's 2025 hot dog series names it; no own site was found. Needs its own site or news.
- **Riley's Hot Dog & Burger Gourmet**, New Britain. Named in WFSB's 2025 series. Its age and address weren't checked.
- **Main Street Diner**, 40 W Main St, Plainville. A 1950s Master diner car, in Plainville since September 1959 (CTMQ, 2017). onlyinyourstate returned 403, and no 2025-26 source was found.
- **Zip's Diner / Zip's Dining Car**, Route 12 and Route 101, Dayville (Killingly). Family-run since 1954. Its own site fails with an SSL certificate error. Dated evidence is Yelp only, and the NECT Chamber lists it by name only. Top priority to recheck.
- **The Country Diner**, 111 Hazard Ave, Enfield. Only an undated visitconnecticut.com listing.
- **Vernon Diner**, 453 Hartford Tpke, Vernon. Own site is undated; founded 2000.
- **Franklin Giant Grinder Shop**, 464 Franklin Ave, Hartford. Its domain is parked and evidence is Yelp only. Could take `grinder`.
- **Dom's Broad Street Eatery**, Windsor. A breakfast spot in WFSB's 2025 series. Not clearly a diner, and not verified.
- **Aetna Diner**, Hartford (1947 Paramount car). Under restoration per Wikipedia, not serving.

### Dairy bars / creameries
- **Collins Creamery**, 9 Powder Hill Rd, Enfield. No website resolves (collinscreamery.com) and evidence is Yelp only.
- **Fish Family Farm Creamery**, 20 Dimock Lane, Bolton. Its site redirects to Facebook; the Buy CT Grown directory entry is undated (site copyright 2026) and gives summer scoop hours to 8 pm. A Fox61 story returned 403.
- **Robb's Farm Ice Cream**, 91 Wassuc Rd, South Glastonbury. The site connection failed. 2026 hours appear only on aggregators. Farm since 2001, ice cream since 2005 (unverified).
- **Grassroots Ice Cream**, 4 Park Pl, Granby. Site returns 403.
- **Main Street Creamery & Cafe**, 271 Main St, Wethersfield. Own site is current (fall flavors posted) but undated; the only dated mention is a June 2025 blog guide (connecticutbuzz.com).
- **Mapleleaf Farm**, Hebron. A dairy farm since 1903; no evidence of a scoop shop, and the website rendered empty.
- **ConeHeads Creamery** (95 Hartford Tpke, Vernon) and **Praline's Own Made** (107 New Britain Ave, Plainville). Only the June 2025 connecticutbuzz blog guide.

### New Britain's Little Poland (`polish`)
The visitnbct.com Little Poland directory is undated and still lists the closed Staropolska, so it can't show a place is open.
- **Kasia Bakery**, 88 Broad St. Paczki, cakes and breads. Undated city listing and Yelp only; no own site found.
- **Polonia Taste / Taste of Poland**, 99 Broad St. Both names appear at the same address (possibly a rename). Undated listing, plus a 2024 Polbox article.
- **Break-Fast House**, 93 Broad St; **Bread of Heaven Bakery**, 35 Broad St. Undated city listing only.
- **Polmart**, 123 Broad St. A large Polish market with deli and bakery. polmart.com is parked for sale.
- **Podlasie Meat Market** (High St) and **Martin Rosol's** (sausage maker). Not checked; markets rather than restaurants.
- **Cracovia Deli**, 994 W Main St (from a 2024 Polbox article). cracoviadeli.com belongs to an unrelated Calgary store.
- **Little Poland restaurant**, 55 Broad St. Only the 2024 Polbox article.
- **Larose's Bakery**, Broad St. Named for paczki in search results, not verified.
- **Polish National Home of Windsor Locks**, 9 1st St (1928). Only the 2024 Polbox article.
- **East Side Restaurant**, 131 Dwight St, New Britain (1934, German). Open per its own site (assets dated Dec 2024), but no kind fits, so it is not in the guide.

### Oldest / Hartford institutions
- **Bidwell Tavern**, Coventry (1822 building). Site returns 404. Verify the year it started serving and its current status.
- **Avon Old Farms Inn**, Avon. The website domain no longer resolves, so it may be closed. Needs news.
- **Carbone's** (Hartford, 1938; site refused connection) and **Max Downtown** (Hartford, 1996; site copyright 2026, open). Neither is pre-1900, and no kind fits.
- Hartford's Puerto Rican (Park Street) and Jamaican (Albany Avenue) institutions were not researched: no `kinds` value fits, and the search budget went to guide kinds.

## Quiet Corner
- **Zip's Diner**: see above.
- **Hank's Restaurant**, 416 Providence Rd, Brooklyn. A family restaurant since April 1971; own site copyright 2024 with nothing dated 2025-26. Possible `diner`.
- **Deary Bros. Mike's Stand**, Putnam. Listed by name only on the NECT Chamber tourism page; its type and age are unknown.
- **Fort Hill Farms**, 260 Quaddick Rd, Thompson. A dairy farm with a 2026 corn maze, but its own site shows no scoop shop (a blog guide lists a "Lavender Creamery").
- **The Inn at Woodstock Hill**, Woodstock. Not confirmed as pre-1900 dining; the site moved to woodstockhill.com and wasn't checked.

## Northwest Hills / Litchfield Hills
- **White Hart Inn**, 15 Under Mountain Rd, Salisbury. A farmhouse built in 1806, reopened in 2014 after renovation. Its own pages show no 2025-26 date, and the year it became an inn wasn't confirmed. Possible `oldest`.
- **Peaches N' Cream**, 632 Torrington Rd, Litchfield. Year-round ice cream; own site undated, plus the June 2025 blog guide.
- **West Shore Seafood**, 449 Bantam Lake Rd, Litchfield. Seasonal lobster dinners (Visit Litchfield); the site wouldn't render. Check for a lobster roll.
- **Twin Colony Diner**, Torrington, and **Kurt's Mucke's hot dog stand**, Torrington. Yelp only.
- **Winsted Diner**, 496 Main St, Winsted (Winchester). Yelp marks it closed, but no dated news was found. Possibly closed.
- **Marketplace Tavern (the Old Jail)**, 7 North St, Litchfield. The building dates to 1812, but the restaurant is recent, so it doesn't fit `oldest`.
- **Blackberry River Inn**, Norfolk (1763 house). Breakfast for inn guests only; no public restaurant.
- **David DiStasi / Bantam (Litchfield)**: left for the honors agent. No guide kind fits the restaurant.

---

## Leads: Western Connecticut + Greater Bridgeport (fairfield_west)

Places that probably belong in a guide but could not be verified with a 2025–26 source under the README rules.
Researched 2026-10-05. 30 of 30 WebSearch calls used, so many of these just need one more dated source.

## Hot dogs / burgers

- **Merritt Canteen**, 4355 Main St, Bridgeport 06606: hot dogs, burgers and chili at the same Main St. spot since 1942 (own site, CTvisit listing). **Undated**: the own site loads its content by script and has no date, and the CTvisit listing has no date either. Only Tripadvisor/Yelp turned up for 2025–26. Needs a dated news item.
- **Duchess**, Connecticut fast-food chain since 1956 (35 Boston Ave, Bridgeport; 2315 Black Rock Tpke and 625 Post Rd, Fairfield; also Stratford). **Original not documented consistently**: Wikipedia says the Berkowitz brothers bought Maraczi's in Bridgeport in 1956, and another source says the first Duchess was in Fairfield. The Duchess site gives no original address. Add only the original once a reliable source pins it down.
- **Danny's Drive-In**, 940 Ferry Blvd, Stratford: dinerville.info says the stand was built on site in 1935. **Possibly closed / stale**: its likely domains are lapsed or spam, and no dated source turned up.
- **Dog Daze**, Wilton: on CTvisit's hot dog tour (last updated June 2026), but its only web presence is **Facebook**, and no street address was confirmed.

## Seafood / lobster rolls

- **Dolphin's Cove Restaurant & Marina**, 421 Seaview Ave, Bridgeport (since 1993). **Possibly closed**: its domain now forwards to a parked "/lander" page, and listing sites mark it closed, but there's no news source (and Yelp/Wanderlog are not allowed sources). If a 2025–26 article confirms the closure, it goes in closed.json.
- **LobsterCraft**, Stratford: in CT Bites' 2026 lobster roll guide, but its site returned no readable content and no address was confirmed.
- **Reef Shack**, Fairfield: in CT Bites' 2026 lobster roll guide, **Instagram only**.
- These are also in CT Bites' 2026 lobster roll or waterfront guides. I didn't add them because they're full-service restaurants rather than shacks or icons; add them if the lobster-roll guide should be comprehensive:
  - Elm, 73 Elm St, New Canaan
  - BRYAC, 3074 Fairfield Ave, Bridgeport
  - Boca Oyster Bar, Steelpointe Harbor, Bridgeport
  - Joey C's Boathouse, Stratford
  - The Landing at Five Twenty, Stratford
  - Luca's Beach Kitchen, 99 Calf Pasture Beach Rd, Norwalk (appears to be new)
  - Match, Norwalk
  - Prime, Stamford
  - Palmer's, Darien (market)
  - Mr. Crab, Bridgeport
  - Harbor Lights, Norwalk

## Diners (open per listings, but no dated 2025–26 source found)

- **Post Road Diner**, 312 Connecticut Ave, Norwalk: own site has no date.
- **Silver Star Diner**, 210 Connecticut Ave, Norwalk: own site (new.silverstarct.com) has no date. A search snippet said three brothers from Greece opened it in 1980; that's unverified.
- **Lakeside Diner**, 1050 Long Ridge Rd, Stamford: known for doughnuts. Undated sources only, and lakesidediner.com is a domain for sale.
- **Parkway Diner**, 1066 High Ridge Rd, Stamford (dinerville: DeRaffele car, 1957). Undated.
- **Curley's Diner**, 62 W Park Pl, Stamford: undated, Yelp only.
- **The Stamford Diner**, 135 Harvard Ave, Stamford: own site has no date.
- **3 Brothers Diner**, 242 White St, Danbury: own site has no date.
- **New Holiday Diner**, 123 White St, Danbury: undated.
- **Mill Plain Diner**, 14 Mill Plain Rd, Danbury: millplaindiner.com is now an unrelated casino site, so possibly closed.
- **Sandy Hook Diner**, Newtown: undated.
- **New Canaan Diner**, 18 Forest St: undated.
- **Windmill Diner**, New Milford: undated.
- **Blue Sky Diner**, 273 Ferry Blvd, Stratford: own site has no date.
- **Frankie's Diner**, 1660 Barnum Ave, Bridgeport: own site has no date.
- **Glory Days Diner**, 69 E Putnam Ave, Greenwich: **blocked** (Cloudflare check).
- **Monroe Diner**, 568 Main St, Monroe: undated.
- **Family Diner**, 71 Main St, Norwalk: undated.
- **Orem's Diner** is in the guide via Connecticut Magazine (Feb 2026), but its own site returns 403 (**blocked**), so its founding year is still unknown.
- **Elmer's Diner** is in the guide via Greenwich Time (May 2025), but its own site returns 403 (**blocked**).

## Dairy bars / ice cream

- **Micalizzi's Italian Ice**, 712 Madison Ave, Bridgeport: long-running Italian ice stand. **Facebook/Instagram/X only** for 2025, and its old domain is lapsed.
- **Timothy's Ice Cream**, Black Rock, Bridgeport: no site found, and no dated source.
- **Twisters Ice Cream Cafe**, New Fairfield: in CT Bites' 2026 ice cream guide, **Facebook only**.
- **Dubl Twister**, Danbury (original) and Brookfield: in CT Bites' 2026 ice cream guide, **Facebook only**.
- **Il Bacio Ice Cream**, Danbury: in CT Bites' 2026 ice cream guide, **Facebook only**.
- **Scoops of Wilton**, Wilton: in CT Bites' 2026 guide, which says it has been in Wilton since 1982 and recently reopened under new owners. **Instagram only**, and no street address was confirmed.
- **Goody Bassett's Olde Fashioned Ice Cream Shop**, Stratford: in CT Bites' 2026 guide (open year-round), **Facebook only**.
- **Longford's Ice Cream**, Stamford: in CT Bites' 2026 guide. I didn't add it because it's an ice cream maker and scoop shop and I couldn't confirm a long-running stand at a fixed address.

## Apizza

- **Sally's Apizza**, 665 Commerce Drive, Fairfield (branch of Sally's, New Haven): listed on Sally's current site, but the page carries no 2025–26 date of its own. The Stamford branch is in the guide via its June 2026 brunch menu.
- **Colony Grill**, Fairfield and Norwalk branches (bar pies, not apizza): only the Stamford original is in the guide. Colony Grill's own site returns 403 (**blocked**).

## Oldest

- **The Elms Inn**, 500 Main St, Ridgefield: an inn since 1799. Its own site (© 2026) mentions the "Elms Restaurant & Tavern", but I found no dated evidence that the restaurant itself is still serving. Verify before tagging `oldest`.
- **Redding Roadhouse**, Redding: its domain now serves an unrelated spam site, so possibly closed.
- I found no other pre-1900 operating restaurant or colonial tavern still serving food in the region. Keeler Tavern in Ridgefield is a museum, and Fairfield's Sun Tavern is a museum building.

## Grinders

- Not researched deeply (search budget). Leads: **Nardelli's Grinder Shoppe**, Norwalk (a 2022 branch of the 1922 Waterbury original), and **Firehouse Deli**, Greenwich (est. 1997, known for wedges). Both need dated sources.

## Danbury / Bridgeport Portuguese, Brazilian and Puerto Rican institutions

- No `kinds` value fits these, so they weren't added. Candidates for a future kind:
  - International Bakery & Market, Danbury's "Portuguese Square" (since 1965 per NewsTimes)
  - Minas Carne & Deli, Danbury (Brazilian barbecue since 1997, per a 2020 article)
  - Favi Lunches & Deli, Danbury (opening a second site, NewsTimes Aug 2025)
- Bridgeport Portuguese and Puerto Rican spots weren't searched.

## Closed (no 2025–26 closure source, so not in closed_fairfield_west.json; do NOT add to a guide)

- **The Original Swanky Franks**, 182 Connecticut Ave, Norwalk: closed in May 2017 after more than 60 years (Daily Voice, Dec 2017, reports a jerk chicken shop in the former Swanky Franks site). Its domain now redirects to an unrelated ticketing site.

---

## Leads: South Central Connecticut and Naugatuck Valley

These places probably belong in a guide, but they couldn't be verified under the README rules. Checked 2026-10-05.

## Apizza

- **Abate Apizza & Seafood**, 129 Wooster St, New Haven. Visit New Haven (page dated 2024) says a fire damaged the Wooster St restaurant and that the business moved to North Haven. That listing gives the North Haven address as "61 North St"; the CTvisit listing gives "61 State St". The site abatepizza.com shows a Wix domain error. No 2025–26 source found. **Status: possibly closed or relocated.**
- **Zuppardi's Apizza, Derby location.** CT Bites (Feb 2025) lists three Zuppardi's (West Haven, Ansonia, Derby). The Derby page on zuppardisapizza.com is now a 404, and the site's menu links only West Haven and Ansonia. **Possibly closed.**
- **Grand Apizza, original New Haven (Fair Haven) location, opened 1955.** grandapizza.com lists only Guilford, Madison and Clinton, and no New Haven shop is shown. Status unknown.
- **Big Green Pizza Truck.** The CT Bites Food Trucks Guide (May 2026) describes antique trucks with wood-fired ovens that do catering and events only. No fixed location, so it isn't a guide entry.
- **Mangia Apizza**, 244 Quinnipiac Ave, North Haven. CT Bites (Feb 2025) lists it, but its domain (mangiaapizza.com) now redirects to an unrelated restaurant site. **Possibly closed**; needs a check.
- **Jimmy's Apizza**, Milford. It is on the CTvisit Connecticut Pizza Trail (updated June 2026) as "apizza style", but jimmysapizza.com returns 403 and no street address was confirmed.
- **New Haven Pizza Place** (Milford) and **Amato's** (Madison). The CTvisit Pizza Trail lists both as "apizza style". Their own sites weren't verified, and amatospizzapasta.com didn't respond.
- **Bartone's Apizza**, Derby. It opened in March 2024 and CT Bites profiled it in Sept 2025. It's a newer place and no street address was captured.
- **Papa's Pizza** (258 Naugatuck Ave and 2005 Bridgeport Ave, Milford) and **Christos** (Wallingford). Both claim New Haven-style or brick-oven pies. Left out because the style is unclear: CTvisit labels both Neapolitan, and Christos calls itself "Modern-Americana".
- **Tipsy Tomato** (656 New Haven Ave, Derby) and **One6Three** (163 Foster St, New Haven). CTvisit lists both as apizza, but CT Bites reviews from late 2025 describe bar-style pies. Left out of the apizza guide.
- **Apizza Grande Bethany**, 119 Amity Rd, Bethany. CTvisit lists it as "Grand Apizza of Bethany", but it is a different business from the Nuzzo family's Grand Apizza. Not verified as apizza.

## Hot dogs, burgers, grinders

- **Top Dog**, Milford. One search found no 2025–26 source and no address.
- **Al's Hot Dog Stand**, 248 S Main St, Naugatuck. A directory summary cites a Feb 2024 Facebook post saying it closed. No 2025–26 source either way. **Possibly closed.**
- **Other Frankie's locations**: Chase Ave and Reidville Dr in Waterbury, Naugatuck, and West Haven (1152 Orange Ave per CTvisit). The CTvisit Hot Dog Tour (June 2026) says the chain has six locations. Only Watertown Ave was put in the guide.
- **Nardelli's Grinder Shoppe**. The chain dates to 1922 in Waterbury. Its oldest standing store is in Naugatuck (late 1970s) and the Plank Rd, Waterbury store dates to 1985. Its site (© 2026) has no street addresses on its location pages. Also, CT News Junkie (Dec 2025) reports the Wallingford store closed in April 2025, but the site still lists it (see the closed file).

## Diners: no dated 2025–26 source found (sites undated or Facebook only)

Diner-car details below come from Dinerville, a crowd-sourced directory, and are unverified.

- **Georgie's Diner**, 427 Elm St, West Haven (1956 DeRaffele car)
- **New Star Diner**, 585 Lombard St, New Haven (1963 Fodero)
- **Tony's Diner**, 46 Columbus St, Seymour (1954 Kullman)
- **Olympos Diner**, 1130 E Main St, Meriden (1950 Silk City)
- **Athenian Diner**, 1064 Boston Post Rd, Milford (1997 DeRaffele)
- **Athena Diner II**, 320 Washington Ave, North Haven (Fodero; site footer © 2026 only)
- **Acropolis Diner**, 1864 Dixwell Ave, Hamden (1974 Paramount)
- **Shoreline Diner**, 345 Boston Post Rd, Guilford (1994 DeRaffele)
- **Valley Diner**, 636 New Haven Ave, Derby (1977 Swingle)
- **Duchess**, 706 Campbell Ave, West Haven (1993 DeRaffele)
- **Colony Diner**, 611 N Colony Rd, Wallingford (Facebook only)

Two more diners need a follow-up:

- **The Coffee Shoppe** (formerly Burnsie's), Maple St, Naugatuck. WTNH (Sept 2025) shows it open and calls it the last original diner in Naugatuck, so the dated evidence is fine. The street number is unconfirmed: directories give both 83 and 85 Maple St.
- **67 Family Diner**, Seymour. WTNH reported flood damage and a delayed reopening. Current status unclear.

## Seafood

- **Lobster Hut**, Milford. Facebook only; the CT Bites Lobster Roll Guide (July 2026) lists it with no address.
- **Szabo's Seafood**, Shelton. A seafood market plus a roaming food truck (CT Bites 2026). The truck has no fixed location, and the market wasn't verified.
- **Jesse Camille's**, Naugatuck. Serves a warm buttered lobster roll (CT Bites July 2026), but it's a full-service restaurant, not a shoreline shack. Optional.
- **Milford bars and restaurants with lobster rolls**: Bonfire Grille, Bridge House, Dockside Brewery and Founder's House (CT Bites July 2026). They aren't shacks. Optional.
- **Website problems on places that ARE in the guide** (verified through CTvisit, CT Bites or Visit New Haven instead):
  - Stowe's Seafood and Lenny & Joe's Fish Tale: their own sites return 403.
  - Lobster Shack, East Haven: connecticutlobster.com has an expired certificate, and lobstershackct.com now redirects to a gambling spam site. Don't link either.

## Ice cream

- **Ashley's Ice Cream**: New Haven, Hamden, Branford, Guilford and Madison; since 1979 per CT Bites 2026. Shop addresses not verified.
- **Scoopin' Ice Cream Shop** (Southbury), **The Ice Cream Shoppe** (Shelton) and **Praline's** (Wallingford, Meriden, Milford; founded 1984 in Wallingford). The CT Bites Ice Cream Guide (July 2026) lists them; own sites and addresses weren't verified.
- **Crazy Cow Creamery**, Wolcott. Came up in one search; unverified.

## Other

- **1754 House** (Woodbury): its own site returns 403. It is in the guide on the strength of the Providence Journal story (March 2026) and the Historic Hotels of America history page.

---

## Leads: Southeastern CT and Lower Connecticut River Valley

These places probably belong in a guide but could not be verified under the README rules (checked 2026-10-05).
Each lead gives the reason it was held back. None of these are in `southeast_river.json`.

## Southeastern Connecticut

### Clam shacks / lobster rolls
- **Dog Watch Café**: Stonington Borough and Mystic. CT Bites' July 2026 lobster roll guide lists both (hot and cold rolls). **Blocked**: its own site (dogwatchcafe.com) returned a 403 bot check, so neither address could be confirmed first-hand.
- **Johnny's Clam Shack**: 184 N Main St, Norwich (address from third-party ordering pages only). Listed in CT Bites' July 2026 lobster roll guide. Its own site (johnnysclamshack.com, © 2025) gives no address or season. **Undated/unconfirmed address.** Veteran-owned seasonal take-out (fried whole bellies, soft serve), reportedly opened in 2017.
- **Lobstah Dawg**: 12 River St, Waterford. Listed in CT Bites' July 2026 guide ("Open Thurs–Sun, weather willing"). **No own site found.**
- **Ford's Lobster**: left 15 Riverview Ave, Noank, after its lease ended (that spot is now Haring's Noank, which is in the guide). Its site still says it will reopen at a new location in "Spring 2024". **Stale site**; logged in `closed_southeast_river.json`. Check again if a new location turns up.
- **Ford's Black & Blue**: 65 Marsh Rd (Spicer's Marina), Noank, which calls itself "home of the original Lobster Bomb". **Undated site**, and no lobster roll is confirmed.
- **Off The Hook** (Mystic), **J&R Seafood Market** (Mystic), **The IRONS** (Hilton Mystic), **Stonington Pizza Palace**, **374 Kitchen + Cocktails** (Niantic), **Kokomo's** (Old Lyme), **The Inishshor** (Colchester town green): each is listed in CT Bites' July 2026 lobster roll guide. **Not checked** against their own sites (search budget). Lower priority: they are restaurants that serve a lobster roll, not shacks.
- **Mystic Drawbridge Ice Cream, Old Mystic branch**: 47 Main St, Old Mystic (former Old Mystic General Store), opened July 2026 (The Connecticut Scoop). **Town not verified**: Old Mystic straddles Groton and Stonington, and the geocoder did not confirm which side.

### Diners
- **Peter Pan Diner** (Norwich): a search snippet said "temporarily closed". **Status unknown.**

### Dairy bars / ice cream
- **Meyer's Crazy Hollow Creamery**: 888 Route 32, North Franklin (town of Franklin). It has nearly 30 hand-scooped flavors plus soft serve and is open daily 12–8. **Only dated source is a readers'-poll post** (The Connecticut Scoop, May 2026), which the README doesn't allow as the basis.
- **Millie's Ice Cream Stand** (Norwich, at Malerba's Golf Driving Range): a seasonal stand. **Facebook only** (listed in CT Bites' 2026 ice cream guide).
- **Mel's Downtown Creamery** (Colchester and Pawcatuck): listed in CT Bites' 2026 ice cream guide as open year-round. **Not checked.**
- **Pop's Premium Ice Cream with Praline's** (Gales Ferry, Ledyard): listed in CT Bites' 2026 guide. **Not checked.**
- **Mango's Homemade Ice Cream** (Olde Mistick Village, Mystic): **Facebook only.**
- **Twister's Ice Cream** (Mystic, riverfront): its own site (twistersicecreammystic.com) shows no address or date. **Undated.**
- **Mystic Sweet Shop** (Mystic): **Facebook only.**
- **Zac Young's Sprinkletown Donuts & Ice Cream** (Foxwoods): a casino outlet, so left out on purpose (casino list kept to signature restaurants).

### Casinos
- **Sally's Apizza at Foxwoods** (Great Cedar Concourse, Mashantucket/Ledyard): it takes over the former California Pizza Kitchen space, which closed Jan 4, 2026. Foxwoods' dining page still says **"Coming Soon"**. Add it as an `apizza` branch of Sally's (New Haven) once it opens.
- **David Burke Prime** (Foxwoods): Foxwoods lists it as "Temporarily Closed"; a Connecticut Scoop headline says it will reopen "this fall".
- **Michael Jordan's Steak House**, **Todd English's Tuscany**, **SolToro**, **TAO** (Mohegan Sun): left out to keep the casino list short. Pages exist on mohegansun.com.

### Polish
- No Polish restaurant, deli or bakery could be found in Norwich (searched). The only Polish place found in the region is Little Polska in Old Saybrook, which is in the guide.

## Lower Connecticut River Valley

### Oldest / historic inns
- **Gelston House**: 8 Main St, East Haddam (Goodspeed Opera House Foundation). Per historicbuildingsct.com, a tavern stood on this site from 1736 (built by Jabez Chapman), the Gelston family ran it 1776–1825, and the core of today's building dates from 1853. Its own site lists current hours but is **undated** (© 2022). The only 2026 evidence is a band's event listing (themediums.net, May/Aug/Dec 2026). If accepted, it would qualify as `oldest`: a colonial-era tavern site that still serves food, though the building is from 1853.
- **Bee and Thistle Inn**: 100 Lyme St, Old Lyme. **Restaurant status unclear**: OpenTable shows "temporarily closed / curbside takeout" and Gayot says "this restaurant is closed". Its own site would not load content.
- **Checked, excluded (not pre-1900 restaurants)**: **Old Lyme Inn** (85 Lyme St): the building dates from c. 1865, but it became an inn (the Barbizon Oak) only after the 1950s, and the Old Lyme Inn came after a 1965 fire. Its site shows © 2026 but no dated menu. **Copper Beech Inn** (46 Main St, Ivoryton): the house dates from 1889, it became a restaurant (the Johnny Cake Inn) in the mid-1950s and the Copper Beech Inn in 1972. Its site is undated. Either could go into a general guide later, but neither fits `oldest`.

### Diners
- **O'Rourke's Diner** (Middletown): closed (see closed file).
- **Thread City Diner** (931 Main St, Willimantic/Windham) and **Blondie's Diner** (1681 Main St, Willimantic/Windham): both have live Toast online ordering pages, but **no dated 2025–26 source**. (Willimantic is in Windham, which was assigned to this region.)
- **The Fino's Diner** (455 E Main St, Middletown): The Connecticut Scoop profiled it in July 2026 (opened 2023, breakfast and pizza). Left out because it's new and not a classic diner. Easy to add if wanted.
- **Charlie's Place** (North Windham): a Connecticut Scoop "Local Gem" headline. **Not checked.**

### Dairy bars / ice cream
- **Tall Man's Homemade Ice Cream** (Cromwell): sold to the Durham Dari Serve/Cromwell Creamery owners in July 2026 (The Connecticut Scoop), so it's open. **Address not confirmed**: its own site has no text content.
- **Cromwell Creamery**: 2 Willowbrook Rd, Cromwell. It's open in 2026 (Connecticut Scoop, July 2026), but the address appears only in a readers'-poll post, and the shop is Facebook-only.
- **Moodus Ice Cream Parlor** (26 Falls Rd, Moodus/East Haddam): "open for the 2026 season" per CT Bites. **Facebook only.**
- **HK Dairy Barn** (Higganum/Haddam): a family-run ice cream barn. **Facebook only.**
- **Deep River Ice** (Deep River): **Facebook only.**
- **Island Vibes Creamery** (East Hampton): **Facebook only.**
- **Sweet P's** (Essex; CT Bites says founded 1989), **Scoops of Centerbrook with Praline's** (Essex), **AL's Ice Cream** (Middletown), **Oh Fudge! And More** (Haddam, seasonal ice cream counter), **Sweet and Savory** (East Haddam), **Rich Farm Ice Cream** (Middlefield location), **Woody's Coffee & Ice Cream** (Cromwell), **Aqua Creamery** (Cedar Island Marina, Clinton): all listed in CT Bites' 2026 ice cream guide. **Not checked**, or Facebook/Instagram only.
- **Old Lyme Ice Cream Shoppe** (Old Lyme): its own site returned an HTTP 520 error. **Unverified.**

### Lobster rolls
- **Drift** (Essex), **Edd's Place** (Westbrook): listed in CT Bites' July 2026 lobster roll guide. **Not checked.**
