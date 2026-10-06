"""Download the Overture Maps extracts the Connecticut pipeline reads -> data/ct/

- overture_ct_bbox.parquet     every place in Connecticut's bounding box (name, category, address, point)
- overture_ct_sources.parquet  which datasets each Connecticut eating/drinking listing came from (Meta, Foursquare, ...)
- addresses_ct.parquet         Overture address points in Connecticut (to place license records, which have no coordinates)

Reads the public Overture bucket over S3 with DuckDB (no account needed). Town outlines come from the Census
(pipeline/fetch_towns.py), not from Overture's divisions.
"""
import os, time
import duckdb

RELEASE = "2026-09-23.1"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "ct")
# Connecticut plus a margin for border towns (Greenwich/Port Chester, Enfield/Springfield, Stonington/Westerly)
BBOX = "bbox.xmin BETWEEN -73.75 AND -71.76 AND bbox.ymin BETWEEN 40.93 AND 42.07"
EAT = "('restaurant','casual_eatery','bar','fast_food_restaurant','coffee_shop','cafe','smoothie_juice_bar','brewery','food_court')"
os.makedirs(OUT, exist_ok=True)

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")
places = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=places/type=place/*.parquet"

t = time.time()
if not os.path.exists(f"{OUT}/overture_ct_bbox.parquet"):
    con.execute(f"""
COPY (
  SELECT id, names.primary AS name, basic_category AS cat, taxonomy.primary AS tax, taxonomy.hierarchy AS hier, confidence,
         operating_status AS status, brand.names.primary AS brand, addresses[1].freeform AS street, addresses[1].locality AS city,
         addresses[1].postcode AS zip, addresses[1].region AS region, ST_Y(geometry) AS lat, ST_X(geometry) AS lon, websites[1] AS web,
         phones[1] AS phone
  FROM read_parquet('{places}', hive_partitioning=1) WHERE {BBOX}
) TO '{OUT}/overture_ct_bbox.parquet' (FORMAT PARQUET)""")
    print("places in bbox", round(time.time() - t), "s", flush=True)
if not os.path.exists(f"{OUT}/overture_ct_sources.parquet"):
    con.execute(f"""
COPY (
  SELECT id, list_transform(sources, x -> x.dataset) AS ds, list_transform(sources, x -> x.update_time) AS ut,
         len(socials) AS n_soc, len(websites) AS n_web, len(phones) AS n_ph
  FROM read_parquet('{places}', hive_partitioning=1)
  WHERE {BBOX} AND addresses[1].region = 'CT' AND basic_category IN {EAT}
) TO '{OUT}/overture_ct_sources.parquet' (FORMAT PARQUET)""")
    print("sources", round(time.time() - t), "s", flush=True)
if not os.path.exists(f"{OUT}/addresses_ct.parquet"):
    a = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=addresses/type=address/*.parquet"
    con.execute(f"""COPY (SELECT number, street, unit, postcode, postal_city, address_levels[1].value AS state,
      address_levels[-1].value AS muni, ST_Y(geometry) lat, ST_X(geometry) lon FROM read_parquet('{a}', hive_partitioning=1)
      WHERE country = 'US' AND {BBOX}) TO '{OUT}/addresses_ct.parquet' (FORMAT PARQUET)""")
    print("addresses", round(time.time() - t), "s", flush=True)
print(con.execute(f"SELECT count(*), count(*) FILTER (WHERE region = 'CT' AND cat IN {EAT}) FROM '{OUT}/overture_ct_bbox.parquet'").fetchall())
print(con.execute(f"SELECT count(*), count(*) FILTER (WHERE state = 'CT') FROM '{OUT}/addresses_ct.parquet'").fetchall(), round(time.time() - t), "s total")
