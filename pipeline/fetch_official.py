"""Official Connecticut records -> data/raw/official/

- dcp_licenses.csv       DCP "State Licenses and Credentials" (data.ct.gov ngch-56tr, Public Domain, refreshed daily): every on-premise
                         liquor permit (restaurant, restaurant wine & beer, cafe, hotel, craft cafe, club, caterer, casino, brewery)
                         and bakery licenses, active and inactive. The `name`/`businessname` columns are the legal permittee (often a
                         person) and are dropped here: only the DBA is kept.
- dcp_suspensions.csv    DCP Liquor Control suspensions (i2yq-278d)
- lhd_by_town.csv        DPH local health department for each of the 169 towns (p3e9-4yjt)
- lhd.csv                DPH local health departments and districts (62ac-rrv4)
- hartford_food.json     City of Hartford "Food Establishments Licenses Current" (ArcGIS, updated nightly from Accela), DBA, class, seating

Polite: one request at a time, an honest user agent, paged with $limit/$offset.
"""
import os, io, json, time, csv
import requests

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "official")
os.makedirs(OUT, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "ct-eats data pipeline (work-with-nick@gmail.com)"
# on-premise eating/drinking permits plus bakeries; package stores, grocery beer, wholesalers and temporary permits are left out
TYPES = ["LIR", "LRW", "LCA", "LIH", "LCR", "LCW", "LRC", "LIC", "LPC", "LCT", "LCN", "LMB", "LMW", "FWBC", "LFW", "LIT", "LRB", "LBP",
         "LMP", "LBA", "LBB", "LAT", "LAB", "LGC", "LCM", "BAK"]
KEEP = ["credentialid", "dba", "type", "fullcredentialcode", "credentialtype", "credentialnumber", "credential", "status", "statusreason",
        "active", "issuedate", "effectivedate", "expirationdate", "address", "city", "state", "zip", "recordrefreshedon"]


def socrata(ds, where=None, select=None, page=50000):
    rows, off = [], 0
    while True:
        p = {"$limit": page, "$offset": off, "$order": ":id"}
        if where: p["$where"] = where
        if select: p["$select"] = select
        r = S.get(f"https://data.ct.gov/resource/{ds}.json", params=p, timeout=120)
        r.raise_for_status()
        got = r.json()
        rows += got
        if len(got) < page:
            return rows
        off += page
        time.sleep(1)


def write_csv(path, rows, cols):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


types = ",".join(f"'{t}'" for t in TYPES)
lic = socrata("ngch-56tr", where=f"credentialtype in ({types})", select=",".join(KEEP))
write_csv(f"{OUT}/dcp_licenses.csv", lic, KEEP)
print("DCP licenses:", len(lic), "| active:", sum(r.get("active") == "1" for r in lic))
time.sleep(1)
sus = socrata("i2yq-278d")
write_csv(f"{OUT}/dcp_suspensions.csv", sus, sorted({k for r in sus for k in r}))
print("suspensions:", len(sus))
for ds, name in (("p3e9-4yjt", "lhd_by_town"), ("62ac-rrv4", "lhd")):
    time.sleep(1)
    rows = socrata(ds)
    write_csv(f"{OUT}/{name}.csv", rows, sorted({k for r in rows for k in r}))
    print(name, len(rows))
# City of Hartford "Food Establishments Licenses Current" (ArcGIS feature table; 736 rows fit in one page of 2,000)
time.sleep(1)
HFD = "https://utility.arcgis.com/usrsvcs/servers/27139a92097e4e6a957646fb633e1e71/rest/services/HartfordOpenDataTables/FeatureServer/2/query"
r = S.get(HFD, params={"where": "1=1", "outFields": "*", "f": "json", "resultRecordCount": 2000}, timeout=120)
r.raise_for_status()
h = r.json()
assert len(h.get("features", [])) < 2000, "Hartford has more rows than one page: add paging"
json.dump(h, open(f"{OUT}/hartford_food.json", "w"))
print("Hartford food licenses:", len(h["features"]))
