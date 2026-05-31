# Beatport

Beatport has no public/documented API, but the website runs on a v4 JSON API
(`https://api.beatport.com/v4`) that you can call with the OAuth access token your
own logged-in browser already holds.

## Getting an access token

You are **logged into beatport.com**. The site exposes its session (incl. the
bearer token) at `/api/auth/session`. In the devtools console:

```js
const s = await fetch('/api/auth/session').then(r => r.json());
s.token.accessToken;   // <-- bearer token for api.beatport.com
```

Pass that to `src/beatport.py`'s `Beatport(token)`. Tokens are short-lived;
re-fetch when calls start returning 401.

### Doing it from a browser-automation context

If you're driving a headless/remote browser (e.g. an MCP browser tool), the same
`fetch('/api/auth/session')` call works in-page. Cross-origin calls from
`beatport.com` to `api.beatport.com` are allowed with the bearer header, so you
can do the whole search→add loop inside one page context.

## Endpoints used

| Purpose | Call |
|---|---|
| Search | `GET /v4/catalog/search/?q=Artist+Title&type=tracks&per_page=3` |
| List your playlists | `GET /v4/my/playlists/?per_page=100` (follow `next`) |
| Playlist tracks | `GET /v4/my/playlists/{id}/tracks/?per_page=100` |
| Create playlist | `POST /v4/my/playlists/` `{"name": "..."}` |
| Bulk add | `POST /v4/my/playlists/{id}/tracks/bulk/` `{"track_ids": [...]}` |
| Remove track | `DELETE /v4/my/playlists/{id}/tracks/{playlist_track_id}/` |

## Gotchas

- **`api.beatport.com` ≠ `www.beatport.com/api`.** The latter returns the SPA
  HTML (you'll see `<!DOCTYPE` parse errors). Always hit `api.beatport.com/v4`.
- **Cloudflare blocks naive server-side requests** to the website. Use the
  in-browser session token approach, not a bare `requests` call from a server.
- **Fuzzy search lies.** `catalog/search` returns the nearest result even when
  the exact track isn't on Beatport. Always run results through genre QA
  (`src/qa.py`) and keep a blocklist of confirmed-wrong `track_id`s.
- **Removing tracks needs the `playlist_track_id`**, not the `track_id` — it's the
  `id` field on each item from the playlist tracks endpoint.
