"""Shared helpers for the standalone scripts (no external deps beyond rapidfuzz)."""
import re
import unicodedata

_MIX = re.compile(
    r"\s*[\(\[]\s*(original mix|extended mix|original|radio edit|extended|club mix|"
    r"original version|vip mix|dub mix|instrumental|mix|edit)\s*[\)\]]", re.I)
_FEAT = re.compile(r"\s*[\(\[]?\s*(feat\.?|ft\.?|featuring)\s+[^\)\]]*[\)\]]?", re.I)


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "")
                   if not unicodedata.combining(c))


def normalize(s, drop_mix=True):
    """Lowercase, de-accent, strip feat/mix noise + punctuation."""
    s = strip_accents(s).lower()
    s = _FEAT.sub(" ", s)
    if drop_mix:
        s = _MIX.sub(" ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def primary_artist(artist):
    """First artist only (handles ', ' / ' & ' / feat splits)."""
    return re.split(r"\s*[,&]\s*|\s+(?:feat|ft|with)\.?\s+", artist or "", flags=re.I)[0]
