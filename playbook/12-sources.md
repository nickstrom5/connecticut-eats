# Connecticut sources, coverage and calibration (checked 2026-10-05; licenses refreshed 2026-10-07)

## Official sources

| Source | What we use | Terms | Cadence | Notes |
|---|---|---|---|---|
| DCP "State Licenses and Credentials", data.ct.gov `ngch-56tr` | Active on-premise liquor permits (restaurant, restaurant wine & beer, cafe, hotel, craft cafe, caterer, club, casino, brewery) and bakery licenses: **DBA, address, permit type, first issue date** | Public Domain (dataset license) | Daily (downloaded 2026-10-07) | 5,530 current records we use (status ACTIVE only: DCP flags LAPSED and APPROVED rows active=1 too); 2,715 restaurant permits, 963 cafe (bar), 131 hotel. `name`/`businessname` (the permittee, often a person) is dropped at download. The "Liquor Permits" view `gwv2-eswx` (permittee and backer names) is never read. No coordinates: placed on Overture address points (90.8% placed, on the permit's own side of a split street (N/S Main St) and street type; exact or interpolated between neighboring numbers on the same street in the same town). |
| DCP Liquor Control suspensions `i2yq-278d` | Downloaded for reference, not shown | Public Domain | Weekly-ish (2026-10-02) | 460 rows. |
| City of Hartford "Food Establishments Licenses Current" (ArcGIS item `27139a92097e4e6a957646fb633e1e71`) | DBA, address, Class 1–4, seating | Badge says "Creative Commons Attribution 1.0 Public Domain" (CC BY 1.0 image, CC0 link): we attribute the City either way | Nightly from Accela | 736 current. Class 1 = groceries/pharmacies, Class 4 = schools, nursing homes, churches (institutions); Classes 2–3 are the restaurants. |
| Farmington Valley Health District food ratings (fvhd.org, one page per town) | Each place's **official A/B/C/U rating and its date** (Avon, Barkhamsted, Canton, Colebrook, East Granby, Farmington, Granby, Hartland, New Hartford, Simsbury) | Public web pages; robots.txt allows; attributed | Rolling, newest 2026-09-30 | 516 ratings; 207 matched one-to-one to places on our list, only where the names share a distinctive word or are the same name (the rest are schools, groceries, churches, mall counters). Fetched one page per 30 s; any 403/429/503 or dropped connection stops the run. Shown in place details only, labeled official, with the date (Nick, 2026-10-05). |
| DPH local health departments `62ac-rrv4`, town-to-department `p3e9-4yjt` | The 61 departments (2 tribal) and the town each serves | data.ct.gov | Updated 2026-10-02 | See coverage below. |
| U.S. Census cartographic boundary file `cb_2025_09_cousub_500k` | The 169 towns and 9 planning regions (shoreline-clipped) | Public domain | 2025 | Every place is placed in its town by its point; villages (Mystic, Noank, Storrs, Cos Cob…) are kept as `village`. |
| Statewide parcel/CAMA `ibe8-9i3q` | Not used | No license stated; lists owners | 2026 collection | No building-value board. |

## There is no statewide inspection data and no official grade

61 local health departments and districts inspect restaurants; none publishes results in bulk, and no state or open-data feed exists
(data.ct.gov, ArcGIS Online, Socrata and Tableau Public searched). Since Feb 17, 2023 the state form (FDA Food Code) has no score and no
pass/fail. So: **no inspection boards**. The full survey is `data/raw/official/LHD_COVERAGE.md` and `lhd_coverage.json`; restaurants per
department are in `data/raw/official/lhd_restaurants_table.md`.

| Status of a department's online results | Departments | Restaurants on our list in their towns |
|---|---:|---:|
| Current (Farmington Valley list; NDDH, Fairfield and Manchester PDFs) | 4 | 929 |
| Stale (Norwalk's pre-2023 "Lighthouse" ratings, Waterbury to 2020, Darien to Dec 2025) | 3 | 805 |
| Blocked to automated checks (not bypassed: New Haven, Stamford, Uncas, Chatham, Stratford…) | 12 | 1,991 |
| None found (calls, email or FOI only) | 42 | 7,382 |

## Map listings (Overture Maps 2026-09-23.1)

17,321 Connecticut eating/drinking listings. Kept for the **web leaderboard**: Meta and chain store feeds, plus anything on an official
list or hand-checked (10,757 restaurants after cleanup and 738 license-only additions, 2026-10-07). Kept for the **app** (no Google data): Meta with
confidence ≥ 0.90, chain store feeds, official, hand-checked (9,358 restaurants after the QA pass: non-restaurants such as cinemas, bowling,
member clubs, chain hotels, banquet halls, smoke lounges and home bakers are hidden; one permit attaches to one place in its own town).

### Calibration: share of each kind of listing that matched an official list

| Kind of listing | Hartford food license (every food business) | Statewide liquor permit (only places that serve alcohol) | Kept? |
|---|---:|---:|---|
| Meta + open in Google 2021 | 70% of 213 | 33% of 5,793 | web: yes |
| Meta only | 35% of 232 | 20% of 4,661 | web: yes |
| Meta, confidence ≥ 0.95 | 68% of 258 | 34% of 6,996 | app: yes, "confirmed" |
| Meta, 0.90–0.95 | 40% of 83 | 17% of 1,734 | app: yes, "listing only" |
| Meta, below 0.90 | 22% of 109 | 8% of 1,788 | app: no |
| BrightQuery ≥ 0.95 | 30% of 64 | 10% of 1,206 | no |
| Foursquare only | 7% of 72 | 4% of 1,730 | no |
| Google 2021 says closed | 3% of 33 | 2% of 646 | no |

For reference, Chicago gave 74% (Meta + Google) and 40% (Meta only); Milwaukee 79% and Dane County 75% for Meta ≥ 0.95.

Coverage the other way: the map listings held **82% of active restaurant liquor permits**, 63% of cafe (bar) permits and 61% of
Hartford's Class 3 food businesses. Licensed places they lacked were added from the lists (773 rows).

## Honors (checked 2026-10-05; data/research/HONORS.md)
- **No MICHELIN Guide for Connecticut** (guide.michelin.com/us/en/connecticut/restaurants is a 404; the Northeast Cities guide covers
  Boston, NYC, Philadelphia, DC and Chicago). Two hotels hold a MICHELIN Key (Belden House & Mews, Mayflower Inn & Spa): hotel, not
  restaurant, distinctions; not shown.
- James Beard: America's Classics Frank Pepe (1999) and Shady Glen (2012); David Standridge (The Shipwright's Daughter, Mystic,
  Stonington) won Best Chef: Northeast 2024; 2023–2026 finalists and semifinalists recorded exactly (finalists are never called winners).

## Hand-checked guides (data/research/app/*.json, 166 places with a 2025–26 source each)
Four regional agents (Oct 5, 2026): New Haven/Naugatuck 51, Southeast + River Valley 47, Fairfield County 38, Capitol + Quiet Corner +
Litchfield Hills 21, plus 11 honorees. Verified closures in `data/research/closed*.json` are removed from every list (Jimmies of Savin
Rock, Charcoal Chef, Sycamore Drive-In, Collins Diner, Ford's Lobster, Buford's, Staropolska, 91 Diner…). Leads that couldn't be
verified are in `data/research/app/LEADS_*.md` (the research budget ran out first in the Capitol region and for diners statewide).
