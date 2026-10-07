"""Writes the public website in docs/ from the same data file the app ships (data/app/places.json).

Pages: the landing page, four statewide guides (New Haven apizza, lobster rolls and clam shacks, burger and hot dog icons,
diners and dairy bars), Connecticut's oldest restaurants, one page per big town, privacy, terms, 404, the web app at explore/,
plus sitemap.xml, robots.txt, site.webmanifest and playbook/site-numbers.json. Everything listed is hand-checked research or
licensed open data; nothing comes from Google or any ratings site, and nothing is ranked by ratings.

Modeled on wi-eats/scripts/make-site.py (Wisconsin). Never hand-edit docs/*.html: change this file and re-run it.

Usage (from ct-eats/): .venv/bin/python scripts/make-site.py
Re-run it after every data rebuild, then run scripts/qa-site.py. When the restaurant or town count changes, it also redraws
docs/og.png (swift scripts/make-brand.swift og), whose tagline carries those numbers.
"""
import base64
import datetime
import hashlib
import html
import json
import math
import os
import re
import shutil
import struct
import subprocess
import urllib.parse
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS = f"{ROOT}/docs"
# Where the site lives. Today: GitHub Pages at the project address, because connecticut.eatsranked.com has no DNS record yet.
# Once Nick adds the Cloudflare record (CNAME connecticut -> nickstrom5.github.io, DNS only) and `dig` shows it, set
# CUSTOM_DOMAIN = "connecticut.eatsranked.com", re-run, push, and switch ConnecticutEats/App/Links.swift with it.
# GitHub then forwards the old github.io links (the ones inside shipped app builds) to it.
CUSTOM_DOMAIN = None
DOMAIN = f"https://{CUSTOM_DOMAIN}" if CUSTOM_DOMAIN else "https://nickstrom5.github.io/connecticut-eats"
BASE = "" if CUSTOM_DOMAIN else "/connecticut-eats"     # path prefix for root-relative links
BRAND = "Connecticut Eats"
SHORT = "CT Eats"
TAGLINE = "Apizza & lobster roll guide"
EMAIL = "work-with-nick@gmail.com"
# Once the App Store listing exists, paste its URL here (looks like https://apps.apple.com/app/id123456789) and re-run: every
# "Get early access" button becomes an App Store link (Apple's official badge if docs/img/app-store-badge.svg is there; get it
# from Apple's marketing tools, never draw the Apple logo), the notes stop saying "coming", the privacy page says the label "is",
# and the web app's place panel links the App Store (it reads window.APP_STORE_URL). Also fill in the apple-itunes-app meta tag
# in page() below.
APP_STORE_URL = ""
TODAY = datetime.date.today().isoformat()   # sitemap lastmod and dateModified; datePublished comes from FIRST_PUBLISHED
CHECKED = "October 2026"
PRIVACY_UPDATED = TERMS_UPDATED = "2026-10-07"   # change these when the policy or terms text changes, not on every build
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def nice_date(iso):
    y, m, d = iso.split("-")
    return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"


D = json.load(open(f"{ROOT}/data/app/places.json"))
SHAPES = json.load(open(f"{ROOT}/data/app/ct_shapes.json"))
DATA_DATE = D["generated"]
CITIES, VILLAGES, CUISINES, HOSTS, REGIONS = D["cities"], D["villages"], D["cuisines"], D["hosts"], D["regions"]
# the bit meanings must match the app (ConnecticutEats/Models/Place.swift: PlaceTags and Kinds)
assert D["tags"] == ["apizza", "lobster", "clams", "steamed", "hotdog", "dairy", "diner", "polish"], D["tags"]
assert D["kinds"] == ["apizza", "lobster roll", "clam shack", "steamed cheeseburger", "burger icon", "hot dog icon", "diner",
                      "dairy bar", "polish", "oldest", "grinder"], D["kinds"]
assert HOSTS == ["Foxwoods", "Mohegan Sun"], HOSTS
TAG = {t: 1 << i for i, t in enumerate(D["tags"])}
KIND = {k: 1 << i for i, k in enumerate(D["kinds"])}
KIND_LABEL = {"apizza": "Apizza", "lobster roll": "Lobster roll", "clam shack": "Clam shack", "steamed cheeseburger": "Steamed cheeseburger",
              "burger icon": "Burger icon", "hot dog icon": "Hot dogs", "diner": "Diner", "dairy bar": "Dairy bar", "polish": "Polish",
              "oldest": "Historic", "grinder": "Grinders"}
ALL_TOWNS = sorted(t["name"] for t in SHAPES["towns"])
N_ALL_TOWNS = len(ALL_TOWNS)
assert N_ALL_TOWNS == 169, N_ALL_TOWNS
REGION_OF_TOWN = {CITIES[i]: REGIONS[r] for i, r in enumerate(D["town_region"]) if r is not None}
# The pipeline takes a village from the mailing city on a license or a research entry. A few carry another town's name
# ("Stamford" for a place in Groton) or a cut-off one ("Prospe"); those aren't villages, so the site doesn't show them.
VALID_VILLAGE = {v: v not in ALL_TOWNS for v in VILLAGES}
HOST_TEXT = {"Foxwoods": "Inside Foxwoods Resort Casino, on Mashantucket Pequot tribal land",
             "Mohegan Sun": "Inside Mohegan Sun, on Mohegan tribal land"}
RATING_MEANING = {"A": "Excellent", "B": "Good", "C": "Fair", "U": "Unsatisfactory"}


class P:
    """One place, with the same meaning the app gives each field (ConnecticutEats/Models/Place.swift)."""

    def __init__(self, i, r):
        self.i, self.r = i, r
        self.id = r["id"]
        self.name = r["n"]
        self.city = CITIES[r["c"]] if r.get("c") is not None else ""
        v = VILLAGES[r["vi"]] if r.get("vi") is not None else None
        self.village = v if v and VALID_VILLAGE[v] and not self.city.startswith(v) else None
        self.region = REGION_OF_TOWN.get(self.city)
        self.cuisine = CUISINES[r["cu"]]
        self.addr = r.get("a") or ""
        self.zip = r.get("z") or ""
        self.lat, self.lon = r.get("la"), r.get("lo")
        self.tags = r.get("g") or 0
        self.kinds = r.get("k") or 0
        self.hc = r.get("hc") == 1   # hand-checked open with a 2025-26 source; the only places the guides list
        self.venue = r.get("v") == 1
        self.chain_n = r.get("ch") or 1
        self.chain = self.chain_n >= 5
        self.ip = r.get("ip")        # iconic points: true icons only (honors, or 40+ years at the address)
        self.fs = r.get("fs")        # the featured score every hand-checked place has (the app's "Featured first")
        self.founded = r.get("f")    # the year at this address (not the brand's founding year)
        self.note = r.get("note") or ""
        self.dish = r.get("dish") or ""
        self.season = r.get("sea") or ""
        self.seasonal = r.get("seas") == 1
        self.branch = r.get("br") or ""
        self.chef = r.get("chef") or ""
        # the James Beard Foundation calls its finalists "nominees" (data/research/HONORS.md); older exports said "finalist"
        self.jbf = re.sub(r"\bfinalist\b", "nominee", r.get("jbf") or "")
        self.hon = r.get("hon") or ""
        self.h = r.get("h") or 0
        self.host = HOSTS[r["host"]] if r.get("host") is not None else None
        w = r.get("w") or ""
        self.site = w if urllib.parse.urlsplit(w).scheme in ("http", "https") else ""   # a link only for http(s), never javascript: or data:
        ph = r.get("ph") or ""
        self.phone = ph if re.fullmatch(r"\+1[2-9]\d{9}", ph) else ""   # a valid US number only; anything else could dial abroad
        self.fv = r.get("fv")

    @property
    def place_name(self):
        """"Mystic (Groton)" or "New Haven", as the app's Place.placeName."""
        return f"{self.village} ({self.city})" if self.village else self.city

    @property
    def jb_label(self):
        # the best honor only, and never a finalist called a winner (Place.jamesBeardLabel)
        return ("America's Classic" if self.h & 1 else "James Beard winner" if self.h & 2 else "James Beard nominee" if self.h & 4
                else "James Beard semifinalist" if self.h & 8 else None)

    def kind_names(self):
        return [KIND_LABEL[k] for k in D["kinds"] if self.kinds & KIND[k]]

    def featured_key(self):
        # the app's "Featured first": the featured score (else iconic points), then the verified year at this address, then name
        score = self.fs if self.fs is not None else self.ip
        return (-(score if score is not None else -1), self.founded or 9999, self.name.lower())


PLACES = [P(i, r) for i, r in enumerate(D["places"])]
REST = [p for p in PLACES if not p.venue]
assert all(not p.venue for p in PLACES if p.hc), "a hand-checked place is hidden as a non-restaurant"
assert all(p.hc for p in PLACES if p.ip is not None or p.fs is not None or p.founded), "a score or a year without hand-checking"
assert all(p.jb_label != "James Beard winner" or re.search(r"\bwinner\b", p.jbf, re.I) for p in PLACES), "a winner label without a win"


def guide(cond):
    return sorted([p for p in REST if p.hc and cond(p)], key=P.featured_key)


# the app's guides (ConnecticutEats/Models/Guide.swift): hand-checked only, by `k` kind bits; a listing merely named
# "... Diner" or "... Apizza" stays in the directory but is not in a guide
APIZZA = guide(lambda p: p.kinds & KIND["apizza"])
LOBSTER = guide(lambda p: p.kinds & (KIND["lobster roll"] | KIND["clam shack"]))
BURGERS = guide(lambda p: p.kinds & (KIND["burger icon"] | KIND["steamed cheeseburger"] | KIND["hot dog icon"]))
DINERS = guide(lambda p: p.kinds & KIND["diner"])
DAIRY = guide(lambda p: p.kinds & KIND["dairy bar"])
DINERS_DAIRY = guide(lambda p: p.kinds & (KIND["diner"] | KIND["dairy bar"]))
POLISH = guide(lambda p: p.kinds & KIND["polish"])
HC = [p for p in REST if p.hc]
OLDEST = sorted([p for p in REST if p.founded], key=lambda p: (p.founded, p.name.lower()))
CASINO = [p for p in REST if p.host]
FV = [p for p in REST if p.fv]
FV_TOWNS = sorted({p.city for p in FV})
# the Farmington Valley Health District's member towns; copy says "its 10 towns", so fail loudly if the data disagrees
assert FV_TOWNS == ["Avon", "Barkhamsted", "Canton", "Colebrook", "East Granby", "Farmington", "Granby", "Hartland", "New Hartford", "Simsbury"], FV_TOWNS
assert all(p.fv["r"] in RATING_MEANING and re.match(r"^\d{4}-\d{2}-\d{2}$", p.fv.get("d") or "") for p in FV)
N_FV = len(FV_TOWNS)
N_REST = len(REST)
assert N_REST == D["count_restaurants"], (N_REST, D["count_restaurants"])
TOWN_COUNT = Counter(p.city for p in REST if p.city)
N_TOWNS = len(TOWN_COUNT)
NAMED_DINER = sum(1 for p in REST if p.tags & TAG["diner"] and not p.hc)
NAMED_APIZZA = sum(1 for p in REST if p.tags & TAG["apizza"] and not p.hc)
# the same per town and tag: directory places named like a classic ("… Diner", "… Apizza") that we haven't checked
NAMED_IN_TOWN = {t: Counter(p.city for p in REST if p.tags & TAG[t] and not p.hc) for t in D["tags"]}

# ---------------------------------------------------------------- planning regions (Connecticut has no county governments)
# shoreline west to east, then inland; must be exactly the data's nine
REGION_ORDER = ["Western Connecticut", "Greater Bridgeport", "South Central Connecticut", "Lower Connecticut River Valley",
                "Southeastern Connecticut", "Northeastern Connecticut", "Capitol", "Naugatuck Valley", "Northwest Hills"]
assert sorted(REGION_ORDER) == sorted(REGIONS), REGIONS
REGION_NAME = {r: ("Capitol region" if r == "Capitol" else r) for r in REGION_ORDER}
REGION_TOWNS = defaultdict(Counter)
for p in REST:
    if p.region:
        REGION_TOWNS[p.region][p.city] += 1
REGION_HINT = {r: [t for t, _ in REGION_TOWNS[r].most_common(3)] for r in REGION_ORDER}


def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


# ---------------------------------------------------------------- html helpers
e = html.escape


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("'", "")).strip("-")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def and_list(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + (", and " if len(xs) > 2 else " and ") + xs[-1]


# A private address must never reach a public page. Only the sha256 digests of its pieces live here (the address, its user and
# domain), so this public file doesn't spell it out; private_words() reports any word or email on a page that hashes to one.
PRIVATE_DIGESTS = {
    "4a7e25559b2ffc162afaef2b1680778c6e77d8c2982c3870595f6ee8fea7a455",
    "ff8ea15b513b5561b1c48b725aff52338eddb8ecdd46af58759e2f2c554b0582",
    "31b7679e2f02e2b0561693acc0c78f067633b6713ac53fb5980dcb0f7c2ea237",
    "928009cbd52e0a32a3542c0f41efa0ac8feef2e05974b8126f26c7d4f9b593e3",
}


def private_words(text):
    t = text.lower()
    words = set(re.findall(r"[\w.%+-]+@[\w.-]+", t)) | set(re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)*", t)) | set(re.findall(r"[a-z0-9]+", t))
    return [w for w in words if hashlib.sha256(w.encode()).hexdigest() in PRIVATE_DIGESTS]


def plural(n, one, many=None):
    return f"{n:,} {one if n == 1 else (many or one + 's')}"


def explore_url(**params):
    """A web app link with its state in the hash, e.g. explore_url(g="all", town="West Hartford", kind="Pizza")."""
    return "/explore/#" + urllib.parse.urlencode(params)


def checked_open(ps):
    """'confirmed open in October 2026', or 'checked in business …' when the list has seasonal places that may be closed for
    the season right now."""
    return f"checked in business in {CHECKED}" if any(p.seasonal for p in ps) else f"confirmed open in {CHECKED}"


# The app icon in miniature (scripts/make-brand.swift): an oblong, charred New Haven apizza on a gray sheet pan, on navy.
_CHAR = "".join(f'<circle cx="{32 + 20.6 * math.cos(t):.1f}" cy="{32 + 13.1 * math.sin(t):.1f}" r="{r}" fill="{c}"/>'
                for t, r, c in [(a * math.pi / 7 + 0.2, 1.9 if a % 2 else 1.4, "#2E1A0E" if a % 3 else "#5A3418") for a in range(14)])
LOGO = ('<svg viewBox="0 0 64 64" width="32" height="32" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#000E2F"/>'
        '<g transform="rotate(15 32 32)"><rect x="5" y="14" width="54" height="36" rx="5" fill="#7C878E"/>'
        '<rect x="7.5" y="16.5" width="49" height="31" rx="3.5" fill="#5F696F"/>'
        '<ellipse cx="32" cy="32" rx="22" ry="14.4" fill="#D99A5B"/><ellipse cx="32" cy="32" rx="17.6" ry="10.8" fill="#B82E1C"/>'
        '<ellipse cx="24" cy="28.5" rx="3.6" ry="2.6" fill="#8F1F12"/><ellipse cx="38" cy="35.5" rx="3.8" ry="2.7" fill="#8F1F12"/>'
        '<ellipse cx="41" cy="27.5" rx="2.5" ry="1.8" fill="#8F1F12"/>'
        '<ellipse cx="29" cy="35" rx="1.3" ry=".9" fill="#F3E3C3"/><ellipse cx="33" cy="27" rx="1.3" ry=".9" fill="#F3E3C3"/>'
        '<ellipse cx="45" cy="33" rx="1.2" ry=".85" fill="#F3E3C3"/><ellipse cx="20" cy="34" rx="1.2" ry=".85" fill="#F3E3C3"/>'
        + _CHAR + "</g></svg>")
FAVICON = "data:image/svg+xml," + LOGO.replace('width="32" height="32" ', "").replace(' aria-hidden="true"', "").replace("<svg ", "<svg xmlns='http://www.w3.org/2000/svg' ").replace('"', "'").replace("#", "%23").replace("<", "%3C").replace(">", "%3E")


def shoreline(n=10, w=1200, h=14):
    """The Long Island Sound shoreline: a low tomato wave under the navy header (the app's Theme.Shoreline)."""
    mid, amp, seg = h * 0.45, h * 0.38, w / n
    d = f"M0 {mid:.1f}"
    for i in range(n):
        x0 = i * seg
        d += f" C{x0 + seg * .33:.1f} {mid - amp:.1f} {x0 + seg * .66:.1f} {mid + amp:.1f} {x0 + seg:.1f} {mid:.1f}"
    return (f'<svg class="shore" viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
            f'<rect width="{w}" height="{h}" fill="#000E2F"/><path d="{d} L{w} {h} L0 {h} Z" fill="#B3261E"/></svg>')


SHORE = shoreline()

CSS = """
  :root {
    color-scheme: light;
    --bg: #f7f8fb; --surface: #fff; --surface2: #f2f4f8; --surface3: #e3e8f0; --rule: #dce2eb; --rule2: #7a879d;   /* --rule2 outlines controls: 3:1 or more on every background */
    --gray: #7c878e;   /* rules only, never text (3.7:1 on white) */
    --ink: #0b1426; --ink2: #2b3a55; --muted: #4c5870;
    --navy: #000e2f; --navy2: #2a4170; --tomato: #b3261e; --tomatosoft: #f8deda; --ontomato: #6b1510;
    --radius: 16px;
    --display: "Avenir Next Condensed", "HelveticaNeue-CondensedBold", "Arial Narrow", system-ui, sans-serif;
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  @media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
  body { margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.55 -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif; -webkit-font-smoothing: antialiased; }
  a { color: var(--navy2); text-underline-offset: 2px; }
  a:focus-visible, summary:focus-visible, button:focus-visible, select:focus-visible, input:focus-visible { outline: 3px solid var(--tomato); outline-offset: 3px; border-radius: 6px; }
  .skip { position: absolute; left: -9999px; top: 0; background: var(--tomato); color: #fff; padding: 10px 14px; font-weight: 700; z-index: 30; }
  .skip:focus { left: 8px; top: 8px; }
  .wrap { max-width: 760px; margin: 0 auto; padding: 0 20px; }
  header.site { background: var(--navy); color: #fff; }
  header.site .bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 20px; }
  .shore { display: block; width: 100%; height: 14px; }
  .logo { display: flex; align-items: center; gap: 10px; min-height: 44px; font: 800 22px/1 var(--display); text-transform: uppercase; letter-spacing: .01em; color: #fff; text-decoration: none; }
  .logo svg { flex: 0 0 auto; border-radius: 8px; box-shadow: 0 0 0 1px rgba(255,255,255,.25); }
  header.site nav { display: flex; flex-wrap: wrap; gap: 4px 16px; justify-content: flex-end; }
  header.site nav a { color: #e3e8f0; text-decoration: none; font-size: 15px; }
  header.site nav a:hover { color: #fff; text-decoration: underline; }
  header.site a:focus-visible { outline-color: #fff; }
  h1, h2 { font-family: var(--display); font-weight: 800; color: var(--navy); letter-spacing: -.005em; }
  h1 { font-size: clamp(36px, 7.5vw, 56px); line-height: 1.02; margin: 0 0 16px; text-transform: uppercase; }
  .kicker { font: 700 15px/1.4 -apple-system, system-ui, sans-serif; letter-spacing: .06em; color: var(--muted); margin: 0 0 12px; }
  .sr { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
  h2 { font-size: 32px; line-height: 1.1; margin: 0 0 10px; }
  h3 { font-size: 18px; margin: 0; line-height: 1.3; }
  .lede { font-size: 19px; color: var(--ink2); margin: 0 0 26px; }
  .hero { padding: 40px 0 28px; }
  section { padding: 36px 0; border-top: 1px solid var(--rule); }
  section.hero { border: 0; }
  .sub { color: var(--ink2); margin: 0 0 22px; }
  .cta-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
  .btn { display: inline-flex; align-items: center; gap: 10px; background: var(--tomato); color: #fff; font-weight: 700; padding: 14px 20px; border-radius: 14px; text-decoration: none; font-size: 17px; }
  .btn svg { width: 22px; height: 22px; }
  .btn-ghost { background: transparent; color: var(--navy); border: 2px solid var(--navy); }
  .store-badge { display: inline-block; border-radius: 10px; }
  .store-badge img { display: block; height: 50px; width: auto; }
  .pill { font-size: 14px; color: var(--muted); }
  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 28px 0 0; padding: 0; list-style: none; }
  .stats li { background: var(--surface); border: 1px solid var(--rule); border-top: 4px solid var(--tomato); border-radius: 14px; padding: 14px; }
  .stats b { display: block; font: 800 30px/1 var(--display); color: var(--navy); }
  .stats span { font-size: 14px; color: var(--muted); }
  .steps { display: grid; gap: 12px; list-style: none; margin: 0; padding: 0; }
  .step { display: flex; gap: 14px; background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius); padding: 18px; }
  .step .n { flex: 0 0 32px; height: 32px; border-radius: 50%; background: var(--tomato); color: #fff; font-weight: 800; display: grid; place-items: center; }
  .step p { margin: 4px 0 0; color: var(--ink2); }
  .shots { display: flex; gap: 14px; overflow-x: auto; margin: 0 -20px; padding: 4px 20px 14px; scroll-snap-type: x proximity; list-style: none; }
  .shots li { flex: 0 0 auto; width: 210px; scroll-snap-align: start; }
  .shots img { display: block; width: 210px; height: auto; border-radius: 24px; border: 1px solid var(--rule); background: var(--surface2); }
  .shots p { font-size: 14px; color: var(--muted); margin: 8px 2px 0; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .card { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius); padding: 18px; }
  .card p { margin: 6px 0 0; color: var(--ink2); }
  a.card { display: block; text-decoration: none; color: var(--ink); }
  a.card h3 { color: var(--navy); }
  a.card:hover h3 { text-decoration: underline; }
  .towns { display: flex; flex-wrap: wrap; gap: 8px; list-style: none; padding: 0; margin: 0; }
  .towns a { display: inline-flex; align-items: center; min-height: 44px; padding: 8px 12px; border-radius: 999px; border: 1px solid var(--rule); background: var(--surface); text-decoration: none; color: var(--ink); font-size: 15px; }
  .towns a:hover { border-color: var(--navy); }
  details { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 2px 18px; margin-bottom: 10px; }
  summary { cursor: pointer; padding: 14px 0; font-weight: 600; list-style: none; display: flex; justify-content: space-between; gap: 12px; }
  summary::-webkit-details-marker { display: none; }
  summary::after { content: "+"; color: var(--tomato); font-weight: 800; }
  details[open] summary::after { content: "\\2013"; }
  details p { margin: 0 0 16px; color: var(--ink2); }
  .final { text-align: center; }
  .final .cta-row { justify-content: center; }
  nav.crumbs { font-size: 14px; color: var(--muted); padding: 16px 0 0; }
  nav.crumbs ol { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 6px; }
  nav.crumbs li + li::before { content: "/"; content: "/" / ""; margin-right: 6px; color: var(--gray); }   /* the separator has no spoken text */
  nav.crumbs a { color: var(--muted); }
  .places { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
  .places li { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 14px 16px; min-width: 0; overflow-wrap: anywhere; }
  .places .where { margin: 2px 0 0; font-size: 15px; color: var(--muted); }
  .places .facts { margin: 8px 0 0; font-size: 15px; color: var(--ink2); }
  .places .facts b { color: var(--ink); font-weight: 600; }
  .places .note { margin: 6px 0 0; font-size: 15px; color: var(--ink2); }
  .places .link { margin: 6px 0 0; font-size: 14px; }
  .tag { display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; background: var(--tomatosoft); color: var(--ontomato); border-radius: 6px; padding: 1px 6px; margin: 0 4px 2px 0; }
  .tag-jb { background: var(--navy); color: #fff; }
  .tag-plain { background: var(--surface2); color: var(--navy); }
  .tag-dash { background: transparent; color: var(--muted); border: 1px dashed var(--rule2); }
  .toc { columns: 2; padding-left: 20px; margin: 0; }
  table { border-collapse: collapse; width: 100%; font-size: 15px; }
  th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--rule); }
  td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
  .places .fv { display: flex; align-items: center; gap: 10px; margin: 8px 0 0; font-size: 15px; color: var(--ink2); }
  .places .fv small { display: block; color: var(--muted); font-size: 14px; }
  .rb { flex: 0 0 auto; display: inline-grid; place-items: center; width: 34px; height: 34px; border-radius: 9px; color: #fff; font: 800 21px/1 var(--display); }
  .rb-A { background: #12733a; } .rb-B { background: #4b6e1b; } .rb-C { background: #8a5a00; } .rb-U { background: #b3261e; }
  .fine { font-size: 14px; color: var(--muted); }
  .legal h2 { font-size: 26px; margin-top: 28px; }
  .legal p, .legal li { color: var(--ink2); }
  .legal blockquote { margin: 0; padding: 12px 16px; background: var(--surface); border: 1px solid var(--rule); border-left: 4px solid var(--gray); border-radius: 10px; font-size: 14px; color: var(--ink2); overflow-wrap: anywhere; }
  .legal blockquote p { margin: 0 0 8px; }
  footer { padding: 32px 0 56px; color: var(--muted); font-size: 14px; border-top: 1px solid var(--gray); margin-top: 20px; }
  footer nav { display: flex; flex-wrap: wrap; gap: 8px 16px; }
  footer a { color: var(--muted); }
  footer p { margin: 12px 0 0; }
  @media (max-width: 600px) {
    .grid2 { grid-template-columns: 1fr; }
    .stats { grid-template-columns: 1fr 1fr; }
    .toc { columns: 1; }
    header.site .bar { flex-direction: column; align-items: flex-start; padding: 14px 20px; }
    header.site nav { justify-content: flex-start; }
    /* 44 px touch targets */
    header.site nav a, footer nav a { display: inline-block; padding: 11px 0; }
    header.site nav { gap: 0 16px; }
    nav.crumbs a { display: inline-block; padding: 12px 0; }
    nav.crumbs { padding-top: 4px; }
    nav.crumbs ol { align-items: center; }
    .places .link a { display: inline-block; padding: 11px 0; }
    .places .link { margin: 0; }
  }
"""


def find_keys(obj, keys):
    if isinstance(obj, dict):
        return [k for k in obj if k in keys] + [x for v in obj.values() for x in find_keys(v, keys)]
    if isinstance(obj, list):
        return [x for v in obj for x in find_keys(v, keys)]
    return []


def jsonld(obj):
    # no ratings or reviews from anyone, ever (structured data included)
    bad = find_keys(obj, {"aggregateRating", "review", "reviews", "reviewRating", "ratingValue"})
    assert not bad, bad
    big = obj.get("@type") == "ItemList"
    text = json.dumps(obj, ensure_ascii=False, indent=None if big else 1, separators=(",", ":") if big else None)
    # a name with "</script>" in it must not end the block: escape the characters HTML cares about (JSON reads them back the same)
    text = text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return '<script type="application/ld+json">\n' + text + "\n</script>"


def crumbs(trail):
    """trail: [(name, url)] ending with the current page."""
    items = "".join(f'<li><a href="{u}">{e(n)}</a></li>' if i < len(trail) - 1 else f'<li aria-current="page">{e(n)}</li>'
                    for i, (n, u) in enumerate(trail))
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u} for i, (n, u) in enumerate(trail)]}
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{items}</ol></nav>', ld


def store_button(label="Get early access"):
    if APP_STORE_URL:
        # Apple's own badge artwork only (never a drawn Apple logo); plain text until the badge file is in docs/img
        if os.path.exists(f"{DOCS}/img/app-store-badge.svg"):
            return (f'<a class="store-badge" href="{e(APP_STORE_URL)}" rel="noopener"><img src="/img/app-store-badge.svg" '
                    'alt="Download on the App Store" width="150" height="50"></a>')
        return f'<a class="btn store-btn" href="{e(APP_STORE_URL)}" rel="noopener">Download on the App Store</a>'
    # pre-launch: no App Store link exists yet, so the button asks for a TestFlight invite by email (Wisconsin's approach)
    return (f'<a class="btn store-btn" href="mailto:{EMAIL}?subject=Connecticut%20Eats%20early%20access&amp;body=Send%20me%20the%20TestFlight%20link.">'
            f'{label}</a>')


def store_note(text="Free for iPhone and iPad."):
    return f'{text} Coming to the App Store.' if not APP_STORE_URL else text


GUIDE_PAGES = [("new-haven-apizza.html", "New Haven apizza"), ("connecticut-lobster-rolls.html", "Lobster rolls & clam shacks"),
               ("connecticut-hot-dogs-burgers.html", "Hot dog & burger icons"), ("connecticut-diners-dairy-bars.html", "Diners & dairy bars")]
OLDEST_PAGE = ("connecticut-oldest-restaurants.html", "Oldest restaurants")


def page(path, title, desc, body, lds=(), robots="index,follow,max-image-preview:large", og_alt=None, extra_css="", head_extra=""):
    assert 50 <= len(title) <= 60 or path == "404.html", (path, len(title), title)
    assert 140 <= len(desc) <= 160 or path == "404.html", (path, len(desc), desc)
    assert body.count("<h1") == 1, path
    assert path in FIRST_PUBLISHED or path == "404.html", f"add {path} to FIRST_PUBLISHED"
    url = DOMAIN + "/" + ("" if path == "index.html" else path.removesuffix("index.html"))
    # GitHub serves 404.html for every missing URL, so it names no canonical address of its own
    canonical = "" if path == "404.html" else f'<link rel="canonical" href="{url}">\n'
    og_url = "" if path == "404.html" else f'<meta property="og:url" content="{url}">\n'
    og_alt = og_alt or f"{BRAND}: {TAGLINE}. Connecticut restaurants, with hand-checked New Haven apizza, lobster rolls, clam shacks, and diners."
    ld = "\n".join(jsonld(x) for x in lds)
    doc = f"""<!DOCTYPE html>
<html lang="en" data-base="{BASE}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{canonical}<meta name="robots" content="{robots}">
<meta name="theme-color" content="#000E2F">
<meta name="color-scheme" content="light">
<!-- Smart App Banner: once the App Store Connect record exists, replace APP_ID with the numeric Apple ID and uncomment.
<meta name="apple-itunes-app" content="app-id=APP_ID">
-->
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
{og_url}<meta property="og:type" content="{'website' if path == 'index.html' else 'article'}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="{DOMAIN}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{DOMAIN}/og.png">
<meta name="twitter:image:alt" content="{e(og_alt)}">
<link rel="icon" type="image/svg+xml" href="{FAVICON}">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
{head_extra}<style>{CSS}{extra_css}</style>
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site">
  <div class="bar wrap">
    <a class="logo" href="/" aria-label="{BRAND} home">{LOGO}{BRAND}</a>
    <nav aria-label="Main">
      <a href="/new-haven-apizza.html">Apizza</a>
      <a href="/connecticut-lobster-rolls.html">Lobster rolls</a>
      <a href="/connecticut-hot-dogs-burgers.html">Hot dogs</a>
      <a href="/connecticut-diners-dairy-bars.html">Diners</a>
      <a href="/#towns">Towns</a>
      <a href="/explore/">Search</a>
    </nav>
  </div>
  {SHORE}
</header>
<div class="wrap">
{body}
  <footer>
    <nav aria-label="Footer">
      <a href="/">{BRAND} app</a>
      <a href="/explore/">Search Connecticut restaurants</a>
      {"".join(f'<a href="/{u}">{e(n)}</a>' for u, n in GUIDE_PAGES + [OLDEST_PAGE])}
      <a href="/privacy.html">Privacy policy</a>
      <a href="/terms.html">Terms of use</a>
      <a href="mailto:{EMAIL}">Email us</a>
    </nav>
    <p>Place data: hand-checked research by {BRAND} (checked {CHECKED}); Overture Maps Foundation places (CDLA Permissive 2.0, and Apache 2.0 for Foursquare data, with the <a href="/terms.html#sources">Foursquare NOTICE</a>); Connecticut Department of Consumer Protection licenses (data.ct.gov, public domain); City of Hartford open data; Farmington Valley Health District food service ratings; U.S. Census Bureau town outlines. In the app, maps and each place's live card come from Apple Maps. Data as of {nice_date(DATA_DATE)}.</p>
    <p>{BRAND} is independent: not affiliated with or endorsed by the State of Connecticut, the City of Hartford, the Farmington Valley Health District, the Mashantucket Pequot or Mohegan tribes or their casinos, the University of Connecticut, the James Beard Foundation, Apple, or any restaurant or chain. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. Places open and close, so check before you go.</p>
    <p>© 2026 {BRAND}.</p>
  </footer>
</div>
</body>
</html>
"""
    if BASE:   # served under /connecticut-eats/: every root-relative link and asset gets the prefix
        doc = re.sub(r'(href|src|srcset)="/', rf'\1="{BASE}/', doc)
    # A Content-Security-Policy in a meta tag (GitHub Pages can't send headers), first in <head>: only this page's own inline
    # scripts run, by hash (JSON-LD blocks are data, not scripts), and nothing loads from any other site. The hashes change
    # with every edit to a script, so they're computed here, after the last change to the page.
    scripts = re.findall(r"<script>(.*?)</script>", doc, re.S)
    hashes = " ".join(f"'sha256-{base64.b64encode(hashlib.sha256(x.encode()).digest()).decode()}'" for x in scripts) or "'none'"
    csp = (f"default-src 'none'; script-src {hashes}; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
           "manifest-src 'self'; base-uri 'none'; form-action 'none'; upgrade-insecure-requests")
    doc = doc.replace("<head>\n", f'<head>\n<meta http-equiv="Content-Security-Policy" content="{csp}">\n', 1)
    # data honesty, checked on every page: no Google-derived wording, no MICHELIN claims, the official FVHD rating only
    # where it may appear (the town pages of its own towns; the web app shows it in the place panel)
    assert "google" not in doc.lower(), path
    assert "michelin" not in doc.lower(), path
    assert not private_words(doc), path
    if re.search(r'class="rb rb-[ABCU]"', body):
        assert path.startswith("towns/") and any(slug(t) in path for t in FV_TOWNS), path
    os.makedirs(os.path.dirname(f"{DOCS}/{path}"), exist_ok=True)
    open(f"{DOCS}/{path}", "w", encoding="utf-8").write(doc)
    return path


def chips(p):
    out = []
    if p.jb_label:
        out.append(f'<span class="tag tag-jb">{p.jb_label}</span>')
    out += [f'<span class="tag">{k}</span>' for k in p.kind_names() if k != "Historic"]
    if p.seasonal:
        out.append('<span class="tag tag-plain">Seasonal</span>')
    if p.host:
        out.append(f'<span class="tag tag-plain">At {e(p.host)}</span>')
    return "".join(out)


def place_where(p, here_town=None):
    """"12 Wooster St, New Haven", with the town linked to its town page when it has one (and isn't this page's town)."""
    town = e(p.place_name)
    if p.city in TOWN_PAGES and p.city != here_town:
        town = f'<a href="{town_url(p.city)}">{town}</a>'
    return ", ".join(x for x in (e(p.addr), town) if x)


def place_item(p, extra=None, show_fv=False, here_town=None):
    """One place on a guide or town page, anchored as #p-<id> (the JSON-LD list items point there). show_fv: the official
    Farmington Valley rating, only on the pages of its own towns. here_town: the town page it's on (its own town isn't linked)."""
    facts = []
    if p.dish:
        facts.append(f"<b>Known for:</b> {e(p.dish)}")
    if p.season:
        facts.append(f"<b>Season:</b> {e(p.season)}")
    elif p.seasonal:
        facts.append("<b>Season:</b> seasonal; check before you go")
    if p.founded:
        facts.append(f"<b>At this address since</b> {p.founded}")
    if p.branch:
        facts.append(f"<b>A branch of</b> {e(p.branch)}")
    where = place_where(p, here_town)
    if extra:
        where += f" · {e(extra)}"
    out = [f'<li id="p-{p.id}"><h3>{e(p.name)}</h3>', f'<p class="where">{where}</p>']
    c = chips(p)
    if c or facts:
        out.append('<p class="facts">' + c + (" " if c and facts else "") + " · ".join(facts) + "</p>")
    if p.host and "tribal land" not in p.note:
        out.append(f'<p class="note">{HOST_TEXT[p.host]}.</p>')
    if p.note:
        out.append(f'<p class="note">{e(p.note)}</p>')
    if p.jbf:
        out.append(f'<p class="note"><b>James Beard:</b> {e(p.jbf)}</p>')
    if show_fv and p.fv and p.city in FV_TOWNS:
        r = p.fv["r"]
        out.append(f'<p class="fv"><span class="rb rb-{r}" aria-hidden="true">{r}</span><span><b>Official health rating: {r} ({RATING_MEANING[r]})</b>'
                   f'<small>Farmington Valley Health District, rated {nice_date(p.fv["d"])}</small></span></p>')
    if p.site:
        host = re.sub(r"^https?://(www\.)?", "", p.site).split("/")[0]
        out.append(f'<p class="link"><a href="{e(p.site)}" rel="noopener nofollow">{e(host)}</a></p>')
    out.append("</li>")
    return "".join(out)


def restaurant_ld(p, url):
    """The place as it appears on the page at `url`: its url is the place's own #p- anchor there, and its own website is sameAs."""
    a = {"@type": "PostalAddress", "streetAddress": p.addr, "addressLocality": p.village or p.city, "addressRegion": "CT",
         "postalCode": p.zip, "addressCountry": "US"}
    x = {"@type": "Restaurant", "name": p.name, "url": f"{url}#p-{p.id}", "address": {k: v for k, v in a.items() if v}}
    if p.lat is not None and p.lon is not None:
        x["geo"] = {"@type": "GeoCoordinates", "latitude": round(p.lat, 5), "longitude": round(p.lon, 5)}
    if p.phone:
        x["telephone"] = p.phone
    if p.site:
        x["sameAs"] = p.site
    if p.cuisine and p.cuisine != "American & Other":
        x["servesCuisine"] = p.cuisine
    return x


def item_list(name, places, url):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name, "url": url, "numberOfItems": len(places),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{url}#p-{p.id}", "item": restaurant_ld(p, url)}
                                for i, p in enumerate(places)]}


def article_ld(url, headline, desc):
    path = url[len(DOMAIN) + 1:]
    return {"@context": "https://schema.org", "@type": "Article", "headline": headline, "description": desc,
            "datePublished": FIRST_PUBLISHED[path], "dateModified": TODAY, "inLanguage": "en", "mainEntityOfPage": url,
            "image": f"{DOMAIN}/og.png", "author": {"@type": "Organization", "name": BRAND, "url": DOMAIN + "/"},
            "publisher": {"@type": "Organization", "name": BRAND, "url": DOMAIN + "/", "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/icon-512.png"}}}


def fit(options, lo, hi):
    for o in options:
        if lo <= len(o) <= hi:
            return o
    raise ValueError(f"nothing fits {lo}-{hi}: {[(len(o), o) for o in options]}")


def by_region(places):
    groups = defaultdict(list)
    for p in places:
        groups[p.region].append(p)
    assert None not in groups, [p.name for p in groups[None]]
    return [(r, sorted(groups[r], key=lambda p: (p.city, p.name.lower()))) for r in REGION_ORDER if groups.get(r)]


def region_sections(places, noun, nouns=None):
    regions = by_region(places)
    toc = '<ul class="toc">' + "".join(f'<li><a href="#{slug(r)}">{e(REGION_NAME[r])}</a> ({len(ps)})</li>' for r, ps in regions) + "</ul>"
    secs = []
    for r, ps in regions:
        secs.append(f'<section id="{slug(r)}" aria-labelledby="h-{slug(r)}"><h2 id="h-{slug(r)}">{e(REGION_NAME[r])}</h2>'
                    f'<p class="sub">{plural(len(ps), noun, nouns)}, by town. The planning region around {e(and_list(REGION_HINT[r]))}.</p><ol class="places">'
                    + "".join(place_item(p) for p in ps) + "</ol></section>")
    return toc, "\n".join(secs)


def year_line(ps, n):
    """The n longest at the same address among ps (all on this page, so each name links to its entry)."""
    return "; ".join(f'<a href="#p-{p.id}">{e(p.name)}</a> in {e(p.place_name)}, there since {p.founded}'
                     for p in sorted([p for p in ps if p.founded], key=lambda p: (p.founded, p.name))[:n])


def oldest_link():
    return f'See <a href="/{OLDEST_PAGE[0]}">Connecticut\'s oldest restaurants</a> for all {len(OLDEST)} with a year at the same address.'


TOWN_PAGES = ["New Haven", "Hartford", "Stamford", "Bridgeport", "Norwalk", "Waterbury", "Danbury", "New Britain", "Groton", "Stonington",
              "Middletown", "West Hartford", "Fairfield", "Milford", "Greenwich", "Manchester", "Meriden", "New London",
              "Farmington", "Simsbury"]
assert all(t in TOWN_COUNT for t in TOWN_PAGES)
# datePublished: when each page first went out (dateModified and the sitemap's lastmod follow TODAY). New pages go here.
FIRST_PUBLISHED = {**dict.fromkeys(["index.html", "new-haven-apizza.html", "connecticut-lobster-rolls.html", "connecticut-hot-dogs-burgers.html",
                                    "connecticut-diners-dairy-bars.html", "explore/index.html", "privacy.html", "terms.html"]
                                   + [f"towns/{slug(t)}.html" for t in TOWN_PAGES], "2026-10-05"),
                   OLDEST_PAGE[0]: "2026-10-07"}


def town_url(t):
    return f"/towns/{slug(t)}.html"


def town_links():
    return '<ul class="towns">' + "".join(f'<li><a href="{town_url(t)}">{e(t)}</a></li>' for t in TOWN_PAGES) + "</ul>"


def town_line():
    links = ", ".join(f'<a href="{town_url(t)}">{e(t)}</a>' for t in TOWN_PAGES)
    return f'<p class="fine">Town pages: {links}.</p>'


def regions_line():
    return f"grouped by Connecticut's {len(REGIONS)} planning regions (the state has no county governments)"


def how_checked(order="the order is by region and town"):
    return (f"Every place was checked in business in {CHECKED} against a 2025 or 2026 source: its own website or menu, a dated post, "
            "local news, or a tourism listing, with the address checked too. Seasonal places list their season, so check it before you "
            f"drive. Places with no current source were left out. Nothing here comes from review sites, and {order}, never by anyone's "
            "rating. Hours and menus change, so check before you go.")


HOW_CHECKED = how_checked()
written = []

# ---------------------------------------------------------------- guide: New Haven apizza
url = f"{DOMAIN}/new-haven-apizza.html"
n = len(APIZZA)
in_nh = sum(1 for p in APIZZA if p.city == "New Haven")
branches = [p for p in APIZZA if p.branch]
title = fit([f"New Haven Apizza Guide: {n} Hand-Checked Pizzerias | {SHORT}", f"New Haven Apizza: {n} Checked Pizzerias | {BRAND}",
             f"New Haven Apizza Guide: {n} Pizzerias | {BRAND}"], 50, 60)
desc = fit([f"{n} New Haven-style apizza pizzerias in Connecticut, each {checked_open(APIZZA)}, from Wooster Street to the shore, by region and town. Free, no ratings.",
            f"{n} New Haven-style apizza pizzerias across Connecticut, {checked_open(APIZZA)} and listed by region and town. Free, no ads, no ratings."], 140, 160)
toc, secs = region_sections(APIZZA, "pizzeria")
nav, bc = crumbs([("Home", "/"), ("New Haven apizza guide", "/new-haven-apizza.html")])
h1 = "New Haven apizza guide"
body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} guide · checked {CHECKED}</p>
    <h1>{h1}</h1>
    <p class="lede">{n} pizzerias that bake New Haven-style apizza, from the Wooster Street originals to their branches around the state, each {checked_open(APIZZA)} on its own website, menu, or recent local news.</p>
    <div class="cta-row">{store_button()}<a class="btn btn-ghost" href="/explore/#g=apizza&amp;view=map">See them on a map</a></div>
    <p class="pill">{store_note()}</p>
  </section>
  <section id="about-apizza">
    <h2>What makes it apizza</h2>
    <p>Apizza (say "ah-BEETS") is New Haven's pizza: thin, chewy, and charred at the edges, baked in a very hot brick oven and served on a sheet pan, often cut into uneven pieces. A plain tomato pie comes with grated cheese and no mozzarella unless you ask for it ("mootz"), and the white clam pie is the one people drive for.</p>
    <h2>The {n} on this list</h2>
    <p>{in_nh} are in New Haven itself and {len(branches)} are branches of an older pizzeria, listed with the original they come from. The longest at the same address: {year_line(APIZZA, 4)}. {oldest_link()} {NAMED_APIZZA} other places have "apizza" in their name; they're in the app's full directory, but not on this list until we check them.</p>
    <p>How the list was built: {HOW_CHECKED}</p>
    <p>In the {BRAND} app, the same list sorts by distance from you, and each place opens Apple Maps' own card for live hours, photos, and directions. For the shore, see the <a href="/connecticut-lobster-rolls.html">lobster roll and clam shack guide</a>.</p>
    <h2>Jump to a region</h2>
    <p class="sub">The list is {regions_line()}.</p>
    {toc}
    {town_line()}
  </section>
{secs}
  </main>"""
written.append(page("new-haven-apizza.html", title, desc, body,
                    [article_ld(url, h1, desc), bc, item_list("New Haven apizza in Connecticut", APIZZA, url)]))

# ---------------------------------------------------------------- guide: lobster rolls and clam shacks
url = f"{DOMAIN}/connecticut-lobster-rolls.html"
n = len(LOBSTER)
n_roll = sum(1 for p in LOBSTER if p.kinds & KIND["lobster roll"])
n_shack = sum(1 for p in LOBSTER if p.kinds & KIND["clam shack"])
seas = [p for p in LOBSTER if p.seasonal]
seas_known = [p for p in seas if p.season]
title = fit([f"Connecticut Lobster Rolls & Clam Shacks: {n} Checked Places", f"Connecticut Lobster Rolls & Clam Shacks: {n} Places",
             f"CT Lobster Rolls & Clam Shacks: {n} Places | {BRAND}"], 50, 60)
desc = fit([f"{n} Connecticut lobster roll and clam shack stops, each {checked_open(LOBSTER)}, by region and town, with the season for the shacks.",
            f"{n} Connecticut lobster roll and clam shack stops, {checked_open(LOBSTER)}, by region and town, with each shack's season. Free.",
            f"{n} places for a hot buttered lobster roll or fried clams in Connecticut, {checked_open(LOBSTER)}, by region and town. Free."], 140, 160)
toc, secs = region_sections(LOBSTER, "place")
nav, bc = crumbs([("Home", "/"), ("Lobster rolls & clam shacks", "/connecticut-lobster-rolls.html")])
h1 = "Connecticut lobster rolls &amp; clam shacks"
body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} guide · checked {CHECKED}</p>
    <h1>{h1}</h1>
    <p class="lede">{n} places along the shore and inland for a hot buttered lobster roll, fried clams, or both, each {checked_open(LOBSTER)}. {len(seas)} of them are seasonal, so check the season listed with each before you drive.</p>
    <div class="cta-row">{store_button()}<a class="btn btn-ghost" href="/explore/#g=lobster&amp;view=map">See them on a map</a></div>
    <p class="pill">{store_note()}</p>
  </section>
  <section id="about-lobster">
    <h2>Hot, with butter</h2>
    <p>A Connecticut lobster roll is served warm: the meat is tossed in melted butter and piled into a toasted roll. The cold kind, dressed with mayonnaise, is the Maine style, and many places here serve both. Clam shacks add fried clams, clam strips, and chowder, and many of them close for the winter.</p>
    <h2>The {n} on this list</h2>
    <p>{n_roll} serve a lobster roll and {n_shack} are clam shacks, many both. {len(seas)} are seasonal; {len(seas_known)} post their season, which is listed with each place. The longest at the same address: {year_line(LOBSTER, 4)}. {oldest_link()}</p>
    <p>How the list was built: {HOW_CHECKED}</p>
    <p>In the {BRAND} app, the list sorts by distance from you, and each place opens Apple Maps' own card with live hours. Inland? See the <a href="/connecticut-hot-dogs-burgers.html">hot dog and burger icons</a> and the <a href="/connecticut-diners-dairy-bars.html">dairy bars</a>.</p>
    <h2>Jump to a region</h2>
    <p class="sub">The list is {regions_line()}.</p>
    {toc}
    {town_line()}
  </section>
{secs}
  </main>"""
written.append(page("connecticut-lobster-rolls.html", title, desc, body,
                    [article_ld(url, html.unescape(h1), desc), bc, item_list("Connecticut lobster rolls and clam shacks", LOBSTER, url)]))

# ---------------------------------------------------------------- guide: burger and hot dog icons
url = f"{DOMAIN}/connecticut-hot-dogs-burgers.html"
n = len(BURGERS)
n_steam = sum(1 for p in BURGERS if p.kinds & KIND["steamed cheeseburger"])
n_dog = sum(1 for p in BURGERS if p.kinds & KIND["hot dog icon"])
n_burg = sum(1 for p in BURGERS if p.kinds & (KIND["burger icon"] | KIND["steamed cheeseburger"]))
steam_towns = sorted({p.city for p in BURGERS if p.kinds & KIND["steamed cheeseburger"]})
title = fit([f"Connecticut Hot Dog & Burger Icons: {n} Checked Places", f"Connecticut Hot Dogs & Burgers: {n} Icons | {BRAND}"], 50, 60)
desc = fit([f"{n} Connecticut hot dog stands and burger icons, steamed cheeseburgers included, each {checked_open(BURGERS)}, by region and town. Free.",
            f"{n} Connecticut hot dog and burger icons, from steamed cheeseburgers to roadside stands, {checked_open(BURGERS)}, by region and town.",
            f"{n} Connecticut hot dog and burger icons, steamed cheeseburgers included, {checked_open(BURGERS)}, by region and town. Free."], 140, 160)
toc, secs = region_sections(BURGERS, "place")
nav, bc = crumbs([("Home", "/"), ("Hot dog & burger icons", "/connecticut-hot-dogs-burgers.html")])
h1 = "Connecticut hot dog &amp; burger icons"
body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} guide · checked {CHECKED}</p>
    <h1>{h1}</h1>
    <p class="lede">{n} hot dog stands, steamed cheeseburger counters, and burger institutions around the state, each {checked_open(BURGERS)} on its own website, menu, or recent local news.</p>
    <div class="cta-row">{store_button()}<a class="btn btn-ghost" href="/explore/#g=burgers&amp;view=map">See them on a map</a></div>
    <p class="pill">{store_note()}</p>
  </section>
  <section id="about-burgers">
    <h2>Steamed, stood at, driven to</h2>
    <p>The steamed cheeseburger belongs to central Connecticut: the burger and a block of cheddar are steamed in small metal trays, and the melted cheese is poured over the top. Hot dog stands and drive-ins with a long history fill out the rest of this list.</p>
    <h2>The {n} on this list</h2>
    <p>{n_dog} are hot dog places and {n_burg} are burger places, {n_steam} of them serving steamed cheeseburgers (in {e(and_list(steam_towns))}). The longest at the same address: {year_line(BURGERS, 4)}. {oldest_link()}</p>
    <p>How the list was built: {HOW_CHECKED}</p>
    <p>In the {BRAND} app, the list sorts by distance from you. For dessert after, see the <a href="/connecticut-diners-dairy-bars.html">dairy bars and diners</a>.</p>
    <h2>Jump to a region</h2>
    <p class="sub">The list is {regions_line()}.</p>
    {toc}
    {town_line()}
  </section>
{secs}
  </main>"""
written.append(page("connecticut-hot-dogs-burgers.html", title, desc, body,
                    [article_ld(url, html.unescape(h1), desc), bc, item_list("Connecticut hot dog and burger icons", BURGERS, url)]))

# ---------------------------------------------------------------- guide: diners and dairy bars
url = f"{DOMAIN}/connecticut-diners-dairy-bars.html"
n = len(DINERS_DAIRY)
dairy_seas = sum(1 for p in DAIRY if p.seasonal)
title = fit([f"Connecticut Diners & Dairy Bars: {n} Checked Places | {SHORT}", f"Connecticut Diners & Dairy Bars: {n} Checked Places"], 50, 60)
desc = fit([f"{len(DINERS)} Connecticut diners and {len(DAIRY)} dairy bars and farm creameries, each {checked_open(DINERS_DAIRY)}, listed by region and town. Free, no ratings.",
            f"{len(DINERS)} Connecticut diners and {len(DAIRY)} dairy bars and farm creameries, each {checked_open(DINERS_DAIRY)}, by region and town. Free, no ratings.",
            f"{len(DINERS)} diners and {len(DAIRY)} dairy bars and creameries in Connecticut, {checked_open(DINERS_DAIRY)}, by region and town. Free."], 140, 160)
toc, secs = region_sections(DINERS_DAIRY, "place")
nav, bc = crumbs([("Home", "/"), ("Diners & dairy bars", "/connecticut-diners-dairy-bars.html")])
h1 = "Connecticut diners &amp; dairy bars"
body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} guide · checked {CHECKED}</p>
    <h1>{h1}</h1>
    <p class="lede">{len(DINERS)} long-running diners and {len(DAIRY)} dairy bars, farm creameries, and ice cream stands, each {checked_open(DINERS_DAIRY)} on its own website, menu, or recent local news.</p>
    <div class="cta-row">{store_button()}<a class="btn btn-ghost" href="/explore/#g=dairy&amp;view=map">See the dairy bars on a map</a></div>
    <p class="pill">{store_note()}</p>
  </section>
  <section id="about-diners">
    <h2>Breakfast, then a cone</h2>
    <p>Diners on this list are the counter-and-booth kind, open for breakfast and lunch and often longer. Dairy bars range from farm stands that make ice cream from their own cows' milk to roadside walk-up windows. {dairy_seas} of the {len(DAIRY)} dairy bars are seasonal, so check the season listed with each.</p>
    <p>{NAMED_DINER} other places have "Diner" in their name. They're in the app's full directory, but they're not on this list until we check them. The longest at the same address here: {year_line(DINERS_DAIRY, 4)}. {oldest_link()}</p>
    <p>How the list was built: {HOW_CHECKED}</p>
    <p>In the {BRAND} app, diners and dairy bars are separate lists that sort by distance from you. Hungry first? See the <a href="/connecticut-hot-dogs-burgers.html">hot dog and burger icons</a>.</p>
    <h2>Jump to a region</h2>
    <p class="sub">The list is {regions_line()}.</p>
    {toc}
    {town_line()}
  </section>
{secs}
  </main>"""
written.append(page("connecticut-diners-dairy-bars.html", title, desc, body,
                    [article_ld(url, html.unescape(h1), desc), bc, item_list("Connecticut diners and dairy bars", DINERS_DAIRY, url)]))

# ---------------------------------------------------------------- Connecticut's oldest restaurants (years at the same address)
url = f"{DOMAIN}/{OLDEST_PAGE[0]}"
n = len(OLDEST)
first = OLDEST[0]
ERAS = [("before-1900", "Before 1900", 0, 1900), ("1900-1949", "1900 to 1949", 1900, 1950), ("1950-1979", "1950 to 1979", 1950, 1980),
        ("since-1980", "1980 and later", 1980, 10000)]
eras = [(i, label, [p for p in OLDEST if lo <= p.founded < hi]) for i, label, lo, hi in ERAS]
eras = [x for x in eras if x[2]]
title = fit([f"Connecticut's Oldest Restaurants: {n} at the Same Address", f"Connecticut's Oldest Restaurants: {n} Places | {SHORT}",
             f"Oldest Restaurants in Connecticut: {n} Places | {BRAND}"], 50, 60)
desc = fit([f"{n} Connecticut restaurants with a checked year at the same address, oldest first, with the year and town for each. Since {first.founded}. Free, no ratings.",
            f"{n} Connecticut restaurants with a checked year at the same address, oldest first, with the year and town for each. Free, no ads, no ratings.",
            f"{n} Connecticut restaurants with a checked year at the same address, listed oldest first with the year and town for each. Free, no ratings."], 140, 160)
nav, bc = crumbs([("Home", "/"), ("Oldest restaurants", "/" + OLDEST_PAGE[0])])
h1 = "Connecticut's oldest restaurants"
toc = '<ul class="toc">' + "".join(f'<li><a href="#{i}">{e(label)}</a> ({len(ps)})</li>' for i, label, ps in eras) + "</ul>"
secs = "\n".join(f'<section id="{i}" aria-labelledby="h-{i}"><h2 id="h-{i}">{e(label)}</h2><p class="sub">{plural(len(ps), "place")}, oldest first.</p>'
                 f'<ol class="places">' + "".join(place_item(p) for p in ps) + "</ol></section>" for i, label, ps in eras)
body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} · years at the same address, checked {CHECKED}</p>
    <h1>{e(h1)}</h1>
    <p class="lede">The {n} places on our hand-checked lists with a known year at their current address, oldest first. {e(first.name)} in {e(first.place_name)} has been at its address since {first.founded}.</p>
    <div class="cta-row">{store_button()}<a class="btn btn-ghost" href="/explore/#g=oldest&amp;view=map">See them on a map</a></div>
    <p class="pill">{store_note()}</p>
  </section>
  <section id="about-oldest">
    <h2>How the years were checked</h2>
    <p>Each year is when the place opened at the address where it is now, checked against the restaurant's own history page or local news. A business that moved counts from its move, so an older name can sit lower on this list. A year is a fact about the address, not a rating, and the list only covers places we checked by hand; the rest of the app's {N_REST:,} restaurants have no checked year.</p>
    <p>How the list was built: {how_checked("the order is by years at the same address")}</p>
    <p>In the {BRAND} app and the <a href="/explore/#g=oldest">web search</a>, the Oldest Places guide has the same list. For more on what these places serve, see the <a href="/new-haven-apizza.html">apizza</a>, <a href="/connecticut-lobster-rolls.html">lobster roll</a>, <a href="/connecticut-hot-dogs-burgers.html">hot dog and burger</a>, and <a href="/connecticut-diners-dairy-bars.html">diner and dairy bar</a> guides.</p>
    <h2>Jump to an era</h2>
    {toc}
    {town_line()}
  </section>
{secs}
  </main>"""
written.append(page(OLDEST_PAGE[0], title, desc, body,
                    [article_ld(url, h1, desc), bc, item_list("Connecticut's oldest restaurants, by years at the same address", OLDEST, url)]))

# ---------------------------------------------------------------- town pages
town_stats = {}
# key, heading, plural noun, the guide's places, "in and near" radius in miles
SECTIONS = [("apizza", "Apizza", "apizza places", APIZZA, 10), ("lobster", "Lobster rolls and clam shacks", "lobster roll and clam shack stops", LOBSTER, 15),
            ("burgers", "Hot dog and burger icons", "hot dog and burger icons", BURGERS, 10), ("diners", "Diners and dairy bars", "diners and dairy bars", DINERS_DAIRY, 10)]
NEAR_N = 5   # the nearest few outside the town; the guide has the rest
GUIDE_URL = {"apizza": "/new-haven-apizza.html", "lobster": "/connecticut-lobster-rolls.html", "burgers": "/connecticut-hot-dogs-burgers.html",
             "diners": "/connecticut-diners-dairy-bars.html"}
GUIDE_N = {"apizza": len(APIZZA), "lobster": len(LOBSTER), "burgers": len(BURGERS), "diners": len(DINERS_DAIRY)}
FAR_LABEL = {"apizza": "apizza", "lobster": "lobster rolls", "burgers": "hot dogs", "diners": "diners"}
# directory places in the town named like a classic that we haven't checked: (name tag, how the name reads, the web search query)
NAMED = {"apizza": [("apizza", "“Apizza”", "apizza")], "lobster": [("clams", "“Clam Shack”", "clam shack")],
         "diners": [("diner", "“Diner”", "diner"), ("dairy", "“Dairy Bar” or “Creamery”", "dairy bar")]}
village_towns = defaultdict(set)
for p in REST:
    if p.village:
        village_towns[p.village].add(p.city)
for t in TOWN_PAGES:
    here_all = [p for p in REST if p.city == t]
    here = [p for p in here_all if p.lat is not None]
    n_town = TOWN_COUNT[t]
    center = (sorted(p.lat for p in here)[len(here) // 2], sorted(p.lon for p in here)[len(here) // 2])

    # per guide: the town's own places, the others within the radius (closest first), and when there are neither, the 3
    # nearest within 30 miles, flagged so the page calls them "the nearest" and says none of ours is closer
    ins, within, shown, nearest_only = {}, {}, {}, {}
    for k, _, _, lst, rad in SECTIONS:
        ins[k] = [p for p in lst if p.city == t]
        outs = sorted([(miles(center, (p.lat, p.lon)), p) for p in lst if p.city != t and p.lat is not None], key=lambda x: (x[0], x[1].name.lower()))
        within[k] = [x for x in outs if x[0] <= rad]
        nearest_only[k] = not ins[k] and not within[k]
        shown[k] = [x for x in outs if x[0] <= 30][:3] if nearest_only[k] else within[k][:NEAR_N]
    full = {k: ins[k] + [p for _, p in (shown[k] if nearest_only[k] else within[k])] for k in ins}   # what each count describes
    counts = {k: len(v) for k, v in full.items()}
    close = {k: counts[k] if not nearest_only[k] else 0 for k in counts}   # what's actually in or near the town
    vill = Counter(p.village for p in here_all if p.village)
    villages = [v for v, c in vill.most_common() if c >= 3]
    split = [v for v in villages if len(village_towns[v]) > 1 and sum(1 for p in REST if p.village == v) >= 6]
    icons = sorted([p for p in here_all if p.hc], key=P.featured_key)
    oldest = sorted([p for p in icons if p.founded], key=lambda p: (p.founded, p.name.lower()))
    cuis = Counter(p.cuisine for p in here_all if p.cuisine != "American & Other").most_common(10)
    casino = [p for p in here_all if p.host]
    rated = sorted([p for p in here_all if p.fv], key=lambda p: p.name.lower()) if t in FV_TOWNS else []
    town_stats[t] = {"restaurants": n_town, **{k + "_near": c for k, c in counts.items()}, "hand_checked_in_town": len(icons),
                     "fvhd_rated": len(rated)}

    fvt = t in FV_TOWNS
    path = f"towns/{slug(t)}.html"
    url = DOMAIN + "/" + path

    def word(k):
        """What a section mostly is, for titles: "Hot Dogs" or "Burgers", "Diners" or "Dairy Bars"."""
        ps = full[k]
        has = lambda kind: sum(1 for p in ps if p.kinds & KIND[kind])
        if k == "apizza":
            return "Apizza"
        if k == "lobster":
            return "Lobster Rolls" if has("lobster roll") * 2 >= len(ps) else "Clam Shacks"
        if k == "burgers":
            return "Hot Dogs" if has("hot dog icon") * 2 >= len(ps) else "Burgers"
        return "Diners" if has("diner") * 2 >= len(ps) else "Dairy Bars"

    words = [word(k) for k in ("apizza", "lobster", "burgers", "diners") if close[k]]
    h1 = f"{t} restaurants: {' & '.join(w.lower() for w in words[:2]) if words else 'the classics nearby'}"
    w2, w3 = " & ".join(words[:2]), (", ".join(words[:2]) + " & " + words[2]) if len(words) >= 3 else " & ".join(words[:2])
    title = fit([f"{t} Restaurants: {w3} | {SHORT}", f"{t} Restaurants: {w3}", f"{t}, CT Restaurants: {w2} | {SHORT}",
                 f"{t}, CT Restaurants: {w2} and Classics Nearby", f"{t}, Connecticut Restaurants: {w2} & More",
                 f"{t} Restaurants: {w2} | {BRAND}", f"{t}, CT Restaurants: {w3}", f"{t} Restaurants: {w2} and More | {SHORT}",
                 f"{t}, Connecticut Restaurants: {w2} and More"], 50, 60)
    lw = [w.lower() for w in words] or ["hand-checked classics"]
    lwl = and_list(lw)
    L = lwl[0].upper() + lwl[1:]
    on_page = icons + [p for k in shown for _, p in shown[k]]
    cw = checked_open([p for k in full for p in full[k]] or on_page)
    # promise only the sections this page has
    extra_long = and_list((["the town's hand-checked icons"] if icons else []) + (["its oldest restaurants"] if oldest else [])
                          or [f"{n_town:,} restaurants in the free app"])
    extra_short = and_list((["local icons"] if icons else []) + (["the oldest places in town"] if oldest else []) or [f"{n_town:,} places in the app"])
    desc = fit([f"{L} in and near {t}, CT, {cw}, plus {extra_long}. Free, no ads, no ratings.",
                f"{L} in and near {t}, CT, {cw}, plus {extra_long}. Free, no ratings.",
                f"{L} in and near {t}, Connecticut, {cw}, plus {extra_long}.",
                f"{L} in and near {t}, CT, {cw}, plus {extra_short}. Free, no ratings.",
                f"{L} in and near {t}, CT, {cw}, plus {extra_short}.",
                f"{L} near {t}, CT, {cw}, plus {extra_short}.",
                f"Hand-checked {lwl} in and near {t}, Connecticut, each {cw}, plus {extra_long}, in a free app.",
                f"Hand-checked {lwl} in and near {t}, Connecticut, each {cw}, plus {extra_short} and the nearest classics.",
                f"Hand-checked {lwl} in and near {t}, CT, {cw}, plus {extra_short}.",
                f"Hand-checked {lwl} near {t}, CT, {cw}, plus {extra_short}."], 140, 160)
    nav, bc = crumbs([("Home", "/"), ("Towns", "/#towns"), (t, "/" + path)])
    lead_bits = [plural(counts["apizza"], "apizza place"), plural(counts["lobster"], "lobster roll and clam shack stop"),
                 plural(counts["burgers"], "hot dog and burger icon"), plural(counts["diners"], "diner and dairy bar", "diners and dairy bars")]
    lead_bits = [b for b, k in zip(lead_bits, ("apizza", "lobster", "burgers", "diners")) if close[k]]
    far_labels = [FAR_LABEL[k] for k, *_ in SECTIONS if counts[k] and nearest_only[k]]
    lede = (f"{e(and_list(lead_bits))} in and around {e(t)}, each {cw}." if lead_bits else "")
    lede += f" For hand-checked {e(and_list(far_labels))}, the nearest are a drive away; they're below too." if far_labels else ""
    lede += f" The {BRAND} app's directory has {n_town:,} restaurants, cafés, bars, and bakeries in {e(t)} and sorts them by distance from you."
    parts = [f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} · {e(t)}, Connecticut{f" · including {e(and_list(villages))}" if villages else ""}</p>
    <h1>{e(h1)}</h1>
    <p class="lede">{lede.strip()}</p>
    <div class="cta-row">{store_button()}<a class="btn btn-ghost" href="{e(explore_url(g="all", town=t))}">Search {e(t)}</a></div>
    <p class="pill">{store_note()}</p>"""]
    if villages:
        vtxt = f"{e(and_list(villages))} {'is a village' if len(villages) == 1 else 'are villages'} in the town of {e(t)}, so places there are listed under {e(t)}."
        for v in split:
            others = [f'<a href="{town_url(o)}">{e(o)}</a>' if o in TOWN_PAGES else e(o) for o in sorted(village_towns[v] - {t})]
            vtxt += f" {e(v)} also reaches into {and_list(others)}, which has its own places with a {e(v)} address."
        parts.append(f'    <p class="fine">{vtxt}</p>')
    parts.append("  </section>")

    # a short, data-driven picture of the town, so each page says something only it can say
    facts = []
    top = cuis[:3]
    vbits = [f"{c:,} in {e(v)}" for v, c in vill.most_common(3) if c >= 3]
    facts.append(f"The app's directory has {n_town:,} places to eat and drink in {e(t)}" + (f", including {and_list(vbits)}" if vbits else "")
                 + (f". The most common kinds are {and_list(f'{e(k)} ({c:,})' for k, c in top)}." if top else "."))
    n_lic = sum(1 for p in here_all if p.r.get("t") == 2)
    if n_lic:
        facts.append(f"{n_lic:,} {'is' if n_lic == 1 else 'are'} matched to {'a state liquor permit or a Hartford food license' if t == 'Hartford' else 'a state liquor permit'}.")
    n_chain = sum(1 for p in here_all if p.chain)
    if n_chain:
        facts.append(f"{plural(n_chain, 'is a location', 'are locations')} of a chain with five or more in Connecticut.")
    if icons:
        n_jb = sum(1 for p in icons if p.h)
        old = f'<a href="#p-{oldest[0].id}">{e(oldest[0].name)}</a>, there since {oldest[0].founded}' if oldest else ""
        facts.append(("One is" if len(icons) == 1 else f"{len(icons)} are") + " on our hand-checked lists"
                     + (f", {n_jb} of them with James Beard honors" if n_jb else "") + (f"; the longest at the same address is {old}." if old else "."))
    else:
        facts.append(f"None of our {len(HC)} hand-checked places is in {e(t)} yet, so the classics below are the nearest ones.")
    if casino:
        hosts = sorted({p.host for p in casino})
        facts.append(f"{len(casino)} of them are inside {e(and_list(hosts))}, on tribal land; the app labels each one.")
    if fvt:
        facts.append(f"{e(t)} is in the Farmington Valley Health District, which posts official ratings; we matched {len(rated)} places here to one (more below).")
    parts.append(f'<section id="about-town"><h2>{e(t)} at a glance</h2><p>{" ".join(facts)}</p></section>')

    rendered = set()

    def mi(d, rad):
        """Whole miles, or tenths where rounding would put a place we call farther than the radius right at it (10.4, not 10)."""
        return f"{d:.1f}" if d > rad and math.floor(d) <= rad else f"{d:.0f}"

    def items(lst, rad):
        out = []
        for d, p in lst:
            if p.id in rendered:   # already on this page: point at it instead of repeating it
                out.append(f'<li class="again"><h3><a href="#p-{p.id}">{e(p.name)}</a></h3><p class="where">{place_where(p, t)} · {mi(d, rad)} mi from {e(t)}; listed above</p></li>')
                continue
            rendered.add(p.id)
            out.append(place_item(p, extra=f"{mi(d, rad)} mi from {t}", show_fv=fvt, here_town=t))
        return "".join(out)

    if icons:
        rendered.update(p.id for p in icons)
        old_txt = f" Longest at the same address: {year_line(oldest, 3)}. {oldest_link()}" if oldest else ""
        parts.append(f'<section id="icons"><h2>On our lists in {e(t)}</h2><p class="sub">Every place in {e(t)} on our hand-checked lists, including James Beard honorees and long-running local institutions, most honored first. Points come from honors and years at the address; not a rating. Honors are facts from the James Beard Foundation\'s own award records and other named sources.{old_txt}</p><ol class="places">'
                     + "".join(place_item(p, show_fv=fvt, here_town=t) for p in icons) + "</ol></section>")
    for k, label, noun, _, rad in SECTIONS:
        named = []
        for tag, how, q in NAMED.get(k, []):
            c = NAMED_IN_TOWN[tag][t]
            if c:
                named.append(f'The app\'s directory also has {plural(c, "place")} in {e(t)} with {how} in the name that we haven\'t checked yet: '
                             f'<a href="{e(explore_url(g="all", town=t, q=q))}">see {"it" if c == 1 else "them"} in the web search</a>.')
        if k == "burgers":
            c = sum(1 for p in here_all if p.cuisine == "Hot Dogs" and not p.hc)
            if c:
                named.append(f'The app\'s directory also files {plural(c, "place")} in {e(t)} as {"a hot dog place" if c == 1 else "hot dog places"} that we haven\'t checked yet: '
                             f'<a href="{e(explore_url(g="all", town=t, kind="Hot Dogs"))}">see {"it" if c == 1 else "them"} in the web search</a>.')
        named = " ".join(named)
        guide_link = f'<a href="{GUIDE_URL[k]}">All {GUIDE_N[k]} in Connecticut</a>.'
        if nearest_only[k]:
            if not shown[k]:
                if named:
                    parts.append(f'<section id="{k}"><h2>{label} in {e(t)}</h2><p class="sub">None of our {GUIDE_N[k]} hand-checked {noun} is in {e(t)} or within 30 miles. {guide_link} {named}</p></section>')
                continue
            lo, hi = mi(shown[k][0][0], rad), math.ceil(shown[k][-1][0])
            parts.append(f'<section id="{k}"><h2>The nearest {label.lower()} to {e(t)}</h2><p class="sub">None of our {GUIDE_N[k]} hand-checked {noun} is in {e(t)} or within {rad} miles. '
                         f'The closest are {lo} to {hi} miles away. {guide_link} {named}</p><ol class="places">{items(shown[k], rad)}</ol></section>')
            continue
        bits = []
        if ins[k]:
            links = and_list(f'<a href="#p-{p.id}">{e(p.name)}</a>' for p in ins[k])
            bits.append(f"In {e(t)}: {links}, listed above.")
        if not within[k]:
            bits.append(f"None of our other {noun} is within {rad} miles.")
        elif len(within[k]) > NEAR_N:
            bits.append(f"The {NEAR_N} nearest of the {len(within[k])} others within {rad} miles, closest first.")
        else:
            bits.append(f"{'The others' if ins[k] else 'Those'} within {rad} miles, closest first.")
        parts.append(f'<section id="{k}"><h2>{label} in and near {e(t)}</h2><p class="sub">{" ".join(bits)} {guide_link} {named}</p>'
                     + (f'<ol class="places">{items(shown[k], rad)}</ol>' if shown[k] else "") + "</section>")
    if rated:
        n_shown = sum(1 for p in rated if p.id in rendered)
        shown_txt = (f"{plural(n_shown, 'place')} on this page {'has' if n_shown == 1 else 'have'} one, shown with the place, labeled official and dated; a rating describes one inspection on that day."
                     if n_shown else "We matched none of the hand-checked places on this page to the district's list.")
        # the official rating shows inside each place's entry above (and in the web app's place panel), never as a list of ratings
        parts.append(f'<section id="health-ratings"><h2>Health ratings in {e(t)}</h2><p class="sub">{e(t)} is one of the {N_FV} towns of the Farmington Valley Health District, which rates restaurants A (Excellent), B (Good), C (Fair), or U (Unsatisfactory) at each routine inspection and requires each one to post its rating. We matched {len(rated)} of the {n_town:,} places in {e(t)} to a published rating. {shown_txt} In the <a href="{e(explore_url(g="all", town=t))}">web search</a>, every place we matched shows its rating on its own page. We don\'t grade restaurants, and the rest of Connecticut has no statewide inspection results.</p><p class="fine">Source: Farmington Valley Health District food service ratings, fetched {nice_date(D["fvhd_fetched"])}.</p></section>')
    if cuis:
        pills = "".join(f'<li><a href="{e(explore_url(g="all", town=t, kind=k))}">{e(k)} ({c:,})</a></li>' for k, c in cuis)
        src = and_list(["open map data", "the state's liquor-permit list"] + (["Hartford's food licenses"] if t == "Hartford" else []))
        parts.append(f'<section id="cuisines"><h2>What {e(t)} eats</h2><p class="sub">The most common kinds of place among the {n_town:,} in {e(t)}, from {src}. Each opens the web search, filtered to {e(t)}.</p><ul class="towns">{pills}</ul></section>')
    parts.append(f'<section id="more"><h2>More Connecticut towns</h2>{town_links()}</section>\n  </main>')
    uniq = icons + [p for k in shown for _, p in shown[k] if p.id not in {x.id for x in icons}]
    uniq = list({p.id: p for p in uniq}.values())
    written.append(page(path, title, desc, "\n".join(parts),
                        [article_ld(url, h1, desc), bc, item_list(f"Hand-checked places in and near {t}", uniq, url)]))

# ---------------------------------------------------------------- web app (docs/explore/): data split + page
os.makedirs(f"{DOCS}/data", exist_ok=True)
CORE_KEYS = ["id", "n", "c", "vi", "cu", "t", "s", "a", "z", "la", "lo", "b", "ch", "v", "g", "hc", "k", "h", "ip", "fs", "f", "host", "seas", "j",
             "dish", "br"]   # br in core: "Hide chains" keeps a hand-checked original (hc, no br) and can drop its branches
DETAIL_KEYS = ["ph", "w", "note", "jbf", "hon", "sea", "chef", "lk", "hcl", "fv"]   # never the permit holder; the data has none
cols = {k: [] for k in CORE_KEYS}
detail = []
for p in PLACES:
    r = p.r
    for k in CORE_KEYS:
        v = r.get(k)
        if k == "vi" and v is not None and not (p.village == VILLAGES[v]):
            v = None   # not a real village (another town's name or a cut-off one)
        cols[k].append(round(v, 5) if k in ("la", "lo") and v is not None else v)
    d = {k: r[k] for k in DETAIL_KEYS if r.get(k)}
    # the same guards as the static pages: a phone only if it's a valid US number, a website only if it's http(s)
    for k, ok in (("ph", p.phone), ("w", p.site), ("jbf", p.jbf)):
        if ok:
            d[k] = ok
        else:
            d.pop(k, None)
    detail.append(d or None)
core = {"generated": D["generated"], "cities": CITIES, "villages": VILLAGES, "cuisines": CUISINES, "brands": D["brands"], "hosts": HOSTS,
        "sources": D["sources"], "regions": REGIONS, "town_region": D["town_region"], "tags": D["tags"], "kinds": D["kinds"],
        "calibration": D.get("calibration", {}), "fv_towns": FV_TOWNS, "cols": cols}
json.dump(core, open(f"{DOCS}/data/core.json", "w"), separators=(",", ":"), ensure_ascii=False)
json.dump(detail, open(f"{DOCS}/data/detail.json", "w"), separators=(",", ":"), ensure_ascii=False)
json.dump(SHAPES, open(f"{DOCS}/data/ct_shapes.json", "w"), separators=(",", ":"))
assert not private_words(open(f"{DOCS}/data/core.json").read() + open(f"{DOCS}/data/detail.json").read()), "a private address in the data"

EXPLORE_CSS = """
  [hidden] { display: none !important; }
  .ex-hero { padding: 28px 0 8px; }
  .ex-hero h1 { font-size: clamp(30px, 6vw, 44px); }
  .ex-controls { background: var(--bg); padding: 10px 0 8px; border-bottom: 1px solid var(--rule); }
  .ex-guides { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; scrollbar-width: none; }
  /* more guides off to the right: the row fades out at its edge until it's scrolled to the end */
  .ex-guides.more { -webkit-mask-image: linear-gradient(90deg, #000 calc(100% - 44px), transparent); mask-image: linear-gradient(90deg, #000 calc(100% - 44px), transparent); }
  @media (min-width: 601px) { .ex-guides { flex-wrap: wrap; overflow-x: visible; } }   /* room to show every guide, also beside the panel */
  .ex-guides button, .ex-view button, .ex-small { flex: 0 0 auto; border: 1px solid var(--rule2); background: var(--surface); color: var(--navy); border-radius: 999px; padding: 7px 12px; font-family: inherit; font-size: 14px; font-weight: 600; line-height: 1.2; cursor: pointer; }
  #ex-app :disabled { opacity: .55; cursor: default; }
  .ex-guides button[aria-pressed="true"], .ex-view button[aria-pressed="true"] { background: var(--navy); color: #fff; border-color: var(--navy); }
  .ex-row1 { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .ex-row1 input[type=search] { flex: 1 1 200px; min-width: 0; font-family: inherit; font-size: 16px; line-height: 1.3; padding: 10px 12px; border: 2px solid var(--navy); border-radius: 12px; background: var(--surface); color: var(--ink); }
  .ex-row2 { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 8px; font-size: 14px; color: var(--ink2); }
  .ex-row2 label { display: inline-flex; align-items: center; gap: 6px; }
  .ex-row2 select { font-family: inherit; font-size: 14px; padding: 6px 8px; border: 1px solid var(--rule2); border-radius: 8px; background: var(--surface); color: var(--ink); max-width: 46vw; }
  .ex-view { margin-left: auto; display: flex; gap: 4px; }
  #ex-count { margin: 8px 0 0; font-size: 14px; color: var(--muted); min-height: 1.55em; }
  #ex-sub { margin: 4px 0 0; font-size: 14px; color: var(--ink2); min-height: 1.55em; }
  /* the list's space is held from the first paint, so nothing below it jumps when the data arrives (CLS) */
  #ex-listwrap { min-height: 70vh; }
  #ex-locmsg { font-size: 13px; color: var(--muted); margin: 4px 0 0; }
  .ex-list { list-style: none; padding: 0; margin: 10px 0; }
  .ex-list li + li { border-top: 1px solid var(--rule); }
  .ex-row { width: 100%; display: flex; gap: 12px; align-items: center; text-align: left; background: none; border: 0; padding: 12px 4px; cursor: pointer; color: var(--ink); font: inherit; }
  .ex-row:hover { background: var(--surface2); }
  .ex-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; overflow-wrap: anywhere; }
  .ex-main b { font-weight: 650; }
  .ex-town { font-size: 14px; color: var(--muted); }
  .ex-metric { text-align: right; display: flex; flex-direction: column; }
  .ex-metric b { font: 800 22px/1 var(--display); color: var(--navy); }
  .ex-metric small { font-size: 11px; color: var(--muted); }
  .ex-rank { flex: 0 0 34px; height: 34px; display: grid; place-items: center; font: 800 20px var(--display); color: var(--navy); border-radius: 8px; }
  .ex-rank.top { background: var(--tomato); color: #fff; }
  .ex-empty { padding: 24px 4px; color: var(--muted); }
  #ex-more { display: block; margin: 8px auto 24px; }
  #ex-mapwrap { position: relative; height: min(68vh, 640px, calc(75vw + 60px)); margin: 10px 0 20px; border: 1px solid var(--rule); border-radius: 16px; overflow: hidden; background: #e6ecf3; }
  #ex-map { width: 100%; height: 100%; display: block; touch-action: none; cursor: grab; }
  .ex-zoom { position: absolute; right: 10px; top: 10px; display: flex; flex-direction: column; gap: 6px; }
  .ex-zoom button { width: 44px; height: 44px; border-radius: 10px; border: 1px solid var(--rule2); background: var(--surface); color: var(--navy); font-family: inherit; font-size: 20px; font-weight: 700; line-height: 1; cursor: pointer; }
  #ex-maphint { position: absolute; left: 10px; bottom: 8px; margin: 0; font-size: 13px; background: var(--surface); padding: 3px 8px; border-radius: 999px; color: var(--ink2); }
  .ex-chooser { position: absolute; z-index: 5; width: min(280px, calc(100% - 20px)); max-height: 60%; overflow-y: auto; background: var(--surface); border: 1px solid var(--rule2); border-radius: 12px; box-shadow: 0 6px 20px rgba(0,14,47,.18); padding: 6px 8px; }
  .ex-chooser p { margin: 4px 6px 6px; font-size: 13px; color: var(--muted); }
  .ex-chooser ul { list-style: none; margin: 0; padding: 0; }
  .ex-chooser button { display: block; width: 100%; min-height: 44px; text-align: left; background: none; border: 0; border-top: 1px solid var(--rule); padding: 8px 6px; font: inherit; font-size: 15px; color: var(--ink); cursor: pointer; }
  .ex-chooser button:hover { background: var(--surface2); }
  .ex-panel { position: fixed; z-index: 20; right: 0; top: 0; bottom: 0; width: clamp(320px, 40vw, 440px); overflow-y: auto; background: var(--surface); border-left: 1px solid var(--rule); box-shadow: -8px 0 24px rgba(0,14,47,.14); padding: 18px 20px 40px; overflow-wrap: anywhere; }
  @media (max-width: 600px) { .ex-panel { width: 100%; top: auto; height: 86vh; border-left: 0; border-top: 4px solid var(--tomato); border-radius: 18px 18px 0 0; } }
  /* wider screens: the open panel is a side column, and the page moves left so it covers none of the controls */
  @media (min-width: 601px) { body.ex-open .wrap { margin-left: auto; margin-right: calc(clamp(320px, 40vw, 440px) + 12px); } }
  .ex-close { position: sticky; top: 0; float: right; width: 44px; height: 44px; border-radius: 50%; border: 1px solid var(--rule2); background: var(--surface); font-size: 24px; line-height: 1; cursor: pointer; color: var(--ink); }
  .ex-kicker { margin: 0; font-size: 12px; font-weight: 700; letter-spacing: .1em; color: var(--navy2); }
  .ex-panel h2 { font-size: 34px; margin: 4px 0 6px; text-transform: uppercase; }
  .ex-addr, .ex-dist { margin: 0 0 4px; color: var(--ink2); font-size: 15px; }
  .ex-actions { margin: 14px 0 8px; display: grid; gap: 8px; }
  .ex-apple { justify-content: center; background: var(--navy); }
  .ex-act-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .ex-act-row a, .ex-act-row button { flex: 1 1 auto; min-width: 0; min-height: 44px; white-space: nowrap; text-align: center; padding: 10px 12px; border: 1px solid var(--rule2); border-radius: 12px; text-decoration: none; color: var(--navy); font-family: inherit; font-size: 15px; font-weight: 600; background: var(--surface); cursor: pointer; }
  .ex-act-row button[aria-pressed="true"] { background: var(--tomatosoft); color: var(--ontomato); }
  .ex-sec { margin-top: 18px; padding: 0; border-top: 0; }
  .ex-sec h3 { font-size: 12px; letter-spacing: .1em; text-transform: uppercase; color: var(--ink2); border-bottom: 1px solid var(--rule); padding-bottom: 6px; margin-bottom: 8px; }
  .ex-sec p, .ex-sec li { font-size: 15px; color: var(--ink2); margin: 6px 0; }
  .ex-kv { display: flex; justify-content: space-between; gap: 12px; font-size: 15px; padding: 3px 0; }
  .ex-kv span { color: var(--ink2); }
  .ex-kv b { text-align: right; }
  .ex-fine { font-size: 13px !important; color: var(--muted) !important; }
  .ex-grade { display: flex; align-items: center; gap: 12px; }
  .ex-grade .rb { width: 46px; height: 46px; font-size: 30px; border-radius: 12px; }
  .ex-grade b { display: block; color: var(--ink); font-size: 17px; }
  .ex-app { margin-top: 22px; font-size: 14px; color: var(--muted); }
  .ex-short { display: none; }
  body.ex-open { overflow: hidden; }
  @media (min-width: 601px) { body.ex-open { overflow: auto; } }
  @media (max-width: 600px) {
    .ex-long { display: none; }
    .ex-short { display: inline; }
    #ex-sub { min-height: 3.1em; }   /* most guides' descriptions take two lines here; hold them so the count below doesn't jump */
    /* 44 px touch targets */
    .ex-guides button, .ex-view button, .ex-small, .ex-row2 select { min-height: 44px; }
    .ex-row2 label { min-height: 44px; }
    .ex-row2 input[type=checkbox] { width: 20px; height: 20px; margin: 0; }
  }
  @media (max-width: 400px) { .ex-row1 input[type=search] { flex-basis: 100%; } }
"""
url = f"{DOMAIN}/explore/"
title = fit(["Search Connecticut Restaurants, Apizza & Lobster Rolls", "Connecticut Restaurant Search & Map | Connecticut Eats"], 50, 60)
desc = fit([f"Search {N_REST:,} Connecticut restaurants by name, town, village, or street, and map the {len(APIZZA)} hand-checked apizza places and {len(LOBSTER)} lobster roll stops.",
            f"Search {N_REST:,} Connecticut restaurants by name, town, or street, and map {len(APIZZA)} hand-checked apizza places and {len(LOBSTER)} lobster roll stops. Free."], 140, 160)
nav, bc = crumbs([("Home", "/"), ("Search", "/explore/")])
guide_buttons = "".join(f'<button type="button" data-g="{k}" aria-pressed="false" disabled>{e(t)}</button>' for k, t in
                        (("apizza", "Apizza"), ("lobster", "Lobster & clams"), ("burgers", "Burgers & hot dogs"), ("diners", "Diners"),
                         ("dairy", "Dairy bars"), ("polish", "Little Poland"), ("icons", "Icons"), ("oldest", "Oldest"), ("near", "Near me"),
                         ("all", "All restaurants"), ("saved", "Saved")))
# The controls are drawn from the first paint, disabled until the data arrives, with the same options explore.js fills in,
# so nothing on screen moves when it does (the list's space is held by CSS).
town_opts = '<option value="">All towns</option>' + "".join(f"<option>{e(t)}</option>" for t in sorted(TOWN_COUNT))
cuis_opts = '<option value="">All kinds</option>' + "".join(f'<option value="{e(c)}">{e(c)} ({k:,})</option>' for c, k in Counter(p.cuisine for p in REST).most_common())
sort_opts = "".join(f"<option>{s}</option>" for s in ("Featured first", "Nearest", "Oldest first", "A to Z"))
body = f"""{nav}
  <main id="main">
  <section class="ex-hero">
    <p class="kicker">{BRAND} · on the web</p>
    <h1>Search Connecticut restaurants</h1>
    <p class="sub"><span class="ex-long">{N_REST:,} restaurants, cafés, bars, and bakeries in {N_TOWNS} towns, with {len(APIZZA)} hand-checked apizza places, {len(LOBSTER)} lobster roll and clam shack stops, {len(BURGERS)} hot dog and burger icons, {len(DINERS)} diners, and {len(DAIRY)} dairy bars. The same data as the free iPhone and iPad app. Nothing about you is stored anywhere but this browser.</span><span class="ex-short">{N_REST:,} places in {N_TOWNS} towns, with the app's hand-checked guides.</span></p>
  </section>
  <noscript><p>The search needs JavaScript. The guides work without it: {", ".join(f'<a href="/{u}">{e(n.lower())}</a>' for u, n in GUIDE_PAGES + [OLDEST_PAGE])}.</p></noscript>
  <div id="ex-app" aria-busy="true">
    <div class="ex-controls">
      <div class="ex-guides" role="group" aria-label="Guides">{guide_buttons}</div>
      <div class="ex-row1">
        <label class="skip" for="ex-q">Search</label>
        <input id="ex-q" type="search" placeholder="Name, town, street, or dish" autocomplete="off" enterkeyhint="search" disabled>
        <button type="button" id="ex-locate" class="ex-small" disabled>Use my location</button>
      </div>
      <div class="ex-row2">
        <label>Sort <select id="ex-sort" aria-label="Sort" disabled>{sort_opts}</select></label>
        <select id="ex-town" aria-label="Town" disabled>{town_opts}</select>
        <select id="ex-cuisine" aria-label="Kind of place" disabled>{cuis_opts}</select>
        <label><input type="checkbox" id="ex-chains" disabled> Hide chains</label>
        <label><input type="checkbox" id="ex-conf" disabled> Confirmed only</label>
        <button type="button" id="ex-clear" class="ex-small" hidden>Clear filters</button>
        <div class="ex-view" role="group" aria-label="View"><button type="button" data-v="list" aria-pressed="true" disabled>List</button><button type="button" data-v="map" aria-pressed="false" disabled>Map</button></div>
      </div>
      <p id="ex-sub"></p>
      <p id="ex-count" aria-live="polite"></p>
      <p id="ex-locmsg"></p>
    </div>
    <div id="ex-listwrap"><ol id="ex-list" class="ex-list"><li class="ex-empty" id="ex-loading">Loading the restaurant list…</li></ol><button type="button" id="ex-more" class="ex-small" hidden></button></div>
    <div id="ex-mapwrap" hidden>
      <canvas id="ex-map" role="img" aria-label="Map of Connecticut's {N_ALL_TOWNS} towns with a dot for each place in the list. The list view has the same places."></canvas>
      <div class="ex-zoom"><button type="button" id="ex-zin" aria-label="Zoom in">+</button><button type="button" id="ex-zout" aria-label="Zoom out">−</button></div>
      <div id="ex-chooser" class="ex-chooser" role="dialog" aria-labelledby="ex-chooser-h" hidden></div>
      <p id="ex-maphint"></p>
    </div>
    <p class="fine">Confirmed = on Connecticut's liquor-permit list or Hartford's food-license list, a high-confidence map listing, or hand-checked by us. Gas-station and grocery counters and other non-restaurants are left out. Health ratings appear only where an official one exists: the {N_FV} Farmington Valley Health District towns. Town outlines: U.S. Census Bureau. See also <a href="/{OLDEST_PAGE[0]}">Connecticut's oldest restaurants</a>.</p>
  </div>
  <div id="ex-panel" class="ex-panel" role="complementary" aria-labelledby="ex-pname" hidden></div>
  </main>
<script>
// read by explore.js for the place panel's app link (set APP_STORE_URL in scripts/make-site.py)
window.APP_STORE_URL = {json.dumps(APP_STORE_URL)};
{open(f"{ROOT}/scripts/explore.js").read()}
</script>"""
webapp_ld = {"@context": "https://schema.org", "@type": "WebApplication", "name": f"{BRAND} web app", "url": url,
             "applicationCategory": "TravelApplication", "operatingSystem": "Any", "browserRequirements": "Requires JavaScript",
             "description": desc, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "publisher": {"@id": f"{DOMAIN}/#org"}}
# fetch the data while the page parses; without JavaScript the (disabled) controls are hidden and the noscript note shows
explore_head = ('<link rel="preload" href="/data/core.json" as="fetch" crossorigin>\n'
                '<noscript><style>#ex-app { display: none; }</style></noscript>\n')
written.append(page("explore/index.html", title, desc, body, [webapp_ld, bc], extra_css=EXPLORE_CSS, head_extra=explore_head))

# ---------------------------------------------------------------- landing page
# App screenshots: screenshots/<name>.png (scripts/capture-screenshots.sh; outside docs/, so the full-size captures aren't
# published) -> docs/img/screen-<name>.png (480 px) + .webp. The strip appears once they exist.
SHOT_SRC = f"{ROOT}/screenshots"
SHOTS = [("home", "Connecticut Eats home screen: New Haven Apizza, Lobster Rolls & Clam Shacks, Burger & Hot Dog Icons, Diners, Dairy Bars, and Connecticut Icons guides, with a search box for the whole directory.", "Guides for apizza, the shore, and the road."),
         ("apizza", "New Haven Apizza list in Connecticut Eats, sorted by distance from the New Haven Green.", "Apizza nearest you first."),
         ("lobster", "Lobster Rolls & Clam Shacks list in Connecticut Eats, with seasonal shacks labeled.", "Lobster rolls and clam shacks, with their seasons."),
         ("detail", "Frank Pepe Pizzeria Napoletana in Connecticut Eats: address, a button for hours and photos in Apple Maps, and its years on Wooster Street.", "Each place, with Apple Maps' live card."),
         ("map", "Connecticut Eats map of Connecticut with pins for apizza, lobster rolls, and dairy bars.", "The map, by apizza, shack, or dairy bar.")]
if os.path.isdir(SHOT_SRC):
    os.makedirs(f"{DOCS}/img", exist_ok=True)
for name, _, _ in SHOTS:
    src, png, webp = f"{SHOT_SRC}/{name}.png", f"{DOCS}/img/screen-{name}.png", f"{DOCS}/img/screen-{name}.webp"
    if os.path.exists(src) and (not os.path.exists(png) or os.path.getmtime(png) < os.path.getmtime(src)):
        subprocess.run(["sips", "--resampleWidth", "480", src, "--out", png], check=True, capture_output=True)
        if shutil.which("cwebp"):
            subprocess.run(["cwebp", "-quiet", "-q", "84", png, "-o", webp], check=True)
shot_html = []
for name, alt, cap in [s for s in SHOTS if os.path.exists(f"{DOCS}/img/screen-{s[0]}.png")]:
    w, h = png_size(f"{DOCS}/img/screen-{name}.png")
    source = f'<source srcset="/img/screen-{name}.webp" type="image/webp">' if os.path.exists(f"{DOCS}/img/screen-{name}.webp") else ""
    # all lazy: the strip starts far below the fold on a phone, and the hero has no image
    shot_html.append(f'<li><picture>{source}<img src="/img/screen-{name}.png" alt="{e(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async"></picture><p>{e(cap)}</p></li>')
screens_section = f"""
  <section id="screens">
    <h2>What it looks like</h2>
    <ul class="shots" tabindex="0" aria-label="Connecticut Eats app screenshots">
      {"".join(shot_html)}
    </ul>
  </section>
""" if shot_html else ""

fv_list = and_list(FV_TOWNS)
faq = [
    ("Is Connecticut Eats free?", "Yes. The app is free, with no ads, no in-app purchases, and no account."),
    ("Where do the apizza and lobster roll lists come from?", f"We checked each place by hand in {CHECKED}: every place on the apizza, lobster roll and clam shack, hot dog and burger, diner, dairy bar, and Little Poland lists has a 2025 or 2026 source such as its own website or menu, local news, or a tourism listing. The rest of the {N_REST:,} restaurants come from Overture Maps' open place data, the Connecticut Department of Consumer Protection's liquor-permit list, and the City of Hartford's food licenses."),
    ("Does the app show ratings or reviews?", "Not ours. The app stores no ratings or reviews, and no list is ordered by them. A place's \"Ratings, hours & photos\" button opens Apple Maps' own live card, which shows Apple's ratings, hours, and photos; that card is Apple's."),
    ("Are there health inspection grades?", f"Connecticut has no statewide restaurant inspection results or grades, and we don't make up our own. The Farmington Valley Health District rates restaurants in its {N_FV} towns ({fv_list}) A, B, C, or U and requires them to post it. For those places, the app and the web search show that official rating with its date."),
    ("What about Foxwoods and Mohegan Sun?", f"Their {len(CASINO)} restaurants are in the app, each labeled as inside the casino, on Mashantucket Pequot or Mohegan tribal land."),
    ("Does it need my location?", "Only if you want lists sorted by distance. Your location stays on your iPhone or iPad, or in your browser on this site, and is never sent to us. Everything else works without it."),
    ("A place closed or is missing. How do I tell you?", f"Email {EMAIL} with the name and town. Corrections go into the next update."),
    ("Is there an Android version?", f"Not yet. Connecticut Eats is for iPhone and iPad, and the web search works on any phone. If enough people ask at {EMAIL}, Android moves up the list."),
]
faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "@id": f"{DOMAIN}/#faq",
          "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
app_entity = {"@type": "MobileApplication", "@id": f"{DOMAIN}/#app", "name": BRAND,
              "alternateName": [SHORT, f"{BRAND}: {TAGLINE}"],
              "description": f"A free guide to {N_REST:,} Connecticut restaurants, with hand-checked lists of {len(APIZZA)} New Haven apizza places, {len(LOBSTER)} lobster roll and clam shack stops, {len(BURGERS)} hot dog and burger icons, {len(DINERS)} diners, and {len(DAIRY)} dairy bars. Sort by distance, open Apple Maps' live place card for hours and photos, and save places for later.",
              "url": f"{DOMAIN}/", "image": f"{DOMAIN}/og.png",
              "operatingSystem": "iOS, iPadOS", "applicationCategory": "TravelApplication", "applicationSubCategory": "Food & Drink",
              "inLanguage": "en", "publisher": {"@id": f"{DOMAIN}/#org"},
              "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "category": "free"}}
if os.path.exists(f"{DOCS}/img/screen-home.png"):
    app_entity["screenshot"] = f"{DOMAIN}/img/screen-home.png"
app_ld = {"@context": "https://schema.org", "@graph": [
    app_entity,
    {"@type": "Organization", "@id": f"{DOMAIN}/#org", "name": BRAND, "url": f"{DOMAIN}/",
     "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/icon-512.png", "width": 512, "height": 512}, "email": EMAIL,
     "contactPoint": {"@type": "ContactPoint", "contactType": "customer support", "email": EMAIL, "availableLanguage": "en"}},
    {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "name": BRAND, "alternateName": [SHORT, f"{BRAND} app"], "url": f"{DOMAIN}/",
     "inLanguage": "en", "publisher": {"@id": f"{DOMAIN}/#org"}}]}
title = fit([f"{BRAND}: Apizza, Lobster Roll & Restaurant App"], 50, 60)
desc = fit([f"Free iPhone and iPad guide to {N_REST:,} Connecticut restaurants, with {len(APIZZA)} hand-checked apizza places, {len(LOBSTER)} lobster roll stops, and {len(DINERS_DAIRY)} diners and dairy bars.",
            f"Free iPhone and iPad guide to {N_REST:,} Connecticut restaurants, with hand-checked New Haven apizza, {len(LOBSTER)} lobster roll stops, diners, and dairy bars.",
            f"A free iPhone and iPad guide to Connecticut restaurants, with {len(APIZZA)} hand-checked apizza places, {len(LOBSTER)} lobster roll stops, diners, and dairy bars."], 140, 160)
town_cards = "".join(f'<li><a href="{town_url(t)}">{e(t)}</a></li>' for t in TOWN_PAGES)
fv_links = " and ".join(f'<a href="{e(explore_url(g="all", town=t))}">{e(t)}</a>' for t in ("Farmington", "Simsbury"))
body = f"""  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND}: the {TAGLINE.lower()} for iPhone and iPad</p>
    <h1>{N_REST:,} Connecticut restaurants, and the apizza worth the drive</h1>
    <p class="lede">{BRAND} is a free Connecticut restaurant guide. Find a New Haven apizza, a hot buttered lobster roll on the shore, a steamed cheeseburger, or a dairy bar for after, from lists we checked by hand, plus {N_REST:,} restaurants, cafés, bars, and bakeries in {N_TOWNS} towns.</p>
    <div class="cta-row">{store_button()}<a class="btn btn-ghost" href="/explore/">Search on the web</a><span class="pill">{store_note("Free. No ads, no account.")}</span></div>
    <ul class="stats" aria-label="What's in the app">
      <li><b>{len(APIZZA)}</b><span>apizza places</span></li>
      <li><b>{len(LOBSTER)}</b><span>lobster roll &amp; clam shack stops</span></li>
      <li><b>{len(DINERS_DAIRY)}</b><span>diners &amp; dairy bars</span></li>
      <li><b>{N_REST:,}</b><span>restaurants statewide</span></li>
    </ul>
  </section>

  <section id="what">
    <h2>A Connecticut restaurant guide that knows apizza from pizza</h2>
    <p class="sub">General restaurant apps rank by star ratings and can't tell you which shacks are open for the season. {BRAND} starts from what people here actually look for: a coal-fired pie on Wooster Street, a lobster roll with butter, not mayo, a steamed cheeseburger in Meriden, and the diners and dairy bars that have been there for decades. Every place on those lists was {checked_open(HC)}, and seasonal places list their season. For hours and photos, each place opens Apple Maps' own live card.</p>
  </section>

  <section id="how">
    <h2>How it works</h2>
    <ol class="steps">
      <li class="step"><div class="n" aria-hidden="true">1</div><div><h3>Pick a guide.</h3><p>New Haven Apizza, Lobster Rolls &amp; Clam Shacks, Burger &amp; Hot Dog Icons, Diners, Dairy Bars, Little Poland, Connecticut Icons, or <a href="/{OLDEST_PAGE[0]}">Oldest Places</a>, or search {N_REST:,} restaurants by name, town, village, or street.</p></div></li>
      <li class="step"><div class="n" aria-hidden="true">2</div><div><h3>See what's near you.</h3><p>Sort by distance, filter by town or kind of food, or browse the map. Seasonal shacks say so.</p></div></li>
      <li class="step"><div class="n" aria-hidden="true">3</div><div><h3>Go.</h3><p>Open Apple Maps' place card for live hours and photos, call, get directions, or save it for the weekend.</p></div></li>
    </ol>
  </section>
{screens_section}
  <section id="guides">
    <h2>Connecticut food guides</h2>
    <p class="sub">The app's hand-checked lists, readable on the web.</p>
    <div class="grid2">
      <a class="card" href="/new-haven-apizza.html"><h3>New Haven apizza guide</h3><p>{len(APIZZA)} pizzerias by region and town, from Wooster Street out.</p></a>
      <a class="card" href="/connecticut-lobster-rolls.html"><h3>Lobster rolls &amp; clam shacks</h3><p>{len(LOBSTER)} places, with the season for the shacks.</p></a>
      <a class="card" href="/connecticut-hot-dogs-burgers.html"><h3>Hot dog &amp; burger icons</h3><p>{len(BURGERS)} stands and counters, steamed cheeseburgers included.</p></a>
      <a class="card" href="/connecticut-diners-dairy-bars.html"><h3>Diners &amp; dairy bars</h3><p>{len(DINERS)} diners and {len(DAIRY)} dairy bars and farm creameries.</p></a>
      <a class="card" href="/{OLDEST_PAGE[0]}"><h3>Connecticut's oldest restaurants</h3><p>{len(OLDEST)} places by years at the same address, from {OLDEST[0].founded} on.</p></a>
      <a class="card" href="/explore/#g=polish"><h3>Little Poland</h3><p>{len(POLISH)} Polish restaurants and bakeries, from New Britain out. In the web search.</p></a>
      <a class="card" href="/explore/#g=all"><h3>The whole state</h3><p>{N_REST:,} places in {N_TOWNS} towns, from open map data, the state's liquor permits, and Hartford's food licenses.</p></a>
    </div>
  </section>

  <section id="towns">
    <h2>Apizza and lobster rolls by town</h2>
    <p class="sub">The classics in and near Connecticut's biggest towns, plus each town's icons and oldest restaurants.</p>
    <ul class="towns">{town_cards}</ul>
  </section>

  <section id="inspections">
    <h2>Health ratings: official ones only</h2>
    <p class="sub">Connecticut has no statewide restaurant inspection results or grades, and we don't invent our own. The Farmington Valley Health District rates restaurants in its {N_FV} towns A, B, C, or U and requires each to post it; for the {len(FV):,} places we matched to its published ratings, the app and the <a href="/explore/">web search</a> show that official rating with its date. See {fv_links} in the web search, where each rated place shows its rating.</p>
  </section>

  <section id="pricing">
    <h2>Free, and staying that way</h2>
    <p class="sub">No ads, no subscription, no in-app purchases, no account. The whole guide is built into the app, so lists open instantly, even with one bar of signal at the beach.</p>
  </section>

  <section id="privacy">
    <h2>Your lunch plans are your business</h2>
    <p class="sub">{BRAND} collects nothing. If you allow location, it only sorts lists by distance on your device. Saved places stay on your device. This website sets no cookies and runs no trackers. <a href="/privacy.html">Read the privacy policy</a>.</p>
  </section>

  <section id="faq">
    <h2>Questions</h2>
    {faq_html}
  </section>

  <section id="download" class="final">
    <h2>Find the next pie</h2>
    <p class="sub">{f"{BRAND} is free on the App Store for iPhone and iPad." if APP_STORE_URL else f"{BRAND} is coming to the App Store for iPhone and iPad. Free."}</p>
    <div class="cta-row">{store_button()}</div>
  </section>
  </main>"""
written.append(page("index.html", title, desc, body, [app_ld, faq_ld]))

# ---------------------------------------------------------------- privacy and terms
nav, bc = crumbs([("Home", "/"), ("Privacy policy", "/privacy.html")])
body = f"""{nav}
  <main id="main" class="legal">
  <section class="hero">
    <h1>Privacy policy</h1>
    <p class="lede">Short version: the {BRAND} app collects nothing about you, and this website doesn't track you. Last updated {nice_date(PRIVACY_UPDATED)}.</p>
  </section>
  <section>
    <h2>The app</h2>
    <ul>
      <li><b>No account, no analytics, no ads.</b> The app has no sign-in, no advertising, and no analytics or crash-reporting code. We receive no data from it.</li>
      <li><b>Location.</b> If you allow it, your location is used on your device to sort places by distance and show where you are on the map. It is never sent to us. You can turn it off in Settings at any time.</li>
      <li><b>Saved places and filters</b> are stored only on your device and are deleted when you delete the app.</li>
      <li><b>Apple Maps.</b> When you open a place's hours and photos, or ask for directions, the app asks Apple Maps for that place. Apple handles that request under <a href="https://www.apple.com/legal/privacy/" rel="noopener">Apple's privacy policy</a>, as it does for any app that shows a map.</li>
      <li><b>Spotlight.</b> The app adds its hand-checked places to your device's search index so you can find them from Spotlight. That index stays on your device.</li>
      <li><b>Calls, websites, and email</b> you start from a place open in the Phone app, your browser or Mail, and are handled by them.</li>
    </ul>
    <p>On the App Store, the app's privacy label {'is' if APP_STORE_URL else 'will be'} "Data Not Collected".</p>
    <h2>This website</h2>
    <p>The site is static pages hosted on GitHub Pages. It sets no cookies and loads no analytics, fonts, maps, or scripts from anyone else. GitHub may keep standard server logs, such as IP addresses, for security; see <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub's privacy statement</a>.</p>
    <p>The <a href="/explore/">web search</a> keeps your saved places and the last guide you opened in your browser's local storage, on your device only; clearing your browser's site data deletes them. If you tap "Use my location", open the "Near me" guide, or sort by "Nearest", your browser asks first, and your location is used in the page to sort by distance. It is never sent to us or anyone else.</p>
    <h2>Email</h2>
    <p>If you email us, we use your message and address only to reply and to fix the listing you told us about. We don't add you to a mailing list or share your address.</p>
    <h2>Children</h2>
    <p>The app collects no personal information from anyone, including children.</p>
    <h2>Changes and contact</h2>
    <p>If this policy changes, the new version will be posted here with a new date. Questions: <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
  </section>
  </main>"""
written.append(page("privacy.html", "Privacy Policy: Connecticut Eats Apizza & Restaurant App",
                    fit(["The Connecticut Eats privacy policy: the app collects no data, keeps your location and saved places on your device, and this site sets no cookies."], 140, 160),
                    body, [bc]))

notice_lines = [l for l in open(f"{ROOT}/ConnecticutEats/Resources/Licenses/Foursquare-NOTICE.txt").read().split("\n") if l.strip()]
notice_body = [l for l in notice_lines if not l.startswith("Notice of changes")]   # the app's own copy names the wrong app; ours is below
notice_html = "".join(f"<p>{e(l)}</p>" for l in notice_body) + (
    f"<p>Notice of changes: {BRAND} filtered the Data to eating and drinking places in Connecticut, removed duplicates and closed, "
    "adult, or unverifiable listings, and reformatted it for this app and website (2026).</p>")
assert "Wisconsin" not in notice_html
# the license texts travel with the data files (docs/data/*.json) too, as the Foursquare NOTICE asks for flat-file copies
LIC_SRC = f"{ROOT}/ConnecticutEats/Resources/Licenses"
os.makedirs(f"{DOCS}/licenses", exist_ok=True)
for name in ("Apache-2.0.txt", "CDLA-Permissive-2.0.txt"):
    shutil.copyfile(f"{LIC_SRC}/{name}", f"{DOCS}/licenses/{name}")
open(f"{DOCS}/licenses/Foursquare-NOTICE.txt", "w").write("\n".join(notice_body) + "\n\n" + re.sub(r"<[^>]+>", "", notice_html.split("<p>")[-1]) + "\n")
nav, bc = crumbs([("Home", "/"), ("Terms of use", "/terms.html")])
body = f"""{nav}
  <main id="main" class="legal">
  <section class="hero">
    <h1>Terms of use</h1>
    <p class="lede">The plain-language terms for the {BRAND} app and this website. Last updated {nice_date(TERMS_UPDATED)}.</p>
  </section>
  <section>
    <h2>What the app is</h2>
    <p>{BRAND} is a free guide to restaurants in Connecticut. It is provided as is, for personal use, without charge and without warranties of any kind.</p>
    <h2>Check before you go</h2>
    <p>Restaurants open, close, and change their hours and menus, and shacks and dairy bars close for the season. Dishes, seasons, and years at an address are what each place or a named source said when we checked in {CHECKED}. We work to keep the lists right, but we can't promise that any listing is current or complete. Call the restaurant before you make the trip.</p>
    <h2>Health ratings</h2>
    <p>Connecticut has no statewide restaurant inspection results or grades, and {BRAND} doesn't grade restaurants. For the {N_FV} towns of the Farmington Valley Health District ({fv_list}), the app and the web search show the district's own official rating (A Excellent, B Good, C Fair, or U Unsatisfactory) with its date, as the district published it. A rating describes one inspection on that day. For the official record, see the Farmington Valley Health District.</p>
    <h2>Casino restaurants</h2>
    <p>Restaurants inside Foxwoods Resort Casino and Mohegan Sun are on Mashantucket Pequot and Mohegan tribal land, and the app labels them that way.</p>
    <h2>Other people's content</h2>
    <p>Hours, photos and other details in each place card come from Apple Maps and are Apple's and its providers', under Apple's terms. Restaurant names and trademarks belong to their owners. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation; honors are reported as facts. {BRAND} is not affiliated with, endorsed by, or operated by the State of Connecticut, its Department of Consumer Protection or Department of Public Health, the City of Hartford, the Farmington Valley Health District, the Mashantucket Pequot or Mohegan tribes or their casinos, the University of Connecticut, the James Beard Foundation, Apple, or any restaurant or chain.</p>
    <h2 id="sources">Data sources and licenses</h2>
    <ul>
      <li>Overture Maps Foundation places data (overturemaps.org), release {e(D.get("overture", ""))}, filtered and reformatted for {BRAND}. Data from Meta, Microsoft, DAC, and BrightQuery under the Community Data License Agreement, Permissive 2.0 (<a href="/licenses/CDLA-Permissive-2.0.txt">CDLA Permissive 2.0 text</a>); data from Foursquare under the Apache License 2.0 (<a href="/licenses/Apache-2.0.txt">Apache 2.0 text</a>; <a href="/licenses/Foursquare-NOTICE.txt">NOTICE</a>, also below); data from AllThePlaces under CC0 1.0. The same licenses cover the web search's data files.</li>
      <li>Connecticut Department of Consumer Protection, State Licenses and Credentials (<a href="https://data.ct.gov/Business/State-Licenses-and-Credentials/ngch-56tr" rel="noopener">data.ct.gov</a>), public domain: on-premise liquor permits, used for the business's trade name, address, and permit type only. The State of Connecticut makes no warranty as to the data and does not endorse this app.</li>
      <li>City of Hartford open data (data.hartford.gov): current food establishment licenses, modified for use here. The City of Hartford makes no warranty as to the data and does not endorse this app.</li>
      <li>Farmington Valley Health District food service ratings by town (<a href="https://fvhd.org/environmental-health/food/food-ratings/" rel="noopener">fvhd.org</a>), shown as published with their dates; fetched {nice_date(D["fvhd_fetched"])}.</li>
      <li>U.S. Census Bureau cartographic boundary files (public domain): the outlines of Connecticut's {N_ALL_TOWNS} towns, used to place each restaurant in its town and to draw the web map.</li>
      <li>James Beard Foundation: award, nominee, semifinalist, and America's Classics history, checked against the foundation's own announcements.</li>
      <li>Apizza, lobster rolls, clam shacks, hot dog and burger icons, diners, dairy bars, and years at an address: our own research, with a source recorded for every place.</li>
      <li>Maps, place cards, and directions in the app: Apple Maps.</li>
    </ul>
    <h2>Foursquare NOTICE</h2>
    <blockquote>{notice_html}</blockquote>
    <h2>Corrections</h2>
    <p>If a listing is wrong, or you own a restaurant and want something fixed, email <a href="mailto:{EMAIL}">{EMAIL}</a>. We fix mistakes in the next update.</p>
    <h2>Liability</h2>
    <p>To the extent the law allows, we are not liable for any loss arising from use of the app or site, including a wasted drive to a closed shack. Connecticut law governs these terms.</p>
    <h2>Changes</h2>
    <p>We may update these terms; the current version and its date are always on this page. See also the <a href="/privacy.html">privacy policy</a>.</p>
  </section>
  </main>"""
written.append(page("terms.html", "Terms of Use: Connecticut Eats Apizza & Restaurant App",
                    fit(["The Connecticut Eats terms of use: a free Connecticut restaurant guide, provided as is. Check before you go, and see where every listing comes from."], 140, 160),
                    body, [bc]))

body = f"""  <main id="main">
  <section class="hero">
    <h1>Page not found</h1>
    <p class="lede">That page isn't here. Try the <a href="/">{BRAND} home page</a>, the <a href="/new-haven-apizza.html">apizza guide</a>, the <a href="/connecticut-lobster-rolls.html">lobster roll guide</a>, or the <a href="/explore/">restaurant search</a>.</p>
  </section>
  </main>"""
page("404.html", f"Page not found | {BRAND}", "This page doesn't exist.", body, robots="noindex,follow")

# ---------------------------------------------------------------- plumbing
urls = ["" if w == "index.html" else w.replace("index.html", "") for w in written]
urls.sort(key=lambda u: (u != "", u.startswith("towns/"), u))
open(f"{DOCS}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                       + "".join(f"  <url><loc>{DOMAIN}/{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
open(f"{DOCS}/robots.txt", "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
json.dump({"name": BRAND, "short_name": SHORT, "description": f"{TAGLINE}, plus {N_REST:,} Connecticut restaurants.", "start_url": f"{BASE}/", "display": "browser",
           "background_color": "#f7f8fb", "theme_color": "#000E2F",
           "icons": [{"src": f"{BASE}/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": f"{BASE}/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
          open(f"{DOCS}/site.webmanifest", "w"), indent=2)
if CUSTOM_DOMAIN:
    open(f"{DOCS}/CNAME", "w").write(CUSTOM_DOMAIN + "\n")
elif os.path.exists(f"{DOCS}/CNAME"):
    os.remove(f"{DOCS}/CNAME")   # no custom domain yet: GitHub serves the project address
open(f"{DOCS}/.nojekyll", "w").write("")
# the share image (docs/og.png) prints the counts in its tagline, so it's redrawn (og.png only, never the app icon) when they change
OG_LINE = f"{TAGLINE} · {N_REST:,} restaurants in {N_TOWNS} towns"
NUMBERS = f"{ROOT}/playbook/site-numbers.json"
og_line = json.load(open(NUMBERS)).get("og_line") if os.path.exists(NUMBERS) else None
if og_line != OG_LINE or not os.path.exists(f"{DOCS}/og.png"):
    try:
        subprocess.run(["swift", "scripts/make-brand.swift", "og", OG_LINE], cwd=ROOT, check=True)
        og_line = OG_LINE
    except (OSError, subprocess.CalledProcessError) as ex:
        print(f"!! docs/og.png still shows the old counts ({ex}); run: swift scripts/make-brand.swift og")
json.dump({"generated": TODAY, "data_generated": DATA_DATE, "domain": DOMAIN, "og_line": og_line, "restaurants": N_REST, "towns": N_TOWNS,
           "apizza": len(APIZZA), "lobster_rolls_and_clam_shacks": len(LOBSTER), "lobster_roll": n_roll, "clam_shack": n_shack,
           "lobster_seasonal": len(seas), "burgers_and_hot_dogs": len(BURGERS), "steamed_cheeseburger": n_steam, "hot_dog": n_dog,
           "diners": len(DINERS), "dairy_bars": len(DAIRY), "dairy_seasonal": dairy_seas, "little_poland": len(POLISH),
           "hand_checked": len(HC), "oldest_known_year": len(OLDEST), "named_diner_not_checked": NAMED_DINER,
           "named_apizza_not_checked": NAMED_APIZZA, "casino_restaurants": len(CASINO), "fvhd_rated": len(FV), "fvhd_towns": FV_TOWNS,
           "towns_pages": town_stats},
          open(NUMBERS, "w"), indent=1)
print("wrote", len(written) + 1, "pages:", ", ".join(written + ["404.html"]))
print(f"restaurants {N_REST:,} in {N_TOWNS} towns | apizza {len(APIZZA)} | lobster {len(LOBSTER)} | burgers {len(BURGERS)} | diners {len(DINERS)} "
      f"| dairy {len(DAIRY)} | polish {len(POLISH)} | hand-checked {len(HC)} | FVHD rated {len(FV)}")
print("core.json", os.path.getsize(f"{DOCS}/data/core.json") // 1024, "KB | detail.json", os.path.getsize(f"{DOCS}/data/detail.json") // 1024, "KB")
