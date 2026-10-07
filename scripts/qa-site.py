"""QA for the website in docs/: every sitemap page in headless Chrome at phone and desktop widths, served under the same path
GitHub Pages will use (/connecticut-eats/ until the custom domain is live).

Page checks: loads with 200, no horizontal scroll, no console errors, no Content-Security-Policy violations, no requests to any
other host (no analytics, third-party scripts, fonts or tiles), one <h1>, a 50-60 character title and 140-160 character
description, valid JSON-LD with no ratings or reviews, no broken internal links (including #anchors) or images.
Static checks (every page, 404 included): the CSP meta tag comes first in <head> with a hash for each inline script; JSON-LD has
no raw "<", every list item points at an #p- anchor on its page, no empty address, phones are +1 numbers, own sites are sameAs;
no "James Beard finalist", no "every restaurant" overclaim, no Apple logo; the 404 page names no canonical URL; town pages that
say none of our hand-checked places of a kind is in or near the town are true (data/app/places.json's export in docs/data).
Web app checks (explore/): the apizza guide lists exactly the hand-checked apizza places; a search for "pepes" finds Frank Pepe
in New Haven and opens it; a shared #p= link opens the place; a Canton place with a Farmington Valley rating shows "official",
the rating and its date; the map draws the state and the dots; an emoji search lists nothing; Save survives a reload; Near me
sorts by distance from the browser's location. Also: no layout shift while the list loads, Back closes an open place, the
phone panel is a modal dialog and the desktop panel covers no control, the search rules shared with the app ("apizza in new
haven", "near mystic", "new preston", "route 32", "pizza near me"), #g=constructor, the skip link, rank numbers only on
ranking sorts and no iconic points, "Confirmed only" keeps hand-checked places, "Hide chains" keeps hand-checked originals,
Featured order from outside Connecticut, a slow drag on the map opens nothing, and stacked dots open a chooser.

Usage: .venv/bin/python scripts/qa-site.py      (serves docs/ itself on a free localhost port; exits 1 on any problem)
  QA_DOCS=<dir>   check another copy of docs/ (used to confirm that each check can fail)
  QA_SHOTS=<dir>  also save a few screenshots there
Copied from wi-eats/scripts/qa-site.py and extended. Never drives anyone's own browser.
"""
import base64
import functools
import hashlib
import html as H
import http.server
import json
import math
import os
import re
import sys
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS = os.path.abspath(os.environ.get("QA_DOCS") or os.path.join(ROOT, "docs"))
SHOTS = os.environ.get("QA_SHOTS")
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
SITEMAP = [e.text for e in ET.parse(os.path.join(DOCS, "sitemap.xml")).getroot().findall("s:url/s:loc", NS)]
HOME = urllib.parse.urlparse(SITEMAP[0])           # the landing page comes first
DOMAIN_HOST = HOME.netloc
BASE = HOME.path.rstrip("/")                        # "/connecticut-eats" on github.io, "" on a custom domain
NEW_HAVEN_GREEN = {"latitude": 41.3083, "longitude": -72.9279}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
BANNED_LD = {"aggregateRating", "review", "reviews", "reviewRating", "ratingValue"}
# what each page records while it runs: CSP violations and layout shifts (not caused by input)
INIT = """window.__csp = []; window.__cls = 0;
document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective + ' ' + (e.blockedURI || '')));
try { new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; })
  .observe({type: 'layout-shift', buffered: true}); } catch (e) {}"""
# sha256 digests of a private address and its pieces (user, domain): no public page may contain them. Only digests are kept,
# so this public file doesn't spell the address out.
PRIVATE_DIGESTS = {
    "4a7e25559b2ffc162afaef2b1680778c6e77d8c2982c3870595f6ee8fea7a455",
    "ff8ea15b513b5561b1c48b725aff52338eddb8ecdd46af58759e2f2c554b0582",
    "31b7679e2f02e2b0561693acc0c78f067633b6713ac53fb5980dcb0f7c2ea237",
    "928009cbd52e0a32a3542c0f41efa0ac8feef2e05974b8126f26c7d4f9b593e3",
}
CSP_REST = ("style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; manifest-src 'self'; base-uri 'none'; "
            "form-action 'none'; upgrade-insecure-requests")


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serves DOCS at BASE/, the way GitHub Pages serves the project site; anything outside BASE is a 404."""

    def translate_path(self, path):
        p = urllib.parse.urlsplit(path).path
        if BASE and p != BASE and not p.startswith(BASE + "/"):
            return os.path.join(DOCS, "__not_under_base__")
        return super().translate_path(path[len(BASE):] if BASE else path)

    def log_message(self, *a):
        pass


def serve():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=DOCS))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"


def local_file(path):
    """The file a site path maps to, or None when it isn't under BASE or doesn't exist."""
    path = urllib.parse.unquote(path)
    if BASE and path != BASE and not path.startswith(BASE + "/"):
        return None
    f = os.path.join(DOCS, path[len(BASE):].lstrip("/"))
    if os.path.isfile(f):
        return f
    if os.path.isfile(os.path.join(f, "index.html")):
        return os.path.join(f, "index.html")
    return None


def banned_keys(obj):
    if isinstance(obj, dict):
        return [k for k in obj if k in BANNED_LD] + [x for v in obj.values() for x in banned_keys(v)]
    if isinstance(obj, list):
        return [x for v in obj for x in banned_keys(v)]
    return []


def nice_date(iso):
    y, m, d = iso.split("-")
    return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"


def load_data():
    core = json.load(open(os.path.join(DOCS, "data", "core.json")))
    detail = json.load(open(os.path.join(DOCS, "data", "detail.json")))
    C = core["cols"]
    n = len(C["id"])
    kbit = {k: 1 << i for i, k in enumerate(core["kinds"])}
    town = lambda i: core["cities"][C["c"][i]] if C["c"][i] is not None else None
    apizza = {i for i in range(n) if C["hc"][i] == 1 and (C["k"][i] or 0) & kbit["apizza"] and C["v"][i] != 1}
    pepe = [i for i in range(n) if C["n"][i] == "Frank Pepe Pizzeria Napoletana" and town(i) == "New Haven"]
    canton = sorted([i for i in range(n) if town(i) == "Canton" and C["v"][i] != 1 and detail[i] and detail[i].get("fv")],
                    key=lambda i: C["n"][i].lower())
    return core, detail, C, apizza, pepe, canton


GUIDE_KINDS = {"new-haven-apizza.html": ["apizza"], "connecticut-lobster-rolls.html": ["lobster roll", "clam shack"],
               "connecticut-hot-dogs-burgers.html": ["burger icon", "steamed cheeseburger", "hot dog icon"],
               "connecticut-diners-dairy-bars.html": ["diner", "dairy bar"]}
OLDEST_PAGE = "connecticut-oldest-restaurants.html"
ENTRY = re.compile(r'<li id="p-[^"]+"><h3>(.*?)</h3>')   # a full place entry (a town page's "listed above" pointer isn't one)


def check_static_guides(data, problems):
    """Each guide page lists exactly the hand-checked places of its kinds (a place merely named "... Diner" is not enough), and
    the oldest-restaurants page exactly the places with a year at the same address."""
    core, _, C, *_ = data
    kbit = {k: 1 << i for i, k in enumerate(core["kinds"])}
    n = len(C["id"])
    pages = {name: (lambda i, mask=sum(kbit[k] for k in kinds): C["hc"][i] == 1 and (C["k"][i] or 0) & mask) for name, kinds in GUIDE_KINDS.items()}
    pages[OLDEST_PAGE] = lambda i: C["f"][i] is not None
    for name, want_it in pages.items():
        f = os.path.join(DOCS, name)
        if not os.path.exists(f):
            problems.append(f"{name}: missing")
            continue
        want = Counter(C["n"][i] for i in range(n) if want_it(i) and C["v"][i] != 1)
        got = Counter(H.unescape(x) for x in ENTRY.findall(open(f).read()))
        if got != want:
            problems.append(f"{name}: lists {sum(got.values())} places, expected {sum(want.values())} "
                            f"(extra {sorted((got - want).elements())[:4]}, missing {sorted((want - got).elements())[:4]})")


def private_words(text):
    t = text.lower()
    words = set(re.findall(r"[\w.%+-]+@[\w.-]+", t)) | set(re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)*", t)) | set(re.findall(r"[a-z0-9]+", t))
    return [w for w in words if hashlib.sha256(w.encode()).hexdigest() in PRIVATE_DIGESTS]


def all_html():
    out = []
    for d, _, files in os.walk(DOCS):
        out += [os.path.join(d, x) for x in files if x.endswith(".html")]
    return sorted(out)


def check_static_pages(problems):
    """What the generator promises on every page, read from the files themselves."""
    for f in all_html():
        name = os.path.relpath(f, DOCS)
        doc = open(f, encoding="utf-8").read()
        # the CSP meta tag first in <head>, with exactly one hash per inline script (JSON-LD blocks are data, not scripts)
        m = re.search(r"<head>\s*<meta http-equiv=\"Content-Security-Policy\" content=\"([^\"]+)\">", doc)
        scripts = re.findall(r"<script>(.*?)</script>", doc, re.S)
        hashes = " ".join(f"'sha256-{base64.b64encode(hashlib.sha256(x.encode()).digest()).decode()}'" for x in scripts) or "'none'"
        want = f"default-src 'none'; script-src {hashes}; {CSP_REST}"
        if not m:
            problems.append(f"{name}: no Content-Security-Policy meta tag first in <head>")
        elif m.group(1) != want:
            problems.append(f"{name}: CSP is {m.group(1)[:120]!r}…, expected {want[:120]!r}…")
        if re.search(r"<script(?![^>]*application/ld\+json)[^>]*\bsrc=", doc) or re.search(r"\son[a-z]+=\"", doc):
            problems.append(f"{name}: an external script or an inline event handler")
        ids = set(re.findall(r'\bid="([^"]+)"', doc))
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', doc, re.S):
            if "<" in raw or ">" in raw:
                problems.append(f"{name}: JSON-LD has a raw < or > (it must be escaped as \\u003c)")
            try:
                ld = json.loads(raw)
            except ValueError:
                continue    # the browser pass reports bad JSON-LD
            if ld.get("@type") == "ItemList":
                for it in ld["itemListElement"]:
                    frag = urllib.parse.urlparse(it.get("url", "")).fragment
                    r = it.get("item", {})
                    if not frag.startswith("p-") or frag not in ids or r.get("url") != it.get("url"):
                        problems.append(f"{name}: list item {r.get('name')!r} doesn't point at its #p- entry on the page ({it.get('url')})")
                    a = r.get("address", {})
                    if any(v == "" for v in a.values()):
                        problems.append(f"{name}: {r.get('name')!r} has an empty address field")
                    if "telephone" in r and not re.fullmatch(r"\+1[2-9]\d{9}", r["telephone"]):
                        problems.append(f"{name}: {r.get('name')!r} has telephone {r['telephone']!r}")
                    if "sameAs" in r and urllib.parse.urlsplit(r["sameAs"]).scheme not in ("http", "https"):
                        problems.append(f"{name}: {r.get('name')!r} sameAs {r['sameAs']!r}")
        text = H.unescape(re.sub(r"<[^>]+>", " ", doc))
        for bad in ("James Beard finalist", "Every Connecticut restaurant", "every restaurant in 169"):
            if bad.lower() in text.lower() or bad.lower() in doc.lower():
                problems.append(f"{name}: says {bad!r}")
        if private_words(doc):
            problems.append(f"{name}: contains a private email address or part of one")
        if "M16.4 12.6c0-2.5" in doc:
            problems.append(f"{name}: draws the Apple logo")
        if re.search(r"<h1[^>]*>\s*<span class=\"kicker\"", doc):
            problems.append(f"{name}: the kicker is inside the <h1>")
        if 'name="twitter:image:alt"' not in doc:
            problems.append(f"{name}: no twitter:image:alt")
        if name == "404.html" and ('rel="canonical"' in doc or 'property="og:url"' in doc):
            problems.append("404.html: has a canonical URL or og:url")
        if name == "index.html":
            imgs = re.findall(r"<img [^>]*>", doc)
            if any('loading="lazy"' not in i for i in imgs):
                problems.append("index.html: a screenshot isn't loading=lazy")
    for d, _, files in os.walk(DOCS):   # the data files, license texts, sitemap and manifest are public too
        for x in files:
            if x.endswith((".json", ".txt", ".xml", ".webmanifest")) and private_words(open(os.path.join(d, x), encoding="utf-8", errors="replace").read()):
                problems.append(f"{os.path.relpath(os.path.join(d, x), DOCS)}: contains a private email address or part of one")


TOWN_SECTIONS = {"apizza": (["apizza"], 10), "lobster": (["lobster roll", "clam shack"], 15),
                 "burgers": (["burger icon", "steamed cheeseburger", "hot dog icon"], 10), "diners": (["diner", "dairy bar"], 10)}
LEDE_KIND = {"apizza": "apizza", "lobster rolls": "lobster", "hot dogs": "burgers", "diners": "diners"}


def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def check_town_claims(data, problems):
    """A town page may say none of our hand-checked places of a kind is in or near the town only when that's true: no
    hand-checked place of that kind in the town or within the section's radius of its center (the median of its places)."""
    core, _, C, *_ = data
    kbit = {k: 1 << i for i, k in enumerate(core["kinds"])}
    n = len(C["id"])
    town = lambda i: core["cities"][C["c"][i]] if C["c"][i] is not None else None
    places = defaultdict(list)
    for i in range(n):
        if C["v"][i] != 1 and C["la"][i] is not None:
            places[town(i)].append(i)
    for f in sorted(glob for glob in all_html() if os.sep + "towns" + os.sep in glob):
        name = os.path.relpath(f, DOCS)
        doc = open(f, encoding="utf-8").read()
        t = H.unescape(re.search(r'<li aria-current="page">(.*?)</li>', doc).group(1))   # the town, from the breadcrumb
        here = places[t]
        if not here:
            problems.append(f"{name}: no places in {t!r} in the data")
            continue
        center = (sorted(C["la"][i] for i in here)[len(here) // 2], sorted(C["lo"][i] for i in here)[len(here) // 2])

        def close(k, rad):
            mask = sum(kbit[x] for x in TOWN_SECTIONS[k][0])
            return sorted(C["n"][i] for i in range(n) if C["hc"][i] == 1 and C["v"][i] != 1 and (C["k"][i] or 0) & mask
                          and (town(i) == t or (C["la"][i] is not None and miles(center, (C["la"][i], C["lo"][i])) <= rad)))

        claims = []
        text = H.unescape(re.sub(r"<[^>]+>", "", doc))
        # a claim about the world ("None in West Hartford", "the nearest are a drive away") can't be backed by our list
        if re.search(r"\bNone in .+? or within \d+ miles", text) or any(
                not x.startswith("hand-checked ") for x in re.findall(r"\bFor ([^.]*?), the nearest are a drive away", text)):
            problems.append(f"{name}: says there's none of a kind in or near {t} at all; say none of our hand-checked ones is")
        for k, body in re.findall(r'<section id="(apizza|lobster|burgers|diners)">(.*?)</section>', doc, re.S):
            for m in re.finditer(r"None of our \d+ hand-checked [^<.]*? is in (.+?) or within (\d+) miles", H.unescape(body)):
                if m.group(1) != t:
                    problems.append(f"{name}: a 'None of our …' sentence names {m.group(1)!r}")
                claims.append((k, int(m.group(2))))
        lede = H.unescape(re.sub(r"<[^>]+>", "", re.search(r'<p class="lede">(.*?)</p>', doc, re.S).group(1)))
        m = re.search(r"For hand-checked (.+?), the nearest are a drive away", lede)
        if m:
            for label in re.split(r",? and |, ", m.group(1)):
                claims.append((LEDE_KIND[label], TOWN_SECTIONS[LEDE_KIND[label]][1]))
        for k, rad in claims:
            wrong = close(k, rad)
            if wrong:
                problems.append(f"{name}: says none of our hand-checked {k} places is in or within {rad} miles of {t}, but {wrong[:3]} are")
        if f"None of our" in doc and re.search(r"hand-checked places is in [^<]*? yet", doc):
            hc_here = [C["n"][i] for i in range(n) if C["hc"][i] == 1 and C["v"][i] != 1 and town(i) == t]
            if hc_here:
                problems.append(f"{name}: says none of our hand-checked places is in {t}, but {hc_here[:3]} are")


def rows(page):
    return page.evaluate("""[...document.querySelectorAll('#ex-list .ex-row')].map(b => ({
        i: +b.dataset.i, name: b.querySelector('.ex-name')?.textContent || '', town: b.querySelector('.ex-town')?.textContent || '',
        metric: b.querySelector('.ex-metric b')?.textContent || ''}))""")


def search(page, text):
    """Types into the search box and waits for the list to re-render (the input is debounced)."""
    before = page.locator("#ex-count").text_content()
    page.locator("#ex-q").fill(text)
    try:
        page.wait_for_function("b => document.querySelector('#ex-count').textContent !== b", arg=before, timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(250)


def close_panel(page):
    if page.locator("#ex-close").count() and page.locator("#ex-close").is_visible():
        page.locator("#ex-close").click()


def pick_guide(page, g):
    page.locator(f'.ex-guides button[data-g="{g}"]').click()
    page.wait_for_timeout(250)


def check_explore(page, base, width, data, problems, errors):
    core, detail, C, apizza, pepe, canton = data
    where = f"explore @{width}"
    errors.clear()
    # the data arrives a second late, as on a phone, so the page paints before it does (that's when a layout can jump)
    slow = lambda route: (time.sleep(1), route.continue_())
    page.route("**/data/core.json", slow)
    page.goto(base + BASE + "/explore/", wait_until="networkidle")
    try:
        page.wait_for_function("document.querySelectorAll('#ex-list .ex-row').length > 0", timeout=15000)
    except Exception:
        problems.append(f"{where}: the list never loaded")
        return
    finally:
        page.unroute("**/data/core.json", slow)
    # 0. nothing moves when the data arrives (the controls and the list's space are there from the first paint)
    page.wait_for_timeout(500)
    cls = page.evaluate("window.__cls || 0")
    if cls > 0.1:
        problems.append(f"{where}: layout shift while the list loaded (CLS {cls:.3f})")

    # 1. the apizza guide lists exactly the hand-checked apizza places (a place merely named "... Apizza" is not enough)
    page.locator("#ex-q").fill("")
    pick_guide(page, "apizza")
    while page.locator("#ex-more").is_visible():
        page.locator("#ex-more").click()
        page.wait_for_timeout(100)
    shown = {r["i"] for r in rows(page)}
    if shown != apizza:
        extra = sorted(C["n"][i] + (" (hand-checked)" if C["hc"][i] == 1 else " (NOT hand-checked)") for i in shown - apizza)
        missing = sorted(C["n"][i] for i in apizza - shown)
        problems.append(f"{where}: apizza guide shows {len(shown)} places, expected the {len(apizza)} hand-checked ones; extra {extra[:5]}, missing {missing[:5]}")
    if any(C["hc"][i] != 1 for i in shown):
        problems.append(f"{where}: apizza guide lists places that aren't hand-checked")

    # 2. the map draws: the state outline filled, and a dot for each hand-checked apizza place
    page.locator('.ex-view button[data-v="map"]').click()
    page.wait_for_timeout(900)
    px = page.evaluate("""() => {
        const cv = document.querySelector('#ex-map'); if (!cv || !cv.width) return null;
        const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
        let white = 0, tomato = 0, navy = 0;
        for (let i = 0; i < d.length; i += 4) {
          const [r, g, b, a] = [d[i], d[i + 1], d[i + 2], d[i + 3]];
          if (a < 200) continue;
          if (r > 245 && g > 245 && b > 245) white++;
          else if (Math.abs(r - 179) < 24 && Math.abs(g - 38) < 24 && Math.abs(b - 30) < 24) tomato++;
          else if (r < 30 && g < 40 && b < 70) navy++;
        }
        return { total: cv.width * cv.height, white, tomato, navy, hint: document.querySelector('#ex-maphint').textContent };
    }""")
    if not px:
        problems.append(f"{where}: the map canvas has no size")
    else:
        if px["white"] < 0.08 * px["total"]:
            problems.append(f"{where}: the map didn't draw Connecticut ({px['white']} of {px['total']} px)")
        if px["tomato"] < 60:
            problems.append(f"{where}: the map drew no apizza dots ({px['tomato']} px)")
        if not px["hint"].startswith(f"{len(apizza)} places"):
            problems.append(f"{where}: map hint says {px['hint']!r}, expected {len(apizza)} places")
    if SHOTS and width == 375:
        page.evaluate("document.querySelector('#ex-controls, .ex-controls').scrollIntoView()")
        page.wait_for_timeout(300)
        page.screenshot(path=os.path.join(SHOTS, "site-explore-map-375.png"))
    page.locator('.ex-view button[data-v="list"]').click()
    page.wait_for_timeout(300)

    # 3. "pepes" finds Frank Pepe in New Haven (a trailing "s" also matches its stem), and opening it shows that place
    pick_guide(page, "all")
    search(page, "pepes")
    hits = [r for r in rows(page) if r["name"] == "Frank Pepe Pizzeria Napoletana" and "New Haven" in r["town"]]
    if not hits:
        problems.append(f"{where}: search 'pepes' didn't find Frank Pepe Pizzeria Napoletana in New Haven ({[r['name'] for r in rows(page)][:5]})")
    else:
        page.locator(f'#ex-list .ex-row[data-i="{hits[0]["i"]}"]').click()
        page.wait_for_timeout(500)
        panel = page.locator("#ex-panel")
        if not panel.is_visible() or panel.locator("#ex-pname").text_content() != "Frank Pepe Pizzeria Napoletana" \
                or "NEW HAVEN" not in (panel.locator(".ex-kicker").text_content() or "") or not panel.locator("a", has_text="Directions").count():
            problems.append(f"{where}: opening Frank Pepe from the search didn't show its details")
        else:
            # 4. Save, then the Saved guide lists it, also after a reload (localStorage)
            panel.locator("#ex-save").click()
            close_panel(page)
            pick_guide(page, "saved")
            page.locator("#ex-q").fill("")
            page.wait_for_timeout(300)
            if hits[0]["i"] not in {r["i"] for r in rows(page)}:
                problems.append(f"{where}: a saved place isn't in the Saved guide")
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(500)
            if hits[0]["i"] not in {r["i"] for r in rows(page)}:
                problems.append(f"{where}: a saved place was gone after a reload")
            if SHOTS and width == 375:
                page.locator(f'#ex-list .ex-row[data-i="{hits[0]["i"]}"]').click()
                page.wait_for_timeout(600)
                page.screenshot(path=os.path.join(SHOTS, "site-explore-panel-375.png"))
                close_panel(page)

    # 5. a shared link (#p=<id>) opens the place on a cold load
    if pepe:
        page.goto("about:blank")
        page.goto(base + BASE + f"/explore/#g=all&p={C['id'][pepe[0]]}", wait_until="networkidle")
        page.wait_for_timeout(700)
        if not page.locator("#ex-panel").is_visible() or page.locator("#ex-pname").text_content() != "Frank Pepe Pizzeria Napoletana":
            problems.append(f"{where}: a #p= link didn't open the place")
        close_panel(page)

    # 6. a Canton place with a Farmington Valley rating shows it as official, with the letter, its meaning and the date
    if not canton:
        problems.append(f"{where}: no Canton place with a Farmington Valley rating in the data")
    else:
        i = canton[0]
        fv = detail[i]["fv"]
        pick_guide(page, "all")
        search(page, f"{C['n'][i]} canton")
        hit = [r for r in rows(page) if r["i"] == i]
        if not hit:
            problems.append(f"{where}: searching '{C['n'][i]} canton' didn't find it")
        else:
            page.locator(f'#ex-list .ex-row[data-i="{i}"]').click()
            try:
                page.wait_for_function("document.querySelector('#ex-panel').dataset.ready === '1'", timeout=8000)
            except Exception:
                pass
            sec = page.locator("#ex-panel .ex-fv")
            text = sec.inner_text() if sec.count() else ""
            meaning = {"A": "Excellent", "B": "Good", "C": "Fair", "U": "Unsatisfactory"}[fv["r"]]
            need = ["official", fv["r"], meaning, nice_date(fv["d"])]
            if not text or any(w.lower() not in text.lower() for w in need):
                problems.append(f"{where}: {C['n'][i]} (Canton) didn't show its official rating with the date; wanted {need}, got {text[:160]!r}")
            close_panel(page)

    # 7. an emoji (nothing searchable) lists nothing rather than everything
    search(page, "🍕")
    if page.locator("#ex-list .ex-row").count():
        problems.append(f"{where}: an emoji search listed places")
    page.locator("#ex-q").fill("")

    # 8. Near me sorts by distance from the browser's location (the context is at the New Haven Green)
    pick_guide(page, "near")
    try:
        page.wait_for_function("document.querySelectorAll('#ex-list .ex-row').length > 0", timeout=8000)
    except Exception:
        pass
    rs = rows(page)
    dists = []
    for r in rs[:40]:
        m = re.match(r"([\d.]+) mi", r["metric"])
        dists.append(float(m.group(1)) if m else None)
    if not rs or None in dists:
        problems.append(f"{where}: Near me listed {len(rs)} places without distances")
    elif dists != sorted(dists) or dists[0] > 1:
        problems.append(f"{where}: Near me isn't sorted by distance from the New Haven Green ({dists[:6]})")

    def fresh(hash_):
        page.goto("about:blank")
        page.goto(base + BASE + "/explore/#" + hash_, wait_until="networkidle")
        try:
            page.wait_for_function("document.querySelector('#ex-app').getAttribute('aria-busy') === 'false'", timeout=15000)
        except Exception:
            problems.append(f"{where}: #{hash_} never finished loading")
        page.wait_for_timeout(300)

    # 9. Back closes an open place (opening one adds a history entry) and keeps the search; the panel is a modal dialog on
    # a phone, with the page behind it inert, and a side column on a desktop that covers none of the controls
    fresh("g=all&q=pepes")
    n0 = page.evaluate("history.length")
    page.locator("#ex-list .ex-row").first.click()
    page.wait_for_timeout(400)
    if page.evaluate("history.length") != n0 + 1 or "p=" not in page.evaluate("location.hash"):
        problems.append(f"{where}: opening a place didn't add a history entry")
    role, modal = page.get_attribute("#ex-panel", "role"), page.get_attribute("#ex-panel", "aria-modal")
    if width <= 600:
        if role != "dialog" or modal != "true" or not page.evaluate("document.getElementById('ex-app').inert && document.querySelector('header.site').inert"):
            problems.append(f"{where}: the open panel isn't a modal dialog with the page behind it inert (role={role}, aria-modal={modal})")
    else:
        if role == "dialog" or page.evaluate("document.querySelectorAll('[inert]').length"):
            problems.append(f"{where}: the side panel is modal on a wide screen")
        covered = page.evaluate("""[...document.querySelectorAll('.ex-guides button, #ex-q, #ex-locate, .ex-row2 select, .ex-row2 input, .ex-view button, header.site nav a')]
            .filter(el => { const r = el.getBoundingClientRect(); if (!r.width || r.bottom > innerHeight) return false;
              return !el.contains(document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)); })
            .map(el => el.textContent.trim() || el.id)""")
        if covered:
            problems.append(f"{where}: with a place open, the panel covers {covered[:6]}")
    page.go_back()
    page.wait_for_timeout(600)
    if page.locator("#ex-panel").is_visible() or "/explore/" not in page.url or "p=" in page.url or "q=pepes" not in page.url:
        problems.append(f"{where}: Back didn't just close the place ({page.url})")
    if page.evaluate("document.querySelectorAll('[inert]').length"):
        problems.append(f"{where}: part of the page stayed inert after the panel closed")

    # 10. the search rules the app shares: stop words go once a town, village or tag is found, "near me" is dropped, the
    # longest town or village wins, and route numbers read alike
    fresh("g=all")

    def result(q):
        search(page, q)
        return page.locator("#ex-count").text_content(), [r["i"] for r in rows(page)][:40]
    for a, b in (("apizza in new haven", "apizza new haven"), ("near mystic", "mystic"), ("pizza near me", "pizza"),
                 ("route 32", "ct 32"), ("rte 32", "route 32")):
        ra, rb = result(a), result(b)
        if ra != rb or not ra[1]:
            problems.append(f"{where}: search {a!r} ({ra[0]}) doesn't give the same places as {b!r} ({rb[0]})")
    search(page, "new preston")
    towns = {r["town"].split(" · ")[0] for r in rows(page)}
    if not towns or any(not t.startswith("New Preston") for t in towns):
        problems.append(f"{where}: search 'new preston' isn't the village New Preston ({sorted(towns)[:4]})")
    page.locator("#ex-q").fill("")

    # 11. a crafted hash (#g=constructor and friends) is just an unknown guide
    errors.clear()
    fresh("g=constructor&sort=toString")
    if not page.locator("#ex-list .ex-row").count():
        problems.append(f"{where}: #g=constructor shows no list")
    fresh("g=__proto__&q=constructor&kind=hasOwnProperty")
    problems.extend(f"{where}: crafted hash: page error: {x}" for x in errors)
    errors.clear()

    # 12. the skip link moves focus without resetting the search or the filters
    fresh("g=all&q=pepes&town=New+Haven")
    page.locator("a.skip").focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)
    if page.locator("#ex-q").input_value() != "pepes" or "in New Haven" not in page.locator("#ex-count").text_content():
        problems.append(f"{where}: the skip link reset the web app")

    # 13. rank numbers only on a ranking sort (iconic, oldest), with "Rank" for screen readers; the Icons explainer
    fresh("g=icons")
    if not page.locator(".ex-rank").count() or not page.evaluate("document.querySelector('.ex-rank .sr')?.textContent === 'Rank '"):
        problems.append(f"{where}: the Icons ranking shows no rank numbers")
    if "not a rating" not in page.locator("#ex-sub").text_content():
        problems.append(f"{where}: the Icons guide doesn't say its points aren't a rating")
    if page.evaluate("[...document.querySelectorAll('.ex-metric small')].some(s => /pts/.test(s.textContent))"):
        problems.append(f"{where}: the Icons list shows iconic points")
    fresh("g=all")
    if page.locator(".ex-rank").count():
        problems.append(f"{where}: rank numbers on an A to Z list")

    # 14. "Confirmed only" keeps hand-checked places, and a hand-checked place is never called "Listing only"
    fresh("g=apizza&conf=1")
    if len(rows(page)) != len(apizza):
        problems.append(f"{where}: Confirmed only drops hand-checked apizza places ({len(rows(page))} of {len(apizza)})")
    lone = [i for i in range(len(C["id"])) if C["hc"][i] == 1 and C["t"][i] == 0 and C["v"][i] != 1]
    if lone:
        fresh(f"g=all&p={C['id'][lone[0]]}")
        text = page.locator("#ex-panel").inner_text() if page.locator("#ex-panel").is_visible() else ""
        if "Hand-checked" not in text or "Listing only" in text:
            problems.append(f"{where}: {C['n'][lone[0]]} (hand-checked, a listing only on the map data) isn't labeled Hand-checked")

    # 15. "Hide chains" never hides a hand-checked original (hc, no br), only branches; from outside Connecticut the classics
    # stay in Featured order rather than Nearest
    fresh("g=apizza&chains=1")
    want = {i for i in apizza if not ((C["ch"][i] or 1) >= 5 and not (C["hc"][i] == 1 and not (C.get("br") or [None] * len(C["id"]))[i]))}
    if {r["i"] for r in rows(page)} != want:
        problems.append(f"{where}: Hide chains on the apizza guide shows {len(rows(page))} places, expected {len(want)} (originals kept)")
    page.context.set_geolocation({"latitude": 37.7749, "longitude": -122.4194})
    fresh("g=apizza")
    page.locator("#ex-locate").click()
    try:
        page.wait_for_function("document.querySelector('#ex-locmsg').textContent.includes('outside Connecticut')", timeout=8000)
    except Exception:
        pass
    if "Featured first" not in page.locator("#ex-count").text_content():
        problems.append(f"{where}: from outside Connecticut the apizza guide isn't in Featured order ({page.locator('#ex-count').text_content()})")
    page.context.set_geolocation(NEW_HAVEN_GREEN)

    # 16. the map: a slow drag opens nothing, and a tap on places stacked on one spot offers a chooser
    pos_js = """([la, lo]) => {
        const LAT0 = 41.5, KX = Math.cos(LAT0 * Math.PI / 180), proj = (lo, la) => [(lo + 72.7) * KX, -(la - LAT0)];
        const CT = { s: 40.95, n: 42.06, w: -73.74, e: -71.78 }, wrap = document.querySelector('#ex-mapwrap');
        const w = wrap.clientWidth, h = wrap.clientHeight, [x0, y0] = proj(CT.w, CT.n), [x1, y1] = proj(CT.e, CT.s);
        const k = Math.min(w / (x1 - x0), h / (y1 - y0)) * 0.94, cam = { k, x: (w - (x1 - x0) * k) / 2 - x0 * k, y: (h - (y1 - y0) * k) / 2 - y0 * k };
        const [px, py] = proj(lo, la), r = document.querySelector('#ex-map').getBoundingClientRect();
        return [r.left + px * cam.k + cam.x, r.top + py * cam.k + cam.y]; }"""
    fresh("g=apizza&view=map")
    page.evaluate("document.querySelector('#ex-map').scrollIntoView({block: 'center'})")
    page.wait_for_timeout(300)
    i = min(apizza)
    x, y = page.evaluate(pos_js, [C["la"][i], C["lo"][i]])
    page.mouse.move(x, y)
    page.mouse.down()
    for k in range(1, 13):
        page.mouse.move(x + k, y)
        page.wait_for_timeout(25)
    page.mouse.up()
    page.wait_for_timeout(300)
    if page.locator("#ex-panel").is_visible():
        problems.append(f"{where}: a slow drag on the map opened a place")
    stacks = defaultdict(list)
    for j in range(len(C["id"])):
        if C["v"][j] != 1 and C["la"][j] is not None and C["a"][j]:
            stacks[(C["la"][j], C["lo"][j], C["a"][j], C["c"][j])].append(j)
    by_town = defaultdict(list)
    for j in range(len(C["id"])):
        if C["v"][j] != 1 and C["la"][j] is not None:
            by_town[C["c"][j]].append(j)

    def alone(g):
        """No other place the town filter and an address search would also list (same town, same street number) within ~1 km,
        so the tap can only hit this stack, even at the state-wide zoom."""
        la, lo, num = C["la"][g[0]], C["lo"][g[0]], C["a"][g[0]].split()[:1]
        return all(abs(C["la"][j] - la) + abs(C["lo"][j] - lo) > 0.01 for j in by_town[C["c"][g[0]]]
                   if (C["la"][j], C["lo"][j]) != (la, lo) and (C["a"][j] or "").split()[:1] == num)
    group = next((g for g in stacks.values() if 2 <= len(g) <= 4 and alone(g)), None)
    if group:
        j = group[0]
        fresh("view=map&" + urllib.parse.urlencode({"g": "all", "town": core["cities"][C["c"][j]], "q": C["a"][j]}))
        page.evaluate("document.querySelector('#ex-map').scrollIntoView({block: 'center'})")
        page.wait_for_timeout(300)
        x, y = page.evaluate(pos_js, [C["la"][j], C["lo"][j]])
        page.mouse.click(x, y)
        page.wait_for_timeout(400)
        names = page.evaluate("[...document.querySelectorAll('#ex-chooser button')].map(b => b.textContent)")
        if not page.locator("#ex-chooser").is_visible() or not {C["n"][g] for g in group} <= set(names):
            problems.append(f"{where}: a tap on {len(group)} places at one spot ({C['a'][j]}) didn't list them ({names})")
        else:
            page.locator("#ex-chooser button").first.click()
            page.wait_for_timeout(400)
            if not page.locator("#ex-panel").is_visible() or page.locator("#ex-pname").text_content() != names[0]:
                problems.append(f"{where}: picking a place from the map's chooser didn't open it")
    problems.extend(f"{where}: console error: {x}" for x in errors)
    problems.extend(f"{where}: CSP violation: {x}" for x in page.evaluate("window.__csp || []"))


def main():
    base = serve()
    pages = [base + urllib.parse.urlparse(u).path for u in SITEMAP]
    data = load_data()
    problems = []
    check_static_guides(data, problems)
    check_static_pages(problems)
    check_town_claims(data, problems)
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        for width in (375, 1280):
            ctx = browser.new_context(viewport={"width": width, "height": 900}, geolocation=NEW_HAVEN_GREEN, permissions=["geolocation"])
            ctx.add_init_script(INIT)
            page = ctx.new_page()
            errors, offsite = [], []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            local = urllib.parse.urlparse(base).netloc
            page.on("request", lambda r: offsite.append(r.url) if urllib.parse.urlparse(r.url).scheme in ("http", "https")
                    and urllib.parse.urlparse(r.url).netloc != local else None)
            for url in pages:
                errors.clear(); offsite.clear()
                try:
                    resp = page.goto(url, wait_until="networkidle")
                except Exception as ex:
                    problems.append(f"{url} @{width}: didn't load ({str(ex).splitlines()[0]})")
                    continue
                path = urllib.parse.urlparse(url).path
                where = f"{path} @{width}"
                if not resp or resp.status != 200:
                    problems.append(f"{where}: HTTP {resp.status if resp else 'no response'}")
                    continue
                over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                if over > 1:
                    problems.append(f"{where}: scrolls sideways by {over}px")
                if page.locator("h1").count() != 1:
                    problems.append(f"{where}: {page.locator('h1').count()} <h1>")
                title = page.title()
                desc = page.evaluate("document.querySelector('meta[name=description]')?.content || ''")
                if not 50 <= len(title) <= 60:
                    problems.append(f"{where}: title is {len(title)} characters")
                if not 140 <= len(desc) <= 160:
                    problems.append(f"{where}: description is {len(desc)} characters")
                for raw in page.locator('script[type="application/ld+json"]').all_text_contents():
                    try:
                        bad = banned_keys(json.loads(raw))
                        if bad:
                            problems.append(f"{where}: JSON-LD has ratings or reviews ({sorted(set(bad))})")
                    except ValueError as ex:
                        problems.append(f"{where}: bad JSON-LD ({ex})")
                if width == 1280:   # links are the same at both widths
                    refs = page.evaluate("""[...document.querySelectorAll('a[href],img[src],link[href],script[src],source[srcset]')]
                        .map(e => e.getAttribute('href') || e.getAttribute('src') || e.getAttribute('srcset'))""")
                    for ref in refs:
                        full = urllib.parse.urljoin(url, ref)
                        p = urllib.parse.urlparse(full)
                        if p.scheme in ("mailto", "tel", "data"):
                            continue
                        if p.netloc not in (local, DOMAIN_HOST):
                            continue
                        if p.netloc == DOMAIN_HOST and not p.path.startswith(BASE + "/") and p.path != BASE:
                            continue    # another site on the same host (another github.io project)
                        f = local_file(p.path)
                        if not f:
                            problems.append(f"{where}: broken link {ref}")
                        elif p.fragment and "=" not in p.fragment and f.endswith(".html"):
                            if not re.search(rf'id="{re.escape(p.fragment)}"', open(f).read()):
                                problems.append(f"{where}: link to a missing anchor {ref}")
                    imgs = page.evaluate("[...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.src)")
                    problems += [f"{where}: image didn't load {s}" for s in imgs]
                    tags = page.evaluate("""[...document.querySelectorAll('script[src],link[rel=stylesheet],iframe,img[src]')]
                        .map(e => e.src || e.href).filter(u => u && !u.startsWith(location.origin) && !u.startsWith('data:'))""")
                    problems += [f"{where}: loads something from another site: {u}" for u in tags]
                if SHOTS and path in (BASE + "/", BASE + "/new-haven-apizza.html", BASE + "/towns/farmington.html"):
                    name = {BASE + "/": "home", BASE + "/new-haven-apizza.html": "apizza", BASE + "/towns/farmington.html": "farmington"}[path]
                    page.screenshot(path=os.path.join(SHOTS, f"site-{name}-{width}.png"), full_page=(name != "home"))
                problems += [f"{where}: console error: {x}" for x in errors]
                problems += [f"{where}: CSP violation: {x}" for x in page.evaluate("window.__csp || []")]
                problems += [f"{where}: request to another site: {u}" for u in offsite]
            offsite.clear()
            try:
                check_explore(page, base, width, data, problems, errors)
            except Exception as ex:   # a broken page shouldn't stop the report
                problems.append(f"explore @{width}: the checks stopped: {str(ex).splitlines()[0]}")
            problems += [f"explore @{width}: request to another site: {u}" for u in offsite]
            ctx.close()
        browser.close()
    print(f"{len(pages)} pages × 2 widths + the web app (served at {BASE or '/'} from {DOCS})")
    for p in problems:
        print("  ✗", p)
    print("OK" if not problems else f"{len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
