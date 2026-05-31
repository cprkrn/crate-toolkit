# Discogs

## Release metadata (public, no auth)

`GET https://api.discogs.com/releases/<id>` returns artists, title, year, label,
`genres`, `styles`, and the full `tracklist`. This is how you tag a vinyl
collection by genre. **Discogs does not store BPM** — there is no BPM field, so
you'll source that elsewhere (your rekordbox library, or a catalog match).

## Your collection / wantlist

- A **public** collection is readable at
  `GET https://api.discogs.com/users/<user>/collection/folders/0/releases`.
- A **private** collection returns 403 from the anonymous API. Either flip it
  public, use a personal access token, or export it to CSV from the web UI
  (Collection → ⋯ → Export) and read that. The CSV gives you `release_id`s; feed
  those to the release endpoint to enrich with genre/style.
- **Wantlist** adds are a logged-in action: the cleanest automation is clicking
  the "Add to Wantlist" button on each release page in a browser session.

## Marketplace (Cloudflare-protected)

The `/sell/release/<id>` marketplace pages are behind Cloudflare. Plain
`urllib`/`requests` and even a Chrome User-Agent get **403**. The combination
that works from a script:

```
HTTP/1.1  +  Sec-Fetch-Mode: navigate  +  Sec-Fetch-Site: none  +  realistic UA
```

(`src/discogs.py:marketplace_listings`). Parse the
`<tr class="...shortcut_navigable...">` rows for price, seller, condition, and
`Ships From`. Filter by `Ships From: <country>` to find domestic sellers and
avoid international shipping. If you still hit 403, fall back to a real browser.

Be gentle — sleep between requests. This is scraping, not an API.
