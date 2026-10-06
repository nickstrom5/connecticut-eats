"""Connecticut signals from Google reviews written up to Sep 2021 (UCSD Google Local, review-Connecticut.json.gz)
-> data/ct/review_signals.parquet. Web leaderboard only: the app uses none of this.

For each Google listing: how many reviews mention apizza (or a white clam pie), a lobster roll (and hot buttered), fried or
whole-belly clams, a steamed cheeseburger, a hot dog, a grinder, or ice cream / a dairy bar, and the average star rating of just
those reviews. The file is streamed from UCSD and never stored (it is 413 MB).
"""
import os, re, gzip, json, time, collections, urllib.request
import pandas as pd
from common import CT

URL = "https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/review-Connecticut.json.gz"
SIG = {
    "apizza": re.compile(r"\bapizza\b|\bwhite clam (?:pie|pizza)\b|\bclam pie\b|\bnew haven(?:-| )style\b|\bcharred crust\b|\bcoal[- ]fired\b"),
    "lobster": re.compile(r"\blobster rolls?\b"),
    "hotbutter": re.compile(r"\b(?:hot|warm)(?: and |, )?buttered? lobster\b|\bbuttered lobster rolls?\b|\bhot lobster rolls?\b|\bconnecticut[- ]style lobster\b"),
    "clams": re.compile(r"\bfried clams?\b|\bwhole[- ]belly\b|\bclam strips?\b|\bclam chowder\b|\bclam fritters?\b|\bsteamers\b"),
    "steamed": re.compile(r"\bsteamed (?:cheese)?burgers?\b|\bsteamed cheeseburgers?\b|\bsteamers? burger\b"),
    "hotdog": re.compile(r"\bhot ?dogs?\b|\bfoot ?long\b|\bweenies?\b|\bfrankfurters?\b"),
    "grinder": re.compile(r"\bgrinders?\b"),
    "icecream": re.compile(r"\bice cream\b|\bsoft serve\b|\bdairy bar\b|\bsundaes?\b|\bcreemees?\b"),
}
PRE = re.compile(r"apizza|clam|lobster|steamed|hot ?dog|foot ?long|weenie|frankfurter|grinder|ice cream|soft serve|dairy bar|sundae|new haven|charred|coal|steamers|whole[- ]belly", re.I)

t = time.time()
cnt = collections.defaultdict(collections.Counter)
n = hit = 0
req = urllib.request.Request(URL, headers={"User-Agent": "ct-eats data pipeline (work-with-nick@gmail.com)"})
with urllib.request.urlopen(req, timeout=120) as resp, gzip.open(resp, "rt") as f:
    for line in f:
        n += 1
        if not PRE.search(line):
            continue
        d = json.loads(line)
        txt = (d.get("text") or "").lower()
        if not txt:
            continue
        g, rt = d.get("gmap_id"), d.get("rating")
        for k, rx in SIG.items():
            if rx.search(txt):
                c = cnt[g]; c[k] += 1
                if rt:
                    c[k + "_sum"] += rt
                hit += 1
        if n % 2_000_000 == 0:
            print(n, "reviews", round(time.time() - t), "s", flush=True)
rows = []
for g, c in cnt.items():
    row = {"gmap_id": g}
    for k in SIG:
        row["n_" + k] = c[k]
        row["r_" + k] = round(c[k + "_sum"] / c[k], 3) if c[k] else None
    rows.append(row)
pd.DataFrame(rows).to_parquet(os.path.join(CT, "review_signals.parquet"))
print("reviews read:", n, "| mentions:", hit, "| listings with a mention:", len(rows), "|", round(time.time() - t), "s")
