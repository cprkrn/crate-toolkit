"""
Normalization + dedup helpers shared across the pipeline.

The core problem: the same track is named differently on Spotify, SoundCloud,
Beatport, and in rekordbox. We normalize aggressively for *matching* (dropping
mix/remix suffixes, punctuation, casing) while keeping the original for display.
"""
import re

_MIX_WORDS = (r"original mix|extended mix|radio edit|club mix|vip edit|"
              r"edit|remix|mix|dub|version|original|radio")


def norm_title(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\([^)]*\)", "", s)            # drop parenthetical mix info
    s = re.sub(rf"\s*-\s*({_MIX_WORDS}).*$", "", s)
    s = re.sub(r"\b(" + _MIX_WORDS + r")\b", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def norm_artist(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\(\d+\)", "", s)              # Discogs disambiguation suffixes
    return re.sub(r"[^a-z0-9]+", "", s.split(",")[0])  # first/primary artist


def sig(artist: str, title: str) -> str:
    return f"{norm_artist(artist)}::{norm_title(title)}"


def dedup_by_id(found, existing_ids: set, blocklist: set):
    """
    `found` = iterable of dicts with at least an 'id'. Returns only items whose
    id is neither already in your library nor on the blocklist. Also drops
    intra-batch duplicate ids. This is what makes re-runs idempotent.
    """
    seen, out = set(), []
    for f in found:
        i = f["id"]
        if i in existing_ids or i in blocklist or i in seen:
            continue
        seen.add(i)
        out.append(f)
    return out
