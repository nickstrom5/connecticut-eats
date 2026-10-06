"""Official Connecticut records: DCP liquor permits and bakery licenses (statewide) and Hartford's food-establishment licenses.

load() returns one table of licensed businesses with a normalized name key, street number and street key, coordinates placed on
Overture address points (the records have none), the municipality, the license kind and whether it is active.

Only the DBA (trade name) is ever kept. DCP's `name`/`businessname` columns are the legal permittee, often a person, and are dropped
in fetch_official.py; the "Liquor Permits" view (gwv2-eswx) with permittee and backer names is never read.
Connecticut publishes no statewide list of restaurant food licenses (those are local), so a restaurant without a liquor permit is
only on an official list in Hartford.
"""
import os, re, math, json
import numpy as np, pandas as pd
from common import norm_name, RAW, CT, canon_city

OFF = os.path.join(RAW, "official")
DIRS = {"N": "N", "S": "S", "E": "E", "W": "W", "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
TYPES = set("""ST STREET AVE AV AVENUE BLVD BOULEVARD RD ROAD DR DRIVE LN LANE CT COURT PL PLACE PKWY PARKWAY TER TERRACE TRL TRAIL WAY
HWY HIGHWAY CIR CIRCLE PLZ PLAZA SQ SQUARE MALL BND PASS XING RUN ROW WALK RDG TPKE TPK TURNPIKE PIKE EXT EXTENSION GRN GREEN CRES
COMMONS CMNS LNDG LANDING""".split())
KIND = {"LIR": "restaurant", "LRW": "restaurant", "LRC": "restaurant", "LRB": "restaurant", "LCA": "bar", "LCR": "bar", "LCW": "bar",
        "LIT": "bar", "LIH": "hotel", "LIC": "club", "LPC": "club", "LGC": "club", "LMB": "brewery", "LMW": "brewery", "FWBC": "brewery",
        "LFW": "brewery", "LBP": "brewery", "LMP": "brewery", "LCN": "venue", "LCM": "venue", "LAT": "venue", "LAB": "venue",
        "LBA": "venue", "LBB": "venue", "LCT": "caterer", "BAK": "bakery"}
ON_PREMISE = {"restaurant", "bar", "hotel"}   # the permits a restaurant or bar holds


def road(a):
    """One spelling for numbered roads: 'ROUTE 12' = 'RT 12' = 'RTE 12' = 'CT-12' = 'STATE ROUTE 12' = 'US ROUTE 6' = 'US-6'."""
    a = re.sub(r"(\d)\s*&\s*(\d)", r"\1-\2", a.upper())
    a = re.sub(r"\b(?:U\.?\s?S\.?|CT|CONN|STATE)[-\s]+(?:ROUTE|RTE|RT|HIGHWAY|HWY)?\s*-?\s*(\d+[A-Z]?)\b", r"RT \1", a)
    a = re.sub(r"\b(?:ROUTE|RTE|RT)\.?\s*#?\s*(\d+[A-Z]?)\b", r"RT \1", a)
    a = re.sub(r"\bTPKE\b|\bTPK\b", "TURNPIKE", a)
    return re.sub(r"\bHIGHWAY\b", "HWY", a)


def street_key(a):
    """'2505 Main St' -> ('2505', 'MAIN'); '134 ROUTE 12' -> ('134', 'RT 12'); '45 Mill Rock Rd E' -> ('45', 'MILL ROCK')."""
    if not isinstance(a, str):
        return None, None
    a = re.sub(r"[.,#]", " ", road(a))
    m = re.match(r"^\s*(\d+)[A-Z]?(?:\s*-\s*\d+[A-Z]?)?\s+(.*)$", a)
    if not m:
        return None, None
    words = [w for w in m.group(2).split() if w]
    while len(words) > 1 and words[0] in DIRS:
        words = words[1:]
    core = []
    for w in words:
        if w in TYPES and core:
            break
        core.append(w)
    core = [{"FIRST": "1ST", "SECOND": "2ND", "THIRD": "3RD", "FOURTH": "4TH", "FIFTH": "5TH", "SIXTH": "6TH"}.get(w, w) for w in core]
    return m.group(1), " ".join(core[:3]) or None


def street_nums(a):
    """'157-159 W Main St' -> {'157', '159'}; '2505 Main St' -> {'2505'}."""
    if not isinstance(a, str):
        return set()
    a = road(a)
    m = re.match(r"^\s*(\d+)[A-Z]?(?:\s*-\s*(\d+)[A-Z]?)?\s", a.upper() + " ")
    if not m:
        return set()
    lo = int(m.group(1)); hi = int(m.group(2)) if m.group(2) else lo
    if hi < lo:   # "1500-02"
        hi = int(str(lo)[: len(str(lo)) - len(m.group(2))] + m.group(2)) if m.group(2) else lo
    return {str(x) for x in range(lo, hi + 1, 2 if (hi - lo) % 2 == 0 else 1)} if 0 <= hi - lo <= 12 else {str(lo)}


def _names(*vals):
    out = []
    for v in vals:
        if not isinstance(v, str):
            continue
        for part in re.split(r"\s*/\s*|\s+\bdba\b\s+|\s+&\s+(?=[A-Z][a-z])", v, flags=re.I):
            k = norm_name(re.sub(r"\b(?:LLC|INC|CORP|CORPORATION|LTD|CO)\b\.?", "", part, flags=re.I))
            if k and k not in out:
                out.append(k)
    return out


_AP = None


def address_index():
    """(street number, street key) -> address points [(lat, lon, municipality, zip)] for Connecticut, plus per (street key, town)
    the sorted numbered points, to interpolate a number the points lack (commercial buildings often have one point for a range)."""
    global _AP
    if _AP is None:
        ap = pd.read_parquet(f"{CT}/addresses_ct.parquet", columns=["number", "street", "postcode", "muni", "state", "lat", "lon"])
        ap = ap[ap.state == "CT"]
        idx, line = {}, {}
        for n, s, z, m, la, lo in zip(ap.number.astype(str), ap.street.fillna(""), ap.postcode.fillna(""), ap.muni, ap.lat, ap.lon):
            s = re.sub(r"\s*\([^)]*\)\s*$", "", s)   # "East Putnam Ave(COS COB)"
            k = street_key(f"{n} {s}")
            if k[1]:
                idx.setdefault(k, []).append((la, lo, m, z[:5]))
                line.setdefault((k[1], m), []).append((int(k[0]), la, lo, z[:5]))
        for v in line.values():
            v.sort()
        _AP = (idx, line)
    return _AP


def _interpolate(num, st, town):
    """A number missing from the points: between the nearest numbers on both sides (same parity first) within 60, else the nearest within 20."""
    import bisect
    pts = address_index()[1].get((st, town))
    if not pts:
        return None
    n = int(num)
    for same_side in (True, False):
        cand = [p for p in pts if (p[0] % 2 == n % 2 or not same_side)]
        nums = [p[0] for p in cand]
        i = bisect.bisect_left(nums, n)
        lo_, hi_ = (cand[i - 1] if i > 0 else None), (cand[i] if i < len(cand) else None)
        if lo_ and hi_ and hi_[0] - lo_[0] <= 120 and n - lo_[0] <= 60 and hi_[0] - n <= 60:
            f = (n - lo_[0]) / max(hi_[0] - lo_[0], 1)
            la, lo = lo_[1] + f * (hi_[1] - lo_[1]), lo_[2] + f * (hi_[2] - lo_[2])
            if math.hypot((hi_[1] - lo_[1]) * 111, (hi_[2] - lo_[2]) * 83) < 0.6:
                return la, lo, town
    near = min(pts, key=lambda p: abs(p[0] - n))
    if abs(near[0] - n) <= 20:
        return near[1], near[2], town
    return None


def geocode(addr, town=None, zip5=None):
    """A license address -> (lat, lon, municipality, exact?) on the address points: same number and street, in the same town or zip
    when the street exists in several towns; else interpolated between neighboring numbers on that street in that town.
    None when it can't be placed or would be a guess (the same address in two far-apart towns)."""
    idx = address_index()[0]
    st = street_key(addr)[1]
    nums = sorted(street_nums(addr))
    for n in nums:
        pts = idx.get((n, st))
        if not pts:
            continue
        same = [p for p in pts if town and p[2] == town] or [p for p in pts if zip5 and p[3] == zip5]
        if (town or zip5) and not same:
            continue   # "123 Main St" in Stamford is not 123 Main St in Groton: never borrow another town's point
        pts = same or pts
        la, lo = float(np.median([p[0] for p in pts])), float(np.median([p[1] for p in pts]))
        if max(math.hypot((p[0] - la) * 111, (p[1] - lo) * 83) for p in pts) > 1.0:
            continue
        return la, lo, pts[0][2], True
    if town and st:
        for n in nums:
            g = _interpolate(n, st, town)
            if g:
                return g[0], g[1], g[2], False
    return None


def zip_towns():
    """zip -> the municipality most of its address points are in (license records give a mailing city, not always the town)."""
    ap = pd.read_parquet(f"{CT}/addresses_ct.parquet", columns=["postcode", "muni", "state"])
    ap = ap[(ap.state == "CT") & ap.postcode.notna()]
    ap["z"] = ap.postcode.str[:5]
    return ap.groupby("z").muni.agg(lambda x: x.mode().iat[0]).to_dict()


def load(cache=True):
    path = f"{CT}/official.pkl"
    if cache and os.path.exists(path) and os.path.getmtime(path) > max(os.path.getmtime(f"{OFF}/dcp_licenses.csv"), os.path.getmtime(__file__)):
        return pd.read_pickle(path)
    towns = {f["properties"]["town"] for f in json.load(open(f"{CT}/ct_towns.geojson"))["features"]}
    ztown = zip_towns()
    rows = []
    d = pd.read_csv(f"{OFF}/dcp_licenses.csv", dtype=str)
    d = d[(d.state.fillna("CT") == "CT") & d.credentialtype.isin(KIND)].fillna("")
    for _, r in d.iterrows():
        z = (r.zip or "")[:5]
        mail = canon_city(r.city)
        town = mail if mail in towns else ztown.get(z)
        num, st = street_key(r.address)
        if not re.match(r"\s*\d", r.address):   # no street number (a few records hold a name or a mall in the address field)
            num, st = None, None
        rows.append({"jur": "dcp", "lic": r.fullcredentialcode, "name": r.dba or None, "keys": _names(r.dba),
                     "addr": r.address, "city": mail, "town": town, "zip": z, "num": num, "street": st, "kind": KIND[r.credentialtype],
                     "cred": r.credential, "active": r.active == "1", "status": r.status, "since": (r.issuedate or "")[:10],
                     "expires": (r.expirationdate or "")[:10], "cls": None, "seats": None})
    h = json.load(open(f"{OFF}/hartford_food.json"))["features"]
    for f in h:
        a = f["attributes"]
        num, st = street_key(a["Full_Address"])
        seats = re.search(r"(\d+)", a.get("Seating_Capacity") or "")
        rows.append({"jur": "hfd", "lic": "HFD-" + a["Record_ID"], "name": (a["DBA"] or "").strip() or None, "keys": _names((a["DBA"] or "").strip()),
                     "addr": a["Full_Address"], "city": "Hartford", "town": "Hartford", "zip": None, "num": num, "street": st, "kind": "food",
                     "cred": a["Classification"], "active": a["Record_Status"] in ("Active", "About to Expire"), "status": a["Record_Status"],
                     "since": None, "expires": None, "cls": a["Classification"], "seats": int(seats.group(1)) if seats else None})
    df = pd.DataFrame(rows)
    df = df[df.name.notna()].reset_index(drop=True)
    g = [geocode(a, t, z) for a, t, z in zip(df.addr, df.town, df.zip)]
    df["lat"] = [x[0] if x else np.nan for x in g]
    df["lon"] = [x[1] if x else np.nan for x in g]
    df["town"] = [x[2] if x else t for x, t in zip(g, df.town)]
    df["geo_exact"] = [bool(x and x[3]) for x in g]
    # one business can hold several licenses (restaurant liquor + bakery, a renewal under a new permit): same address, a name in common
    from common import name_sim, _stems, GENERIC
    df["biz"] = np.arange(len(df))
    for (town, num, st), grp in df[df.num.notna() & df.street.notna()].groupby(["town", "num", "street"]):
        idx = list(grp.index)
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                ka, kb = df.at[idx[a], "keys"], df.at[idx[b], "keys"]
                if any(name_sim(x, y) >= 85 or ((_stems(x) - GENERIC) & (_stems(y) - GENERIC)) for x in ka for y in kb):
                    old, new = df.at[idx[b], "biz"], df.at[idx[a], "biz"]
                    df.loc[df.biz == old, "biz"] = new
    df.to_pickle(path)
    return df


if __name__ == "__main__":
    df = load(cache=False)
    a = df[df.active]
    print("records:", len(df), "| active:", len(a), "| placed on an address point:", f"{a.lat.notna().mean():.1%}")
    print(a.groupby("kind").agg(n=("lic", "size"), placed=("lat", lambda s: round(s.notna().mean(), 3))).to_string())
    print("active on-premise businesses:", a[a.kind.isin(ON_PREMISE)].biz.nunique(), "| towns:", a.town.nunique())
    print(a[a.lat.isna() & a.kind.isin(ON_PREMISE)][["name", "addr", "city", "town"]].head(15).to_string())
