"""How often is a map listing a real, licensed restaurant? Measured against Connecticut's official lists -> data/ct/calibration*.json

Two yardsticks:
- Hartford (City of Hartford food-establishment licenses, every kind of food business): an absolute rate, like Milwaukee/Dane in
  Wisconsin and Chicago's license list.
- Statewide (DCP on-premise liquor permits: restaurant, restaurant wine & beer, cafe, hotel): only places that serve alcohol hold
  one, so these rates are much lower than a food-license rate. They compare source groups across the whole state, and show which
  kinds of places (bars, sit-down restaurants) the listings miss.
A match = the same business name nearby, or the same street address with a distinctive name word in common (listings_util).
Both directions are reported: listings that match a license, and licenses found among the listings (one per business).
"""
import json
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely.prepared import prep
from common import CT
import official
from official import ON_PREMISE
from listings_util import official_match

o = pd.read_pickle(f"{CT}/stage1.pkl")
F = official.load()
o = o[~o.j_junk & ~o.j_outside & o.town.notna()].reset_index(drop=True)
TOWNWORDS = frozenset(w for t in o.town.dropna().unique() for w in t.upper().split())


def groups_web(L):
    s = L.src.fillna("none")
    return np.select([L.closed21, L.ov_closed, (s == "meta") & L.in21, s == "meta", s.isin(["AllThePlaces", "DAC"]) & L.in21,
                      s.isin(["AllThePlaces", "DAC"]), L.in21, s == "Foursquare", s == "BrightQuery", s == "Microsoft"],
                     ["Google 2021 says closed", "Overture says closed", "Meta + open in Google 2021", "Meta only",
                      "brand feed + Google 2021", "brand feed only", "Foursquare/BrightQuery/Microsoft + Google 2021",
                      "Foursquare only", "BrightQuery only", "Microsoft only"], "other")


def groups_app(L):
    conf, s = L.confidence.fillna(0), L.src.fillna("none")
    return np.select([L.ov_closed, (s == "meta") & (conf >= 0.95), (s == "meta") & (conf >= 0.9), s.isin(["AllThePlaces", "DAC"]),
                      (s == "BrightQuery") & (conf >= 0.95), s == "meta"],
                     ["Overture says closed", "Meta, confidence 0.95+", "Meta, 0.90-0.95", "brand feed", "BrightQuery 0.95+", "Meta, below 0.90"],
                     "other sources")


def measure(L, R, grp_fn, label):
    m = official_match(L.reset_index(drop=True), R.reset_index(drop=True), town_words=TOWNWORDS)
    L = L.reset_index(drop=True)
    L["hit"] = L.index.map(lambda i: i in m)
    L["grp"] = grp_fn(L)
    t = L.groupby("grp").hit.agg(["size", "mean"]).sort_values("size", ascending=False)
    print(f"\n== {label}: {len(L)} listings vs {R.biz.nunique()} licensed businesses")
    print(t.assign(mean=(t["mean"] * 100).round(1)).rename(columns={"size": "listings", "mean": "% matched"}).to_string())
    got = set(R.reset_index(drop=True).biz.iloc[list(m.values())])
    return L, m, {g: {"n": int(r["size"]), "matched": round(float(r["mean"]), 3)} for g, r in t.iterrows()}, got


res = {"web": {}, "app": {}, "coverage": {}}
# ---- Hartford: every food license
hfd = prep(shape(next(f["geometry"] for f in json.load(open(f"{CT}/ct_towns.geojson"))["features"] if f["properties"]["town"] == "Hartford")).buffer(0.0003))
LH = o[[hfd.contains(Point(x, y)) for x, y in zip(o.lon, o.lat)]]
RH = F[(F.jur == "hfd") & F.active]
for kind, fn in (("web", groups_web), ("app", groups_app)):
    _, m, res[kind]["hartford"], got = measure(LH, RH, fn, f"Hartford food licenses, {kind} grouping")
cover = np.mean([b in got for b in RH.drop_duplicates("biz").biz])
by_cls = RH.drop_duplicates("biz").assign(found=lambda d: d.biz.isin(got)).groupby("cls").found.agg(["size", "mean"])
print(f"Hartford licensed food businesses found among the map listings: {cover:.1%} of {RH.biz.nunique()}\n" + by_cls.to_string())
res["coverage"]["hartford"] = {"share": round(float(cover), 3), "n": int(RH.biz.nunique()),
                               "by_class": {c: {"n": int(r["size"]), "found": round(float(r["mean"]), 3)} for c, r in by_cls.iterrows()}}

# ---- statewide: on-premise liquor permits
RS = F[(F.jur == "dcp") & F.active & F.kind.isin(ON_PREMISE | {"brewery", "club", "venue"})]
for kind, fn in (("web", groups_web), ("app", groups_app)):
    L, m, res[kind]["statewide_liquor"], got = measure(o, RS, fn, f"statewide on-premise liquor permits, {kind} grouping")
RB = RS.drop_duplicates("biz").assign(found=lambda d: d.biz.isin(got))
by_kind = RB.groupby("kind").found.agg(["size", "mean"])
print("\nliquor-permit businesses found among the map listings:\n" + by_kind.assign(mean=(by_kind["mean"] * 100).round(1)).to_string())
res["coverage"]["liquor"] = {k: {"n": int(r["size"]), "found": round(float(r["mean"]), 3)} for k, r in by_kind.iterrows()}
# the other direction, by cuisine-ish category: which listings tend to hold a liquor permit
L["cat"] = L.cat.fillna("?")
t = L[L.grp.isin(["Meta, confidence 0.95+", "Meta, 0.90-0.95"])].groupby("cat").hit.agg(["size", "mean"]).sort_values("size", ascending=False)
print("\nMeta 0.90+ listings with a liquor permit, by Overture category:\n" + t.assign(mean=(t["mean"] * 100).round(1)).to_string())
res["liquor_by_category"] = {c: {"n": int(r["size"]), "matched": round(float(r["mean"]), 3)} for c, r in t.iterrows()}
json.dump(res, open(f"{CT}/calibration.json", "w"), indent=1)
print("\nwrote calibration.json")
