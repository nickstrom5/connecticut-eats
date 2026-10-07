# App Store listing (ASO): Connecticut Eats

Numbers here must match the app data and `site-numbers.json` (rewritten by `scripts/make-site.py`). Current (2026-10-07 build, after
the QA pass, the full link re-check and closures): 27 apizza places, 58 lobster rolls & clam shacks, 21 burger & hot dog icons, 11 diners,
34 dairy bars, 166 hand-checked places, 42 Connecticut Icons, 9,358 restaurants in 166 towns. **Recount after the last rebuild before pasting anything.**

## Name (30 max)
`Connecticut Eats: Restaurants` (29). Home Screen: `CT Eats`.

## Subtitle (30 max)
`Apizza & Lobster Roll Guide` (27)

Together they index: connecticut, eats, restaurants, apizza, lobster, roll, guide.

## Keywords (100 max, commas, no spaces, nothing from the name or subtitle, no trademarks)
`ct,new haven,hartford,stamford,mystic,pizza,clam,seafood,diner,ice cream,hot dog,burger,dairy` (93)

- Town names are the biggest win (Apple combines them with "restaurants" from the name). Norwalk, Groton and Waterbury didn't fit;
  rotate after a month of App Store Connect search-term data.
- No place names (Pepe's, Sally's, Louis' Lunch are restaurants' own marks).

## Promotional text (170 max, editable any time without review)
`Hand-checked New Haven apizza, lobster rolls, clam shacks, diners and dairy bars, plus 9,600+ Connecticut restaurants statewide, nearest first.` (143)

## Description
```
Connecticut's restaurants, from Wooster Street apizza to the shoreline lobster shacks.

Connecticut Eats is a free guide to eating in Connecticut: New Haven apizza, hot buttered lobster rolls and clam shacks, burger and hot dog icons, diners and dairy bars we checked open by hand, plus 9,358 restaurants, cafés, bars and bakeries in 166 of the state's 169 towns. No account, no ads.

CONNECTICUT GUIDES
• New Haven Apizza: the coal- and oven-fired pies, white clam to tomato, with the year each opened at its address where we could verify it.
• Lobster Rolls & Clam Shacks: hot buttered rolls and fried clams along the shore, with seasons where the shacks post them.
• Burger & Hot Dog Icons: Louis' Lunch, Meriden's steamed cheeseburgers and the long-running stands.
• Diners and Dairy Bars: classic diners and farm creameries.
• Connecticut Icons: James Beard honorees, America's Classics and places with 40 or more years at their address.
• Oldest Places: years at the same address, oldest first.

FIND IT FAST
• Sort by distance, or browse the map by apizza, lobster and clams, burgers and dogs, or dairy bars.
• Search by name, town, village or street: "apizza new haven", "lobster roll mystic", "noank".
• Filter by town or cuisine, hide chains.
• Save places for your next trip.
• Find hand-checked places from iPhone search (Spotlight).

LIVE DETAILS FROM APPLE MAPS
Tap "Ratings, hours & photos" on a place to open Apple Maps' own place card, with current hours, photos, ratings and directions.

HOW THE LISTS ARE BUILT
Every place in the Connecticut guides was checked by hand in October 2026 against a 2025 or 2026 source: its own website or menu, local news, or a tourism listing. The rest of the restaurants come from Overture Maps open data, the state's liquor-permit list and Hartford's food-license list; map listings are kept only at high confidence, measured against those official lists. In the Farmington Valley's 10 towns, a restaurant's official health rating is shown with its date; no other Connecticut health department publishes ratings, and most post no inspection results online. Website links are checked too. Nothing is ranked by star ratings.

PRIVATE BY DESIGN
No account, no tracking, no ads. Your location, if you share it, only sorts lists on your device. Saved places stay on your device.

Places open and close, and many shacks are seasonal, so check before you go. Spot a mistake? Email work-with-nick@gmail.com.

An independent app, not affiliated with any restaurant, chain, casino, university or government agency, or with the James Beard Foundation. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. Place data from Overture Maps Foundation (CDLA Permissive 2.0) and others; sources and licenses are on the About tab.
```

## What's New
Not shown for a first version. For 1.0.1 and later, say what changed.

## Screenshots (upload one at a time to the 6.9" slot; verify the order after a reload)
| # | File (iPhone 6.9" / iPad 13") | Caption (optional) |
|---|---|---|
| 1 | `home.png` / `ipad-home.png` | 9,358 Connecticut restaurants |
| 2 | `apizza.png` / `ipad-apizza.png` | New Haven apizza, checked open |
| 3 | `detail.png` / `ipad-detail.png` | Live hours & photos from Apple Maps |
| 4 | `lobster.png` / `ipad-lobster.png` | Lobster rolls & clam shacks |
| 5 | `map.png` / `ipad-map.png` | The map, by guide |
| 6 | `burgers.png` / `ipad-burgers.png` | Burger & hot dog icons |
| 7 | `icons.png` / `ipad-icons.png` | Connecticut icons, checked open |
| 8 | `saved.png` / `ipad-saved.png` | Save it for your next trip |

No negative boards and no U- or C-rated place in any image.

## Category
Primary Food & Drink, secondary Travel. Availability: United States. Price: Free.

## App Store Connect fields
- Version: `1.0.0` (must equal the build's CFBundleShortVersionString; App Store Connect defaults to "1.0").
- Support URL and Marketing URL: https://nickstrom5.github.io/connecticut-eats/ (there is no support.html; the home page has the
  support email). Privacy Policy URL (on the App Privacy page): https://nickstrom5.github.io/connecticut-eats/privacy.html.
  Switch all three to connecticut.eatsranked.com once that CNAME resolves.
- Copyright: `© 2026 Nicholas Soderstrom`.
- Sign-in required: untick. Contact: Nick's name, email and phone (private to App Review).
- Content rights: Yes, third-party content, with the rights (open data, public records, Apple's place card).
- App Privacy: Data Not Collected. Tracking: No.
- Age rating: Alcohol, Tobacco or Drug Use or References = Infrequent (bars, liquor permits, a historic cigar bar); Gambling = No
  (casino restaurants are listed as restaurants; the app has no gambling); Unrestricted web access = No (links open in Safari);
  everything else None/No → 13+.
- App Review attachment: the screen recording (see 13-app-review-reply.md), uploaded under App Review Information → Attachment.

## Review notes (fallback only: App Review Information → Notes holds 13-app-review-reply.md's reply, which already covers this; never paste both, the field holds 4,000 characters)
```
Connecticut Eats is a free guide to Connecticut restaurants. No login, no account, no purchases.

• Lists: the apizza, lobster roll & clam shack, burger & hot dog, diner and dairy bar guides were checked by hand (each place has a
  2025–2026 source on file). All other restaurants come from Overture Maps open data (CDLA Permissive 2.0) and public records: the
  Connecticut Department of Consumer Protection's liquor-permit list (trade names only) and the City of Hartford's food licenses.
  Attribution is on the About tab.
• Ratings, hours and photos are Apple's: tap "Ratings, hours & photos" on a place to open the MapKit place card. The app does not
  store or rank by ratings.
• Health ratings appear only for the 10 towns of the Farmington Valley Health District, which publishes official A/B/C/U ratings;
  each is labeled official and dated. No other Connecticut health department publishes ratings; most post no inspection results online.
• Location is optional and only sorts lists by distance on the device.

To try it: Guides → New Haven Apizza → Frank Pepe Pizzeria Napoletana → "Ratings, hours & photos".
```
