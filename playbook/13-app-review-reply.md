# App Review: Guideline 2.1 "Information Needed" (prepared before submitting)

Wisconsin's first submission (2026-09-28) drew a 2.1 request for a physical-device screen recording plus six answers, because the
developer account has a short review history. Expect the same here. Record the screen recording **before** submitting and upload it
in **App Review Information → Attachment**; put the reply text below into **App Review Information → Notes** from the start (only the
reply: the Notes field holds 4,000 characters). If Apple asks anyway, paste it into **Reply to App Review** with the recording. Keep it
under 4,000 characters after any edit (count it). Recount the numbers after the final data build.

## Screen recording (Nick, on his iPhone, latest iOS)

Install through TestFlight first (internal group; the tester email must be the Apple ID under Settings › your name › Media &
Purchases on the phone, or TestFlight shows "not available"). Record with Control Center → Screen Recording, 60–120 s, no sound:

0. If CT Eats was installed before, delete it and reinstall from TestFlight, so location starts unset and the guides open in
   Featured order (with location on in Chicago, a Pepe's branch could sort first).
1. Start on the Home Screen and tap **CT Eats**. The recording must begin with the launch.
2. Home: scroll the guide cards a little.
3. Tap **New Haven Apizza**, then **Frank Pepe Pizzeria Napoletana**, the first row ("New Haven · Pizza", America's Classic).
4. Tap **Ratings, hours & photos**. Apple's place card opens. Close it.
5. Tap the **heart** (Save), then go back twice.
6. Tap the Home search box and type `lobster roll mystic`. Open one result.
7. Tap the **Map** tab, then **Lobster & clams**. Tap a numbered circle to zoom in, then a red pin, then the ⓘ in its bubble.
8. Tap **Saved**, where the saved place shows. Then **About**, and scroll to the sources.

## Reply text

```
Thank you. Here is the information requested. A screen recording from an iPhone running the latest iOS is attached. It starts at launch and shows the full flow.

1. Screen recording: attached. There is no account, login, user-generated content or paid content.

2. Purpose and audience: Connecticut Eats is a free guide to restaurants in Connecticut. Its focus is the state's food traditions: New Haven apizza (27 places), hot buttered lobster rolls and clam shacks (58), burger and hot dog icons such as Louis' Lunch and Meriden's steamed cheeseburgers (21), diners and dairy bars. Each was checked by hand in October 2026 against a 2025 or 2026 source: the restaurant's own website or menu, local news, or a tourism listing. It also lists 9,358 restaurants, cafés, bars and bakeries in the state's towns. It is for Connecticut residents and visitors deciding where to eat, with sourced facts and no ads, account or tracking.

3. How to use it (no login, no setup, no sample files needed):
- Guides tab (Home) → New Haven Apizza (or Lobster Rolls & Clam Shacks, Burger & Hot Dog Icons, Diners, Dairy Bars, Connecticut Icons, Oldest Places, All Restaurants) → tap a place.
- On a place, tap "Ratings, hours & photos" to open Apple Maps' own place card through MapKit. Directions, Call and Website are below it.
- Search from the Home search box by name, town, village or street ("apizza new haven", "lobster roll mystic").
- The Map tab shows each guide as pins. "My location" and the Nearest sort use location only if allowed, on the device.
- The heart saves a place on the device, under the Saved tab. The About tab lists the data sources, licenses and the independence statement.
- On iPad, a sidebar replaces the tabs; a place opens in the right-hand column.
- Location: if you're outside Connecticut (as App Review usually is), the map says so and stays on Connecticut, and distance sorting still works from where you are.
- "CT Eats" is the short Home Screen name of "Connecticut Eats: Restaurants".

4. External services and data:
- Apple MapKit: maps, local search to find a place's Apple Maps listing, and Apple's place card for live hours, photos and ratings.
- Core Location: optional, on-device only, for distance sorting.
- Core Spotlight: on-device indexing so places appear in iPhone search.
- No backend, accounts, analytics, advertising, payments or AI services. The restaurant data is bundled in the app.
- Bundled data: Overture Maps Foundation open place data (CDLA Permissive 2.0 / Apache 2.0 / CC0; license texts in the app); Connecticut DCP's public liquor-permit list (trade names and addresses only); City of Hartford food-license open data; Farmington Valley Health District's published ratings; U.S. Census town boundaries; James Beard award records (facts only); and our research of restaurants' own websites, menus and local news.
- The website with the privacy policy and support page is static and hosted on GitHub Pages: https://nickstrom5.github.io/connecticut-eats/

5. Regional differences: none. The content covers Connecticut; the app is offered in the United States and works the same everywhere.

6. Regulated or protected material: the app is not in a regulated industry and includes no protected third-party material. The data is open-licensed or public record, with attribution and licenses on the About tab. Ratings, hours and photos are shown only inside Apple's own place card through MapKit, under Apple's terms; the app stores no ratings or reviews. Health ratings appear only where a health department publishes official ones (the Farmington Valley Health District's 10 towns), labeled official with their dates. Restaurant names are factual references. Every website link was checked before release, and adult venues are excluded. The app is independent and not affiliated with any restaurant, casino, agency or the James Beard Foundation.

Support: work-with-nick@gmail.com
```

## If App Review cites Guideline 4.3(a) (Resolution Center only; never in the Notes)

Nick's call (2026-10-07): submit Connecticut Eats as its own app and keep this answer ready. Don't volunteer a comparison with the other
state apps. If Apple still asks for one app, the fallback is a single multi-state app with a state picker (Nick decides then).

```
Thank you for the review. Connecticut Eats is not a repackaged copy of another app. It is a guide built for Connecticut, from
Connecticut's own sources:
- Its guides are Connecticut's food traditions, each place checked by hand against a 2025 or 2026 source: New Haven apizza
  (27 places), hot buttered lobster rolls and clam shacks (58), Louis' Lunch and Meriden's steamed cheeseburgers, diners, dairy bars
  and Little Poland in New Britain.
- It shows the Farmington Valley Health District's official A/B/C/U restaurant ratings, with their dates. No other Connecticut health
  department publishes ratings, and the app says so.
- Its directory is built from Connecticut's own public records: the Department of Consumer Protection's liquor-permit list and the
  City of Hartford's food licenses, placed on Connecticut town boundaries, with its two tribal casinos' restaurants labeled by host.
- None of its places, research, guides or text is shared with any other app; the people who use it are in Connecticut or traveling
  there.
We're glad to answer any question about how the app works.
```
