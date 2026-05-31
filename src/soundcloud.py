"""
SoundCloud playlist → track list, via the undocumented api-v2.

SoundCloud's web app talks to api-v2.soundcloud.com with a `client_id` that is
embedded in one of its JS bundles. We scrape the client_id, resolve the playlist
to get its track stub IDs, then batch-fetch full track metadata.

Returns: list of {"title": str, "user": str}  (title often "Artist - Track")
"""
import json
import re
import time
import requests

UA = "Mozilla/5.0 (compatible; crate-toolkit/1.0)"


def get_client_id() -> str:
    """Extract a working client_id from SoundCloud's JS bundles."""
    home = requests.get("https://soundcloud.com/", headers={"User-Agent": UA}, timeout=20).text
    scripts = re.findall(r'https://a-v2\.sndcdn\.com/assets/[^"]+\.js', home)
    for src in reversed(scripts):  # the client_id tends to live in a later bundle
        js = requests.get(src, headers={"User-Agent": UA}, timeout=20).text
        m = re.search(r'client_id:"([a-zA-Z0-9]{32})"', js)
        if m:
            return m.group(1)
    raise RuntimeError("Could not extract a SoundCloud client_id")


def playlist_tracks(set_url: str, client_id: str | None = None):
    cid = client_id or get_client_id()
    meta = requests.get(
        "https://api-v2.soundcloud.com/resolve",
        params={"url": set_url, "client_id": cid},
        headers={"User-Agent": UA}, timeout=20,
    ).json()
    ids = [str(t["id"]) for t in meta.get("tracks", [])]

    out = []
    for i in range(0, len(ids), 30):  # api-v2 caps the ids batch
        chunk = ",".join(ids[i:i + 30])
        data = requests.get(
            "https://api-v2.soundcloud.com/tracks",
            params={"ids": chunk, "client_id": cid},
            headers={"User-Agent": UA}, timeout=20,
        ).json()
        for t in data:
            out.append({"title": t.get("title", ""),
                        "user": t.get("user", {}).get("username", "")})
        time.sleep(0.4)  # be polite
    return out


if __name__ == "__main__":
    import sys
    for t in playlist_tracks(sys.argv[1]):
        print(f"{t['user']} :: {t['title']}")
