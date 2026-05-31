"""
Spotify playlist → track list.

Two strategies:
  1. embed_tracks(playlist_id)  — no auth, works for the first ~100 tracks via the
     public /embed/playlist/<id> page's __NEXT_DATA__ JSON. Good enough for most.
  2. For playlists >100 tracks you need a logged-in browser session and must scroll
     the virtualized tracklist, collecting [data-testid="tracklist-row"] as you go.
     See docs/spotify.md for the browser-side snippet (it can't be done with requests
     because the full list is lazy-loaded and the web API needs OAuth).

Returns: list of {"title": str, "artists": str}
"""
import json
import re
import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def embed_tracks(playlist_id: str):
    """Scrape up to ~100 tracks from the public embed page. No auth required."""
    url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    html = requests.get(url, headers={"User-Agent": UA}, timeout=20).text
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', html, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find __NEXT_DATA__ on embed page")
    data = json.loads(m.group(1))

    def find_tracklist(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get("trackList"), list):
                return obj["trackList"]
            for v in obj.values():
                r = find_tracklist(v)
                if r:
                    return r
        elif isinstance(obj, list):
            for v in obj:
                r = find_tracklist(v)
                if r:
                    return r
        return None

    tl = find_tracklist(data) or []
    return [{"title": t.get("title", ""), "artists": t.get("subtitle", "")} for t in tl]


if __name__ == "__main__":
    import sys
    for t in embed_tracks(sys.argv[1]):
        print(f"{t['artists']} - {t['title']}")
