#!/usr/bin/env python3
"""Build a Beatport playlist from a list of tracks.

Input JSON is a list of either:
  - {"artist": "...", "name": "..."}  -> each is searched + fuzzy-matched to a Beatport
    track_id (artist-overlap guard, so a same-title/different-artist track can't match), or
  - {"track_id": 12345}               -> added directly.

Not-found tracks are reported so you can source them elsewhere (Bandcamp/SoundCloud).

Auth: export BEATPORT_TOKEN with a short-lived token from a logged-in beatport.com tab:
  fetch('/api/auth/session').then(r=>r.json()).then(j=>console.log(j.token.accessToken))

Run:  BEATPORT_TOKEN=... python beatport_playlist.py "<playlist name>" tracks.json
"""
import json, os, re, sys, time
import requests
from rapidfuzz import fuzz
from _util import normalize, primary_artist

API = "https://api.beatport.com/v4"
THRESHOLD = 84  # rapidfuzz token_set_ratio cutoff for a confident match


def headers():
    tok = os.environ.get("BEATPORT_TOKEN") or os.environ.get("BPTOK")
    if not tok:
        sys.exit("Set BEATPORT_TOKEN (see docstring).")
    return {"Authorization": f"Bearer {tok}", "Accept": "application/json",
            "Content-Type": "application/json"}


def clean(s):
    s = re.sub(r"[\(\[][^\)\]]*[\)\]]", " ", s)
    s = re.sub(r"(?i)\b(feat|ft|featuring)\b.*", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def search(h, q):
    if not q:
        return []
    r = requests.get(f"{API}/catalog/search/", headers=h, params={"q": q, "per_page": 20}, timeout=30)
    if r.status_code == 401:
        sys.exit("401 — token expired; grab a fresh one and rerun.")
    if r.status_code != 200:
        return []
    d = r.json()
    return d.get("tracks") or d.get("results") or []


def match(h, artist, name):
    tracks = search(h, clean(f"{primary_artist(artist)} {name}")) or search(h, clean(name))
    qn = normalize(f"{artist} {name}")
    aset = set(normalize(primary_artist(artist)).split())
    best, score = None, 0
    for t in tracks:
        ta = ", ".join(a.get("name", "") for a in t.get("artists", []))
        sc = fuzz.token_set_ratio(qn, normalize(f"{ta} {t.get('name','')}"))
        if sc > score and (aset & set(normalize(ta).split())):
            best, score = t, sc
    return best if best and score >= THRESHOLD else None


def main():
    if len(sys.argv) < 3:
        sys.exit('usage: beatport_playlist.py "<name>" tracks.json')
    name, path = sys.argv[1], sys.argv[2]
    h = headers()
    items = json.load(open(path))

    ids, missing = [], []
    for it in items:
        if it.get("track_id"):
            ids.append(it["track_id"])
            continue
        m = match(h, it.get("artist", ""), it.get("name", ""))
        if m:
            ids.append(m["id"])
        else:
            missing.append(f"{it.get('artist')} - {it.get('name')}")
        time.sleep(0.1)
    ids = list(dict.fromkeys(ids))  # dedup, keep order
    print(f"matched {len(ids)} / {len(items)}; not found: {len(missing)}")
    for m in missing:
        print(f"   ✗ {m}")
    if not ids:
        return

    r = requests.post(f"{API}/my/playlists/", headers=h, json={"name": name}, timeout=30)
    if r.status_code not in (200, 201):
        sys.exit(f"create failed {r.status_code}: {r.text[:200]}")
    pid = r.json().get("id")
    added = 0
    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        rr = requests.post(f"{API}/my/playlists/{pid}/tracks/bulk/", headers=h,
                           json={"track_ids": batch}, timeout=30)
        if rr.status_code in (200, 201):
            added += len(batch)
        time.sleep(0.3)
    print(f"built '{name}' (id={pid}) with {added} tracks.")


if __name__ == "__main__":
    main()
