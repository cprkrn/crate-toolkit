# SoundCloud

SoundCloud's web app uses an undocumented `api-v2.soundcloud.com`. All you need
is a `client_id`, which is embedded in one of the JS bundles the site loads.

## Extracting a client_id

1. Fetch `https://soundcloud.com/`
2. Find the `https://a-v2.sndcdn.com/assets/*.js` script URLs
3. Fetch them (the id tends to be in a later bundle) and regex:
   `client_id:"([a-zA-Z0-9]{32})"`

`src/soundcloud.py:get_client_id()` does this. The id rotates occasionally — just
re-extract when calls start failing.

## Resolving a playlist

```
GET https://api-v2.soundcloud.com/resolve?url=<set_url>&client_id=<cid>
```

returns playlist metadata including `track_count` and a `tracks` array of stubs
(IDs only for tracks past the first page). Batch-hydrate the IDs:

```
GET https://api-v2.soundcloud.com/tracks?ids=<id,id,...>&client_id=<cid>   (≤~30 ids)
```

## Notes

- Titles are free-form; many are `"Artist - Track"`, others put the artist in the
  uploader (`user.username`). Normalize accordingly before matching to Beatport.
- SoundCloud playlists drift (re-curation, bootleg edits with junk titles). Run
  everything through genre QA so a `MACARENA` bootleg doesn't end up in your crate.
- Rate-limit yourself (a short sleep between batches). The endpoints are not meant
  for heavy automated use.
