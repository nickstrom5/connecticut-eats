"""Connecticut's 169 towns -> data/ct/

Connecticut has no county government: towns are the unit people know, and the Census now uses 9 planning regions in place of the
8 old counties. Source: Census cartographic boundary file cb_2025_09_cousub_500k (public domain, clipped to the shoreline).

- ct_towns.geojson   every town, full detail, with its planning region (for placing each restaurant in its town)
- ct_shapes.json     the simplified state outline (Long Island Sound already cut out) and town outlines for the maps
"""
import os, json
import duckdb
from shapely import wkb
from shapely.geometry import mapping, Polygon
from shapely.ops import unary_union

CT = os.path.join(os.path.dirname(__file__), "..", "data", "ct")
con = duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial;")
rows = con.execute(f"SELECT NAME, NAMELSADCO, GEOID, ST_AsWKB(geom) FROM ST_Read('{CT}/cousub/cb_2025_09_cousub_500k.shp') ORDER BY NAME").fetchall()
towns = [(n, r.replace(" Planning Region", ""), g, wkb.loads(bytes(w)).buffer(0)) for n, r, g, w in rows]
assert len(towns) == 169, len(towns)
json.dump({"type": "FeatureCollection", "features": [
    {"type": "Feature", "properties": {"town": n, "region": r, "geoid": g}, "geometry": mapping(geom)} for n, r, g, geom in towns]},
    open(f"{CT}/ct_towns.geojson", "w"))


def rings(geom, tol, min_area, holes=False):
    geom = geom.simplify(tol, preserve_topology=True)
    polys = [p for p in getattr(geom, "geoms", [geom]) if p.geom_type == "Polygon" and p.area >= min_area]
    r = lambda ring: [[round(x, 4), round(y, 4)] for x, y in ring.coords]
    if holes:
        return [[r(p.exterior)] + [r(h) for h in p.interiors if abs(Polygon(h).area) >= min_area] for p in polys]
    return [r(p.exterior) for p in polys]


state = unary_union([t[3] for t in towns]).buffer(0)
json.dump(mapping(state.simplify(0.0003, preserve_topology=True)), open(f"{CT}/ct_state_detail.geojson", "w"))
out = {"state": rings(state, 0.0008, 0.00002, holes=True),
       "towns": [{"name": n, "region": r, "c": rings(geom, 0.0015, 0.00002)} for n, r, g, geom in towns]}
json.dump(out, open(f"{CT}/ct_shapes.json", "w"), separators=(",", ":"))
print("towns:", len(out["towns"]), "| state rings:", len(out["state"]), "|", os.path.getsize(f"{CT}/ct_shapes.json") // 1024, "KB")
