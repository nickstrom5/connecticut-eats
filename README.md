# ct-eats

Connecticut's version of the state restaurant products (models: `../wi-eats/`, `../chi-eats/`):

1. **Connecticut Eats**, a free iPhone and iPad app (App Store name "Connecticut Eats: Restaurants", subtitle "Apizza & Lobster Roll
   Guide", home screen "CT Eats"), and its generated website in `docs/` (GitHub Pages; planned connecticut.eatsranked.com).
2. **The web leaderboard** of every restaurant in Connecticut, a private claude.ai Artifact from `site/index.html`
   (https://claude.ai/artifact/JDWfmR2pey4q1RDYBDqWZF). Its JSON is not committed: it carries Google 2021-derived ratings.

| Path | What |
|---|---|
| `pipeline/` | Data: Overture listings, Census towns, DCP liquor permits, Hartford food licenses, Farmington Valley ratings, research, link check |
| `data/research/` | Hand-checked guides (`app/*.json`), James Beard honors, verified closures, leads |
| `ConnecticutEats/` | SwiftUI app (XcodeGen: `project.yml`) |
| `ConnecticutEatsTests/`, `ConnecticutEatsUITests/` | Unit tests (data rules, search, villages, guides) and the UI smoke tour |
| `scripts/` | `make-brand.swift` (icon, og image), `make-site.py` (website), `explore.js` (web app), `qa-site.py`, `capture-screenshots.sh` |
| `playbook/` | Sources and calibration (`12-sources.md`), naming (`05`), App Store listing (`06`), App Review reply (`13`) |

See `CLAUDE.md` for the rebuild commands and rules, and `playbook/12-sources.md` for what each source is and how reliable the map
listings proved against Connecticut's official lists.
