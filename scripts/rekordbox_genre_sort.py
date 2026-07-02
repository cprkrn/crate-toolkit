#!/usr/bin/env python3
"""Reconcile every track in your rekordbox collection into a playlist under a
"Genre" folder, matched by each track's Genre tag.

- Idempotent: only adds a track to its genre playlist if it isn't already there,
  so re-running just folds in newly-imported tracks (no duplicates).
- ALIAS maps the platform's verbose sub-genres onto the playlists you actually keep
  (e.g. "Techno (Peak Time / Driving)" -> "Techno"). Edit it for your own crates.
- EXCLUDE keeps non-tracks (sampler loops etc.) out of your genre crates.
- Auto-backs-up master.db before writing.

SAFETY: rekordbox must be CLOSED (writes fail/corrupt while it runs).

Run:  python rekordbox_genre_sort.py [--dry] [--folder Genre]
"""
import argparse, os, shutil, sys, time

# Map verbose/aliased genre tags -> the lowercase name of the playlist you keep.
# Extend this to match your own genre-playlist set.
ALIAS = {
    "techno (peak time / driving)": "techno",
    "techno (raw / deep / hypnotic)": "techno",
    "electro (classic / detroit / modern)": "techno",
    "melodic house & techno": "deep house",
    "organic house / downtempo": "deep house",
    "progressive house": "house",
    "afro house": "house",
    "breaks / breakbeat / uk bass": "uk garage / bassline",
}
EXCLUDE = {"loop samples"}  # genres to keep OUT of genre crates (sample packs, etc.)


def backup_db():
    try:
        from pyrekordbox.config import get_config
        dbp = get_config("rekordbox6", "db_path")
    except Exception:
        dbp = None
    if not dbp:  # fall back to the default location
        cand = os.path.expanduser("~/Library/Pioneer/rekordbox/master.db")
        dbp = cand if os.path.exists(cand) else None
    if dbp and os.path.exists(dbp):
        bak = f"{dbp}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(dbp, bak)
        print(f"backed up -> {bak}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="report only, no writes")
    ap.add_argument("--folder", default="Genre", help='parent folder name (default "Genre")')
    args = ap.parse_args()

    from pyrekordbox import Rekordbox6Database
    if not args.dry:
        backup_db()
    db = Rekordbox6Database()

    pls = list(db.get_playlist())
    folder = next((p for p in pls if (p.Name or "") == args.folder
                   and getattr(p, "Attribute", 0) == 1), None)
    if not folder:
        sys.exit(f'No "{args.folder}" folder found — create it + your genre playlists first.')
    gmap = {(p.Name or "").strip().lower(): p for p in pls
            if getattr(p, "ParentID", None) == folder.ID and getattr(p, "Attribute", 0) == 0}
    other = gmap.get("other")
    print("genre playlists:", sorted(gmap))

    members = {}
    for name, p in gmap.items():
        try:
            members[name] = {sp.ContentID for sp in p.Songs}
        except Exception:
            members[name] = set()

    added = {}
    for c in db.get_content():
        g = ((c.Genre.Name if getattr(c, "Genre", None) else "") or "").strip().lower()
        if g in EXCLUDE:
            continue
        target = gmap.get(g) or gmap.get(ALIAS.get(g, "")) or other
        if not target:
            continue
        tname = (target.Name or "").lower()
        if c.ID in members[tname]:
            continue
        members[tname].add(c.ID)
        added[target.Name] = added.get(target.Name, 0) + 1
        if not args.dry:
            db.add_to_playlist(target, c)

    if not args.dry:
        db.commit()
    total = sum(added.values())
    print(f"{'[dry] would add' if args.dry else 'added'} {total} tracks:")
    for g, n in sorted(added.items(), key=lambda kv: -kv[1]):
        print(f"   +{n:>3}  {g}")


if __name__ == "__main__":
    main()
