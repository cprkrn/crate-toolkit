"""
rekordbox library access via pyrekordbox.

rekordbox 6+ stores everything in an encrypted SQLite database (master.db,
SQLCipher). pyrekordbox handles the key, giving read/write access — useful for:
  - pulling your existing tracks (for dedup) with BPM/key/genre
  - auto-sorting the collection into genre playlists

IMPORTANT: rekordbox must be CLOSED before writing, or the write silently fails.
Reads usually work while it's open (you'll see a warning).
"""
from collections import defaultdict


def load_db():
    from pyrekordbox import Rekordbox6Database
    return Rekordbox6Database()


def all_tracks(db):
    """Return [{title, artist, genre, bpm, key, path}] for the whole library."""
    out = []
    for t in db.get_content():
        artist = ""
        try:
            artist = t.Artist.Name if t.Artist else ""
        except Exception:
            pass
        bpm = t.BPM
        if bpm and bpm > 1000:      # some versions store BPM * 100
            bpm = round(bpm / 100, 1)
        out.append({
            "title": t.Title or "",
            "artist": artist,
            "genre": (t.Genre.Name if t.Genre else None),
            "bpm": bpm or None,
            "path": t.FolderPath or "",
        })
    return out


def sort_into_genre_playlists(db, parent_folder_name="Genre", commit=True):
    """Rebuild one playlist per genre under a folder. rekordbox must be CLOSED."""
    tracks = list(db.get_content())
    buckets = defaultdict(list)
    for t in tracks:
        g = (t.Genre.Name if t.Genre else "Other")
        buckets[g].append(t)

    folder = next((p for p in db.get_playlist() if p.Name == parent_folder_name), None)
    if folder is None:
        folder = db.create_playlist_folder(parent_folder_name)

    for name, items in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        pl = db.create_playlist(name, parent=folder)
        for t in items:
            db.add_to_playlist(pl, t)
    if commit:
        db.commit()
    return {g: len(v) for g, v in buckets.items()}
