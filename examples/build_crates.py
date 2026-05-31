"""
End-to-end example: reference playlists -> deduped, genre-QA'd Beatport crates.

Run:  python examples/build_crates.py
(after copying config.example.yaml -> config.yaml and setting BEATPORT_TOKEN)

This is a reference flow, not a turnkey CLI — read it, adapt the bucket logic to
your own taste, and wire in your token capture.
"""
import os
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import spotify, soundcloud, beatport, qa            # noqa: E402
from dedup import dedup_by_id                        # noqa: E402

cfg = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "..", "config.yaml")))
bp = beatport.Beatport(os.environ["BEATPORT_TOKEN"])  # see src/beatport.py

# 1. gather source tracks (bucket -> list of "Artist Title" queries)
queries = {"tech": [], "minimal": []}
# ... map each source playlist into a bucket however you like ...
for pid in cfg["sources"]["spotify"]:
    for t in spotify.embed_tracks(pid):
        queries["minimal"].append(f"{t['artists']} {t['title']}")
for url in cfg["sources"]["soundcloud"]:
    for t in soundcloud.playlist_tracks(url):
        queries["tech"].append(t["title"])

# 2. existing-library ids (dedup) + blocklist
existing = set()
for pl in bp.my_playlists():
    existing |= set(bp.playlist_track_ids(pl["id"]))
blocklist = set(cfg.get("blocklist", []))

# 3. search + dedup + genre QA per bucket
for bucket, qs in queries.items():
    matched = [m for q in qs if (m := bp.search_track(q))]
    fresh = dedup_by_id(matched, existing, blocklist)
    clean, suspect = qa.split_matches(fresh)
    print(f"{bucket}: {len(clean)} new clean, {len(suspect)} suspect (review)")

    # 4. add clean tracks, splitting at max_per_playlist
    cap = cfg["beatport"]["max_per_playlist"]
    base = cfg["beatport"]["buckets"][bucket]
    for i in range(0, len(clean), cap):
        name = f"{base} {chr(ord('A') + i // cap)}"   # "Tech A", "Tech B", ...
        pid = bp.create_playlist(name)
        bp.add_tracks(pid, [t["id"] for t in clean[i:i + cap]])
        print(f"  created {name} ({len(clean[i:i+cap])} tracks)")

    # 5. suspects -> review (and append confirmed-wrong ids to config blocklist)
    for s in suspect:
        print(f"  SUSPECT [{s['genre']}] {s['artists']} - {s['name']}  (id {s['id']})")
