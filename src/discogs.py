"""
Discogs: release metadata, your collection, and marketplace listings.

- Individual release lookups (/releases/<id>) are public — no auth.
- Your *collection* may be private; if so, export it to CSV from the Discogs
  web UI (Collection -> ... -> Export) and read that, or pass a personal access
  token. Genre/style come from the release endpoint; Discogs does NOT store BPM.
- Marketplace pages are Cloudflare-protected; plain requests/urllib get 403.
  The trick that works is HTTP/1.1 + browser-like Sec-Fetch headers (below).
"""
import re
import time
import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def release(release_id: int) -> dict:
    """Public release metadata: artists, title, genres, styles, label, tracklist."""
    r = requests.get(f"https://api.discogs.com/releases/{release_id}",
                     headers={"User-Agent": UA, "Accept": "application/json"}, timeout=20)
    r.raise_for_status()
    d = r.json()
    clean = lambda s: re.sub(r"\s*\(\d+\)", "", s)
    return {
        "id": d["id"],
        "artist": clean(", ".join(a["name"] for a in d.get("artists", []))),
        "title": d.get("title", ""),
        "year": d.get("year"),
        "label": clean((d.get("labels") or [{}])[0].get("name", "")),
        "genres": d.get("genres", []),
        "styles": d.get("styles", []),
        "tracklist": [{"pos": t.get("position"), "title": t.get("title")}
                      for t in d.get("tracklist", []) if t.get("type_") == "track"],
    }


# Cloudflare-protected marketplace pages: the working combination is
# requests with HTTP/1.1 + navigate-style Sec-Fetch headers.
_MARKET_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


def marketplace_listings(release_id: int, ships_to=None):
    """
    Scrape marketplace listings for a release. `ships_to` (e.g. 'United States')
    filters by seller location. Returns [{price_usd, ship_usd, seller, condition,
    ships_from, url}]. Be gentle — sleep between calls.
    """
    url = (f"https://www.discogs.com/sell/release/{release_id}"
           f"?sort=price%2Casc&limit=50")
    # NOTE: requests must use HTTP/1.1; if you still get 403, use a real browser.
    html = requests.get(url, headers=_MARKET_HEADERS, timeout=25).text
    rows = re.findall(r'<tr[^>]*shortcut_navigable[^>]*>.*?</tr>', html, re.DOTALL)
    out = []
    for row in rows:
        m = re.search(r'href="(/sell/item/\d+)"', row)
        if not m:
            continue
        get = lambda pat: (re.search(pat, row, re.DOTALL) or [None, None])[1] \
            if re.search(pat, row, re.DOTALL) else None
        ships_from = get(r'Ships From:</span>\s*([A-Za-z][^<\n]*)')
        price = get(r'class="converted_price"[^>]*>\s*about\s+\$?([\d,.]+)') \
            or get(r'data-currency=USD\s+data-pricevalue=([\d.]+)')
        listing = {
            "url": "https://www.discogs.com" + m.group(1),
            "ships_from": (ships_from or "?").strip(),
            "price_usd": float(price.replace(",", "")) if price else None,
            "seller": get(r'href="/seller/([^/]+)/profile"'),
        }
        if ships_to and ships_to.lower() not in listing["ships_from"].lower():
            continue
        if listing["price_usd"] is not None:
            out.append(listing)
    time.sleep(1.5)
    return sorted(out, key=lambda x: x["price_usd"])
