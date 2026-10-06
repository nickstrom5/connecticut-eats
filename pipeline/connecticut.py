"""Stage 2: the Connecticut list -> site/connecticut.json (web leaderboard) or, with CT_APP=1, data/app/places.json (the app)

Statewide base: Overture Maps listings (stage1.pkl), each placed in one of the 169 towns by its point, kept by the rule calibrate.py
measured against official lists (Hartford's food licenses and DCP's liquor permits):
  - Meta listings and chain store feeds (AllThePlaces, DAC) are kept; single sources like Foursquare, BrightQuery and Microsoft are
    dropped (in Hartford 6-15% of them matched a licensed food business);
  - anything Google (2021) or Overture already shows as closed is dropped, unless it's on an official list.
Official records: every listing is checked against DCP's active on-premise liquor permits (restaurant, restaurant wine & beer, cafe,
hotel, craft cafe) and bakery licenses statewide, and in Hartford against the city's food-establishment licenses. Licensed
restaurants, bars and (in Hartford) full-service food businesses the map data doesn't have are added from the lists. Only the DBA
(trade name) of a license is ever used. Connecticut publishes no inspection results in bulk, so there are no inspection boards.
Web leaderboard only: ratings, reviews and price level from Google's Sep 2021 snapshot (UCSD Google Local), and dish signals from
Google reviews written through Sep 2021. CT_APP=1 drops all of that (the App Store build ships no Google-derived data).
"""
import os, re, sys, json, math, glob, hashlib, unicodedata, collections
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely.prepared import prep
from rapidfuzz import fuzz
from common import (norm_name, nice, name_sim, cuisine, FOOD_COST, MARGIN, MARGIN_CUISINE, SPEND, GENERIC, _stems, DATA, CT, ROOT, RAW,
                    canon_city, CUISINE_RULES)
from brands import brand_of
import official
from official import street_key, street_nums, ON_PREMISE
from listings_util import official_match, _close_words

APP = os.environ.get("CT_APP") == "1"
SITE = os.environ.get("CT_SITE") or (os.path.join(ROOT, "data", "app") if APP else os.path.join(ROOT, "site"))
GENERATED = "2026-10-05"
OVERTURE = "2026-09-23.1"
GOOD_SOURCES = {"meta", "AllThePlaces", "DAC"}
BASE = {1: 600_000, 2: 1_000_000, 3: 2_200_000, 4: 3_500_000}   # typical yearly sales by price tier (same as Chicago)
B_FIT = 0.764   # review-volume exponent fit on Chicago's published sales (chi-eats meta.model.b)
TAX_CUISINE = {
    "pizza_restaurant": "Pizza", "mexican_restaurant": "Mexican", "taco_restaurant": "Mexican", "texmex_restaurant": "Mexican",
    "sandwich_shop": "Sandwiches & Deli", "delicatessen": "Sandwiches & Deli", "bakery": "Bakery & Sweets", "donut_shop": "Bakery & Sweets",
    "dessert_shop": "Bakery & Sweets", "ice_cream_shop": "Bakery & Sweets", "bagel_shop": "Bakery & Sweets", "cupcake_shop": "Bakery & Sweets",
    "frozen_yogurt_shop": "Bakery & Sweets", "chocolatier": "Bakery & Sweets", "popcorn_shop": "Bakery & Sweets",
    "bar_and_grill_restaurant": "Bar & Pub", "gastropub": "Bar & Pub", "bar": "Bar & Pub", "brewery": "Bar & Pub", "pub": "Bar & Pub",
    "sports_bar": "Bar & Pub", "cocktail_bar": "Bar & Pub", "wine_bar": "Bar & Pub", "dive_bar": "Bar & Pub", "beer_bar": "Bar & Pub",
    "irish_pub": "Bar & Pub", "tiki_bar": "Bar & Pub", "speakeasy": "Bar & Pub", "hookah_bar": "Bar & Pub", "gay_bar": "Bar & Pub",
    "chinese_restaurant": "Chinese", "italian_restaurant": "Italian", "burger_restaurant": "Burgers",
    "breakfast_and_brunch_restaurant": "Breakfast & Diner", "diner": "Breakfast & Diner", "barbecue_restaurant": "BBQ",
    "chicken_restaurant": "Chicken & Wings", "chicken_wings_restaurant": "Chicken & Wings", "sushi_restaurant": "Japanese & Sushi",
    "japanese_restaurant": "Japanese & Sushi", "ramen_restaurant": "Japanese & Sushi", "seafood_restaurant": "Seafood", "poke_restaurant": "Seafood",
    "steakhouse": "Steakhouse", "indian_restaurant": "South Asian", "pakistani_restaurant": "South Asian", "thai_restaurant": "Thai",
    "hot_dog_restaurant": "Hot Dogs", "mediterranean_restaurant": "Mediterranean & Middle Eastern",
    "greek_restaurant": "Mediterranean & Middle Eastern", "middle_eastern_restaurant": "Mediterranean & Middle Eastern",
    "korean_restaurant": "Korean", "vietnamese_restaurant": "Vietnamese", "salad_bar": "Healthy & Vegan", "vegan_restaurant": "Healthy & Vegan",
    "vegetarian_restaurant": "Healthy & Vegan", "health_food_restaurant": "Healthy & Vegan", "coffee_shop": "Coffee & Café", "cafe": "Coffee & Café",
    "coffee_roastery": "Coffee & Café", "smoothie_juice_bar": "Healthy & Vegan", "juice_bar": "Healthy & Vegan", "bubble_tea_shop": "Coffee & Café",
    "tea_room": "Coffee & Café", "soul_food": "Soul & Southern", "southern_american_restaurant": "Soul & Southern",
    "cajun_and_creole_restaurant": "Seafood", "caribbean_restaurant": "Latin & Caribbean", "jamaican_restaurant": "Latin & Caribbean",
    "latin_american_restaurant": "Latin & Caribbean", "cuban_restaurant": "Latin & Caribbean", "puerto_rican_restaurant": "Latin & Caribbean",
    "peruvian_restaurant": "Latin & Caribbean", "brazilian_restaurant": "Latin & Caribbean", "colombian_restaurant": "Latin & Caribbean",
    "dominican_restaurant": "Latin & Caribbean", "salvadoran_restaurant": "Latin & Caribbean", "african_restaurant": "African",
    "ethiopian_restaurant": "African", "french_restaurant": "European", "german_restaurant": "European", "polish_restaurant": "European",
    "portuguese_restaurant": "European", "spanish_restaurant": "European", "tapas_bar": "European", "noodles_restaurant": "Chinese",
    "belgian_restaurant": "European", "russian_restaurant": "European", "fondue_restaurant": "European", "irish_restaurant": "European",
    "scandinavian_restaurant": "European", "european_restaurant": "European", "eastern_european_restaurant": "European",
    "hungarian_restaurant": "European", "british_restaurant": "European", "dutch_restaurant": "European", "ukrainian_restaurant": "European",
}
# Connecticut's two tribal casinos: their restaurants are real places, inspected by tribal health departments, shown "at" the casino
CASINOS = [("Foxwoods", 41.4734, -71.9600, ("TROLLEY LINE", "FOX TOWER")), ("Mohegan Sun", 41.4895, -72.0905, ("MOHEGAN SUN",))]
KINDS = ["apizza", "lobster roll", "clam shack", "steamed cheeseburger", "burger icon", "hot dog icon", "diner", "dairy bar", "polish", "oldest", "grinder"]
TAGS = ["apizza", "lobster", "clams", "steamed", "hotdog", "dairy", "diner", "polish"]   # bit order in the data files


def pct(s):
    return (s.rank(pct=True) * 100).round(1)


def km(la1, lo1, la2, lo2):
    return math.hypot((la1 - la2) * 111, (lo1 - lo2) * 83)


def curated_matcher(frame):
    """A researched place -> row of frame: same street number and street with a similar name; else a near-exact name in the same town;
    else a near-exact name that's unique statewide."""
    by_key, by_num = {}, {}
    for i, a in enumerate(frame.street):
        sk = street_key(a)[1]
        for n in street_nums(a):
            if sk:
                by_key.setdefault((n, sk), []).append(i)
                by_num.setdefault(n, []).append((sk, i))
    towns = [c.lower() if isinstance(c, str) else "" for c in frame.city]
    row_nums = [street_nums(a) for a in frame.street]
    vills = [c.lower() if isinstance(c, str) else "" for c in frame.get("village", pd.Series(None, index=frame.index))]
    ks = list(frame.k.fillna(""))

    def match(c):
        keys = {norm_name(m) for m in (c.get("match_names") or [])} | {norm_name(c["name"])}
        keys.discard("")
        _, sk = street_key(c.get("address") or "")
        cands = set()
        for n in street_nums(c.get("address") or ""):
            cands.update(by_key.get((n, sk), []))
            if sk:   # a spelling slip in the street ("Poquonock" / "Poquonnock")
                cands.update(i for sk2, i in by_num.get(n, []) if sk2 != sk and fuzz.ratio(sk, sk2) >= 85)
        best, bs = None, 0
        for i in cands:
            s_ = max((fuzz.token_set_ratio(m, ks[i]) for m in keys), default=0)
            if s_ >= 60 and s_ > bs:
                best, bs = i, s_
        if best is None and not c.get("chain"):
            # a near-exact name in the same town or village, never at a different street number ("The Spot" at 163 Wooster St is not
            # Pepe's at 157); statewide only when the research gives no street number (a second location elsewhere is its own place)
            ctown = (c.get("city") or "").lower()
            cvil = (c.get("village") or "").lower()
            cnums = street_nums(c.get("address") or "")
            ok = lambda i: not (cnums and row_nums[i] and not (cnums & row_nums[i]))
            sim = [max(fuzz.ratio(m, k) for m in keys) if k else 0 for k in ks]
            hits = [i for i, s_ in enumerate(sim) if s_ >= 90 and (towns[i] == ctown or (cvil and vills[i] == cvil)) and ok(i)] \
                or ([i for i, s_ in enumerate(sim) if s_ >= 95 and ok(i)] if not cnums else [])
            if len(hits) == 1:
                best = hits[0]
        return best
    return match


def load_research():
    """data/research/app/*.json (the hand-checked guides) and data/research/honors.json (James Beard), facts only, each with sources.
    A place in several files is one entry with everything the files know."""
    out, by = [], {}
    files = sorted(glob.glob(f"{DATA}/research/app/*.json")) + [f for f in [f"{DATA}/research/honors.json"] if os.path.exists(f)]
    for f in files:
        try:
            entries = json.load(open(f))
        except json.JSONDecodeError as e:
            print("!! research file doesn't parse, skipped:", f, e); continue
        for e in entries:
            if e.get("open") is False or not e.get("name") or not e.get("sources"):
                continue
            town = e.get("town") or e.get("city")
            key = (norm_name(e["name"]), (town or "").lower(), (street_key(e.get("address") or "")[0] or ""))
            c = by.get(key)
            if c is None:
                c = {"name": e["name"], "address": e.get("address"), "city": town, "village": e.get("village"), "zip": e.get("zip"),
                     "chain": False, "match_names": [e["name"].upper()], "founded": None, "open": True, "tags": [], "dishes": [],
                     "james_beard": [], "other_honors": [], "rsources": [], "research_only": True}
                by[key] = c; out.append(c)
            c["tags"] = list(dict.fromkeys(c["tags"] + [k.lower() for k in (e.get("kinds") or [])]))
            c["dishes"] = list(dict.fromkeys(c["dishes"] + (e.get("dishes") or [])))
            c["james_beard"] = list(dict.fromkeys(c["james_beard"] + (e.get("james_beard") or [])))
            c["other_honors"] = list(dict.fromkeys(c["other_honors"] + (e.get("other_honors") or [])))
            c["rsources"] = list(dict.fromkeys(c["rsources"] + (e.get("sources") or [])))
            for k in ("note", "website", "season", "branch_of", "chef", "village", "zip"):
                c[k] = c.get(k) or e.get(k)
            c["seasonal"] = bool(c.get("seasonal") or e.get("seasonal"))
            if not c.get("founded") and isinstance(e.get("founded"), int):
                c["founded"] = e["founded"]
            if e.get("note") and not c.get("iconic_reason"):
                c["iconic_reason"] = e["note"]
    return out


o = pd.read_pickle(f"{CT}/stage1.pkl")
o["city"] = o.town            # the town is the polygon's; the mailing name survives as `village` when it's a village
G = pd.read_pickle(f"{CT}/google21.pkl")
if APP:   # the App Store build ignores every Google 2021 match
    o["in21"] = False; o["closed21"] = False; o["gi"] = np.nan
calib = json.load(open(f"{CT}/calibration.json"))
TOWNWORDS = frozenset(w for t in o.town.dropna().unique() for w in norm_name(t).split())

# ---------------------------------------------------------------- official records: DCP statewide, Hartford's food licenses
F = official.load()
F = F[F.active & F.lat.notna()].reset_index(drop=True)
for jur, kinds in (("dcp", ON_PREMISE | {"brewery", "bakery", "club", "venue", "caterer"}), ("hfd", {"food"})):
    sel = o.index[o.town.eq("Hartford")] if jur == "hfd" else o.index
    R = F[(F.jur == jur) & F.kind.isin(kinds)]
    m = official_match(o.loc[sel].reset_index(drop=True), R.reset_index(drop=True), town_words=TOWNWORDS)
    o["off_" + jur] = np.nan
    for i, j in m.items():
        o.at[sel[i], "off_" + jur] = R.index[j]
o["off"] = o.off_dcp.where(o.off_dcp.notna(), o.off_hfd)
o["official"] = o.off.notna()
print("listings matched to an active license:", int(o.official.sum()), "| DCP:", int(o.off_dcp.notna().sum()), "| Hartford:", int(o.off_hfd.notna().sum()))

# ---------------------------------------------------------------- keep rule (see calibrate.py / calibration.json)
base_ok = ~o.j_junk & ~o.j_closedname & ~o.j_outside & ~o.j_far & ~o.ov_closed & ~(o.nowhere & ~o.in21) & o.town.notna()
CUR = load_research()
print("hand-checked research entries:", len(CUR))
_m = curated_matcher(o[base_ok].reset_index())
_bo = o.index[base_ok]
verified = pd.Series(False, index=o.index)
for c in CUR:
    j = _m(c)
    if j is not None:
        verified[_bo[j]] = True
keep = base_ok & (~o.closed21 | o.official | verified) & (o.src.isin(GOOD_SOURCES) | o.official | verified)
if APP:
    # measured against Hartford's food licenses (calibration.json): Meta listings with Overture confidence >= 0.95 matched a licensed
    # food business 67% of the time, Meta 0.90-0.95 40%; lower-confidence Meta 22%, BrightQuery >= 0.95 30% and the rest 7% are dropped
    conf = o.confidence.fillna(0)
    keep = base_ok & (o.official | verified | ((o.src == "meta") & (conf >= 0.9)) | o.src.isin(["AllThePlaces", "DAC"]))
print("kept listings:", int(keep.sum()), "of", len(o), "| dropped single-source (Foursquare/BrightQuery/Microsoft):",
      int((base_ok & ~o.src.isin(GOOD_SOURCES) & ~o.official & ~verified).sum()), "| closed per Google 2021:", int((base_ok & o.closed21 & ~o.official).sum()))
o = o[keep].reset_index(drop=True)

# ---------------------------------------------------------------- duplicate listings of one place
o["biz"] = o.off.map(lambda j: F.biz.iat[int(j)] if j == j else np.nan)
o["rank"] = o.official.astype(int) * 8 + o.in21.astype(int) * 4 + o.src.isin(GOOD_SOURCES).astype(int) * 2 + o.confidence.fillna(0)
o = o.sort_values("rank", ascending=False).reset_index(drop=True)
cell, drop = {}, set()
for i, r in o.iterrows():
    key = (round(r.lat / 0.001), round(r.lon / 0.0013))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for j in cell.get((key[0] + dy, key[1] + dx), []):
                d_ = math.hypot((o.lat.iat[j] - r.lat) * 111000, (o.lon.iat[j] - r.lon) * 83000)
                same_biz = r.biz == r.biz and r.biz == o.biz.iat[j] and name_sim(r.k, o.k.iat[j]) >= 80
                if same_biz or (d_ < 80 and (r.k == o.k.iat[j] or (fuzz.token_set_ratio(r.k, o.k.iat[j]) >= 92 and r.st & o.st.iat[j]))) or (
                        d_ < 150 and isinstance(r.brand_n, str) and r.brand_n == o.brand_n.iat[j]):
                    drop.add(i); break
            if i in drop: break
        if i in drop: break
    if i not in drop:
        cell.setdefault(key, []).append(i)
o = o.drop(index=list(drop)).reset_index(drop=True)
akey = [(b if isinstance(b, str) else k, n, c) if n and isinstance(c, str) else None for b, k, n, c in zip(o.brand_n, o.k, o.num, o.city)]
seen, dup = set(), []
for a in akey:   # o is sorted best-first, so the better-sourced copy survives
    dup.append(a is not None and a in seen)
    if a is not None:
        seen.add(a)
has_addr = o.num.notna()
for b, grp in o[o.brand_n.notna()].groupby("brand_n"):
    with_a, without = grp[has_addr[grp.index]], grp[~has_addr[grp.index]]
    for i, r in without.iterrows():
        if len(with_a) and (np.hypot((with_a.lat - r.lat) * 111, (with_a.lon - r.lon) * 83) < 1.5).any():
            dup[i] = True
o = o[~np.array(dup)].reset_index(drop=True)
near_dup = set()
for (k, c), grp in o[o.brand_n.isna() & o.k.fillna("").str.len().ge(4) & o.city.notna()].groupby(["k", "city"]):
    if len(grp) < 2 or not (_stems(k) - GENERIC):
        continue
    idx = list(grp.index)   # already best-first
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            if idx[b] in near_dup or idx[a] in near_dup:
                continue
            if math.hypot((o.lat[idx[a]] - o.lat[idx[b]]) * 111000, (o.lon[idx[a]] - o.lon[idx[b]]) * 83000) < 500 and not (o.official[idx[a]] and o.official[idx[b]]):
                near_dup.add(idx[b])
    good = grp[grp.in21 | grp.official]
    for i in grp.index[~(grp.in21 | grp.official)]:
        if i not in near_dup and len(good) and i not in good.index and (np.hypot((good.lat - o.lat[i]) * 111, (good.lon - o.lon[i]) * 83) < 1.5).any():
            near_dup.add(i)
o = o.drop(index=list(near_dup)).reset_index(drop=True)
print("after merging duplicate listings:", len(o), "(dropped", len(drop) + sum(dup) + len(near_dup), "; same name within 500 m:", len(near_dup), ")")
confirmed = ((o.src == "meta") & (o.confidence.fillna(0) >= 0.95)) if APP else o.in21
o["tier"] = np.where(o.official, "official", np.where(confirmed, "both", "listing"))

# ---------------------------------------------------------------- licensed places the map listings don't have
# DCP: active restaurant, cafe (bar), hotel and craft-cafe permits. Hartford: Class 2-3 food licenses (Class 1 is groceries and
# pharmacies, Class 4 schools, nursing homes and other institutions) whose name says food.
FOODWORD = re.compile(r"\b(?:PIZZA|PIZZERIA|APIZZA|RESTAURANT|GRILL|KITCHEN|CAFE|BAKERY|BAKE SHOP|DELI|DINER|BAR|PUB|TAVERN|TACOS?|TAQUERIA|BURGERS?|"
                      r"WINGS|CHICKEN|SUSHI|THAI|CHINA|CHINESE|JERK|PATTY|PATTIES|SEAFOOD|FISH|COFFEE|ESPRESSO|TEA|BISTRO|EATERY|BBQ|BAGELS?|DONUTS?|"
                      r"DUNKIN|SUBWAY|WENDYS|MCDONALDS|BURGER KING|TACO BELL|POPEYES|KFC|DOMINOS|STARBUCKS|PHO|RAMEN|HALAL|GYRO|KEBAB|EMPANADAS?|"
                      r"LOUNGE|CANTINA|TRATTORIA|STEAK|SOUL|CUISINE|FOOD)\b")
NOT_REST = re.compile(r"\b(?:SCHOOL|ACADEMY|ELEMENTARY|MIDDLE|HIGH|COLLEGE|UNIVERSITY|CHURCH|MINISTR\w*|SHELTER|SOUP KITCHEN|PANTRY|HEAD START|"
                      r"CHILD|DAYCARE|NURSING|HOSPITAL|MEDICAL|CENTER$|MARKET|GROCERY|SUPERMARKET|PHARMACY|CVS|WALGREENS|DOLLAR|WALMART|TARGET|"
                      r"STADIUM|PARK -|CONCESSIONS?|THEATRE|THEATER|XFINITY|SALVATION ARMY|YMCA|COMMUNITY|SOCIETY|CORRECTIONAL|DISTRIBUT\w*)\b")
found = set(o.biz.dropna())
add_d = F[(F.jur == "dcp") & F.kind.isin(ON_PREMISE) & ~F.biz.isin(found)].copy()
add_h = F[(F.jur == "hfd") & F.cls.isin(["Class 2", "Class 3"]) & ~F.biz.isin(found)].copy()
add_h = add_h[add_h.name.map(norm_name).str.contains(FOODWORD) & ~add_h.name.str.upper().str.contains(NOT_REST)]
# a Hartford license at the same address as a DCP permit already being added is the same place
add = pd.concat([add_d, add_h])
add["pri"] = add.kind.map({"restaurant": 0, "food": 1, "bar": 2, "hotel": 3})
add = add.sort_values("pri").drop_duplicates("biz")
ENTITY = re.compile(r"\b(?:LLC|L\.L\.C|INC|CORP|CORPORATION|LTD|LIMITED|LLP|ENTERPRISES?|HOLDINGS?|GROUP|MANAGEMENT|PARTNERS|ASSOCIATES)\b\.?", re.I)
# a trade name that is only a legal entity ("FLORIDA LLC", "GLOBAL LEAN OPERATIONS LLC") is never shown: kept only when the rest names food
ent = add.name.str.contains(ENTITY) & ~add.name.map(lambda n: norm_name(ENTITY.sub(" ", n))).str.contains(FOODWORD)
print("license-only records left out because the trade name is a legal entity:", int(ent.sum()), add.name[ent].head(8).tolist())
add = add[~ent]
# ... or plainly another kind of business ("Zhang's Remodels" holds a restaurant liquor permit): not a name to show as a restaurant
OTHER_BIZ = re.compile(r"\b(?:REMODEL\w*|CONSTRUCTION|CONTRACTING|CONTRACTORS?|PLUMBING|ROOFING|LANDSCAP\w*|AUTOMOTIVE|AUTO (?:BODY|REPAIR|SALES)|"
                       r"TIRES?|INSURANCE|REALTY|REAL ESTATE|HAIR|SALON|BARBER\w*|NAILS|CLEANERS|CLEANING|MOVERS|STORAGE|PROPERTIES)\b")
other = add.name.map(norm_name).str.contains(OTHER_BIZ)
print("license-only records left out because the trade name is another business:", int(other.sum()), add.name[other].tolist()[:8])
add = add[~other]
print("licensed places not in the map listings:", len(add), add.kind.value_counts().to_dict())
rows = []
for _, f in add.iterrows():
    rows.append({"id": f.lic, "name": f["name"], "street": f.addr, "city": f.town, "village": f.city if f.city and f.city != f.town else None,
                 "zip": f.zip or None, "lat": f.lat, "lon": f.lon, "cat": "bar" if f.kind == "bar" else "restaurant", "tax": None,
                 "confidence": np.nan, "brand": None, "src": "official", "official": True, "off": f.name, "biz": f.biz, "tier": "official",
                 "in21": False, "closed21": False, "dom": None, "web": None, "phone": None})
A = pd.DataFrame(rows)


def clean_official(n):
    n = re.split(r"\s*;\s*", n or "")[0]
    m = re.search(r"\bD/?B/?A\b\.?\s+(.+)$", n, flags=re.I)
    if m:
        n = m.group(1)
    n = re.sub(r"\s*#\s*\d+\w*.*$|\s*\(#?[A-Z]?\d+\)|\s+\d{3,}\s*$", "", n)
    n = ENTITY.sub("", n)
    n = re.split(r"\s*/\s*", n)[0] if "/" in n else n
    n = re.sub(r"\s+", " ", n).strip(" -,&/.")
    return nice(n) if n.isupper() or n.islower() else n


A["name"] = A.name.map(clean_official)
A = A[A.name.str.len() >= 2].reset_index(drop=True)
A["k"] = A.name.map(norm_name)
A["st"] = A.k.map(lambda k: _stems(k) - GENERIC if k else set())
A["num"] = A.street.map(lambda a: (re.match(r"\s*(\d+)", a or "") or [None, None])[1])
A["brand_n"] = A.k.map(brand_of)
# Google 2021 listings for the added rows (web only; the ones no map listing took)
taken = set(o.gi.dropna().astype(int))
grid = {}
for i, (la, lo) in enumerate(zip(G.latitude, G.longitude)):
    grid.setdefault((round(la / 0.0015), round(lo / 0.002)), []).append(i)
pairs = []
for ai, r in ([] if APP else A.iterrows()):
    if not r.k:
        continue
    gy, gx = round(r.lat / 0.0015), round(r.lon / 0.002)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for gi in grid.get((gy + dy, gx + dx), []):
                if gi in taken or not G.k.iat[gi] or G.closed21.iat[gi]:
                    continue
                dist = math.hypot((G.latitude.iat[gi] - r.lat) * 111000, (G.longitude.iat[gi] - r.lon) * 83000)
                if dist > 200:
                    continue
                s = name_sim(r.k, G.k.iat[gi])
                same_num = r.num is not None and G.num.iat[gi] == r.num
                if same_num and r.st & G.st.iat[gi]:
                    s = max(s, 80)
                if s < 95 and not r.st & G.st2.iat[gi]:
                    continue
                if (s >= 88 and dist < 150) or (s >= 75 and same_num):
                    pairs.append((s + (10 if same_num else 0) - dist / 25, ai, gi))
A["gi"] = np.nan
ta, tg = set(), set()
for sc, ai, gi in sorted(pairs, key=lambda t: -t[0]):
    if ai in ta or gi in tg:
        continue
    ta.add(ai); tg.add(gi); A.at[ai, "gi"] = gi
A["in21"] = A.gi.notna()
# a licensed place the address match missed can sit on top of its own map listing under a slightly different name: merge it into that
# listing, unless the listing already matched a license of its own (two neighbors are two places)
kgrid = {}
for j, (la, lo) in enumerate(zip(o.lat, o.lon)):
    kgrid.setdefault((round(la / 0.0015), round(lo / 0.002)), []).append(j)
merge, same_lic = {}, set()
for ai, r in A.iterrows():
    if not r.k:
        continue
    best, bs = None, -1
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for j in kgrid.get((round(r.lat / 0.0015) + dy, round(r.lon / 0.002) + dx), []):
                if j in merge.values():
                    continue
                dist = math.hypot((o.lat.iat[j] - r.lat) * 111000, (o.lon.iat[j] - r.lon) * 83000)
                s = name_sim(r.k, o.k.iat[j]) if o.k.iat[j] else 0
                if o.official.iat[j]:   # a listing with its own license: only the same business's second license
                    if dist <= 80 and s >= 95:
                        same_lic.add(ai)
                    continue
                shared = bool(r.st & o.st.iat[j]) or _close_words(r.st, o.st.iat[j])
                nested = len(r.k.split()) >= 2 and o.k.iat[j] and (set(r.k.split()) <= set(o.k.iat[j].split()) or set(o.k.iat[j].split()) <= set(r.k.split()))
                if (dist <= 60 and (s >= 88 or (shared and s >= 60) or nested)) or (dist <= 25 and s >= 75):
                    if s - dist / 10 > bs:
                        best, bs = j, s - dist / 10
    if best is not None:
        merge[ai] = best
for ai, j in merge.items():
    for c in ("official", "off", "biz", "tier"):
        o.at[o.index[j], c] = A.at[ai, c]
A = A.drop(index=list(set(merge) | same_lic)).reset_index(drop=True)
print("license rows merged into a map listing on the second pass:", len(merge), "| second licenses:", len(same_lic - set(merge)), "| license rows added:", len(A))
o = pd.concat([o, A], ignore_index=True)

# ---------------------------------------------------------------- hand-checked places the map listings don't have as a place to eat
import duckdb
OV = duckdb.connect().execute(f"""SELECT name, street, city, zip, lat, lon, cat, tax, web FROM '{CT}/overture_ct_bbox.parquet'
                                  WHERE region = 'CT' AND name IS NOT NULL""").df()
OV["k"] = OV.name.map(norm_name)
_m = curated_matcher(o)
missing = [c for c in CUR if not c.get("chain") and _m(c) is None]
added, not_placed = [], []
for c in missing:
    keys = {norm_name(m) for m in (c.get("match_names") or [])} | {norm_name(c["name"])}
    spot = None
    near = OV  # any-category Overture listing of the business (an inn, a farm stand, a marina shack) in the same area
    g = official.geocode(c.get("address") or "", c.get("city"), (c.get("zip") or "")[:5] or None)
    if g:
        spot = (g[0], g[1])
        cand = OV[(np.abs(OV.lat - g[0]) < 0.004) & (np.abs(OV.lon - g[1]) < 0.005)]
        sims = [max(fuzz.ratio(m, k) for m in keys) if isinstance(k, str) and k else 0 for k in cand.k]
        if len(sims) and max(sims) >= 85:
            h = cand.iloc[int(np.argmax(sims))]
            spot = (h.lat, h.lon)
    if spot is None:   # no address point: Overture's own listing of the place (any category) in the same town, by name
        town_l = {(c.get("city") or "").lower(), (c.get("village") or "").lower()} - {""}
        cand = OV[OV.city.fillna("").str.lower().isin(town_l)]
        sims = [max(fuzz.ratio(m, k) for m in keys) if isinstance(k, str) and k else 0 for k in cand.k]
        if len(sims) and max(sims) >= 88:
            h = cand.iloc[int(np.argmax(sims))]
            spot = (h.lat, h.lon)
    if spot is None:
        not_placed.append(c["name"]); continue
    added.append({"id": "research-" + c["name"], "name": c["name"], "street": c.get("address"), "city": c.get("city"), "village": c.get("village"),
                  "zip": c.get("zip"), "lat": spot[0], "lon": spot[1], "cat": "restaurant", "tax": None, "confidence": np.nan, "brand": None,
                  "src": "research", "official": False, "off": np.nan, "biz": np.nan, "tier": "both", "in21": False, "closed21": False,
                  "dom": None, "gi": np.nan, "k": norm_name(c["name"]), "st": _stems(norm_name(c["name"])) - GENERIC,
                  "num": (re.match(r"\s*(\d+)", c.get("address") or "") or [None, None])[1], "brand_n": None, "web": c.get("website")})
if added:
    o = pd.concat([o, pd.DataFrame(added)], ignore_index=True)
print("hand-checked places added (not in the map listings as a place to eat):", len(added), "| not placed:", not_placed)
# town from the point for every added row (license records give a mailing city)
TF = json.load(open(f"{CT}/ct_towns.geojson"))["features"]
TP = [(f["properties"]["town"], prep(shape(f["geometry"])), shape(f["geometry"])) for f in TF]


def town_at(x, y):
    pt = Point(x, y)
    for n, pg, g in TP:
        if pg.contains(pt):
            return n
    d, n = min((g.distance(pt), n) for n, pg, g in TP)
    return n if d < 0.015 else None


fix = o.src.isin(["official", "research"]) & o.lat.notna()
o.loc[fix, "city"] = [town_at(x, y) or c for x, y, c in zip(o.loc[fix, "lon"], o.loc[fix, "lat"], o.loc[fix, "city"])]
o["village"] = o.get("village", pd.Series(None, index=o.index))
# a village is a real village name: not one of the 169 towns (a neighbor's mailing name) and not a typo of its own town ("Prospe")
TOWN_SET = {n for n, _, _ in TP}
def real_village(v, town):
    if not isinstance(v, str) or not v.strip() or v in TOWN_SET:
        return None
    if isinstance(town, str) and (fuzz.ratio(v.lower(), town.lower()) >= 85 or town.lower().startswith(v.lower())):
        return None
    return v
o["village"] = [real_village(v, t) for v, t in zip(o.village, o.city)]

# ---------------------------------------------------------------- fields
gi = [int(v) if v == v and v is not None else None for v in o.gi]
o["rating"] = [G.avg_rating.iat[i] if i is not None else np.nan for i in gi]
o["reviews"] = [G.num_of_reviews.iat[i] if i is not None else np.nan for i in gi]
o["gprice"] = [len(G.price.iat[i]) if i is not None and isinstance(G.price.iat[i], str) else np.nan for i in gi]
o["gcats"] = ["|".join(G.category.iat[i] or []) if i is not None else "" for i in gi]
o["gmap_id"] = [G.gmap_id.iat[i] if i is not None else None for i in gi]
o["name_out"] = [b if isinstance(b, str) and fuzz.ratio(norm_name(n), norm_name(b)) >= 88 else nice(n) if n.isupper() or n.islower() else n
                 for n, b in zip(o.name, o.brand_n)]


def pick_cuisine(tax, k, gcats, raw):
    for c, pat in CUISINE_RULES[:-1]:          # a specific word in the name wins ("Sally's Apizza", "Staropolska")
        if pat.search(k or ""):
            return c
    if isinstance(tax, str) and tax in TAX_CUISINE:
        return TAX_CUISINE[tax]
    return cuisine(k, gcats, raw)              # "bar"-type names, then Google's categories


o["cuisine"] = [pick_cuisine(t, k, gc, n) for t, k, gc, n in zip(o.tax, o.k, o.gcats, o.name)]
first_cat = o.gcats.str.split("|").str[0].fillna("")
cafe_tax = o.tax.isin(["cafe", "coffee_shop"]) & o.cuisine.eq("Coffee & Café") & first_cat.ne("") & ~first_cat.str.contains(r"Coffee|Cafe|Café|Espresso|Tea|Bakery|Donut|Dessert|Ice cream|Juice|Breakfast")
o.loc[cafe_tax, "cuisine"] = [cuisine(k, g, "") for k, g in zip(o.loc[cafe_tax, "k"], o.loc[cafe_tax, "gcats"])]
o.loc[o.cat.isin(["bar", "brewery"]) & (o.cuisine == "American & Other"), "cuisine"] = "Bar & Pub"
o.loc[o.cat.isin(["coffee_shop", "cafe"]) & (o.cuisine == "American & Other"), "cuisine"] = "Coffee & Café"
o.loc[o.city.fillna("") == "", "city"] = None


# brand sanity: a brand rule that matched a name prefix must agree with the listing's website, Overture's brand feed, or its kind of food
def mode(x):
    return x.mode().iat[0]


bdom = {}
for b, grp in o[o.brand_n.notna()].groupby("brand_n"):
    d = grp.dom.dropna()
    if len(d) >= 3:
        top, n = collections.Counter(d).most_common(1)[0]
        if n >= 0.5 * len(d):
            bdom[b] = top
FAMILY = {"Chicken & Wings": "quick", "Burgers": "quick", "Hot Dogs": "quick", "Sandwiches & Deli": "cafe", "Pizza": "pizza",
          "Mexican": "mex", "Latin & Caribbean": "mex", "Coffee & Café": "cafe", "Bakery & Sweets": "cafe",
          "Breakfast & Diner": "cafe", "Healthy & Vegan": "cafe", "Steakhouse": "sitdown", "Seafood": "sea",
          "Bar & Pub": "bar", "Italian": "italian", "Chinese": "asian", "Japanese & Sushi": "asian", "Thai": "asian", "Korean": "asian",
          "Vietnamese": "asian", "South Asian": "sasian", "Mediterranean & Middle Eastern": "med", "European": "sitdown", "BBQ": "bbq",
          "Soul & Southern": "soul", "African": "african"}
brand_cuisine = o[o.brand_n.notna()].groupby("brand_n").cuisine.agg(mode)


def core(k):
    w = [x for x in k.split() if x not in GENERIC and x not in ("RESTAURANT", "RESTAURANTS", "CAFE", "STORE")]
    return " ".join(w) or k


def brand_ok(b, dm, cu, tax, obrand, name, src):
    if not isinstance(b, str):
        return None
    dm = dm if isinstance(dm, str) else None
    nk, bk = norm_name(name), norm_name(b)
    if src not in ("AllThePlaces", "DAC") and brand_of(nk) != b:
        return None                                 # only Overture's label says so
    ob = norm_name(obrand) if isinstance(obrand, str) else ""
    brand_feed = src in ("AllThePlaces", "DAC")
    label = bool(ob) and fuzz.token_set_ratio(ob, bk) >= 80
    related = brand_feed or fuzz.partial_ratio(bk, nk) >= 60 or (label and fuzz.partial_ratio(ob, nk) >= 60)
    if not related:
        return None
    squashed = re.sub(r"[^a-z]", "", b.lower())
    own_site = dm and (bdom.get(b) == dm or dm.split(".")[0].replace("-", "") in (squashed, squashed + "s"))
    exact = fuzz.ratio(core(nk), core(bk)) >= 90 or (label and fuzz.ratio(core(nk), core(ob)) >= 90) \
        or (len(bk) >= 6 and (nk == bk or nk.startswith(bk + " ")))
    if exact or own_site or (label and brand_feed):
        return b
    if dm and b in bdom and src != "BrightQuery":
        return None
    want = brand_cuisine.get(b)
    if isinstance(tax, str) and tax in TAX_CUISINE and want and FAMILY.get(cu) and FAMILY.get(want) and FAMILY[cu] != FAMILY[want]:
        return None
    return b


old_brand = o.brand_n.copy()
o["brand_n"] = [brand_ok(b, dm, cu, t, ob, n, sr) for b, dm, cu, t, ob, n, sr in zip(o.brand_n, o.dom, o.cuisine, o.tax, o.brand, o.name, o.src)]
rej = o[old_brand.notna() & o.brand_n.isna()]
print("brand matches rejected:", len(rej), collections.Counter(old_brand[rej.index]).most_common(10))
o.loc[o.brand_n.notna(), "name_out"] = [b if fuzz.ratio(norm_name(n), norm_name(b)) >= 80 or len(norm_name(n)) <= len(norm_name(b)) + 2 else n
                                        for n, b in zip(o.loc[o.brand_n.notna(), "name_out"], o.loc[o.brand_n.notna(), "brand_n"])]


def chain_mode(x):
    real = x[x != "American & Other"]
    return (real if len(real) else x).mode().iat[0]


CHAIN_CUISINE = {"Frank Pepe Pizzeria Napoletana": "Pizza", "Sally's Apizza": "Pizza", "Colony Grill": "Pizza", "Wood-n-Tap": "Bar & Pub",
                 "Plan B Burger Bar": "Burgers", "Archie Moore's": "Bar & Pub", "Duchess": "Burgers", "Friendly's": "American & Other",
                 "Bertucci's": "Italian", "Papa Gino's": "Pizza", "D'Angelo": "Sandwiches & Deli", "Moe's Southwest Grill": "Mexican",
                 "99 Restaurant": "American & Other", "Ninety Nine": "American & Other", "Max Burger": "Burgers", "Rizzuto's": "Italian",
                 "Dunkin'": "Coffee & Café", "Starbucks": "Coffee & Café", "Tim Hortons": "Coffee & Café", "Honey Dew Donuts": "Coffee & Café",
                 "Dairy Queen": "Bakery & Sweets", "Cold Stone Creamery": "Bakery & Sweets", "Baskin-Robbins": "Bakery & Sweets",
                 "Carvel": "Bakery & Sweets", "Rita's": "Bakery & Sweets", "Ben & Jerry's": "Bakery & Sweets", "Panera Bread": "Sandwiches & Deli",
                 "Einstein Bros. Bagels": "Bakery & Sweets", "Bruegger's": "Bakery & Sweets", "Texas Roadhouse": "Steakhouse",
                 "Tropical Smoothie Cafe": "Healthy & Vegan", "Smoothie King": "Healthy & Vegan", "Sweetgreen": "Healthy & Vegan",
                 "Shake Shack": "Burgers", "Five Guys": "Burgers", "Cracker Barrel": "American & Other", "Golden Corral": "American & Other",
                 "Nathan's Famous": "Hot Dogs", "Bareburger": "Burgers", "Little Pub": "Bar & Pub", "Bonefish Grill": "Seafood",
                 "Carrabba's": "Italian", "J. Timothy's": "Bar & Pub", "City Steam Brewery": "Bar & Pub"}
allc = o.loc[o.brand_n.notna(), ["brand_n", "cuisine"]]
all_brand_cuisine = allc.groupby("brand_n").cuisine.agg(chain_mode)
o.loc[o.brand_n.notna(), "cuisine"] = o.loc[o.brand_n.notna(), "brand_n"].map(lambda b: CHAIN_CUISINE.get(b) or all_brand_cuisine.get(b))

# price: Google price level, else the chain's usual level, else the cuisine's usual level (both from Connecticut's own Google data)
o["price"] = o.gprice
o["price_est"] = o.price.isna().astype(int)
bp = o[o.gprice.notna()].groupby("brand_n").gprice.median()
o.loc[o.price.isna() & o.brand_n.notna(), "price"] = o.brand_n.map(bp)
cp = o[o.gprice.notna()].groupby("cuisine").gprice.median()
o.loc[o.price.isna(), "price"] = o.cuisine.map(cp)
o["price"] = o.price.fillna(2).round().clip(1, 4).astype(int)

# chain size statewide. Unbranded same-name places count as one chain only when they share a website
bc = o.brand_n.value_counts()
o["chain_n"] = o.brand_n.map(lambda b: int(bc.get(b, 0)) if isinstance(b, str) else 1)
STORE_DOMS_ALL = {"cumberlandfarms.com", "stopandshop.com", "bigy.com", "shoprite.com", "pricechopper.com", "walmart.com", "target.com",
                  "costco.com", "bjs.com", "wholefoodsmarket.com", "traderjoes.com", "stewleonards.com", "xtramart.com", "alltown.com",
                  "7-eleven.com", "cvs.com", "walgreens.com"}
first_stem = o.k.fillna("").map(lambda k: next((w for w in k.split() if w not in GENERIC and len(w) >= 3), None))
grpkey = pd.Series([(d, s) if isinstance(d, str) and isinstance(s, str) and not isinstance(b, str) and d not in STORE_DOMS_ALL else None
                    for d, s, b in zip(o.dom, first_stem, o.brand_n)], index=o.index)
gsize = grpkey.dropna().value_counts()
member = [g is not None and gsize.get(g, 0) >= 2 for g in grpkey]
o.loc[member, "chain_n"] = [int(gsize[g]) for g, m in zip(grpkey, member) if m]
o["ckey"] = grpkey.map(lambda g: "|".join(g) if g else None)
chain_dom = set(o.ckey[member])
grp_cuisine = o[member].groupby("ckey").cuisine.agg(chain_mode)
o.loc[member, "cuisine"] = [grp_cuisine.get(k) for k in o.loc[member, "ckey"]]
sib = o.gprice.notna()
for key, sel in (("brand_n", o.brand_n.notna()), ("ckey", pd.Series(member, index=o.index))):
    med = o[sel & sib].groupby(key).gprice.median()
    fill = sel & (o.price_est == 1) & o[key].isin(med.index)
    o.loc[fill, "price"] = o.loc[fill, key].map(med).round().clip(1, 4).astype(int)
print("name-based chains:", len(chain_dom), "|", int(sum(member)), "locations")

o["bar"] = o.cat.isin(["bar", "brewery"]) | (o.cuisine == "Bar & Pub")
o["name_out"] = o.name_out.map(lambda n: re.sub(r"\b(?:Tcby|Ihop|Bj's|Bjs)\b", lambda m: {"tcby": "TCBY", "ihop": "IHOP"}.get(m.group(0).lower(), "BJ's"), n))
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]+")
CJK = r"[぀-ヿ㐀-鿿가-힯豈-﫿＀-￯]"
TAILWORDS = re.compile(r"^(?:best|award|voted|magazine|official|order|delivery|takeout|take out|catering|now open|open|to go|curbside|franchise|inside .*|"
                       r"(?:(?:ice cream|chocolates?|fudge|coffee|cafe|café|restaurant|bar|grill|pizza|apizza|shawarma|hookah lounge|seafood|lobster rolls?|"
                       r"bakery|deli|sandwiches|grinders|tacos|gifts?|shopping|treats|sweets|full bar|food|game room|drinks|spirits|live music|events|patio|"
                       r"lodging|rooms|resort|motel|cocktails|beer|wine|burgers|wings|craft beer|sports bar|and|&|,|-|\s)+))$", re.I)


def tidy(n, brand):
    """Emoji and non-Latin duplicates of an English name, LLC in the middle, marketing tails, notes in parentheses."""
    n = unicodedata.normalize("NFKC", n)
    if re.search(r"[ÃÂâð][\u0080-¿ŒœŠšŸŽžƒˆ˜–-›€™]", n):
        for enc in ("cp1252", "latin-1"):   # UTF-8 read as Windows-1252
            try:
                n = n.encode(enc).decode("utf-8"); break
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
    n = re.sub(r"[®™©]", "", EMOJI.sub("", n))
    if re.search(r"[A-Za-z]{3,}", re.sub(CJK, "", n)):
        n = re.sub(r"\s*\([^()]*" + CJK + r"[^()]*\)", "", n)
    latin = re.sub(CJK + "+", " ", n)
    if re.search(r"[A-Za-z]{3,}", latin) and re.search(CJK, n):
        n = re.sub(r"\(\s*\)", "", latin)
    m = re.match(r"^(.*?)[,\s]+(?:LLC|Inc)\.?\s*-{1,2}\s*(.+)$", n, flags=re.I)
    if m:
        n = m.group(2) if len(m.group(2).split()) >= 2 and len(m.group(1).split()) <= 2 else m.group(1)
    n = re.sub(r"[,\s]+(?:LLC|L\.L\.C|LLP|L\.L\.P|Inc|Corp)\.?(?=\s|$|,)", "", n, flags=re.I)
    n = re.sub(r"\s*\([^()]*\)\s*$", "", n) if re.sub(r"\s*\([^()]*\)\s*$", "", n).strip() else n
    n = re.sub(r",?\s+(?:CT|Conn\.?|Connecticut)\s*$", "", n)
    parts = re.split(r"\s+[-–]{1,2}\s+|--", n)
    if len(parts) > 1:
        tail = " ".join(parts[1:])
        if TAILWORDS.match(tail.strip()) or re.search(r"\b(?:Best|Award|Magazine|Voted|20\d\d)\b", tail):
            n = parts[0]
    if isinstance(brand, str):
        n = re.sub(r"\s*#\s*\d+\s*$", "", n)
    n = re.sub(r"\s+", " ", n).strip(" -–,") or n
    return nice(n) if n.isupper() and len(n) > 4 else n


o["name_out"] = [tidy(n, b) for n, b in zip(o.name_out, o.brand_n)]
o.loc[o.brand_n.notna(), "name_out"] = [b if norm_name(n).startswith(norm_name(b)) and len(norm_name(b)) >= 3 else n
                                        for n, b in zip(o.loc[o.brand_n.notna(), "name_out"], o.loc[o.brand_n.notna(), "brand_n"])]
o["spell"] = o.name_out.map(lambda n: re.sub(r"[^a-z0-9]", "", n.lower()))
o["name_out"] = o.groupby("spell").name_out.transform(lambda s: s.mode().iat[0] if len(s) > 1 else s.iat[0])
# names that aren't a business: a street address, "closed", a town or "Town of X", a lone generic word, no Latin letters
towns_l = set(o.city.dropna().str.lower()) | set(o.village.dropna().str.lower())
nm = o.name_out.fillna("")
junk = (nm.str.match(r"(?i)^\d+\s+(?:[NSEW]\.?\s+)?[\w.' ]+?\b(?:St|Street|Ave|Avenue|Dr|Drive|Rd|Road|Blvd|Ln|Lane|Way|Ct|Pl|Hwy|Pkwy|Trl|Tpke|Turnpike)\b\.?(?:\s*#\s*\w+)?(?:\s*,.*)?$")
        | nm.str.contains(r"(?i)(?:\bclosed|\bretired)\s*\)?\s*$") | (nm.str.lower().str.strip().isin(towns_l) & o.brand_n.isna())
        | nm.str.match(r"(?i)^(?:city|town|borough) of ") | nm.str.strip().str.lower().isin(["kitchen", "bar", "pub", "tavern", "grill", "deli", "pizza", "bakery", "coffee", "diner", "restaurant", "cafe", "café"])
        | ~nm.str.contains(r"[A-Za-z]"))
print("junk names dropped:", int(junk.sum()), nm[junk].head(12).tolist())
o = o[~junk].reset_index(drop=True)

# ---------------------------------------------------------------- not restaurants (hidden unless "include non-restaurants" is on)
STORE = re.compile(r"^(?:CUMBERLAND FARMS|XTRA ?MART|ALLTOWN(?: FRESH)?|MOBIL|SHELL|SUNOCO|GULF|CITGO|VALERO|BP|EXXON|SPEEDWAY|7 ELEVEN|PRIDE|"
                   r"STOP AND SHOP|STOP SHOP|BIG Y(?: WORLD CLASS MARKET)?|SHOPRITE|SHOP RITE|PRICE CHOPPER|WALMART\b.*|COSTCO\b.*|TARGET|"
                   r"BJS WHOLESALE.*|WHOLE FOODS(?: MARKET)?|TRADER JOES|ALDI|STEW LEONARDS|GEISSLERS|HIGHLAND PARK MARKET|CVS|WALGREENS|DOLLAR \w+|"
                   r"DASHMART|GOPUFF)$|\b(?:ZENSHI|SUSHI WITH GUSTO|HISSHO SUSHI|AFC SUSHI|SNOWFOX)\b|\b(?:GAS STATION|TRAVEL (?:CENTER|PLAZA)|TRUCK STOP|SERVICE PLAZA|PACKAGE STORE|LIQUORS? (?:STORE|SHOPPE?|OUTLET)|"
                   r"WINE (?:MERCHANTS?|SHOP|STORE|OUTLET)|WINE AND SPIRITS|AND SPIRITS$|VENDING|COMMISSARY|FOOD PANTRY|MEAT MARKET|BUTCHER|"
                   r"GHOST KITCHEN|VIRTUAL KITCHEN|MRBEAST|MR BEAST|ITS JUST WINGS|WOW BAO|GENTLEM[AE]NS CLUB|TRAMPOLINE|INDOOR PLAYGROUND|"
                   r"LINDT|ROCKY MOUNTAIN CHOCOLATE|JELLY BELLY)\b")
REALFOOD = re.compile(r"\b(?:RESTAURANT|GRILL|BAR|PUB|TAVERN|PIZZA|APIZZA|CAFE|KITCHEN|STEAK|BISTRO|DINER|BREWING|BREWERY|TAP|SALOON|"
                      r"TAPROOM|LOUNGE|INN|EATERY|BURGERS?|BBQ|TACOS?|DRIVE IN|DELI|COFFEE|ICE CREAM|CREAMERY|BAKERY|DAIRY|SEAFOOD|LOBSTER|CLAM|DONUTS?)\b")
CANDY = re.compile(r"\b(?:CANDY|CANDIES|FUDGE|POPCORN|CONFECTION\w*|CHOCOLATES?|CHOCOLATIER|TRUFFLES?|SWEETS? SHOPPE?|KETTLE CORN|NUTRITION)\b")
HARD = re.compile(r"\b(?:AIRPORT|TERMINAL|CONCOURSE|GATE [A-Z]?\d+|BRADLEY INTERNATIONAL|XL CENTER|RENTSCHLER|DUNKIN PARK|TOTAL MORTGAGE ARENA|"
                  r"LEVY|SODEXO|ARAMARK|DELAWARE NORTH|CENTERPLATE|COMPASS GROUP|CHARTWELLS|BON APPETIT|HMSHOST|EUREST|GUCKENHEIMER|SSP AMERICA|"
                  r"DELTA SKY CLUB|COMMISSARY|DINING HALL|UNIVERSITY DINING|YALE DINING|UCONN DINING|CORRECTIONAL|PRISON|CAREERS|TRUCK ENTRANCE)\b")
SOFT = re.compile(r"\b(?:STADIUM|ARENA|FESTIVAL|CONCESSIONS?|FOOD ?SERVICES?|UNIVERSITY|COLLEGE|SCHOOL|ACADEMY|ELEMENTARY|STUDENT|CAMPUS|"
                  r"HOSPITAL|MEDICAL CENTER|CLINIC|HEALTH CENTER|SENIOR|RETIREMENT|ASSISTED LIVING|NURSING|CARE CENTER|REHAB|CHURCH|PARISH|"
                  r"CONGREGATION|TEMPLE|SYNAGOGUE|MOSQUE|MINISTR(?:Y|IES)|VFW|AMERICAN LEGION|AMVETS|FRATERNAL ORDER|ELKS LODGE|"
                  r"MOOSE LODGE|KNIGHTS OF COLUMBUS|COUNTRY CLUB|GOLF CLUB|GOLF COURSE|YACHT CLUB|ATHLETIC CLUB|SOCIAL CLUB|BEACH CLUB|"
                  r"SPORTSMEN'?S CLUB|ROD AND GUN|FISH AND GAME|CATERING|CATERERS?|BANQUETS?|BANQUET HALL|EVENT (?:CENTER|VENUE|SPACE)|"
                  r"CONVENTION CENTER|CONFERENCE CENTER|MUSEUM|ZOO|AQUARIUM|THEATER|THEATRE|CINEMAS?|BOWLING|LANES|"
                  r"HOTEL|MOTEL|INN AND SUITES|SUITES|MARRIOTT|HILTON|HYATT|SHERATON|WESTIN|HOLIDAY INN|HAMPTON INN|FAIRFIELD INN|RESIDENCE INN|"
                  r"COURTYARD|SPRINGHILL|RADISSON|BEST WESTERN|COMFORT INN|SUPER 8|RED ROOF|DAYS INN|GREAT WOLF|"
                  r"CORPORATE|EMPLOYEE|CAFETERIA|MOBILE|FOOD TRUCK|KIOSK|GYM|FITNESS|YMCA|YWCA|BOYS AND GIRLS CLUB|DAYCARE|DAY CARE|CHILD CARE|"
                  r"CHILDCARE|LEARNING CENTER|JAIL|MILITARY|NATIONAL GUARD|SUBMARINE BASE|COAST GUARD ACADEMY|BUILDING)\b")
kd = o.name_out.map(norm_name).fillna("")
k_ = o.k.fillna("")
busy = o.reviews.fillna(0) >= 200
gfirst = o.gcats.fillna("").str.split("|").str[0]
plainly_food = kd.str.contains(REALFOOD) | o.cat.isin(["bar", "brewery", "coffee_shop", "cafe"]) \
    | gfirst.str.contains(r"\b(?:Bar|Pub|Restaurant|Cafe|Café|Coffee|Tavern|Grill|Brewery|Diner|Bakery)\b", regex=True)
brand_store = o.brand_n.isin(["Cumberland Farms", "Stop & Shop", "Big Y", "ShopRite", "Price Chopper", "Xtra Mart", "Alltown",
                              "Grade A ShopRite", "Whole Foods Market", "Trader Joe's", "7-Eleven"])
store = kd.str.contains(STORE) | brand_store | (o.dom.isin(STORE_DOMS_ALL) & ~plainly_food) \
    | (kd.str.contains(CANDY) & ~kd.str.contains(REALFOOD) & ~busy)
venue = kd.str.contains(HARD) | k_.str.contains(HARD) | o.name.fillna("").str.upper().str.contains(r"\(T-?\d|\bGATE [A-Z]?\d", regex=True) \
    | (kd.str.contains(SOFT) & ~(busy | plainly_food))
LICENSE_ONLY_NONREST = re.compile(r"\b(?:APARTMENTS?|POOLS?|SWIM|AQUATIC|SPORTSM[AE]NS?|GUN CLUB|ASSOCIATION|ATTN|C O|EVENTS?|STUDIOS?|"
                                  r"BOATS|SPORTS CENTER|HOSPITALITY GROUP|KNIGHTS|HEALTH|CONDOMINIUMS?|HOMEOWNERS|NEIGHBORHOOD|COMMUNITY|"
                                  r"PARKS AND REC|RECREATION|CAMP|BIBLE|FOUNDATION|SOCIETY|COUNCIL|LEAGUE|UNION|INSTITUTE|CENTER$|FARMS?|AMUSEMENT|"
                                  r"ENTERTAINMENT|CORPORATION|HOLDINGS|MANAGEMENT|VENTURES|FIELD|PERFORMING ARTS|VINEYARDS?|WINERY)\b")
lic_only = o.src.eq("official")
club = kd.str.contains(r"\bCLUB\b") & ~kd.str.contains(r"NIGHT ?CLUB|CLUB CAR|CLUB SANDWICH|SUPPER CLUB")
venue |= lic_only & (kd.str.contains(LICENSE_ONLY_NONREST) | club) & ~busy
# airports: Bradley (Windsor Locks) and Tweed (New Haven/East Haven) terminals
for la, lo in ((41.9389, -72.6832), (41.2637, -72.8868)):
    venue |= (np.hypot((o.lat - la) * 111, (o.lon - lo) * 83) < 0.6) & ~busy
# betting lounges (a sportsbook is gaming first) and private member clubs (lodges, fire companies, legion posts) aren't restaurants
# open to the public, whatever their category says
GAMING = re.compile(r"\b(?:SPORTSBOOK|SPORTS BOOK|OFF TRACK|OTB|TELETRACK|BETTING|SLOT|SLOTS|GAMING)\b")
MEMBERS = re.compile(r"\b(?:ELKS|MOOSE|LODGE NO|HOSE CO(?:MPANY)?|FIRE (?:COMPANY|DEPARTMENT|DEPT)|VOLUNTEER FIRE|VFW|AMERICAN LEGION|"
                     r"KNIGHTS OF COLUMBUS|SONS OF ITALY|AMVETS|ORDER OF EAGLES|EAGLES AERIE|POLISH FALCONS|ROD AND GUN|FISH AND GAME|"
                     r"SPORTSM[AE]NS|YACHT CLUB|COUNTRY CLUB|GOLF CLUB|BEACH CLUB|SOCIAL CLUB|ATHLETIC CLUB|SWIM CLUB|TENNIS CLUB)\b")
gaming, members = kd.str.contains(GAMING), kd.str.contains(MEMBERS)
print("betting venues hidden:", int(gaming.sum()), o.name_out[gaming].tolist()[:6], "| member clubs hidden:", int(members.sum()))
o["venue"] = store | venue | gaming | members
print("non-restaurants flagged:", int(o.venue.sum()), "| stores:", int(store.sum()), "| venues:", int((venue & ~store).sum()))
# host venues: the two tribal casinos
st_up = o.street.fillna("").str.upper()
o["host"] = None
for name, la, lo, streets in CASINOS:
    at = (np.hypot((o.lat - la) * 111, (o.lon - lo) * 83) < 0.8) | st_up.str.contains("|".join(streets))
    o.loc[at & o.host.isna(), "host"] = name
print("restaurants at the casinos:", o.host.value_counts().to_dict())

# ---------------------------------------------------------------- Connecticut signals from 2021 reviews (web leaderboard only)
SIGS = ["apizza", "lobster", "hotbutter", "clams", "steamed", "hotdog", "grinder", "icecream"]
if not APP and os.path.exists(f"{CT}/review_signals.parquet"):
    sig = pd.read_parquet(f"{CT}/review_signals.parquet").set_index("gmap_id")
    for k in SIGS:
        o["n_" + k] = o.gmap_id.map(sig["n_" + k]).fillna(0).astype(int)
        o["r_" + k] = o.gmap_id.map(sig["r_" + k])
else:
    for k in SIGS:
        o["n_" + k] = 0; o["r_" + k] = np.nan
share = lambda k: o["n_" + k] / o.reviews.clip(lower=1)
nkey = o.name_out.map(norm_name).fillna("")
o["t_apizza"] = nkey.str.contains(r"\bAPIZZA\b") | ((o.cuisine == "Pizza") & (o.n_apizza >= 3) & (share("apizza") >= 0.03))
o["t_lobster"] = (o.n_lobster >= 3) & (share("lobster") >= 0.03)
o["t_clams"] = nkey.str.contains(r"\bCLAM SHACK\b|\bCLAM ?CASTLE\b") | ((o.n_clams >= 3) & (share("clams") >= 0.03) & o.cuisine.isin(["Seafood", "American & Other", "Bar & Pub"]))
o["t_steamed"] = (o.n_steamed >= 2) | nkey.str.contains(r"\bSTEAMED CHEESEBURGERS?\b")
o["t_hotdog"] = (o.cuisine == "Hot Dogs") | ((o.n_hotdog >= 5) & (share("hotdog") >= 0.10))
o["t_dairy"] = nkey.str.contains(r"\bDAIRY BAR\b|\bCREAMERY\b") | ((o.n_icecream >= 5) & (share("icecream") >= 0.25) & o.cuisine.eq("Bakery & Sweets") & o.brand_n.isna())
o["t_diner"] = nkey.str.contains(r"\bDINER\b")
o["t_polish"] = nkey.str.contains(r"\bPOLISH|POLSKI|POLSKA|STAROPOLSKA|PODLASIE|CRACOVIA|KIELBASA|PIEROGI")
if APP:   # tags in the app come from names and the hand-checked research only, never from reviews
    o["t_apizza"] = nkey.str.contains(r"\bAPIZZA\b"); o["t_lobster"] = False; o["t_steamed"] = nkey.str.contains(r"\bSTEAMED CHEESEBURGERS?\b")
    o["t_clams"] = nkey.str.contains(r"\bCLAM SHACK\b"); o["t_hotdog"] = o.cuisine == "Hot Dogs"; o["t_dairy"] = nkey.str.contains(r"\bDAIRY BAR\b|\bCREAMERY\b")
print("tags:", {t: int(o["t_" + t].sum()) for t in TAGS})

# ---------------------------------------------------------------- the hand-checked research (data/research), honors
for col in ("jbf", "honors", "icon", "founded", "cur_tags", "dishes", "season", "branch", "rnote", "rsite", "chef", "rsrc"):
    o[col] = None
o["seasonal"] = False
match_curated = curated_matcher(o)
o["hc"] = False   # hand-checked: matched to an open research entry with a 2025-26 source
matched_cur, unmatched = 0, []
for c in CUR:
    best = match_curated(c)
    if best is None:
        unmatched.append(c["name"] + " (" + (c.get("city") or "") + ")")
        continue
    matched_cur += 1
    i = o.index[best]
    o.at[i, "hc"] = True
    for col, vals in (("jbf", c.get("james_beard")), ("honors", c.get("other_honors")), ("cur_tags", c.get("tags")), ("dishes", c.get("dishes"))):
        if vals:
            have = [x for x in (o.at[i, col] or "").split("; ") if x]
            o.at[i, col] = "; ".join(have + [v for v in dict.fromkeys(vals) if v not in have])
    for col, v in (("icon", c.get("iconic_reason")), ("founded", c.get("founded")), ("season", c.get("season")), ("branch", c.get("branch_of")),
                   ("rnote", c.get("note")), ("rsite", c.get("website")), ("chef", c.get("chef")), ("rsrc", (c.get("rsources") or [None])[0])):
        if v and not o.at[i, col]:
            o.at[i, col] = v
    if c.get("seasonal"):
        o.at[i, "seasonal"] = True
    if c.get("village") and not isinstance(o.at[i, "village"], str):
        o.at[i, "village"] = c["village"]
print(f"research entries matched: {matched_cur}/{len(CUR)}; unmatched ({len(unmatched)}): {unmatched[:20]}")
closed_v = []
for f in sorted(glob.glob(f"{DATA}/research/closed*.json")):
    try:
        closed_v += [dict(c, city=c.get("town") or c.get("city")) for c in json.load(open(f))]
    except json.JSONDecodeError as e:
        print("!! closed file doesn't parse, skipped:", f, e)
gone = [(c["name"], o.name_out.iat[b]) for c in closed_v for b in [match_curated(c)] if b is not None]
drop_closed = {o.index[b] for c in closed_v for b in [match_curated(c)] if b is not None}
o = o.drop(index=list(drop_closed)).reset_index(drop=True)
print("verified closed, removed:", len(drop_closed), gone)
# ---------------------------------------------------------------- Farmington Valley Health District's official A/B/C/U ratings (10 towns)
# Posted at each restaurant and published by FVHD as one page per town (pipeline/fetch_fvhd.py). Shown only with its date.
o["fv_r"] = None; o["fv_d"] = None
FVP = f"{RAW}/official/fvhd_ratings.json"
FV_FETCHED = None
if os.path.exists(FVP):
    FV = json.load(open(FVP)); FV_FETCHED = FV.get("fetched")
    by_town = {t: g for t, g in o.assign(kk=o.name_out.map(norm_name)).groupby("city")}
    taken_fv, n_fv, miss_fv = set(), 0, []
    for e in FV["ratings"]:
        g = by_town.get(e["town"])
        if not e.get("date") or g is None:
            continue
        k = norm_name(e["name"]); nums = street_nums(e.get("address") or ""); sk = street_key(e.get("address") or "")[1]
        best, bs = None, 0
        for i, kk, st in zip(g.index, g.kk, g.street):
            if i in taken_fv or not kk:
                continue
            sim = name_sim(k, kk)
            same_addr = bool(nums & street_nums(st)) and sk and street_key(st)[1] == sk
            shared = bool((_stems(k) - GENERIC) & (_stems(kk) - GENERIC))
            sc = sim + (20 if same_addr else 0)
            if ((same_addr and (sim >= 60 or shared)) or sim >= 90) and sc > bs:
                best, bs = i, sc
        if best is None:
            miss_fv.append(e["name"]); continue
        taken_fv.add(best); n_fv += 1
        o.at[best, "fv_r"] = e["rating"]; o.at[best, "fv_d"] = e["date"]
    print("Farmington Valley ratings matched:", n_fv, "of", len(FV["ratings"]), "| unmatched (groceries, schools, places not on our list):", len(miss_fv), miss_fv[:10])
tags_c = o.cur_tags.fillna("").str.lower()
for t, kinds in (("apizza", ["apizza"]), ("lobster", ["lobster roll"]), ("clams", ["clam shack"]), ("steamed", ["steamed cheeseburger"]),
                 ("hotdog", ["hot dog icon"]), ("dairy", ["dairy bar"]), ("diner", ["diner"]), ("polish", ["polish"])):
    o["t_" + t] |= tags_c.map(lambda s: any(k in s.split("; ") for k in kinds))
# a hand-checked place the map data files as "American & Other" takes its cuisine from what the research says it is
KIND_CUISINE = [("apizza", "Pizza"), ("steamed cheeseburger", "Burgers"), ("burger icon", "Burgers"), ("hot dog icon", "Hot Dogs"),
                ("diner", "Breakfast & Diner"), ("polish", "European"), ("lobster roll", "Seafood"), ("clam shack", "Seafood"),
                ("dairy bar", "Bakery & Sweets"), ("grinder", "Sandwiches & Deli")]   # the signature first: a hot dog stand that sells lobster rolls
generic = o.hc & o.cuisine.eq("American & Other")
o.loc[generic, "cuisine"] = [next((c for k, c in KIND_CUISINE if k in t.split("; ")), "American & Other") for t in tags_c[generic]]
print("hand-checked places given a cuisine from their research kind:", int((generic & o.cuisine.ne("American & Other")).sum()))
o["t_burger"] = tags_c.str.contains("burger icon") | tags_c.str.contains("steamed cheeseburger")
o["t_oldest"] = tags_c.str.contains("oldest")
o["honored"] = o.hc
o.loc[o.honored, "venue"] = False
o["bar"] = o.cat.isin(["bar", "brewery"]) | (o.cuisine == "Bar & Pub")

# ---------------------------------------------------------------- sales / profit: the Chicago model (web leaderboard only)
auv = {a["brand"]: a for a in json.load(open(f"{DATA}/chain_auv.json")) if a.get("auv_usd")}
for mine, theirs in {"Ninety Nine": "99 Restaurant"}.items():
    if theirs in auv and mine not in auv:
        auv[mine] = auv[theirs]
med_rev = o[o.reviews.notna() & (o.chain_n < 5)].groupby("price").reviews.median()
rel = (o.reviews + 10) / (o.price.map(med_rev) + 10)
bump = np.where(o.bar, 1.15, 1.0)
o["rev"] = (o.price.map(BASE) * bump * rel.fillna(0.6) ** B_FIT).clip(100_000, 40_000_000)
o["rev_src"] = np.where(o.reviews.notna(), "model", "model-low")
n_auv = 0
for b, a in auv.items():
    sel = o.brand_n == b
    if not sel.any():
        continue
    n_auv += 1
    med = o.loc[sel, "reviews"].median()
    r_ = (o.loc[sel, "reviews"] / med) ** 0.35 if med == med else pd.Series(np.nan, index=o.index[sel])
    o.loc[sel, "rev"] = a["auv_usd"] * r_.fillna(0.85).clip(0.6, 1.5)
    o.loc[sel, "rev_src"] = "chain"
o.loc[o.venue & o.rev_src.isin(["model", "model-low"]), "rev_src"] = "venue"
m_rat = o.rating.mean()
o["bayes"] = (o.reviews * o.rating + 40 * m_rat) / (o.reviews + 40)
margin = o.price.map(MARGIN)
margin = o.cuisine.map(MARGIN_CUISINE).fillna(margin) * (0.8 + 0.4 * pct(o.bayes).fillna(40) / 100)
o["margin"] = margin.round(4)
o["profit"] = o.rev * o.margin
o["food_cost"] = o.cuisine.map(FOOD_COST).fillna(30)
o["value_raw"] = o.bayes - 0.18 * (o.price - 1)
# iconic points (hand-checked places only): honors + history (verified year at this address) + how many people know it
jb = o.jbf.fillna("")
# the best honor counts: a winner, else a finalist (a "semifinalist" mention doesn't cancel a finalist one), else a semifinalist
win = jb.str.contains(r"\bwinner\b", case=False); fin = jb.str.contains(r"(?<!semi)finalist", case=False); semi = jb.str.contains("semifinalist", case=False)
acc = (jb.str.contains("America's Classic") * 35 + win * 22 + (fin & ~win) * 12 + (semi & ~fin & ~win) * 5 + o.icon.notna() * 24 + o.honors.notna() * 6).clip(upper=48)
years = (2026 - pd.to_numeric(o.founded, errors="coerce")).clip(lower=0)
o["s_icon"] = np.where(o.honored, (acc + years.fillna(0).clip(upper=80) / 80 * 32 + pct(np.log1p(o.reviews)).fillna(0) / 100 * 20).clip(upper=100), np.nan)


def r(x, n=0):
    if x is None or (isinstance(x, float) and x != x):
        return None
    return int(round(float(x))) if n == 0 else round(float(x), n)


def clean_url(u):
    """Website links without tracking parameters (Reserve with Google tokens, utm_*, click ids)."""
    base, _, q = u.partition("?")
    keep_ = [kv for kv in q.split("&") if kv and not re.match(r"(rwg_token|utm_[a-z]+|fbclid|gclid|y_source|cmpid|ref)=", kv)]
    return base + ("?" + "&".join(keep_) if keep_ else "")


o = o[o.lat.notna()].reset_index(drop=True)
# the license this place's facts come from (shown as "on DCP's list" with the permit type; never the permittee)
o["lic_kind"] = o.off.map(lambda j: F.cred.iat[int(j)] if j == j else None)
o["lic_jur"] = o.off.map(lambda j: F.jur.iat[int(j)] if j == j else None)
o["lic_since"] = o.off.map(lambda j: F.since.iat[int(j)] if j == j else None)
o["lic"] = o.off.map(lambda j: F.lic.iat[int(j)] if j == j else None)
o["hfd_cls"] = o.off_hfd.map(lambda j: F.cls.iat[int(j)] if j == j else None) if "off_hfd" in o else None
o["seats"] = o.off_hfd.map(lambda j: F.seats.iat[int(j)] if j == j else None) if "off_hfd" in o else None
# the address shown: a license address only when it starts with a street number
o["street"] = o.street.map(lambda a: a if isinstance(a, str) and re.match(r"\s*\d", a) else (a if isinstance(a, str) and not re.search(r"\b[A-Z][a-z]+ [A-Z][a-z]+$", a) else None))

if APP:
    # the same place twice: same name at the same street address, or (not a chain) same name in the same town within 400 m.
    # The licensed record wins, then a confirmed listing, then the one with more facts; the kept copy inherits what the dropped one knew.
    rank = o.tier.map({"official": 2, "both": 1, "listing": 0}).fillna(0) * 10 + o.hc.astype(int) * 5 + o.web.notna().astype(int)
    keyname = o.name_out.map(lambda n: norm_name(n) or re.sub(r"[^a-z0-9]", "", str(n).lower()))
    keyaddr = ["|".join(k) if all(k := street_key(s_)) else None for s_ in o.street]
    drop, merged, seen = set(), [], {}
    for pos, i in enumerate(o.index):
        if keyaddr[pos] and keyname[i]:
            k = (keyname[i], keyaddr[pos])
            if k in seen:
                j = seen[k]
                lose = i if rank[i] <= rank[j] else j
                drop.add(lose); seen[k] = j if lose == i else i
                merged.append((seen[k], lose))
            else:
                seen[k] = i
    single = o[(o.chain_n.fillna(1) < 2) & ~o.index.isin(drop)]
    for (nm_, town), g in single.groupby([keyname[single.index], single.city]):
        if len(g) < 2 or not nm_:
            continue
        idx = list(g.index)
        for a_ in range(len(idx)):
            for b_ in range(a_ + 1, len(idx)):
                i, j = idx[a_], idx[b_]
                if i in drop or j in drop:
                    continue
                if km(o.at[i, "lat"], o.at[i, "lon"], o.at[j, "lat"], o.at[j, "lon"]) < 0.4:
                    lose = i if rank[i] <= rank[j] else j
                    drop.add(lose); merged.append((j if lose == i else i, lose))
    for keep_i, lose in merged:
        if o.at[keep_i, "cuisine"] == "American & Other" and o.at[lose, "cuisine"] != "American & Other":
            o.at[keep_i, "cuisine"] = o.at[lose, "cuisine"]   # a license row's generic cuisine gives way to what the research says
        for col in [c for c in o.columns if c.startswith("t_")] + ["hc", "honored", "seasonal"]:
            if bool(o.at[lose, col]) and not bool(o.at[keep_i, col]):
                o.at[keep_i, col] = o.at[lose, col]
        for col in ("dishes", "season", "branch", "rnote", "rsite", "rsrc", "web", "phone", "founded", "icon", "jbf", "honors", "chef", "s_icon", "village", "cur_tags"):
            if pd.isna(o.at[keep_i, col]) and not pd.isna(o.at[lose, col]):
                o.at[keep_i, col] = o.at[lose, col]
    print("duplicates removed for the app:", len(drop), [o.at[i, "name_out"] for i in list(drop)[:8]])
    o = o.drop(index=list(drop))
    fixes = json.load(open(f"{DATA}/research/name_fixes.json")) if os.path.exists(f"{DATA}/research/name_fixes.json") else []
    for fx in fixes:
        hit = (o.name_out.str.upper() == fx["name"].upper()) & (o.city == fx["town"]) & o.street.fillna("").str.startswith(fx["street_number"] + " ")
        o.loc[hit, "name_out"] = fx["fixed"]
        print("name fix:", fx["name"], "->", fx["fixed"], int(hit.sum()))
# adult clubs aren't restaurants and don't belong in a 13+ app or the leaderboard; smoke/vape/cigar shops are hidden with non-restaurants
webs = o.web.fillna("").astype(str) + " " + o.rsite.fillna("").astype(str)
adult = (o.name_out.str.contains(r"gentlem[ae]n'?s club|exotic dancer|strip club|adult entertainment", case=False, regex=True)
         | (o.name_out.str.contains(r"\bcabaret\b", case=False, regex=True) & ~o.name_out.str.contains(r"yale|theat|dinner", case=False, regex=True))) \
    | webs.str.contains(r"centerfolds|gentlemensclub|stripclub", case=False, regex=True)
print("adult clubs removed:", int(adult.sum()), o.name_out[adult].tolist())
o = o[~adult]
smoke = o.name_out.str.contains(r"\bvape\b|smoke shop|\btobacco\b|cigar|\bcbd\b|dispensary|head shop|hookah lounge", case=False, regex=True) & ~o.hc
o.loc[smoke, "venue"] = True
print("smoke/vape/cigar shops hidden with non-restaurants:", int(smoke.sum()))
o = o.reset_index(drop=True)
nv = o[~o.venue]
CITIES = sorted(o.city.dropna().unique().tolist()); CUIS = sorted(o.cuisine.unique().tolist()); BRANDS = sorted(o.brand_n.dropna().unique().tolist())
VILLS = sorted(o.village.dropna().unique().tolist())
ci, cu, br, vi = {c: i for i, c in enumerate(CITIES)}, {c: i for i, c in enumerate(CUIS)}, {c: i for i, c in enumerate(BRANDS)}, {c: i for i, c in enumerate(VILLS)}
TIER = {"listing": 0, "both": 1, "official": 2}
JUR = {"dcp": 1, "hfd": 2}
SRCS = ["official", "meta", "AllThePlaces", "DAC", "research", "BrightQuery", "Foursquare", "Microsoft"]
HOSTS = [c[0] for c in CASINOS]
REGION = {f["properties"]["town"]: f["properties"]["region"] for f in TF}
REGIONS = sorted(set(REGION.values()))
KBIT = {k: 1 << i for i, k in enumerate(KINDS)}


def jbf_flags(jb):
    jb = jb or ""
    return (1 if "America's Classic" in jb else 0) | (2 if re.search(r"\bwinner\b", jb, re.I) else 0) \
        | (4 if re.search(r"(?<!semi)finalist", jb, re.I) else 0) | (8 if re.search(r"semifinalist", jb, re.I) else 0) | (16 if jb == "" else 0)


if APP:
    places, seen_ids = [], set()
    LINKS = json.load(open(f"{CT}/website_check.json")) if os.path.exists(f"{CT}/website_check.json") else None
    link_drops, link_cands = collections.Counter(), {}
    for i, x in o.iterrows():
        # a stable id (name + ~100 m cell) so saved places survive a data refresh
        idsrc = f"{norm_name(x.name_out)}|{round(float(x.lat), 3)}|{round(float(x.lon), 3)}"
        p = {"id": hashlib.md5(idsrc.encode()).hexdigest()[:12], "n": x.name_out, "c": ci.get(x.city) if isinstance(x.city, str) else None,
             "cu": cu[x.cuisine], "t": TIER[x.tier], "s": SRCS.index(x.src) if x.src in SRCS else 1}
        if isinstance(x.village, str): p["vi"] = vi[x.village]
        if isinstance(x.street, str): p["a"] = nice(x.street, addr=True)
        if isinstance(x.zip, str) and re.match(r"^06\d{3}", x.zip): p["z"] = x.zip[:5]
        p["la"], p["lo"] = round(float(x.lat), 5), round(float(x.lon), 5)
        if isinstance(x.brand_n, str): p["b"] = br[x.brand_n]
        if x.chain_n and int(x.chain_n) > 1: p["ch"] = int(x.chain_n)
        if x.official and isinstance(x.lic_jur, str): p["j"] = JUR[x.lic_jur]
        if isinstance(x.lic_kind, str): p["lk"] = x.lic_kind.title().replace("Wine & Beer", "Wine & Beer")
        if isinstance(x.hfd_cls, str): p["hcl"] = x.hfd_cls
        if x.venue: p["v"] = 1
        if x.bar: p["bar"] = 1
        if isinstance(x.host, str): p["host"] = HOSTS.index(x.host)
        tags = sum(1 << bi for bi, tg in enumerate(TAGS) if bool(x["t_" + tg]))
        if tags: p["g"] = tags
        if x.hc:
            p["hc"] = 1
            kinds = [k for k in (x.cur_tags or "").split("; ") if k in KBIT]
            if kinds: p["k"] = sum(KBIT[k] for k in kinds)
            p["ip"] = round(float(x.s_icon), 1)
            for k, v in (("note", x.rnote), ("jbf", x.jbf), ("hon", x.honors), ("dish", x.dishes), ("sea", x.season), ("br", x.branch), ("chef", x.chef), ("src", x.rsrc)):
                if isinstance(v, str) and v:
                    if k == "hon":   # honors are facts; ratings and readers' polls stay out
                        v = "; ".join(h for h in v.split("; ") if not re.search(r"readers'? ?choice|\bvote[ds]?\b|\bpoll\b|yelp|tripadvisor|opentable|\bstars?\b|\bbest of\b", h, re.I)) or None
                    if v: p[k] = v
            if x.seasonal: p["seas"] = 1
            if isinstance(x.jbf, str) and x.jbf: p["h"] = jbf_flags(x.jbf)
        if x.founded == x.founded and x.founded is not None: p["f"] = int(float(x.founded))
        web = x.rsite if isinstance(x.rsite, str) else (x.web if isinstance(x.web, str) else None)
        if web:
            w_ = clean_url(web)
            link_cands[w_] = x.brand_n if isinstance(x.brand_n, str) else x.name_out
            if LINKS is None or LINKS.get(w_, {}).get("ok"):
                p["w"] = w_
            else:
                link_drops[LINKS.get(w_, {}).get("why", "not checked yet")] += 1
        if isinstance(x.phone, str) and x.phone: p["ph"] = x.phone
        if isinstance(x.lic, str) and x.lic_jur == "dcp": p["lic"] = x.lic
        if isinstance(x.fv_r, str) and isinstance(x.fv_d, str): p["fv"] = {"r": x.fv_r, "d": x.fv_d}
        while p["id"] in seen_ids:
            p["id"] = p["id"] + "x"
        seen_ids.add(p["id"])
        places.append(p)
    print("website links dropped:", sum(link_drops.values()), link_drops.most_common(8))
    json.dump(link_cands, open(f"{CT}/website_candidates.json", "w"), indent=0, ensure_ascii=False)
    out = {"v": 1, "generated": GENERATED, "overture": OVERTURE, "cities": CITIES, "villages": VILLS, "regions": REGIONS,
           "town_region": [REGIONS.index(REGION[c]) if c in REGION else None for c in CITIES], "cuisines": CUIS, "brands": BRANDS,
           "tags": TAGS, "kinds": KINDS, "hosts": HOSTS, "sources": SRCS, "count": len(places), "count_restaurants": int(len(nv)),
           "calibration": calib.get("app", {}), "fvhd_fetched": FV_FETCHED, "places": places}
    os.makedirs(SITE, exist_ok=True)
    json.dump(out, open(f"{SITE}/places.json", "w"), separators=(",", ":"), ensure_ascii=False, allow_nan=False, default=str)
    json.dump(json.load(open(f"{CT}/ct_shapes.json")), open(f"{SITE}/ct_shapes.json", "w"), separators=(",", ":"))
    print("APP: wrote", len(places), "places (", len(nv), "restaurants ) |", os.path.getsize(f"{SITE}/places.json") // 1024, "KB | tiers:",
          nv.tier.value_counts().to_dict(), "| tags:", {tg: int(nv["t_" + tg].sum()) for tg in TAGS}, "| hand-checked:", int(nv.hc.sum()))
    sys.exit(0)

SRC = {"model": 0, "model-low": 1, "chain": 2, "reported": 3, "venue": 4}
# columnar: one array per field; decimals stored as integers (lat 41.3083 -> 413083) and scaled back in the page
SCALE = {"lat": 10000, "lon": 10000, "rating": 10, "margin": 1000, "value_raw": 1000}
C = collections.OrderedDict((c, []) for c in ["name", "addr", "city", "vil", "zip", "lat", "lon", "cuisine", "brand", "chain_n", "rating", "reviews",
                                               "price", "price_est", "rev_k", "rev_src", "margin", "value_raw", "tier", "jur", "bar", "venue", "tags",
                                               "src", "host", "hc"])
# sparse fields: [row, values...] for the few places that have them
SP = {k: [] for k in ("ap", "lr", "hb", "cl", "sb", "hd", "gr", "ic", "hon")}
SIGKEY = {"ap": "apizza", "lr": "lobster", "hb": "hotbutter", "cl": "clams", "sb": "steamed", "hd": "hotdog", "gr": "grinder", "ic": "icecream"}
extra = {}
for i, x in o.iterrows():
    tags = sum(1 << b for b, t in enumerate(TAGS) if bool(x["t_" + t]))
    z = int(x.zip[:5]) if isinstance(x.zip, str) and re.match(r"^06\d{3}", x.zip) else None
    vals = {"name": x.name_out, "addr": nice(x.street, addr=True) if isinstance(x.street, str) else None,
            "city": ci.get(x.city) if isinstance(x.city, str) else None, "vil": vi.get(x.village) if isinstance(x.village, str) else None,
            "zip": z, "lat": x.lat, "lon": x.lon, "cuisine": cu[x.cuisine],
            "brand": br.get(x.brand_n) if isinstance(x.brand_n, str) else None, "chain_n": int(x.chain_n), "rating": x.rating, "reviews": r(x.reviews),
            "price": int(x.price), "price_est": int(x.price_est), "rev_k": int(round(x.rev / 1000)), "rev_src": SRC[x.rev_src], "margin": x.margin,
            "value_raw": x.value_raw, "tier": TIER[x.tier], "jur": JUR.get(x.lic_jur, 0) if isinstance(x.lic_jur, str) else 0, "bar": int(bool(x.bar)),
            "venue": int(bool(x.venue)), "tags": tags, "src": SRCS.index(x.src) if x.src in SRCS else 1,
            "host": HOSTS.index(x.host) + 1 if isinstance(x.host, str) else 0, "hc": int(bool(x.hc))}
    for key, sk in SIGKEY.items():
        n, rr = x["n_" + sk], x["r_" + sk]
        if n:
            SP[key].append([i, int(n), int(round(rr * 100)) if rr == rr and rr is not None else None])
    if x.honored:
        SP["hon"].append([i, int(round(x.s_icon * 10)), jbf_flags(x.jbf) if isinstance(x.jbf, str) and x.jbf else 0])
    for c, v in vals.items():
        if c in SCALE:
            v = None if v is None or v != v else int(round(float(v) * SCALE[c]))
        elif isinstance(v, float):
            v = None if v != v else v
        C[c].append(v.item() if hasattr(v, "item") else v)
    e = {}
    if x.hc:
        e.update({k: v for k, v in (("jbf", x.jbf), ("honors", x.honors), ("note", x.rnote), ("founded", r(x.founded)), ("dishes", x.dishes),
                                    ("season", x.season), ("branch", x.branch), ("chef", x.chef), ("kinds", x.cur_tags), ("src", x.rsrc),
                                    ("site", x.rsite)) if v is not None and v == v and v != ""})
    if x.official:
        e["lic_kind"] = x.lic_kind; e["lic_since"] = x.lic_since if x.lic_jur == "dcp" else None
        e["found"] = "list" if x.src == "official" else "match"
        if isinstance(x.hfd_cls, str):
            e["hfd"] = x.hfd_cls + (f", {int(x.seats)} seats" if x.seats == x.seats and x.seats else "")
    if isinstance(x.fv_r, str) and isinstance(x.fv_d, str):
        e["fv"] = x.fv_r + "|" + x.fv_d
    e = {k: v for k, v in e.items() if v is not None and not (isinstance(v, float) and v != v)}
    if e:
        extra[i] = e
meta = {"generated": GENERATED, "cities": CITIES, "villages": VILLS, "regions": REGIONS,
        "town_region": [REGIONS.index(REGION[c]) if c in REGION else None for c in CITIES], "cuisines": CUIS, "brands": BRANDS,
        "src": list(SRC), "tiers": list(TIER), "tags": TAGS, "hosts": HOSTS, "food_cost": dict(FOOD_COST), "spend": SPEND, "count": len(o),
        "count_restaurants": int(len(nv)), "count_official": int(nv.official.sum()), "count_both": int((nv.tier == "both").sum()),
        "count_listing": int((nv.tier == "listing").sum()), "n_cities": int(nv.city.nunique()), "overture_release": OVERTURE,
        "rating_mean": round(float(m_rat), 3), "model": {"b": B_FIT, "n_chains": n_auv}, "calibration": calib, "n_honored": int(o.honored.sum()),
        "n_hc": int(o.hc.sum()), "srcs": SRCS, "license_date": "Oct 5, 2026", "fvhd_fetched": FV_FETCHED}
for _k, _v in list(C.items()) + list(SP.items()):
    _bad = [j for j, x in enumerate(_v) if (isinstance(x, float) and x != x) or (isinstance(x, list) and any(isinstance(y, float) and y != y for y in x))]
    if _bad: print("NaN in", _k, len(_bad), _v[_bad[0]])
os.makedirs(SITE, exist_ok=True)
json.dump({"n": len(o), "scale": SCALE, "cols": C, "sparse": SP, "meta": meta},
          open(f"{SITE}/connecticut.json", "w"), separators=(",", ":"), allow_nan=False, default=str)
json.dump({"n": len(o), "extra": {str(k): v for k, v in extra.items()}}, open(f"{SITE}/ct_detail.json", "w"), separators=(",", ":"), allow_nan=False, default=str)
json.dump(json.load(open(f"{CT}/ct_shapes.json")), open(f"{SITE}/ct_shapes.json", "w"), separators=(",", ":"))
o.to_pickle(f"{CT}/stage2.pkl")
print("wrote", len(o), "places (", int(len(nv)), "restaurants ) in", nv.city.nunique(), "towns;", os.path.getsize(f"{SITE}/connecticut.json") // 1024,
      "KB | tiers:", nv.tier.value_counts().to_dict(), "| top towns:", nv.city.value_counts().head(8).to_dict())
