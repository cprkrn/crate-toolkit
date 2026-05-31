"""
Genre QA — catch wrong fuzzy matches before they pollute your crates.

Catalog search returns the *closest* result, which for a niche/vinyl-only track
is often a completely different song that merely shares a word. The cheapest
reliable signal that something is wrong: the matched track's genre is nowhere
near what you're curating (a Hip-Hop / Pop / Drum & Bass / Rock result landing
in a House/Minimal crate).

Feed every match through `is_suspect()`. Quarantine suspects for manual review,
and once confirmed wrong, append their ids to your blocklist so future runs skip
them automatically.
"""

# Genres that fit a house / minimal / techno aesthetic. Tune to taste.
ACCEPTED_GENRES = {
    "Minimal / Deep Tech", "Deep House", "House", "Tech House", "Electronica",
    "Indie Dance", "Melodic House & Techno", "Nu Disco / Disco", "Organic House",
    "Afro House", "Techno (Raw / Deep / Hypnotic)", "Techno (Peak Time / Driving)",
    "Progressive House", "Downtempo", "UK Garage / Bassline",
    "Electro (Classic / Detroit / Modern)", "Breaks / Breakbeat / UK Bass",
}


def is_suspect(track: dict) -> bool:
    """True if the match's genre is outside the accepted set (probably wrong)."""
    g = track.get("genre")
    return bool(g) and g not in ACCEPTED_GENRES


def split_matches(matches):
    """Return (clean, suspect) given an iterable of match dicts with 'genre'."""
    clean, suspect = [], []
    for m in matches:
        (suspect if is_suspect(m) else clean).append(m)
    return clean, suspect
