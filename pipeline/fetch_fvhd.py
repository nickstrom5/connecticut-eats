"""Farmington Valley Health District's official food-establishment ratings -> data/raw/official/fvhd_ratings.json

FVHD (Avon, Barkhamsted, Canton, Colebrook, East Granby, Farmington, Granby, Hartland, New Hartford, Simsbury) gives each food
service establishment an A (Excellent) / B (Good) / C (Fair) / U (Unsatisfactory) rating at each routine inspection, and the
establishment must post it near its permit. FVHD publishes the current ratings as one public page of cards per town
(https://fvhd.org/environmental-health/food/food-ratings/). It is the only current, list-form inspection result in Connecticut.

Polite: robots.txt allows these pages; an honest user agent; one page at a time, 30 s apart. Any 403, 429 or 503, or a dropped connection, stops the run
(no retry, no workaround): the previous file is kept and the next refresh tries again.
"""
import collections, os, re, sys, json, time, html
import requests

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "official")
TOWNS = {t: "environmental-health/food/food-ratings/" + slug + "/" for t, slug in [("Avon", "avon"), ("Barkhamsted", "barkhamsted"), ("Canton", "canton"),
         ("Colebrook", "colebrook"), ("East Granby", "east-granby"), ("Farmington", "farmington"), ("Granby", "granby"), ("Hartland", "hartland"),
         ("New Hartford", "new-hartford"), ("Simsbury", "simsbury")]}
S = requests.Session()
S.headers["User-Agent"] = "ct-eats data pipeline (work-with-nick@gmail.com)"


def parse(page, town):
    """Each place is a card: name, street address, "Current Rating: A – 4/29/2026", then a history of earlier ratings."""
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S)
    toks = [html.unescape(re.sub(r"\s+", " ", t)).strip() for t in re.split(r"<[^>]+>", text)]
    toks = [t for t in toks if t and t not in ("|", "–", "-")]
    out = []
    for i, t in enumerate(toks):
        m = re.match(r"Current Rating:\s*([ABCU])\b", t)
        if not m or i < 2:
            continue
        # the date can be split across tags ("– 5" + "/28/2026"): read it from the card text up to its History list
        card = "".join(toks[i:i + 6]).split("History")[0].replace(" ", "")
        dm = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", card)
        date = dm.group(1) if dm else None
        name, addr = toks[i - 2], toks[i - 1]
        if not re.match(r"\d", addr):   # no street address on the card: the token before the rating is the name
            name, addr = toks[i - 1], None
        if date:
            mo, d, y = date.split("/"); date = f"{y}-{int(mo):02d}-{int(d):02d}"
        out.append({"town": town, "name": name, "address": addr, "rating": m.group(1), "date": date})
    return out


def main():
    prev = collections.Counter(e["town"] for e in json.load(open(f"{OUT}/fvhd_ratings.json"))["ratings"]) if os.path.exists(f"{OUT}/fvhd_ratings.json") else {}
    rows, pages = [], {}
    for i, (town, path) in enumerate(TOWNS.items()):
        if i:
            time.sleep(30)
        url = "https://fvhd.org/" + path
        try:
            r = S.get(url, timeout=60, allow_redirects=False)
        except requests.ConnectionError as e:
            print(f"stopped: {url} dropped the connection ({e.__class__.__name__}); keeping the previous file, try again on the next refresh")
            sys.exit(1)
        if r.status_code in (403, 429, 503) or r.is_redirect:
            print(f"stopped: {url} answered {r.status_code}; keeping the previous file, try again on the next refresh")
            sys.exit(1)
        r.raise_for_status()
        got = parse(r.text, town)
        print(town, len(got), "rated places", flush=True)
        # a 200 that isn't the ratings page (a bot check, a redesign) parses to nothing: never let it erase a town's ratings
        if not got or len(got) < 0.5 * prev.get(town, 0):
            print(f"stopped: {url} gave {len(got)} ratings (last time {prev.get(town, 0)}); keeping the previous file, check the page by hand")
            sys.exit(1)
        rows += got; pages[town] = url
    json.dump({"source": "Farmington Valley Health District, food ratings by town", "index": "https://fvhd.org/environmental-health/food/food-ratings/",
               "pages": pages, "fetched": time.strftime("%Y-%m-%d"), "ratings": rows}, open(f"{OUT}/fvhd_ratings.json", "w"), indent=1)
    print("wrote", len(rows), "ratings")


if __name__ == "__main__":
    main()
