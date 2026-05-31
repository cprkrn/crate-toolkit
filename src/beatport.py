"""
Beatport: search the catalog and manage your library playlists.

Beatport has no public API, but the website's v4 API is usable with the OAuth
access token your browser already holds once you're logged in. You capture that
token from the logged-in session and pass it here.

How to get the token (run in the devtools console on beatport.com, logged in):

    const s = await fetch('/api/auth/session').then(r => r.json());
    copy(s.token.accessToken);   // paste into BEATPORT_TOKEN

Then everything below is plain HTTPS against https://api.beatport.com/v4.
See docs/beatport.md for the browser-automation version of the same flow.
"""
import time
import requests

BASE = "https://api.beatport.com/v4"


class Beatport:
    def __init__(self, access_token: str):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {access_token}"

    # ---- catalog ----
    def search_track(self, query: str):
        """Return the first catalog match for a free-text 'Artist Title' query."""
        r = self.s.get(f"{BASE}/catalog/search/",
                       params={"q": query, "type": "tracks", "per_page": 3}, timeout=20)
        r.raise_for_status()
        items = r.json().get("tracks", [])
        if not items:
            return None
        t = items[0]
        return {
            "id": t["id"],
            "name": t["name"],
            "mix": t.get("mix_name"),
            "artists": ", ".join(a["name"] for a in t["artists"]),
            "genre": (t.get("genre") or {}).get("name"),
            "bpm": t.get("bpm"),
        }

    # ---- playlists ----
    def my_playlists(self):
        out, url = [], f"{BASE}/my/playlists/?per_page=100"
        while url:
            j = self.s.get(url, timeout=20).json()
            out += [{"id": p["id"], "name": p["name"], "count": p["track_count"]}
                    for p in j.get("results", [])]
            url = j.get("next")
        return out

    def playlist_track_ids(self, playlist_id: int):
        ids, url = [], f"{BASE}/my/playlists/{playlist_id}/tracks/?per_page=100"
        while url:
            j = self.s.get(url, timeout=20).json()
            ids += [it["track"]["id"] for it in j.get("results", [])]
            url = j.get("next")
        return ids

    def create_playlist(self, name: str) -> int:
        r = self.s.post(f"{BASE}/my/playlists/", json={"name": name}, timeout=20)
        r.raise_for_status()
        return r.json()["id"]

    def add_tracks(self, playlist_id: int, track_ids: list[int]):
        """Bulk-add in chunks of 50."""
        added = 0
        for i in range(0, len(track_ids), 50):
            chunk = track_ids[i:i + 50]
            r = self.s.post(f"{BASE}/my/playlists/{playlist_id}/tracks/bulk/",
                            json={"track_ids": chunk}, timeout=30)
            if r.ok:
                added += len(chunk)
            time.sleep(0.3)
        return added
