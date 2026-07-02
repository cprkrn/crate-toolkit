#!/usr/bin/env python3
"""Find duplicate tracks in your rekordbox collection.

- TRUE dupes: same artist + same title + same version, but 2+ separate files
  (e.g. you own both the MP3 and the AIFF). These are the ones worth cleaning.
- Version pairs: same song, different mix (Original vs Extended vs a remix) —
  usually intentional, listed separately as FYI.

Read-only. Remove the ones you don't want in rekordbox itself
(right-click -> Remove from Collection) — safest for the library's sync state.

Run:  python rekordbox_dupes.py
"""
import os
from collections import defaultdict
from _util import normalize, primary_artist


def main():
    from pyrekordbox import Rekordbox6Database
    db = Rekordbox6Database()
    strict, loose = defaultdict(list), defaultdict(list)
    for c in db.get_content():
        ar = (c.Artist.Name if getattr(c, "Artist", None) else "") or ""
        ti = c.Title or ""
        fp = getattr(c, "FolderPath", "") or ""
        ext = fp.rsplit(".", 1)[-1].lower() if "." in fp else "?"
        rec = {"id": c.ID, "ar": ar, "ti": ti, "ext": ext}
        strict[normalize(primary_artist(ar)) + " | " + normalize(ti, drop_mix=False)].append(rec)
        loose[normalize(primary_artist(ar)) + " | " + normalize(ti, drop_mix=True)].append(rec)

    true_dupes = [v for v in strict.values() if len({x["id"] for x in v}) > 1]
    strict_ids = {x["id"] for grp in true_dupes for x in grp}
    version_pairs = [v for v in loose.values()
                     if len({x["id"] for x in v}) > 1
                     and not all(x["id"] in strict_ids for x in v)]

    print(f"=== TRUE DUPES (same track+version, 2+ files): {len(true_dupes)} ===")
    for g in true_dupes:
        print(f"• {g[0]['ar']} - {g[0]['ti']}")
        for r in g:
            print(f"     [{r['ext']}] id={r['id']}")
    print(f"\n=== same song, different version (FYI, not dupes): {len(version_pairs)} ===")
    for g in version_pairs:
        print("• " + " / ".join(sorted({r["ti"] for r in g})) + f"  — {g[0]['ar']}")


if __name__ == "__main__":
    main()
