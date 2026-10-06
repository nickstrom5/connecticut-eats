# Connecticut research records (hand-checked guides and honors)

Everything here is **facts only**, each with source URLs. No review text, no ratings or stars from anyone, no readers' polls,
no "best of" votes, no Yelp/TripAdvisor/Google. A place enters a guide only when a **2025 or 2026 source** shows it open:
its own current site or menu (with a 2025–26 date, season or event on it), a dated 2025–26 news story, or a dated
2025–26 official listing (CTvisit, a town page). Never bypass bot protection: a 403, a 503 on repeat, a bot check,
a login wall or Facebook-only means the place goes in `app/LEADS.md`, not in the guide.

## `app/<region>.json`: a JSON array of places

```json
{
  "name": "Frank Pepe Pizzeria Napoletana",      // the name on the place's own sign/site (not a legal entity, never a person's legal name)
  "address": "157 Wooster St",                   // street address of THIS location
  "town": "New Haven",                           // one of Connecticut's 169 towns (the municipality, not the mailing village)
  "village": null,                               // the village/mailing name people use, if different: "Mystic", "Noank", "Niantic", "Storrs"
  "zip": "06511",
  "kinds": ["apizza"],                           // from the list below; a place can have several
  "dishes": ["white clam pie", "tomato pie"],    // signature dishes, plain words, from its own menu or the source
  "seasonal": false,                             // true for shacks and dairy bars that close for winter
  "season": null,                                // e.g. "late April to mid-October" when the source says so
  "founded": 1925,                               // year it opened AT THIS ADDRESS (not the brand's founding, not before a move); null if unsure
  "founded_note": "Opened on Wooster Street in 1925", // how the source states it (keep claims like "first hamburger" as the place's claim)
  "branch_of": null,                             // for a branch: the original's name ("Frank Pepe Pizzeria Napoletana, New Haven")
  "note": "One line in our own words: what it is and what it's known for.",
  "website": "https://pepespizzeria.com/",
  "open": true,
  "evidence_date": "2026-08",                    // month of the newest source showing it open
  "sources": ["https://...", "https://..."]      // every fact above must be supported by one of these
}
```

`kinds` (use these exact strings):
- `apizza` — New Haven–style apizza (coal- or oven-fired, thin, charred; "apizza" pies, white clam pie). Pepe's/Sally's/Modern/Zuppardi's and peers.
- `lobster roll` — serves a lobster roll; add `hot buttered` to `dishes` when it's the warm, buttered Connecticut style.
- `clam shack` — a seafood shack/stand (fried clams, whole-belly clams, chowder), often seasonal and counter-service.
- `burger icon` — a historic or signature burger place (Louis' Lunch, Shady Glen, Meriden steamed cheeseburgers).
- `steamed cheeseburger` — serves the Meriden-area steamed cheeseburger.
- `hot dog icon` — a historic or signature hot dog stand (Blackie's, Super Duper Weenie, Rawley's...).
- `diner` — a diner (ideally a classic diner car or long-running diner).
- `dairy bar` — an ice cream stand / dairy bar / farm creamery that scoops (often seasonal).
- `polish` — Polish restaurant, bakery or deli (New Britain's Little Poland on Broad Street, and elsewhere).
- `oldest` — operating since before 1900 at this address, or a colonial-era inn/tavern still serving food (verify the year).
- `grinder` — a signature grinder/sandwich shop (only notable, long-running ones).

## `honors.json`: James Beard and other honors (statewide)

Same place fields plus:
```json
  "james_beard": ["America's Classics 1999"],     // exact award and year; semifinalist/finalist/winner said exactly. NEVER call a finalist a winner.
  "other_honors": [],                             // only real honors (awards, guide inclusions). No polls, votes, "best of" lists, star ratings.
  "chef": "David Standridge"                      // the honored person, when the honor is a chef award
```

## `closed.json`
Places a 2025–26 source shows closed: `{"name", "address", "town", "closed_reason", "sources"}`.

## `app/LEADS.md`
Places that probably belong in a guide but couldn't be verified (Facebook-only, stale site, blocked, undated menu), grouped by region.
