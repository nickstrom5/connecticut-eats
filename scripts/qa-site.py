"""QA for the website in docs/: every sitemap page in headless Chrome at phone and desktop widths, served under the same path
GitHub Pages will use (/connecticut-eats/ until the custom domain is live).

Page checks: loads with 200, no horizontal scroll, no console errors, no requests to any other host (no analytics, third-party
scripts, fonts or tiles), one <h1>, a 50-60 character title and 140-160 character description, valid JSON-LD with no ratings
or reviews, no broken internal links (including #anchors) or images.
Web app checks (explore/): the apizza guide lists exactly the hand-checked apizza places; a search for "pepes" finds Frank Pepe
in New Haven and opens it; a shared #p= link opens the place; a Canton place with a Farmington Valley rating shows "official",
the rating and its date; the map draws the state and the dots; an emoji search lists nothing; Save survives a reload; Near me
sorts by distance from the browser's location.

Usage: .venv/bin/python scripts/qa-site.py      (serves docs/ itself on a free localhost port; exits 1 on any problem)
  QA_DOCS=<dir>   check another copy of docs/ (used to confirm that each check can fail)
  QA_SHOTS=<dir>  also save a few screenshots there
Copied from wi-eats/scripts/qa-site.py and extended. Never drives anyone's own browser.
"""
import functools
import http.server
import json
import os
import re
import sys
import threading
import urllib.parse
import xml.etree.ElementTree as ET

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


def check_static_guides(data, problems):
    """Each guide page lists exactly the hand-checked places of its kinds (a place merely named "... Diner" is not enough)."""
    import html as H
    from collections import Counter
    core, _, C, *_ = data
    kbit = {k: 1 << i for i, k in enumerate(core["kinds"])}
    for name, kinds in GUIDE_KINDS.items():
        f = os.path.join(DOCS, name)
        if not os.path.exists(f):
            problems.append(f"{name}: missing")
            continue
        mask = sum(kbit[k] for k in kinds)
        want = Counter(C["n"][i] for i in range(len(C["id"])) if C["hc"][i] == 1 and (C["k"][i] or 0) & mask and C["v"][i] != 1)
        got = Counter(H.unescape(x) for x in re.findall(r"<li><h3>(.*?)</h3>", open(f).read()))
        if got != want:
            problems.append(f"{name}: lists {sum(got.values())} places, expected the {sum(want.values())} hand-checked ones "
                            f"(extra {sorted((got - want).elements())[:4]}, missing {sorted((want - got).elements())[:4]})")


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
    page.goto(base + BASE + "/explore/", wait_until="networkidle")
    try:
        page.wait_for_function("document.querySelectorAll('#ex-list .ex-row').length > 0", timeout=15000)
    except Exception:
        problems.append(f"{where}: the list never loaded")
        return

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
    problems.extend(f"{where}: console error: {x}" for x in errors)


def main():
    base = serve()
    pages = [base + urllib.parse.urlparse(u).path for u in SITEMAP]
    data = load_data()
    problems = []
    check_static_guides(data, problems)
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        for width in (375, 1280):
            ctx = browser.new_context(viewport={"width": width, "height": 900}, geolocation=NEW_HAVEN_GREEN, permissions=["geolocation"])
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
