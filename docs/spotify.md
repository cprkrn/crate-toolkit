# Spotify

Spotify's Web API needs OAuth and won't authenticate with your web-player
session, so for read-only playlist scraping we avoid it entirely.

## ≤100 tracks: the embed page (no auth)

`https://open.spotify.com/embed/playlist/<id>` is public and ships the first
~100 tracks inside a `__NEXT_DATA__` script tag. `src/spotify.py:embed_tracks()`
parses it. This is the easy path and covers most playlists.

## >100 tracks: authenticated scroll-collect

The embed caps at ~100, and the full list is virtualized (only rendered rows
exist in the DOM). To get everything you need a **logged-in browser** and must
scroll, harvesting rows as they render:

```js
// run in the open.spotify.com playlist page (logged in)
const seen = new Map();
const grid = document.querySelector('[data-testid="playlist-tracklist"]');
const scroller = grid.closest('[data-overlayscrollbars-viewport]') || grid.parentElement;
const collect = () => document.querySelectorAll('[data-testid="tracklist-row"]').forEach(row => {
  const i = row.querySelector('[aria-colindex="1"]')?.textContent?.trim();
  const t = row.querySelector('[aria-colindex="2"] a[href*="/track/"]')?.textContent;
  const a = [...row.querySelectorAll('[aria-colindex="2"] a[href*="/artist/"]')]
              .map(x => x.textContent).join(', ');
  if (t && i) seen.set(i, { title: t, artists: a });
});
let last = 0, stable = 0;
for (let n = 0; n < 80; n++) {
  collect();
  if (seen.size === last) { if (++stable >= 4) break; } else stable = 0;
  last = seen.size; scroller.scrollTop += 700;
  await new Promise(r => setTimeout(r, 380));
}
JSON.stringify([...seen.values()]);
```

### Exfiltrating large results

If your automation channel truncates big return values, `console.log` the JSON in
~4 KB chunks and read them back from the console buffer:

```js
const data = JSON.stringify([...seen.values()]);
for (let i = 0; i < data.length; i += 4000) console.log(`CHUNK_${i/4000}::` + data.slice(i, i+4000));
```

## Song count

The header text contains `"<N> songs, …"` — match `/(\d+)\s+songs?,/` against
`document.querySelector('main').textContent`. (Don't trust `h1` — in the web
player that's the sidebar "Your Library".)
