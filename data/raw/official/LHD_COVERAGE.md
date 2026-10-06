# Connecticut restaurant inspections online: coverage by health department

Checked 2026-10-05. We visited each of the 61 local health departments' own websites and their food-protection pages, plus data.ct.gov, ArcGIS Online and CT DPH. Per-department detail and source URLs are in `lhd_coverage.json`, next to this file.

**Status key.** **Current**: results posted with dates in the last ~3 months. **Stale**: results posted, but old or on the retired scale. **Blocked**: the site refused automated access (403 or a bot check); we did not get around it, so these are unconfirmed. **None**: the site has licensing info but no inspection results.

**Counts.** 4 current (24 towns), 3 stale (3 towns), 12 blocked (29 towns), 42 none (115 towns). That is 171 jurisdictions: 169 towns plus 2 tribal nations.

## What we found

- **There is no bulk or official feed.** data.ct.gov has no restaurant-inspection dataset; its only restaurant data is liquor licenses. CT DPH publishes only the blank inspection form. Our searches found no CT inspection layer on ArcGIS Online, Socrata or Tableau Public. None of the 61 departments offers a CSV, an API or open data. Hartford's open data has a food *license* list, not inspections.
- **Only 4 departments have current results online, covering 24 towns, about 14% of the state:**
  - **Northeast District (NDDH)**, 12 towns: scanned PDF reports in a public document system, newest upload Aug 2026.
  - **Farmington Valley (FVHD)**, 10 towns: per-town web tables with its own A/B/C/U letter rating, newest Sept 30, 2026. This is the easiest to use.
  - **Fairfield**: monthly PDF bundles through Sept 2026. It says a searchable database is coming.
  - **Manchester**: only the last two months of scanned PDFs (Jul–Aug 2026).
- **Every format is different.** Even the current sources are a document system, HTML tables or monthly PDFs. Using any of them means building a separate scraper or PDF reader for each department.
- **The three sources found earlier are now stale.**
  - Darien's search portal stops at Dec 2025.
  - Norwalk's "Lighthouse" ratings still use the 100-point scale that was retired in Feb 2023, and the city's health pages no longer link to them.
  - Waterbury's PDFs stop in 2020.
- **Some blocked sites may have results we couldn't confirm.**
  - **Chatham**: links an inspection portal on MyHealthDepartment.
  - **Uncas**: has pages on the same platform.
  - **Newtown**: has a "Restaurant Inspection List" that a search snippet says was updated Sept 2026.
  - **Stamford**: according to the press, has a partial new search (since Dec 2025).

  Together these cover 21 more towns. Someone could check them by hand in a normal browser.
- **The big cities have nothing usable.** New Haven, Bridgeport and Hartford post no results. Stamford's is partial at best and Waterbury's is from 2020. The rest of the state answers by phone, email or FOI request. Since Feb 17, 2023, every CT report uses the FDA Food Code form, which has no score and no pass/fail. FVHD's letter grade is that district's own addition.

## By department

| Department | Towns | What's online | Newest date seen | Bulk? |
|---|---:|---|---|---|
| Northeast District Department of Health | 12 | **Current**: Public document system, PDF reports by town/year | 2026-08 | No |
| Farmington Valley Health District | 10 | **Current**: Per-town list, A/B/C/U letter rating + date | 2026-09 | No |
| Fairfield Health Department | 1 | **Current**: Monthly PDF bundles of reports | 2026-09 | No |
| Manchester Health Department | 1 | **Current**: Last 2 months of scanned PDFs | 2026-08 | No |
| Darien Health Department | 1 | **Stale**: Search portal (ct.healthinspections.us) | 2025-12 | No |
| Norwalk Health Department | 1 | **Stale**: "Lighthouse" ratings search, old 100-point scale | — | No |
| Waterbury Health Department | 1 | **Stale**: Yearly PDFs, newest year 2020 | 2020 (year only) | No |
| Uncas Health District | 11 | **Blocked**: Pages on MyHealthDepartment found via search, not linked from its site (we were blocked) | — | No |
| Chatham Health District | 6 | **Blocked**: Portal on MyHealthDepartment (we were blocked) | — | No |
| Newtown Health District | 3 | **Blocked**: "Restaurant Inspection List" page (we were blocked) | — | No |
| Brookfield Health Department | 1 | **Blocked**: Site blocked; has a "Food Establishment Inspections" page (contents unknown) | — | No |
| East Hartford Health and Social Services | 1 | **Blocked**: Site blocked; nothing found via search | — | No |
| Glastonbury Health Department | 1 | **Blocked**: Site blocked; nothing found via search | — | No |
| New Fairfield Health Department | 1 | **Blocked**: Site blocked; nothing found via search | — | No |
| New Haven Health Department | 1 | **Blocked**: Site blocked; nothing found via search | — | No |
| South Windsor Health Department | 1 | **Blocked**: Site blocked; nothing found via search | — | No |
| Stamford Department of Health and Human Services | 1 | **Blocked**: Site blocked; press says partial new search since Dec 2025 | — | No |
| Stratford Health Department | 1 | **Blocked**: Site has a bot check; nothing found via search | — | No |
| Wilton Health Department | 1 | **Blocked**: Site blocked; nothing found via search | — | No |
| Torrington Area Health District | 18 | **None**: Nothing (licensing info only) | — | No |
| Eastern Highlands Health District | 10 | **None**: Nothing (licensing info only) | — | No |
| Ledge Light Health District | 9 | **None**: Nothing ("please call") | — | No |
| North Central District Health Department | 8 | **None**: Nothing (its 2013 search database is gone) | — | No |
| Connecticut River Area Health District | 7 | **None**: Nothing (licensing info only) | — | No |
| Housatonic Valley Health District | 6 | **None**: Nothing (licensing info only) | — | No |
| Naugatuck Valley Health District | 6 | **None**: Reports page says "under construction", links 404 | — | No |
| Central Connecticut Health District | 4 | **None**: Nothing (licensing info only) | — | No |
| Quinnipiack Valley Health District | 4 | **None**: Nothing (licensing info only) | — | No |
| Aspetuck Health District | 3 | **None**: Nothing (licensing info only) | — | No |
| Chesprocott Health District | 3 | **None**: Nothing (licensing info only) | — | No |
| East Shore District Health Department | 3 | **None**: Nothing (licensing info only) | — | No |
| South Central Health District | 3 | **None**: Nothing (licensing info only) | — | No |
| Bristol-Burlington Health District | 2 | **None**: Nothing (licensing info only) | — | No |
| West Hartford-Bloomfield Health District | 2 | **None**: Nothing (licensing info only) | — | No |
| Bethel Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Bridgeport Health and Social Services | 1 | **None**: Nothing (licensing info only) | — | No |
| Cromwell Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Danbury Health and Human Services | 1 | **None**: Nothing (licensing info only) | — | No |
| Essex Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Greenwich Health Department | 1 | **None**: Nothing (records by email request) | — | No |
| Guilford Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Hartford Health & Human Services | 1 | **None**: Nothing (licensing info only) | — | No |
| Madison Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Mashantucket Pequot Tribal Health Services | 1 | **None**: Nothing (no public website) | — | No |
| Meriden Department of Health and Human Services | 1 | **None**: Nothing (licensing info only) | — | No |
| Middletown Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Milford Health Department | 1 | **None**: Nothing (page still describes old point grading) | — | No |
| Mohegan Tribal Health Department | 1 | **None**: Nothing (no public website) | — | No |
| Monroe Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| New Britain Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| New Canaan Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Orange Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Redding Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Ridgefield Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Sherman Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Somers Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Trumbull Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Wallingford Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| West Haven Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Westbrook Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
| Windsor Health Department | 1 | **None**: Nothing (licensing info only) | — | No |
