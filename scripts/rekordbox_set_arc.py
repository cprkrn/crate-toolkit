#!/usr/bin/env python3
"""Auto-build an ordered rekordbox playlist shaped as a DJ set "arc" — pulled from
your own library by genre + BPM.

Define PHASES (label, genres, bpm range, how many). Each phase picks a BPM-spread
selection from those genres; phases are concatenated into one ordered playlist so
energy ramps the way you want. Edit PHASES for the vibe you're going for — the
default below is a gentle "warm open -> housey middle -> deep/hypnotic -> close."

Auto-backs-up master.db. SAFETY: rekordbox must be CLOSED.

Run:  python rekordbox_set_arc.py "<playlist name>" [--folder "<parent folder>"]
"""
import argparse, os, shutil, sys, time

# Verbose sub-genre -> canonical bucket (edit to your library's genre tags).
ALIAS = {
    "techno (peak time / driving)": "Techno", "techno (raw / deep / hypnotic)": "Techno",
    "electro (classic / detroit / modern)": "Techno", "melodic house & techno": "Deep House",
    "organic house / downtempo": "Deep House", "progressive house": "House", "afro house": "House",
    "breaks / breakbeat / uk bass": "UK Garage / Bassline",
}
# (label, {genres}, bpm_low, bpm_high, count)
PHASES = [
    ("open",  {"Deep House", "Electronica"},                 108, 118, 7),
    ("warm",  {"Nu Disco / Disco", "House", "Indie Dance"},  118, 124, 9),
    ("deep",  {"Minimal / Deep Tech", "Tech House"},         123, 128, 8),
    ("close", {"Techno"},                                    126, 134, 4),
]


def backup_db():
    try:
        from pyrekordbox.config import get_config
        dbp = get_config("rekordbox6", "db_path")
    except Exception:
        dbp = None
    dbp = dbp or (os.path.expanduser("~/Library/Pioneer/rekordbox/master.db"))
    if dbp and os.path.exists(dbp):
        shutil.copy2(dbp, f"{dbp}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        print("backed up master.db")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--folder", default=None, help="optional parent folder name")
    args = ap.parse_args()

    from pyrekordbox import Rekordbox6Database
    backup_db()
    db = Rekordbox6Database()

    rows = []
    for c in db.get_content():
        g = ((c.Genre.Name if getattr(c, "Genre", None) else "") or "").strip()
        gg = ALIAS.get(g.lower(), g)
        bpm = getattr(c, "BPM", None)
        bpm = round(bpm / 100, 1) if bpm and bpm > 1000 else (bpm or 0)
        if c.Title:
            rows.append({"c": c, "g": gg, "bpm": bpm})

    used, ordered = set(), []
    for label, genres, lo, hi, n in PHASES:
        pool = sorted([r for r in rows if r["g"] in genres and lo <= r["bpm"] < hi
                       and r["c"].ID not in used], key=lambda x: x["bpm"])
        if len(pool) > n:
            step = len(pool) / n
            pool = [pool[int(i * step)] for i in range(n)]
        for r in pool:
            used.add(r["c"].ID)
        ordered += pool
        print(f"{label}: {len(pool)} tracks")

    pls = list(db.get_playlist())
    parent = None
    if args.folder:
        parent = next((p for p in pls if (p.Name or "") == args.folder
                       and getattr(p, "Attribute", 0) == 1), None)
    existing = next((p for p in pls if (p.Name or "") == args.name), None)
    if existing:
        for sp in list(existing.Songs):
            db.remove_from_playlist(existing, sp)
        pl = existing
    else:
        pl = db.create_playlist(args.name, parent=parent) if parent else db.create_playlist(args.name)
    for r in ordered:
        db.add_to_playlist(pl, r["c"])
    db.commit()
    print(f"\nbuilt '{args.name}' with {len(ordered)} tracks (BPM {ordered[0]['bpm']} -> {ordered[-1]['bpm']}).")


if __name__ == "__main__":
    main()
