# rekordbox

rekordbox 6+ keeps its library in an encrypted SQLite database
(`master.db`, SQLCipher). You can't open it with plain `sqlite3` — you'll get
`file is not a database`. [pyrekordbox](https://github.com/dylanljones/pyrekordbox)
handles the decryption key.

```python
from pyrekordbox import Rekordbox6Database
db = Rekordbox6Database()
for t in db.get_content():
    print(t.Title, t.Artist.Name if t.Artist else "", t.BPM, t.Genre.Name if t.Genre else "")
```

## Uses in this toolkit

- **Dedup**: pull every track's title/artist as the "I already own this" set so
  the pipeline doesn't re-add things you have.
- **BPM / key enrichment**: your analyzed tracks have real measured BPM and key —
  more trustworthy than guessing from a catalog match.
- **Auto-sort**: rebuild one playlist per genre from the `Genre` field
  (`src/rekordbox_tools.py:sort_into_genre_playlists`).

## Gotchas

- **Close rekordbox before writing.** Reads work while it's open (you'll get a
  "Rekordbox is running" warning), but writes silently fail / can corrupt state.
  Quit the app, run your script, reopen.
- **BPM scaling**: some versions store BPM × 100 (e.g. `12300` → 123.0). Normalize.
- **Back up `master.db`** before any write. pyrekordbox is great but you're
  editing your live library.
- The DB path is OS-specific; pyrekordbox auto-discovers it. Never commit it — it
  contains your full library and local file paths.
