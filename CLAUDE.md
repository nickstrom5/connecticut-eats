# Connecticut Eats (ct-eats): notes for Claude Code sessions

Three products share this folder and one data pipeline:
- **The iOS/iPadOS app** "Connecticut Eats: Restaurants" (subtitle "Apizza & Lobster Roll Guide", home screen "CT Eats", bundle
  `com.connecticuteats.ios`; SwiftUI, iOS 18+), with its website in `docs/` (GitHub Pages; planned home connecticut.eatsranked.com).
- **The web leaderboard** (`site/`, untracked), a private claude.ai Artifact whose URL is in `LOCAL.md` (untracked; republish
  `site/index.html` with `connecticut.json`, `ct_detail.json`, `ct_shapes.json` from the same path to keep the URL). It uses Google 2021
  ratings and review signals; the app never does. Keep its URL out of tracked files.

Read `../STATE_EATS_PLAYBOOK.md` (the shared playbook next to this folder) and `playbook/12-sources.md` first. Never modify `../chi-eats/`,
`../wi-eats/`, `../co-eats/` or `../wa-eats/`.

## Nick's decisions (2026-10-05)
- Name, subtitle and home-screen name above; icon = a charred, oblong New Haven apizza on a sheet pan (`scripts/make-brand.swift`).
- Palette: UConn-inspired navy #000E2F, white, gray #7C878E (rules only, never text), tomato #B3261E as a fill with white text.
  One Connecticut element: a Long Island Sound shoreline wave. No Husky marks; no flag, seal or grapevine arms (CGS §3-106a).
- Farmington Valley Health District's official A/B/C/U ratings appear in place details only (with the date), never as a board.

## Data rules (the app's promise)
- The App Store build ships **no Google-derived data**: `CT_APP=1 .venv/bin/python pipeline/connecticut.py` writes
  `data/app/places.json`; copy it to `ConnecticutEats/Resources/places.json` after every rebuild.
- Only a license's **trade name (DBA)** is ever used. DCP's `name`/`businessname` (the permittee, often a person) is dropped at download,
  and the `gwv2-eswx` view with permittees and backers is never read. License-only rows whose trade name is just a legal entity are left out.
- The classics guides (apizza, lobster rolls & clam shacks, burger & hot dog icons, diners, dairy bars, Little Poland) list only
  **hand-checked** places (`hc`, matched to `data/research/app/*.json` or `honors.json`, each with a 2025–26 source). A listing merely
  named "… Diner" stays in the directory only. Closures with a source go in `data/research/closed*.json`.
- Research matching never merges two locations: a name-only match must be in the same town or village and at a compatible street
  number (The Spot at 163 Wooster St is not Pepe's at 157).
- Connecticut has no statewide inspection data. Say so; no inspection boards.
- Website links: `pipeline/check_websites.py` checks every candidate link politely and the export keeps only verified ones (fail closed:
  without `data/ct/website_check.json` no links ship; only http/https; an http link the checker saw end on https at the same host ships as
  https). The name test reads page text only, never the URL; meta-refresh and script redirects are followed one hop; blocked hosts match
  by registered domain, never as substrings; every chain store page is checked. Verdicts are dated and re-fetched after 14 days or when
  `RULES` changes; run `check_websites.py --fresh` before each submission, then rebuild. Never bypass bot protection (403s, 503s, bot
  checks, logins): a domain that refuses twice isn't asked again in that run.
- Place ids come from the source record (Overture GERS id, permit number, or researched name + town), never from names or rounded
  coordinates. `data/id_history.json` (committed) remembers every id ever exported; an id that disappears gets an alias to the same-named
  place within 300 m (`aliases` in places.json), and the app remaps saved places through it. `data_version` (a content hash) drives
  Spotlight re-indexing.
- Phones ship as `+1` and ten digits or not at all. Permit numbers (`lic`) don't ship.
- Licenses: only an ACTIVE status is a current permit (DCP flags LAPSED rows active=1). One permit, one place (best name match); the
  same number and street in another town is another address; a casino's umbrella permit (LCN) makes no listing "licensed".
- Farmington Valley ratings attach one-to-one, best match first, and only when the names share a distinctive word (never by address
  alone: the Exxon's C is not the Dunkin' next door).
- Hand-checked places show the researched address, and the researched name when the listing only adds a tail to it. A closure entry can
  list `alt_addresses` when the permit and the news disagree on the number.
- Hidden as non-restaurants: club permits, license-only hotel and caterer permits (unless the name says dining), cinemas, golf, bowling
  and other activity venues, member clubs, smoke/hookah/cigar lounges (The Owl Shop is kept: a licensed 1934 cigar bar), home bakers and
  delivery-only brands. Brand renames happen only when the rest of the name is generic ("Five Guys Flippin' Pies" is not Five Guys).
- Casino restaurants (Foxwoods, Mohegan Sun) are real places on tribal land, labeled with their host.

## Rebuild
```bash
.venv/bin/python pipeline/fetch_overture.py      # Overture places + address points -> data/ct
.venv/bin/python pipeline/fetch_towns.py         # Census towns -> data/ct/ct_towns.geojson, ct_shapes.json
.venv/bin/python pipeline/fetch_official.py      # DCP licenses, LHD lists -> data/raw/official (Hartford: see fetch notes in official.py)
.venv/bin/python pipeline/fetch_fvhd.py          # Farmington Valley ratings (polite; stops on any block)
cd pipeline
../.venv/bin/python official.py                  # geocode the license records -> data/ct/official.pkl
../.venv/bin/python listings.py                  # clean listings, towns, Google 2021 match -> data/ct/stage1.pkl
../.venv/bin/python calibrate.py                 # match rates -> data/ct/calibration.json
../.venv/bin/python reviews.py                   # streams UCSD reviews (never stored) -> data/ct/review_signals.parquet (web only)
../.venv/bin/python connecticut.py               # web leaderboard -> site/
CT_APP=1 ../.venv/bin/python connecticut.py      # app data -> data/app/places.json
../.venv/bin/python check_websites.py            # then rerun the CT_APP=1 export
```
The venv is an APFS clone of wi-eats' (`cp -c -R`), so it costs no disk.

## Build the app
- The Xcode project is generated: `xcodegen generate`. Never commit `ConnecticutEats.xcodeproj`.
- Compile check without a simulator: `DEVELOPER_DIR="/Applications/Xcode 1.app/Contents/Developer" xcodebuild build -project
  ConnecticutEats.xcodeproj -scheme ConnecticutEats -destination 'generic/platform=iOS Simulator' -derivedDataPath ./DerivedData CODE_SIGNING_ALLOWED=NO`
- **Archive and upload only with the public Xcode** (`/Applications/Xcode 1.app`, 27.0); `Xcode.app` is a 27.1 beta that App Review
  refuses. Check `DTXcodeBuild` in the archive. Bump `CURRENT_PROJECT_VERSION` for every upload.
- Simulators: this Mac is shared. Before booting, check `ps -u $(id -u) | wc -l` (wait if over ~2,300) and
  `xcrun simctl list devices | grep Booted` (wait if other sessions have 2+ booted). Use only our own "CT Eats 6.9" (iPhone 17 Pro Max,
  1320×2868) and "CT Eats iPad 13" (2064×2752), one booted at a time, shut down when done. UI tests need a signed runner (no
  `CODE_SIGNING_ALLOWED=NO`).
- Light mode only (`UIUserInterfaceStyle: Light`). `-screenshot <home|apizza|lobster|burgers|detail|map|icons|saved|about>` is DEBUG-only.

## Website (`docs/`)
Generated by `scripts/make-site.py` (never hand-edit `docs/*.html`); QA with `scripts/qa-site.py`. Until the
`connecticut.eatsranked.com` CNAME resolves, `CUSTOM_DOMAIN = None` and the site and the app's `Links.swift` use
https://nickstrom5.github.io/connecticut-eats/.

## Outward actions need Nick's explicit yes, every time
Creating the public repo, pushing, Pages, anything in App Store Connect, uploads, emails, records requests. Never submit for review or
accept agreements. Public commits use `329204362+nickstrom5@users.noreply.github.com`. Never publish scraped or Google data files.
