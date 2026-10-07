// Connecticut Eats web app: the iPhone app's guides, search, filters, map and place details, in the browser.
// Same data file as the app (split into core + detail by scripts/make-site.py). No cookies, no trackers, no third-party
// scripts or map tiles; saved places and the last guide live in this browser's localStorage only.
// Ported from ConnecticutEats/Models/{Guide,Search,Place}.swift and Views/PlaceDetailView.swift: keep them in step.
(() => {
  "use strict";
  const BASE = document.documentElement.dataset.base || "";
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const store = {
    get(k, d) { try { const v = localStorage.getItem("ce-" + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem("ce-" + k, JSON.stringify(v)); } catch { /* private mode */ } },
  };
  // lookups keyed by what people type or what a URL says have no prototype, so "constructor" or "__proto__" is just a word
  const dict = (...objs) => Object.assign(Object.create(null), ...objs);
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const niceDate = (iso) => { const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || ""); return m ? `${MONTHS[+m[2] - 1]} ${+m[3]}, ${m[1]}` : String(iso || ""); };

  // ---------------------------------------------------------------- search (a port of ConnecticutEats/Models/Search.swift)
  const typeSyn = dict({ avenue: "ave", av: "ave", street: "st", boulevard: "blvd", road: "rd", drive: "dr", place: "pl", court: "ct",
    parkway: "pkwy", highway: "hwy", lane: "ln", trail: "trl", circle: "cir", terrace: "ter", turnpike: "tpke", route: "rt", rte: "rt" });
  const syn = dict(typeSyn, { north: "n", south: "s", east: "e", west: "w", saint: "st", mount: "mt" });
  const abbrs = new Set(Object.values(syn)), typeAbbrs = new Set(Object.values(typeSyn));
  // a route number: "CT-32", "US 1", "Rte 66" and "route 32" all read "rt <number>"
  const ROUTE_WORDS = new Set(["ct", "us", "rte", "route", "rt"]);
  const routes = (words) => words.map((w, i) => (ROUTE_WORDS.has(w) && /^\d+$/.test(words[i + 1] || "") ? "rt" : w));
  // tag bits come from the data file's "tags" order; the phrases are Search.tagPhrases
  let T = {};
  const TAG_PHRASES = [["apizza", "apizza"],
    ["lobster rolls", "lobster"], ["lobster roll", "lobster"], ["clam shacks", "clams"], ["clam shack", "clams"],
    ["fried clams", "clams"], ["steamed cheeseburgers", "steamed"], ["steamed cheeseburger", "steamed"],
    ["steamed burger", "steamed"], ["hot dogs", "hotdog"], ["hot dog", "hotdog"], ["hotdogs", "hotdog"],
    ["dairy bars", "dairy"], ["dairy bar", "dairy"], ["diners", "diner"], ["diner", "diner"],
    ["pierogi", "polish"], ["polish", "polish"]];
  const STOP = new Set(["the", "and", "of", "a", "in", "near"]);
  function normalize(s) {
    let t = String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
    t = t.replace(/\b([a-z0-9])\s*&\s*([a-z0-9])\b/g, "$1$2").replace(/&/g, " and ").replace(/['’`]/g, "");
    return t.replace(/[^\p{L}\p{N}]+/gu, " ").trim();
  }
  const normAddr = (s) => routes(normalize(s).split(" ")).map((w) => syn[w] || w).join(" ");
  // town and village names as typed, longest first; a town wins a tie with a village of the same length
  let TOWN_KEYS = dict(), VILLAGE_KEYS = dict(), PLACE_KEYS = [];

  function parse(text) {
    const q = { tokens: [], town: null, village: null, placePhrase: null, tag: 0, tagPhrase: null, unsearchable: false };
    const raw = normalize(text).split(" ").filter(Boolean);
    q.unsearchable = !raw.length && String(text || "").trim() !== "";   // "🍕", "!!!": nothing to look for
    for (let i = 0; i + 1 < raw.length;) { if (raw[i] === "near" && raw[i + 1] === "me") raw.splice(i, 2); else i++; }   // "near me" asks for nothing
    if (!raw.length) return q;
    const mapped = routes(raw).map((w) => syn[w] || w);
    const find = (phrase) => {
      const p = phrase.split(" ");
      for (let i = 0; i + p.length <= mapped.length; i++) if (p.every((w, k) => mapped[i + k] === w)) return [i, i + p.length];
      return null;
    };
    const cut = ([a, b]) => { const words = raw.slice(a, b).join(" "); raw.splice(a, b - a); mapped.splice(a, b - a); return words; };
    for (const [phrase, tag] of TAG_PHRASES) { const r = find(normalize(phrase)); if (r) { q.tag = T[tag]; q.tagPhrase = cut(r); break; } }
    // the single longest town or village named in the query wins ("new preston" is the village, not the town of Preston),
    // unless a street type follows it ("new britain ave" is a street)
    for (const [key, kind, name] of PLACE_KEYS) {
      const r = find(key);
      if (r && !(r[1] < mapped.length && typeAbbrs.has(mapped[r[1]]))) { q[kind] = name; q.placePhrase = cut(r); break; }
    }
    // stop words go once a town, village or tag is set, or when any other word is left ("apizza in new haven")
    let idx = raw.map((_, i) => i);
    if (q.town || q.village || q.tag || idx.some((i) => !STOP.has(mapped[i]))) idx = idx.filter((i) => !STOP.has(mapped[i]));
    idx.forEach((i, n) => {
      const token = raw[i], isLast = n === idx.length - 1;
      if (mapped[i] !== token) { q.tokens.push([` ${mapped[i]} `, ` ${token}`]); return; }
      const whole = (abbrs.has(token) && (!isLast || token.length > 1)) || (token.length <= 2 && !isLast);
      const needles = [" " + token + (whole ? " " : "")];
      // what people call a place ("pepes", "sallys") may be a possessive the name doesn't have: Frank Pepe Pizzeria
      if (token.length >= 4 && token.endsWith("s") && !whole) needles.push(" " + token.slice(0, -1));
      if (isLast && token.length >= 3) for (const [word, abbr] of Object.entries(typeSyn)) if (word !== token && word.startsWith(token)) needles.push(` ${abbr} `);
      q.tokens.push(needles);
    });
    // "chapel st": a finished street type sticks to the word before it
    if (q.tokens.length >= 2 && idx.length && typeAbbrs.has(mapped[idx[idx.length - 1]])) {
      const last = idx[idx.length - 1], prev = idx[idx.length - 2];
      q.tokens.splice(-2, 2, [` ${mapped[prev]} ${mapped[last]} `, ` ${raw[prev]} ${raw[last]}`]);
    }
    return q;
  }
  const qEmpty = (q) => !q.tokens.length && !q.town && !q.village && !q.tag;
  function matches(p, q) {
    if (q.tag && !(p.g & q.tag)) {
      const stem = normalize(q.tagPhrase || "").replace(/s$/, "");
      if (!stem || !p.nameText.includes(" " + stem)) return false;
    }
    if (q.town && p.c !== q.town && !p.nameText.includes(" " + normalize(q.placePhrase || ""))) return false;
    if (q.village && p.vil !== q.village && !p.nameText.includes(" " + normalize(q.placePhrase || ""))) return false;
    return q.tokens.every((needles) => needles.some((n) => p.search.includes(n)));
  }
  // name matches first ("haven" puts Haven Hot Chicken ahead of places in New Haven)
  const nameMatches = (p, q) => q.tokens.length && q.tokens.every((needles) => needles.some((n) => p.nameText.includes(n)));

  // The search text of each place (Place.swift: name, town, village, zip, cuisine, brand, host, dishes, then the address with
  // street words abbreviated) is built on the first search, or bit by bit when the browser is idle, not while the page loads.
  let indexed = 0;
  function indexPlace(p) {
    p.search = " " + normalize([p.n, p.c, p.vil, p.z, p.cu, p.brand, p.host, p.dish].filter(Boolean).join(" ")) + " " + normAddr(p.a || "") + " ";
    p.nameText = " " + normalize([p.n, p.brand].filter(Boolean).join(" ")) + " ";
  }
  function ensureIndex() { for (; indexed < P.length; indexed++) indexPlace(P[indexed]); }
  function indexWhenIdle() {
    const idle = window.requestIdleCallback || ((f) => setTimeout(f, 50));
    const step = () => {
      for (const end = Math.min(P.length, indexed + 2000); indexed < end; indexed++) indexPlace(P[indexed]);
      if (indexed < P.length) idle(step);
    };
    idle(step);
  }

  // ---------------------------------------------------------------- guides (ConnecticutEats/Models/Guide.swift)
  // The classics list only hand-checked places, by the research's kind bits: a listing merely named "… Diner" isn't enough.
  let K = {};
  const CLASSIC_SORTS = ["featured", "nearest", "oldest", "name"];
  const RANKING = new Set(["iconic", "oldest"]);   // the sorts that rank; only these show rank numbers
  const GUIDES = {
    apizza: { title: "New Haven Apizza", sub: "Coal- and oven-fired pies, white clam to tomato, hand-checked", inc: (p) => p.hc && p.k & K.apizza, sorts: CLASSIC_SORTS, classic: true },
    lobster: { title: "Lobster Rolls & Clam Shacks", sub: "Hot buttered rolls and fried clams, many open in season, hand-checked", inc: (p) => p.hc && p.k & (K["lobster roll"] | K["clam shack"]), sorts: CLASSIC_SORTS, classic: true },
    burgers: { title: "Burger & Hot Dog Icons", sub: "Louis' Lunch, Meriden steamed cheeseburgers, and the stands, hand-checked", inc: (p) => p.hc && p.k & (K["burger icon"] | K["steamed cheeseburger"] | K["hot dog icon"]), sorts: CLASSIC_SORTS, classic: true },
    diners: { title: "Diners", sub: "Long-running diners, hand-checked open", inc: (p) => p.hc && p.k & K.diner, sorts: CLASSIC_SORTS, classic: true },
    dairy: { title: "Dairy Bars", sub: "Farm creameries and ice cream stands, hand-checked", inc: (p) => p.hc && p.k & K["dairy bar"], sorts: CLASSIC_SORTS, classic: true },
    polish: { title: "Little Poland", sub: "Pierogi, kielbasa, and bakeries, from New Britain out, hand-checked", inc: (p) => p.hc && p.k & K.polish, sorts: CLASSIC_SORTS, classic: true },
    icons: { title: "Connecticut Icons", sub: "James Beard honorees and long-running institutions", note: "Points come from honors and years at the address; not a rating.", inc: (p) => p.ip != null, sorts: ["iconic", "oldest", "nearest"], ranked: true },
    oldest: { title: "Oldest Places", sub: "Years at the same address, oldest first", inc: (p) => p.f != null, sorts: ["oldest"], ranked: true },
    near: { title: "Near Me", sub: "Everything around you, closest first", inc: () => true, sorts: ["nearest"], needsHere: true },
    all: { title: "All Restaurants", sub: "Restaurants, cafés, bars, and bakeries statewide", inc: () => true, sorts: ["name", "nearest"] },
    saved: { title: "Saved", sub: "Places you saved in this browser", inc: (p) => saved.has(p.id), sorts: ["name", "nearest"] },
  };
  const isGuide = (g) => typeof g === "string" && Object.hasOwn(GUIDES, g);
  // "Featured first": the featured score every hand-checked place has (fs), else the iconic points only true icons have (ip)
  const featured = (p) => p.fs ?? p.ip ?? -1;
  const SORT_LABEL = { featured: "Featured first", nearest: "Nearest", oldest: "Oldest first", name: "A to Z", iconic: "Most iconic" };

  // ---------------------------------------------------------------- state
  let P = [], D = null, CAL = {}, SOURCES = [], HOSTS = [], N_TOWNS = 0;
  let here = null, locDenied = false, shown = 100, current = [], view = "list";
  const saved = new Set(store.get("saved", []));
  const st = { g: "apizza", q: "", sort: "", town: "", cuisine: "", chains: false, conf: false, p: "" };
  const CT_BOX = { s: 40.95, n: 42.06, w: -73.74, e: -71.78 };
  const inCT = (pt) => pt && pt.la >= CT_BOX.s && pt.la <= CT_BOX.n && pt.lo >= CT_BOX.w && pt.lo <= CT_BOX.e;

  const miles = (a, b) => {
    const r = Math.PI / 180, dLa = (b.la - a.la) * r, dLo = (b.lo - a.lo) * r;
    const h = Math.sin(dLa / 2) ** 2 + Math.cos(a.la * r) * Math.cos(b.la * r) * Math.sin(dLo / 2) ** 2;
    return 3958.8 * 2 * Math.asin(Math.sqrt(h));
  };
  const milesText = (m) => (m < 10 ? m.toFixed(1) : Math.round(m)) + " mi";

  function order() {
    const g = GUIDES[st.g];
    if (st.sort && g.sorts.includes(st.sort)) return st.sort;
    return g.classic && here && inCT(here) ? "nearest" : g.sorts[0];   // from outside Connecticut, distance isn't the point
  }

  function allows(p) {   // Guide.swift Filters.allows
    if (p.v && st.g !== "saved") return false;            // gas-station counters, airport stands and the like
    if (st.town && p.c !== st.town) return false;
    if (st.cuisine && p.cu !== st.cuisine) return false;
    if (st.chains && p.ch >= 5 && !(p.hc && !p.br)) return false;   // a hand-checked original stays; its branches can go
    if (st.conf && p.t === 0 && !p.hc) return false;      // hand-checked counts as confirmed
    return true;
  }

  function list() {
    const g = GUIDES[st.g], q = parse(st.q), o = order();
    if (q.unsearchable) return [];   // typed something, but nothing searchable ("🍕", "!!!")
    if (g.needsHere && !here) return [];
    if (!qEmpty(q)) ensureIndex();
    let out = P.filter((p) => g.inc(p) && allows(p) && (qEmpty(q) || matches(p, q)));
    // same-name places (Frank Pepe's eight): the most iconic first, so the original leads, then by town
    const byName = (a, b) => a.n.localeCompare(b.n, "en", { sensitivity: "base" }) || (b.ip ?? -1) - (a.ip ?? -1) || (a.c || "").localeCompare(b.c || "");
    const dist = (p) => (here && p.la != null ? miles(here, p) : Infinity);
    if (o === "nearest" && here) out.sort((a, b) => dist(a) - dist(b) || byName(a, b));
    else if (o === "featured" || o === "nearest") out.sort((a, b) => featured(b) - featured(a) || (a.f ?? 9999) - (b.f ?? 9999) || byName(a, b));
    else if (o === "oldest") out.sort((a, b) => (a.f ?? 9999) - (b.f ?? 9999) || byName(a, b));
    else if (o === "iconic") out.sort((a, b) => (b.ip ?? -1) - (a.ip ?? -1) || byName(a, b));
    else out.sort(byName);
    if (q.tokens.length && !g.ranked) {       // name matches first when searching
      const named = out.filter((p) => nameMatches(p, q));
      if (named.length && named.length < out.length) { const ids = new Set(named); out = named.concat(out.filter((p) => !ids.has(p))); }
    }
    return out;
  }

  // ---------------------------------------------------------------- rendering
  let KIND_LABELS = [];
  const kindNames = (p) => KIND_LABELS.filter(([bit]) => p.k & bit).map(([, l]) => l);
  const jbLabel = (p) => (p.h & 1 ? "America's Classic" : p.h & 2 ? "James Beard winner" : p.h & 4 ? "James Beard nominee" : p.h & 8 ? "James Beard semifinalist" : null);
  const placeName = (p) => (p.vil ? `${p.vil} (${p.c})` : p.c);

  function chips(p, max) {   // GuideListView.swift PlaceChips
    const c = [];
    const jb = jbLabel(p);
    if (jb) c.push(`<span class="tag tag-jb">${jb}</span>`);
    for (const k of kindNames(p)) if (k !== "Historic") c.push(`<span class="tag">${k}</span>`);
    if (!p.k) {   // places outside the research still carry tags from their names (a "… Diner", an "… Apizza")
      if (p.g & T.apizza) c.push('<span class="tag">Apizza</span>');
      if (p.g & T.diner) c.push('<span class="tag">Diner</span>');
    }
    if (p.seas) c.push('<span class="tag tag-plain">Seasonal</span>');
    if (p.host) c.push(`<span class="tag tag-plain">At ${esc(p.host)}</span>`);
    if (p.ch >= 5) c.push(`<span class="tag tag-plain">Chain · ${p.ch}</span>`);
    if (p.t === 0 && !p.hc && !p.g) c.push('<span class="tag tag-dash">Listing only</span>');
    return (max ? c.slice(0, max) : c).join("");
  }

  function metric(p, o) {
    if (o === "nearest" && here && p.la != null) return [milesText(miles(here, p)), "away"];
    if (o === "oldest" && p.f) return [String(p.f), "since"];
    if (o === "iconic") return p.f ? [String(p.f), "since"] : null;   // what earns the place (a James Beard chip, or its year), not points
    if (p.f && st.g !== "all") return [String(p.f), "since"];
    return null;
  }

  function render() {
    const g = GUIDES[st.g], o = order();
    current = list();
    hideChooser();
    document.querySelectorAll(".ex-guides button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.g === st.g)));
    $("#ex-sub").textContent = (st.g === "all" ? `Restaurants, cafés, bars, and bakeries in ${N_TOWNS} towns` : g.sub) + (g.note ? `. ${g.note}` : "");
    const sortSel = $("#ex-sort");
    sortSel.innerHTML = g.sorts.map((s) => `<option value="${s}"${s === o ? " selected" : ""}>${SORT_LABEL[s]}</option>`).join("");
    sortSel.disabled = g.sorts.length < 2;
    const filters = [st.town && `in ${st.town}`, st.cuisine && st.cuisine, st.chains && "no chains", st.conf && "confirmed only"].filter(Boolean);
    $("#ex-count").textContent = `${current.length.toLocaleString("en-US")} ${current.length === 1 ? "place" : "places"} · ${SORT_LABEL[o]}` + (filters.length ? ` · ${filters.join(", ")}` : "");
    $("#ex-clear").hidden = !filters.length;
    if (view === "list") renderList(o); else drawMap();
    saveHash();
  }

  function renderList(o) {
    const ol = $("#ex-list");
    const g = GUIDES[st.g];
    if (!current.length) {
      const msg = st.g === "saved" ? "Nothing saved yet. Open a place and tap Save to keep it here, in this browser."
        : g.needsHere && !here ? (locDenied
          ? "Location is blocked for this site, so Near me has nothing to sort. Allow location for this site in your browser's settings, then tap “Use my location”."
          : "Tap “Use my location” to see the places around you. Your location stays in this browser.")
          : "No places match. Try fewer words or clear the filters.";
      ol.innerHTML = `<li class="ex-empty">${msg}</li>`;
      $("#ex-more").hidden = true;
      return;
    }
    const ranked = RANKING.has(o);
    ol.innerHTML = current.slice(0, shown).map((p, i) => {
      const m = metric(p, o);
      const rank = ranked ? `<span class="ex-rank${i < 3 ? " top" : ""}"><span class="sr">Rank </span>${i + 1}</span>` : "";
      return `<li><button class="ex-row" data-i="${p.i}">${rank}<span class="ex-main"><b class="ex-name">${esc(p.n)}</b><span class="ex-town">${esc([placeName(p), p.cu].filter(Boolean).join(" · "))}</span><span class="ex-chips">${chips(p, 4)}</span></span>${m ? `<span class="ex-metric"><b>${esc(m[0])}</b><small>${m[1]}</small></span>` : ""}</button></li>`;
    }).join("");
    const left = current.length - shown;
    $("#ex-more").hidden = left <= 0;
    $("#ex-more").textContent = `Show more (${left.toLocaleString("en-US")} left)`;
  }

  // ---------------------------------------------------------------- place panel (PlaceDetailView.swift)
  const JUR_LIST = { 1: "Connecticut Department of Consumer Protection's list of liquor permits", 2: "City of Hartford's list of food-establishment licenses" };
  const TIER = { 2: "Licensed", 1: "Confirmed listing", 0: "Listing only" };
  const RATING = { A: "Excellent", B: "Good", C: "Fair", U: "Unsatisfactory" };
  const HOST_TEXT = {
    Foxwoods: "Inside Foxwoods Resort Casino, on Mashantucket Pequot tribal land, where Mashantucket Pequot Tribal Health Services inspects restaurants.",
    "Mohegan Sun": "Inside Mohegan Sun, on Mohegan tribal land, where the Mohegan Tribal Health Department inspects restaurants.",
  };
  const CHECKED = "checked in October 2026 against a 2025 or 2026 source";
  // a phone number only when it dials the US (+1, a real area code); anything else could ring abroad
  const usPhone = (ph) => (/^\+1[2-9]\d{9}$/.test(ph || "") ? ph : null);
  const phoneText = (ph) => `(${ph.slice(2, 5)}) ${ph.slice(5, 8)}-${ph.slice(8)}`;
  const webLink = (w) => { try { const u = new URL(w); return u.protocol === "http:" || u.protocol === "https:" ? u.href : null; } catch { return null; } };

  function rate(p) {   // AppModel.matchRate: how often a listing like this matched a licensed food business in Hartford
    const src = SOURCES[p.s] || "meta";
    let group;
    if (src === "meta") group = p.t === 1 ? "Meta, confidence 0.95+" : "Meta, 0.90-0.95";
    else if (src === "AllThePlaces" || src === "DAC") group = "brand feed";
    else return null;
    const g = CAL.hartford && CAL.hartford[group];
    if (!g || g.n < 20) return null;
    return `${Math.round(g.matched * 100)}%`;
  }

  function howWeKnow(p) {
    const src = SOURCES[p.s] || "meta";
    if (src === "research") return `On our hand-checked list (${CHECKED}). The open map data didn't list it as a place to eat, so it's placed at its street address.`;
    if (p.t === 2) return (src === "official"
      ? `From the ${JUR_LIST[p.j] || "official license list"}. The open map data didn't have it, so it's placed at its street address.`
      : `Matched to an active entry on the ${JUR_LIST[p.j] || "official license list"}.`) + (p.hc ? ` It's also on our hand-checked list, ${CHECKED}.` : "");
    if (p.hc) return `${p.t === 1 ? "A high-confidence listing" : "A listing"} in Overture's open map data, and on our hand-checked list, ${CHECKED}.`;
    const r = rate(p);
    return (p.t === 1 ? "A high-confidence listing in Overture's open map data." : "A single listing in Overture's open map data, so it may be closed or misfiled.")
      + (r ? ` Checked against Hartford's food licenses, listings like this matched a licensed food business ${r} of the time.` : "");
  }

  const kv = (k, v) => (v == null || v === "" ? "" : `<div class="ex-kv"><span>${esc(k)}</span><b>${esc(v)}</b></div>`);
  const fact = (k, v) => (v ? `<p><b>${esc(k)}</b><br>${esc(v)}</p>` : "");
  const section = (t, body, cls = "") => `<section class="ex-sec${cls}"><h3>${esc(t)}</h3>${body}</section>`;

  // On a phone the panel is a modal sheet: a dialog, with everything behind it inert so Tab can't reach what it covers.
  // Wider, it's a side column next to the list (the page moves over for it) and the rest stays usable.
  const PHONE = window.matchMedia("(max-width: 600px)");
  let inerted = [];
  function setModal() {
    const panel = $("#ex-panel"), modal = PHONE.matches && !panel.hidden;
    panel.setAttribute("role", PHONE.matches ? "dialog" : "complementary");
    if (PHONE.matches) panel.setAttribute("aria-modal", "true"); else panel.removeAttribute("aria-modal");
    inerted.forEach((el) => { el.inert = false; });
    inerted = [];
    if (!modal) return;
    for (let el = panel; el.parentElement && el !== document.body; el = el.parentElement) {
      for (const sib of el.parentElement.children) if (sib !== el && !sib.inert && sib.tagName !== "SCRIPT") { sib.inert = true; inerted.push(sib); }
    }
  }
  PHONE.addEventListener("change", setModal);

  // Back closes a place: opening one adds a history entry (beforePush is the entry under it), and closing it goes back over it
  let pushed = false, closingBack = false, beforePush = "";

  function openPlace(p, push = true) {
    st.p = p.id;
    const d = (D && D[p.i]) || {};
    const addr = [p.a, [p.vil || p.c, p.z].filter(Boolean).join(" ")].filter(Boolean).join(", ");
    const apple = p.la != null
      ? `https://maps.apple.com/?q=${encodeURIComponent(p.n)}&ll=${p.la},${p.lo}`
      : `https://maps.apple.com/?q=${encodeURIComponent(p.n + ", " + addr)}`;
    const dirs = p.la != null ? `https://maps.apple.com/?daddr=${p.la},${p.lo}&dirflg=d` : apple;
    const site = d.w ? webLink(d.w) : null;
    const ph = usPhone(d.ph);
    let html = `<button class="ex-close" id="ex-close" aria-label="Close">×</button>
      <p class="ex-kicker">${esc((p.vil ? `${p.vil} · ${p.c}` : p.c || "Connecticut").toUpperCase())}</p>
      <h2 id="ex-pname">${esc(p.n)}</h2>
      <p class="ex-addr">${esc([addr, p.cu].filter(Boolean).join(" · "))}</p>
      ${ph ? `<p class="ex-addr">${esc(phoneText(ph))}</p>` : ""}
      ${here && p.la != null ? `<p class="ex-dist">${milesText(miles(here, p))} away</p>` : ""}
      <p class="ex-chips">${chips(p)}</p>
      <div class="ex-actions">
        <a class="btn ex-apple" href="${esc(apple)}" rel="noopener" target="_blank">Hours, photos &amp; more · Apple Maps</a>
        <div class="ex-act-row">
          <a href="${esc(dirs)}" rel="noopener" target="_blank">Directions</a>
          ${ph ? `<a href="tel:${esc(ph)}" aria-label="Call ${esc(phoneText(ph))}">Call</a>` : ""}
          ${site ? `<a href="${esc(site)}" rel="noopener nofollow" target="_blank">Website</a>` : ""}
          <button id="ex-save" type="button" aria-pressed="${saved.has(p.id)}">${saved.has(p.id) ? "Saved" : "Save"}</button>
        </div>
      </div>`;
    if (p.hc) {
      const kinds = kindNames(p);
      html += section("Hand-checked", (d.note ? `<p>${esc(d.note)}</p>` : "")
        + fact("On our lists", kinds.join(", ")) + fact("Known for", p.dish)
        + (d.sea ? fact("Season", d.sea) : p.seas ? fact("Season", "Seasonal; check before you go.") : "")
        + (p.f ? fact("At this address since", String(p.f)) : "") + fact("A branch of", p.br)
        + `<p class="ex-fine">${p.seas ? "Checked in business" : "Checked open"} in October 2026 against a 2025 or 2026 source: the place's own site or menu, local news, or a tourism listing.${p.seas ? " It's seasonal, so check its season." : ""} Hours and menus change, so check before you go.</p>`);
    }
    if (d.jbf || d.hon) {
      const lines = [...(d.jbf ? d.jbf.split("; ").map((x) => "James Beard: " + x) : []), ...(d.hon ? d.hon.split("; ") : [])];
      html += section("Honors", `<ul>${lines.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>` + (d.chef ? kv("Chef", d.chef) : "")
        + '<p class="ex-fine">Honors are facts, not ratings. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation.</p>');
    }
    if (d.fv) {   // the Farmington Valley Health District's own rating, posted at the restaurant; shown only here, never ranked
      const r = d.fv.r;
      html += section("Health rating · official",
        `<div class="ex-grade"><span class="rb rb-${esc(r)}" aria-hidden="true">${esc(r)}</span><span><b>${esc(RATING[r] || r)} (${esc(r)})</b>${d.fv.d ? `<span class="ex-rated">Rated ${esc(niceDate(d.fv.d))}</span>` : ""}</span></div>`
        + `<p class="ex-fine">The Farmington Valley Health District rates restaurants A (Excellent), B (Good), C (Fair), or U (Unsatisfactory) at each routine inspection, and each place must post its rating. This is the district's official rating as published. Only its ${FV_TOWNS.length} towns publish a current rating; Connecticut has no statewide inspection results.</p>`, " ex-fv");
    }
    if (p.host) html += section("Host venue", `<p>${esc(HOST_TEXT[p.host] || "Inside a casino, on tribal land.")}</p>`);
    html += section("How we know it's here", kv("Listed as", p.hc ? "Hand-checked" : TIER[p.t])
      + (p.t === 2 ? kv("License list", p.j === 2 ? "City of Hartford food license" : "Connecticut liquor permit") + kv("Permit", d.lk) + kv("Hartford license", d.hcl) : "")
      + (p.ch >= 2 ? kv("Locations in Connecticut", p.ch.toLocaleString("en-US")) : "") + `<p class="ex-fine">${esc(howWeKnow(p))}</p>`);
    // the App Store link once there is one (window.APP_STORE_URL, set by scripts/make-site.py); until then, say it's coming
    const appUrl = webLink(window.APP_STORE_URL || "");
    html += appUrl
      ? `<p class="ex-app">Save it on your phone: <a href="${esc(appUrl)}" rel="noopener">Get the free iPhone app</a></p>`
      : `<p class="ex-app"><a href="${BASE}/#download">The free iPhone app is coming soon</a></p>`;
    const panel = $("#ex-panel");
    panel.innerHTML = html;
    panel.hidden = false;
    panel.dataset.ready = D ? "1" : "0";
    document.body.classList.add("ex-open");
    setModal();
    $("#ex-close").onclick = () => closePlace();
    $("#ex-save").onclick = (e) => {
      if (saved.has(p.id)) saved.delete(p.id); else saved.add(p.id);
      store.set("saved", [...saved]);
      e.target.textContent = saved.has(p.id) ? "Saved" : "Save";
      e.target.setAttribute("aria-pressed", String(saved.has(p.id)));
      if (st.g === "saved") render();
    };
    panel.scrollTop = 0;
    $("#ex-close").focus();
    if (push) {   // one entry however many places are opened in a row
      if (!pushed) beforePush = location.hash;
      saveHash(!pushed); pushed = true;
    }
    if (!D) loadDetail().then(() => { if (st.p === p.id) openPlace(p, false); });
  }

  // fromHistory: Back (or Forward) already moved the history, so only the panel closes
  function closePlace(fromHistory = false) {
    const was = st.p;
    st.p = "";
    $("#ex-panel").hidden = true;
    document.body.classList.remove("ex-open");
    setModal();
    if (!fromHistory && pushed) { pushed = false; closingBack = true; history.back(); }
    else { pushed = false; saveHash(); }
    const row = was && document.querySelector(`.ex-row[data-i="${P.findIndex((p) => p.id === was)}"]`);
    if (row) row.focus();
  }

  // ---------------------------------------------------------------- map (canvas: the state, its 169 town lines, a dot per place)
  let SHAPES = null, cam = null;
  const LAT0 = 41.5, KX = Math.cos(LAT0 * Math.PI / 180);
  const proj = (lo, la) => [(lo + 72.7) * KX, -(la - LAT0)];

  function fitCam(w, h) {
    const [x0, y0] = proj(CT_BOX.w, CT_BOX.n), [x1, y1] = proj(CT_BOX.e, CT_BOX.s);
    const k = Math.min(w / (x1 - x0), h / (y1 - y0)) * 0.94;
    return { k, x: (w - (x1 - x0) * k) / 2 - x0 * k, y: (h - (y1 - y0) * k) / 2 - y0 * k };
  }

  async function drawMap() {
    const cv = $("#ex-map"), wrap = $("#ex-mapwrap");
    const w = wrap.clientWidth, h = wrap.clientHeight, dpr = window.devicePixelRatio || 1;
    if (!w || !h) return;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    if (!cam) cam = fitCam(w, h);
    if (!SHAPES) SHAPES = await fetchJSON(`${BASE}/data/ct_shapes.json`).catch(() => ({ state: [], towns: [] }));
    const c = cv.getContext("2d");
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    c.clearRect(0, 0, w, h);
    const X = (lo, la) => { const [x, y] = proj(lo, la); return [x * cam.k + cam.x, y * cam.k + cam.y]; };
    const ring = (r) => { r.forEach(([lo, la], i) => { const [x, y] = X(lo, la); i ? c.lineTo(x, y) : c.moveTo(x, y); }); c.closePath(); };
    c.fillStyle = "#ffffff";
    c.beginPath(); (SHAPES.state || []).forEach((poly) => poly.forEach(ring)); c.fill("evenodd");
    c.strokeStyle = "rgba(124,135,142,.55)"; c.lineWidth = 0.7;
    for (const t of SHAPES.towns || []) { c.beginPath(); t.c.forEach(ring); c.stroke(); }
    c.strokeStyle = "#7c878e"; c.lineWidth = 1.2;
    c.beginPath(); (SHAPES.state || []).forEach((poly) => poly.forEach(ring)); c.stroke();
    const pts = current.filter((p) => p.la != null);
    const r = Math.max(2.2, Math.min(5, 1.6 + cam.k / 160));
    for (const classic of [false, true]) {
      c.fillStyle = classic ? "#b3261e" : "#000e2f";
      c.strokeStyle = "#ffffff"; c.lineWidth = 1;
      for (const p of pts) {
        if (Boolean(p.hc) !== classic) continue;
        const [x, y] = X(p.lo, p.la);
        if (x < -5 || y < -5 || x > w + 5 || y > h + 5) continue;
        c.beginPath(); c.arc(x, y, classic ? r + 1 : r, 0, 6.2832); c.fill(); if (classic) c.stroke();
      }
    }
    if (here && inCT(here)) {
      const [x, y] = X(here.lo, here.la);
      c.fillStyle = "#2a4170"; c.strokeStyle = "#ffffff"; c.lineWidth = 2.5;
      c.beginPath(); c.arc(x, y, 6, 0, 6.2832); c.fill(); c.stroke();
    }
    $("#ex-maphint").textContent = pts.length ? `${pts.length.toLocaleString("en-US")} ${pts.length === 1 ? "place" : "places"} · tap a dot` : "No places to show";
  }

  function nearestDot(px, py) {
    let best = null, bd = 14 * 14;
    for (const p of current) {
      if (p.la == null) continue;
      const [x0, y0] = proj(p.lo, p.la), x = x0 * cam.k + cam.x, y = y0 * cam.k + cam.y;
      const d = (x - px) ** 2 + (y - py) ** 2;
      if (d < bd) { bd = d; best = p; }
    }
    return best;
  }

  // several places on the very same spot (one address, a food hall, a casino) can't be told apart by tapping: list them
  function showChooser(stack, x, y) {
    const box = $("#ex-chooser"), wrap = $("#ex-mapwrap");
    stack.sort((a, b) => a.n.localeCompare(b.n, "en", { sensitivity: "base" }));
    box.innerHTML = `<p id="ex-chooser-h">${stack.length} places at this spot</p><ul>${stack.map((p) => `<li><button type="button" data-i="${p.i}">${esc(p.n)}</button></li>`).join("")}</ul>`;
    box.hidden = false;
    box.style.left = Math.max(10, Math.min(x + 8, wrap.clientWidth - box.offsetWidth - 10)) + "px";
    box.style.top = Math.max(10, Math.min(y + 8, wrap.clientHeight - box.offsetHeight - 10)) + "px";
    box.querySelector("button").focus();
  }
  function hideChooser() { const box = $("#ex-chooser"); if (box && !box.hidden) { box.hidden = true; box.innerHTML = ""; } }

  function zoomAt(f, px, py) {
    const k = Math.min(Math.max(cam.k * f, 60), 120000);
    const s = k / cam.k;
    cam = { k, x: px - (px - cam.x) * s, y: py - (py - cam.y) * s };
    hideChooser();
    drawMap();
  }

  function mapEvents() {
    const cv = $("#ex-map");
    const ptrs = new Map();
    let moved = false, pinch0 = null, start = null;
    cv.addEventListener("wheel", (e) => { e.preventDefault(); const b = cv.getBoundingClientRect(); zoomAt(e.deltaY < 0 ? 1.25 : 0.8, e.clientX - b.left, e.clientY - b.top); }, { passive: false });
    cv.addEventListener("pointerdown", (e) => {
      cv.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, [e.clientX, e.clientY]);
      moved = false; pinch0 = null; start = [e.clientX, e.clientY];
      hideChooser();
    });
    cv.addEventListener("pointermove", (e) => {
      if (!ptrs.has(e.pointerId)) return;
      const prev = ptrs.get(e.pointerId);
      ptrs.set(e.pointerId, [e.clientX, e.clientY]);
      if (ptrs.size === 2) {
        const [a, b] = [...ptrs.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
        const r = cv.getBoundingClientRect();
        if (pinch0) zoomAt(d / pinch0, (a[0] + b[0]) / 2 - r.left, (a[1] + b[1]) / 2 - r.top);
        pinch0 = d; moved = true; return;
      }
      // a drag, however slow, is a drag: measured from where the finger went down, not move by move
      if (start && Math.hypot(e.clientX - start[0], e.clientY - start[1]) > 6) moved = true;
      cam.x += e.clientX - prev[0]; cam.y += e.clientY - prev[1]; drawMap();
    });
    const up = (e) => {
      ptrs.delete(e.pointerId);
      if (!moved && ptrs.size === 0) {
        const b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, p = nearestDot(x, y);
        if (p) {
          const stack = current.filter((o) => o.la === p.la && o.lo === p.lo);
          if (stack.length > 1) showChooser(stack, x, y); else openPlace(p);
        }
      }
      if (ptrs.size < 2) pinch0 = null;
    };
    cv.addEventListener("pointerup", up);
    cv.addEventListener("pointercancel", (e) => ptrs.delete(e.pointerId));
    $("#ex-chooser").addEventListener("click", (e) => { const b = e.target.closest("button[data-i]"); if (b) { hideChooser(); openPlace(P[+b.dataset.i]); } });
    $("#ex-zin").onclick = () => zoomAt(1.6, cv.clientWidth / 2, cv.clientHeight / 2);
    $("#ex-zout").onclick = () => zoomAt(0.625, cv.clientWidth / 2, cv.clientHeight / 2);
    let rt = null;
    window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { if (view === "map") { cam = null; drawMap(); } }, 150); });
    // the page narrowing for the side panel resizes the map without a window resize
    if ("ResizeObserver" in window) new ResizeObserver(() => { if (view === "map") drawMap(); }).observe($("#ex-mapwrap"));
  }

  function centerOn(pt) {
    const cv = $("#ex-map"), w = cv.clientWidth, h = cv.clientHeight;
    const k = 2500, [x, y] = proj(pt.lo, pt.la);
    cam = { k, x: w / 2 - x * k, y: h / 2 - y * k };
  }

  // ---------------------------------------------------------------- data, URL state, controls
  let FV_TOWNS = [];
  async function fetchJSON(url) { const r = await fetch(url); if (!r.ok) throw new Error(r.status + " " + url); return r.json(); }
  let detailPromise = null;
  function loadDetail() {
    detailPromise ||= fetchJSON(`${BASE}/data/detail.json`).then((d) => { D = d; }).catch(() => { D = []; });
    return detailPromise;
  }

  async function load() {
    const d = await fetchJSON(`${BASE}/data/core.json`);
    CAL = d.calibration || {}; SOURCES = d.sources || []; HOSTS = d.hosts || []; FV_TOWNS = d.fv_towns || [];
    T = Object.fromEntries(d.tags.map((t, i) => [t, 1 << i]));
    K = Object.fromEntries(d.kinds.map((k, i) => [k, 1 << i]));
    const LABEL = { apizza: "Apizza", "lobster roll": "Lobster roll", "clam shack": "Clam shack", "steamed cheeseburger": "Steamed cheeseburger",
      "burger icon": "Burger icon", "hot dog icon": "Hot dogs", diner: "Diner", "dairy bar": "Dairy bar", polish: "Polish", oldest: "Historic", grinder: "Grinders" };
    KIND_LABELS = d.kinds.map((k, i) => [1 << i, LABEL[k] || k]);
    const C = d.cols, n = C.id.length, towns = new Map(), vills = new Set();
    P = new Array(n);
    for (let i = 0; i < n; i++) {
      const city = C.c[i] == null ? null : d.cities[C.c[i]], vil = C.vi[i] == null ? null : d.villages[C.vi[i]];
      const cu = d.cuisines[C.cu[i]], brand = C.b[i] == null ? null : d.brands[C.b[i]], host = C.host[i] == null ? null : HOSTS[C.host[i]];
      P[i] = { i, id: C.id[i], n: C.n[i], c: city, vil, cu, brand, t: C.t[i], s: C.s[i], a: C.a[i], z: C.z[i], la: C.la[i], lo: C.lo[i],
        ch: C.ch[i] || 1, v: C.v[i] === 1, g: C.g[i] || 0, hc: C.hc[i] === 1, k: C.k[i] || 0, h: C.h[i] || 0, ip: C.ip[i],
        fs: C.fs ? C.fs[i] : null, f: C.f[i], host, seas: C.seas[i] === 1, j: C.j[i], dish: C.dish[i], br: C.br ? C.br[i] : null };
      if (city && !P[i].v) towns.set(city, (towns.get(city) || 0) + 1);
      if (vil) vills.add(vil);
    }
    N_TOWNS = towns.size;
    // AppModel.apply: the biggest town wins a shared spelling; a village key only when no town has it
    const byCount = [...towns.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    for (const [name] of byCount) { const k = normAddr(name); if (!(k in TOWN_KEYS)) TOWN_KEYS[k] = name; }
    for (const v of vills) { const k = normAddr(v); if (!(k in TOWN_KEYS)) VILLAGE_KEYS[k] = v; }
    PLACE_KEYS = [...Object.keys(TOWN_KEYS).map((k) => [k, "town", TOWN_KEYS[k]]), ...Object.keys(VILLAGE_KEYS).map((k) => [k, "village", VILLAGE_KEYS[k]])]
      .sort((a, b) => b[0].length - a[0].length || (a[1] === "town" ? 0 : 1) - (b[1] === "town" ? 0 : 1));
    $("#ex-town").innerHTML = '<option value="">All towns</option>' + [...towns.keys()].sort((a, b) => a.localeCompare(b)).map((t) => `<option>${esc(t)}</option>`).join("");
    const cuis = new Map();
    for (const p of P) if (!p.v) cuis.set(p.cu, (cuis.get(p.cu) || 0) + 1);
    $("#ex-cuisine").innerHTML = '<option value="">All kinds</option>' + [...cuis.entries()].sort((a, b) => b[1] - a[1]).map(([c, k]) => `<option value="${esc(c)}">${esc(c)} (${k.toLocaleString("en-US")})</option>`).join("");
  }

  function readHash() {
    const h = new URLSearchParams(location.hash.slice(1));
    const remembered = store.get("guide", "apizza");
    st.g = isGuide(h.get("g")) ? h.get("g") : isGuide(remembered) ? remembered : "apizza";
    st.q = h.get("q") || ""; st.town = h.get("town") || ""; st.cuisine = h.get("kind") || "";
    st.chains = h.get("chains") === "1"; st.conf = h.get("conf") === "1";
    st.sort = h.get("sort") || ""; st.p = h.get("p") || "";
    view = h.get("view") === "map" ? "map" : "list";
  }
  let lastHash = "";
  function saveHash(push = false) {
    const h = new URLSearchParams();
    h.set("g", st.g);
    if (st.q) h.set("q", st.q); if (st.town) h.set("town", st.town); if (st.cuisine) h.set("kind", st.cuisine);
    if (st.chains) h.set("chains", "1"); if (st.conf) h.set("conf", "1"); if (st.sort) h.set("sort", st.sort);
    if (view === "map") h.set("view", "map"); if (st.p) h.set("p", st.p);
    // filters and searches replace the entry (Back leaves the page); opening a place adds one, so Back closes it
    if (push) history.pushState({ place: true }, "", "#" + h.toString());
    else history.replaceState(history.state, "", "#" + h.toString());
    lastHash = location.hash;
    store.set("guide", st.g);
  }

  function locate() {
    if (!navigator.geolocation) { $("#ex-locmsg").textContent = "This browser can't share its location."; return; }
    $("#ex-locmsg").textContent = "Finding you…";
    // a fresh fix on every tap (the playbook's lesson: a fix from launch jumps back home after a drive)
    navigator.geolocation.getCurrentPosition((pos) => {
      here = { la: pos.coords.latitude, lo: pos.coords.longitude };
      locDenied = false;
      $("#ex-locmsg").textContent = inCT(here)
        ? "Sorted by distance from you. Your location stays in this browser."
        : "You're outside Connecticut, so distances are long. The map stays on the state. Your location stays in this browser.";
      st.sort = inCT(here) && GUIDES[st.g].sorts.includes("nearest") ? "nearest" : st.sort;
      if (view === "map" && inCT(here)) centerOn(here);
      shown = 100; render();
    }, (err) => {
      locDenied = err.code === 1;   // 1 = denied; 2 and 3 = no fix (unavailable, timed out)
      $("#ex-locmsg").textContent = locDenied
        ? "Location is blocked for this site. Allow it in your browser's settings to sort by distance."
        : "Couldn't get a fix on your location. Try again.";
      if (GUIDES[st.g].needsHere) render();
    }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 0 });
  }

  function setView(v) {
    view = v;
    document.querySelectorAll(".ex-view button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.v === v)));
    $("#ex-listwrap").hidden = v !== "list";
    $("#ex-mapwrap").hidden = v !== "map";
    render();
  }

  // a link, the address bar, Back or Forward changed the hash (our own updates set lastHash, so they're skipped)
  function onHistory() {
    if (closingBack) { closingBack = false; saveHash(); return; }   // the Back that closed a place: keep the current filters
    if (location.hash === lastHash) return;                         // also the hashchange that follows a handled popstate
    if (!location.hash.includes("=")) return;                       // "#main" from the skip link isn't app state
    if (pushed && location.hash === beforePush) { closePlace(true); return; }   // Back from an open place: close it, keep the filters
    pushed = false;
    readHash(); syncInputs(); shown = 100; setView(view);
    const p = st.p && P.find((x) => x.id === st.p);
    if (p) openPlace(p, false); else if (!$("#ex-panel").hidden) closePlace(true);
  }

  function controls() {
    document.querySelectorAll(".ex-guides button").forEach((b) => b.onclick = () => {
      st.g = b.dataset.g; st.sort = ""; shown = 100;
      if (st.g === "near" && !here) locate();
      render();
    });
    let t = null;
    $("#ex-q").addEventListener("input", (e) => { clearTimeout(t); t = setTimeout(() => { st.q = e.target.value; shown = 100; render(); }, 120); });
    $("#ex-sort").onchange = (e) => { st.sort = e.target.value; if (st.sort === "nearest" && !here) locate(); shown = 100; render(); };
    $("#ex-town").onchange = (e) => { st.town = e.target.value; shown = 100; render(); };
    $("#ex-cuisine").onchange = (e) => { st.cuisine = e.target.value; shown = 100; render(); };
    $("#ex-chains").onchange = (e) => { st.chains = e.target.checked; shown = 100; render(); };
    $("#ex-conf").onchange = (e) => { st.conf = e.target.checked; shown = 100; render(); };
    $("#ex-clear").onclick = () => { st.town = st.cuisine = ""; st.chains = st.conf = false; syncInputs(); shown = 100; render(); };
    $("#ex-locate").onclick = locate;
    $("#ex-more").onclick = () => { shown += 200; renderList(order()); };
    document.querySelectorAll(".ex-view button").forEach((b) => b.onclick = () => setView(b.dataset.v));
    $("#ex-list").addEventListener("click", (e) => { const b = e.target.closest(".ex-row"); if (b) openPlace(P[+b.dataset.i]); });
    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      if (!$("#ex-chooser").hidden) hideChooser(); else if (st.p) closePlace();
    });
    window.addEventListener("popstate", onHistory);
    window.addEventListener("hashchange", onHistory);
    mapEvents();
  }
  function syncInputs() {
    $("#ex-q").value = st.q; $("#ex-town").value = st.town; $("#ex-cuisine").value = st.cuisine;
    $("#ex-chains").checked = st.chains; $("#ex-conf").checked = st.conf;
  }

  // the guide pills scroll sideways on a phone: fade the edge while more are off to the right
  const pills = $(".ex-guides");
  const pillHint = () => pills.classList.toggle("more", pills.scrollLeft + pills.clientWidth < pills.scrollWidth - 4);
  pills.addEventListener("scroll", pillHint, { passive: true });
  window.addEventListener("resize", pillHint);
  pillHint();

  (async () => {
    readHash();
    try { await load(); } catch (e) { $("#ex-loading").textContent = "The restaurant list couldn't load. Refresh to try again."; return; }
    // the controls were drawn disabled with the page (so nothing moves now); switch them on
    $("#ex-app").querySelectorAll(":disabled").forEach((el) => { el.disabled = false; });
    $("#ex-app").setAttribute("aria-busy", "false");
    syncInputs(); controls();
    setView(view);
    const open = st.p && P.find((p) => p.id === st.p);
    if (open) { await loadDetail(); openPlace(open, false); }
    const idle = window.requestIdleCallback || ((f) => setTimeout(f, 200));
    idle(() => { loadDetail(); indexWhenIdle(); });
  })();
})();
