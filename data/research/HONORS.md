# Connecticut honors: MICHELIN and James Beard (checked 2026-10-05)

The James Beard Foundation (JBF) calls its finalists "nominees". Below, **finalist** means a JBF nominee who did not win. Every finalist was first a semifinalist.

## MICHELIN Guide: no Connecticut restaurants

- On 2026-10-05, `https://guide.michelin.com/us/en/connecticut/restaurants` returned **404**. The same address for Massachusetts (`/us/en/massachusetts/restaurants`) lists 26 restaurants.
- MICHELIN's article "The MICHELIN Guide Debuts in Boston and Philadelphia" (May 12, 2025) says the Northeast Cities edition covers Chicago, New York City and Washington, D.C., plus the new cities Boston and Philadelphia. It does not mention Connecticut. https://guide.michelin.com/us/en/article/news-and-views/michelin-guide-boston-philadelphia-massachusetts-pennsylvania-philly
- I found no MICHELIN announcement adding Connecticut in 2026, and no Connecticut restaurant on guide.michelin.com. I could not find a "Northeast Cities 2026" reveal page; the URL I guessed returned 404.
- Hotels only, not restaurants: two Connecticut hotels have **One MICHELIN Key** each in "All the Key Hotels in the United States: The Full 2026 Selection" (Sept 18, 2026). They are Belden House & Mews (Litchfield) and Mayflower Inn & Spa, Auberge Collection (Washington). https://guide.michelin.com/us/en/article/travel/all-the-key-hotels-united-states

## James Beard America's Classics: every Connecticut honoree

| Year | Place | Town | Open now? |
|---|---|---|---|
| 1999 | Frank Pepe Pizzeria Napoletana, 157 Wooster St | New Haven | Yes (100th anniversary, June 2025) |
| 2012 | Shady Glen, 840 Middle Turnpike East | Manchester | Yes (April 2025 story; own site) |

- No Connecticut honoree in 2025 (JBF press release, Feb 26, 2025) or 2026 (JBF, Feb 25, 2026).
- The years come from Wikipedia's list of America's Classics (through 2026) and CTvisit. JBF's own past-awards search builds its results in the browser, so I couldn't read it.

## James Beard Restaurant and Chef Awards 2023–2026: Connecticut

Source: JBF's semifinalist, nominee and winner pages and press releases for each year (links are in `honors.json`).

**2023** (no Connecticut winners)
- Coracora, West Hartford: Outstanding Restaurant **finalist**. The winner was Friday Saturday Sunday.
- Christian Hunter, Community Table, New Preston: Best Chef: Northeast **finalist**. The winner was Sherry Pocknett.
- Renee Touponce, The Port of Call, Mystic: Best Chef: Northeast **finalist**.

**2024**
- David Standridge, The Shipwright's Daughter, Mystic: Best Chef: Northeast **WINNER**.
- Renee Touponce, The Port of Call, Mystic: Outstanding Chef **finalist**. The winner was Michael Rafidi.
- Coracora, West Hartford: Outstanding Restaurant **semifinalist**.

**2025** (no Connecticut winners)
- Brian Lewis, The Cottage, Westport: Best Chef: Northeast **finalist**. The winner was Sky Haneul Kim.
- Michelle Greenfield, Allium Eatery, Westport: Best Chef: Northeast **semifinalist**. That location is now closed (see below).
- Oyster Club, Mystic: Outstanding Wine and Other Beverages Program **semifinalist**.

**2026** (no Connecticut winners)
- David Standridge, The Shipwright's Daughter, Mystic: Outstanding Chef **finalist**. The winner was Michael Tusk.
- David DiStasi, Materia Ristorante, Bantam: Best Chef: Northeast **finalist**. The winner was Evan Hennessey.
- The Port of Call, Mystic: Outstanding Wine and Other Beverages Program **finalist**. The winner was Kato.
- ROLi, New Haven: Best New Restaurant **semifinalist**.
- Bolivar Hilario, Community Table, New Preston: Best Chef: Northeast **semifinalist**.
- Shilimat Tessema, Lalibela Ethiopian Restaurant, New Haven: Best Chef: Northeast **semifinalist**.

**Totals for 2023–2026:** 15 honors. That is 1 winner, 8 finalists and 6 semifinalists, across 10 places. Two more places hold America's Classics, for 12 honored places in all. Of these, 11 are open (`honors.json`) and 1 is closed (`closed_honors.json`).

## Where the honorees are now

- **Allium Eatery** (54 Railroad Place, Westport) is **closed**. Its own site says the location is closed and is moving to a new home, with no address yet. It is in `closed_honors.json`.
- **Christian Hunter** (2023) is no longer the chef JBF lists for Community Table. JBF's 2026 list names Bolivar Hilario. I didn't find where Hunter cooks now.
- **Coracora**: the honored restaurant was the original at 162 Shield St, which is still open. It now serves the classics in a casual format, because the upscale flagship opened at 51 Isham Rd in Blue Back Square by February 2026 (CT Bites).
- **Renee Touponce** now leads the kitchens at both The Port of Call and Oyster Club (Oyster Club's own site).
- **David Standridge** is still at The Shipwright's Daughter. **David DiStasi** is still at Materia. **Brian Lewis** is still at The Cottage, Westport.

## Corrections to the 2026-09-27 claims

1. **MICHELIN:** the claim is correct. There is still no Connecticut restaurant coverage, and the Northeast Cities edition is Boston, NYC, Philadelphia, D.C. and Chicago. One addition: two Connecticut hotels have MICHELIN Keys, which are hotel distinctions, not restaurant ones.
2. **America's Classics** (Pepe's 1999, Shady Glen 2012): correct, and the list is complete.
3. **Standridge, Best Chef: Northeast 2024 winner:** correct.
4. **2026 finalists** (Standridge, DiStasi, The Port of Call): correct, and none won. DiStasi's restaurant is **Materia Ristorante**, at 637 Bantam Rd. Bantam is a borough in the town of **Litchfield**.
5. **The claims were incomplete.** They left out the 2023 finalists (Coracora, Christian Hunter, Renee Touponce), Touponce's 2024 Outstanding Chef finalist honor, Brian Lewis's 2025 finalist honor, and all the semifinalists.
6. **Town fix:** Oyster Club and The Port of Call (Water St) are in the town of **Groton**. The Shipwright's Daughter (E Main St) is in **Stonington**. All three are in the village of Mystic. I assigned these towns, plus Washington for New Preston and Litchfield for Bantam, from the project's own address points and town shapes (`data/ct/addresses_ct.parquet`, `data/ct/ct_towns.geojson`).

## Left out on purpose

- Connecticut Restaurant Association awards, such as Community Table's "Restaurant of the Year 2025" and Materia's 2023 Chef of the Year. I couldn't confirm whether they're decided by judges or by votes.
- Honors from before 2023, such as Coracora and Macarena Ludena in 2022, and Brian Lewis in 2018 and 2022. These are outside the 2023–2026 window and I only saw them on secondary sites.

## Blocked or unreadable (not bypassed)

- WTNH (403), Hartford Business Journal (403) and Yale Daily News (403).
- The cga.ct.gov Mystic parking study failed with a TLS certificate error.
- JBF's past-awards search builds its results in the browser and can't be read by fetching the page.
