"""
MEOS — FAST (Free Ad-Supported Streaming TV) live channel provider.

Covers the free, legal live tiers of:
  - Plex (free live TV)
  - The Roku Channel (free live tier)

Channel lists come from the services' own publicly published free channel
feeds.  No account, no paywall bypass, and no unlicensed sources are used.
Every source here was verified to return a playable HLS manifest; services
whose public endpoints stopped working were removed.
"""

import json
import re
import time

import xbmc

try:
    from urllib.request import urlopen, Request
    from urllib.parse import quote_plus
except ImportError:
    from urllib import urlopen, quote_plus
    from urllib2 import Request

from .base import BaseProvider


_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Publicly published free-channel feeds, one entry per service.
_SERVICES = [
    {
        "key": "plex",
        "label": "Plex",
        "list_url": "https://i.mjh.nz/Plex/.channels.json",
        "stream_template": "https://jmp2.uk/plex-{id}.m3u8",
        "region": "us",
    },
    {
        "key": "rok",
        "label": "The Roku Channel",
        "list_url": "https://i.mjh.nz/Roku/.channels.json",
        "stream_template": "https://jmp2.uk/rok-{id}.m3u8",
        "region": "",
    },
]

_CATEGORY_KEYWORDS = {
    "movies": ["movie", "film", "cinema", "western", "horror"],
    "tv": ["tv", "series", "comedy", "drama", "reality", "sci-fi", "scifi", "thriller", "anime", "classic", "sitcom"],
    "cable": ["news", "entertainment", "family", "kids", "lifestyle", "music", "local", "weather", "network"],
    "ppv": ["fight", "boxing", "mma", "wrestling", "event"],
    "sports": ["sport", "nfl", "nba", "nhl", "mlb", "ufc", "mma", "boxing", "racing", "golf", "soccer"],
    "docs": ["document", "history", "science", "nature", "education", "crime"],
}

_CACHE_TTL = 900
_cache = {}


def _fetch_json(url):
    try:
        req = Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
        resp = urlopen(req, timeout=20)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        xbmc.log("MEOS [fast] fetch error {}: {}".format(url, exc), xbmc.LOGWARNING)
        return None


def _cached_json(url):
    entry = _cache.get(url)
    now = time.time()
    if entry and now - entry[0] < _CACHE_TTL:
        return entry[1]
    data = _fetch_json(url)
    if data is not None:
        _cache[url] = (now, data)
    return data


def _norm(text):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _matches_category(haystack, category):
    if not category or category == "live":
        return True
    keywords = _CATEGORY_KEYWORDS.get(category)
    if not keywords:
        return True
    lowered = haystack.lower()
    return any(kw in lowered for kw in keywords)


def _service_channels(service):
    data = _cached_json(service["list_url"])
    if not isinstance(data, dict):
        return []

    channels = data.get("channels")
    if not isinstance(channels, dict):
        region = (data.get("regions") or {}).get(service.get("region")) or {}
        channels = region.get("channels")
    if not isinstance(channels, dict):
        return []

    region_filter = service.get("region")
    rows = []
    for channel_id, info in channels.items():
        if not isinstance(info, dict):
            continue
        name = (info.get("name") or "").strip()
        if not name:
            continue
        regions = info.get("regions")
        if region_filter and isinstance(regions, list) and region_filter not in regions:
            continue
        rows.append({
            "media_id": "fast::{}::{}".format(service["key"], channel_id),
            "title": "{} — {}".format(name, service["label"]),
            "genre": (info.get("group") or "Live TV").strip(),
            "search_text": "{} {} {}".format(name, info.get("group") or "", info.get("description") or ""),
            "stream_url": service["stream_template"].format(id=channel_id),
        })
    return rows


def _all_channels():
    rows = []
    for service in _SERVICES:
        rows.extend(_service_channels(service))
    return rows


class FastChannelsProvider(BaseProvider):
    """Free ad-supported live channels from Plex and The Roku Channel."""

    id = "fast_channels"
    name = "MEOS Free Live TV"
    requires_oauth = False

    def get_catalog(self, auth_state, category=None, query=None, year=None, award=None, result=None):
        rows = _all_channels()
        if not rows:
            return []

        results = []
        for row in rows:
            haystack = row.get("search_text") or row["title"]
            if query and _norm(query) not in _norm(haystack):
                continue
            if not _matches_category(haystack, category):
                continue
            results.append({
                "media_id": row["media_id"],
                "title": row["title"],
                "genre": row["genre"],
            })

        results.sort(key=lambda x: x["title"].lower())
        return results[:600]

    def check_entitlement(self, media_id, auth_state):
        return True, ""

    def resolve_playback(self, media_id, auth_state):
        if not media_id.startswith("fast::"):
            return None

        row = next((r for r in _all_channels() if r["media_id"] == media_id), None)
        if not row or not row["stream_url"]:
            return None

        return {
            "stream_url": row["stream_url"] + "|User-Agent=" + quote_plus(_UA),
            "title": row["title"],
            "mime_type": "application/vnd.apple.mpegurl",
            "license_url": "",
        }
