# crate-toolkit

A toolkit for DJs who pull inspiration from streaming playlists and want to turn that into an organized, deduplicated record/track library across **Beatport**, **rekordbox**, **Discogs**, **Bandcamp**, **Spotify**, and **SoundCloud**.

It started as a personal workflow ("I have 13 reference playlists across Spotify + SoundCloud and want them as clean Beatport crates without buying duplicates"). The pieces below are generic and reusable — point them at your own accounts and playlists.

> **Ethics / legal:** These tools read and organize *metadata* (track names, artists, BPM, genre) and automate playlist management on services **you are logged into**. They do **not** rip audio, bypass DRM, or download copyrighted tracks. Buy your music. Respect each platform's Terms of Service and rate limits.

---

## What it does

| Capability | Module |
|---|---|
| Parse a Spotify playlist → track list | `src/spotify.py` |
| Parse a SoundCloud playlist → track list | `src/soundcloud.py` |
| Search Beatport catalog, build/manage playlists | `src/beatport.py` |
| Read/write the rekordbox library (genre sort, BPM, dedup) | `src/rekordbox_tools.py` |
| Look up Discogs releases / collection / marketplace | `src/discogs.py` |
| Dedup tracks across sources + library + blocklist | `src/dedup.py` |
| Genre-based QA (flag wrong fuzzy matches) | `src/qa.py` |

## Architecture

```
 Reference playlists (Spotify / SoundCloud)
            │  scrape track lists
            ▼
     Normalize + dedup  ◄── existing library (rekordbox) + blocklist
            │
            ▼
   Beatport catalog search (fuzzy match → track_id)
            │
            ▼
   Genre QA (drop wrong-genre matches)
            │
            ▼
   Build Beatport playlists  +  organized notes (Discogs / BPM)
```

## Quick start

```bash
git clone https://github.com/<you>/crate-toolkit
cd crate-toolkit
pip install -r requirements.txt
cp examples/config.example.yaml config.yaml   # edit with your IDs (gitignored)
```

Each module is runnable and documented. See `docs/` for the platform-specific techniques (these are the interesting bits — how to talk to each service's undocumented endpoints from a logged-in browser session).

## Design notes

- **No credentials in code.** Tokens are captured at runtime from your own logged-in browser session, never stored in the repo. `config.yaml` (your playlist IDs etc.) is gitignored.
- **Fuzzy matching lies.** Catalog search returns the *closest* result, not always the right one. `src/qa.py` cross-checks genre metadata to catch obvious mismatches (a Hip-Hop track matched into a House crate), and a persistent blocklist prevents re-adding known-bad matches on future runs.
- **Idempotent.** Re-running only adds genuinely new tracks — everything dedupes against your existing library by ID.

## Docs

- [docs/spotify.md](docs/spotify.md) — scraping playlists (embed JSON, authenticated scroll, console exfil)
- [docs/soundcloud.md](docs/soundcloud.md) — api-v2 + client_id extraction
- [docs/beatport.md](docs/beatport.md) — search + playlist API
- [docs/rekordbox.md](docs/rekordbox.md) — reading the encrypted master.db with pyrekordbox
- [docs/discogs.md](docs/discogs.md) — release API, collection, marketplace (US-shipping filter)

## License

MIT — see [LICENSE](LICENSE).
