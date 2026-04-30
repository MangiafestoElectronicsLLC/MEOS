"""
MEOS — Pluto TV provider.

Pluto TV is a free, ad-supported legal streaming service owned by Paramount.
Their channel/on-demand API is unauthenticated and returns publicly accessible
HLS streams.  This is the same approach used by the official Kodi Pluto TV
community addon.

API base: https://api.pluto.tv/v2/
"""

import json

import xbmc

try:
    from urllib.request import urlopen, Request
    from urllib.parse import quote_plus
except ImportError:
    from urllib import urlopen, quote_plus
    from urllib2 import Request

from .base import BaseProvider


_CHANNELS_URLS = [
    "https://api.pluto.tv/v2/channels",
    "https://api.pluto.tv/v2/channels?deviceType=web",
    "https://api.pluto.tv/v2/channels?deviceType=web&deviceMake=Chrome&deviceModel=web",
]
_VOD_URL = (
    "https://api.pluto.tv/v3/vod/categories"
    "?includeItems=true&deviceType=web"
)

# Map MEOS UI category → Pluto TV genre keywords (case-insensitive substring match)
_LIVE_GENRE_MAP = {
    "live": None,          # all channels
    "movies": "movie",
    "tv": ["tv", "comedy", "drama", "reality", "sci-fi", "thriller"],
    "sports": "sports",
    "docs": ["documentary", "news", "education", "science", "nature"],
}


def _fetch_json(url):
    try:
        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; MEOS-Kodi/1.0)",
                "Accept": "application/json",
            },
        )
        resp = urlopen(req, timeout=15)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        xbmc.log("MEOS [pluto.tv] fetch error: {}".format(exc), xbmc.LOGWARNING)
        return None


def _genre_text(channel):
    genre = channel.get("genre") or channel.get("category") or ""
    if isinstance(genre, dict):
        return (genre.get("name") or genre.get("slug") or "").lower()
    if isinstance(genre, list):
        names = []
        for g in genre:
            if isinstance(g, dict):
                names.append(g.get("name") or g.get("slug") or "")
            else:
                names.append(str(g))
        return " ".join(names).lower()
    return str(genre).lower()


def _channel_matches(channel, category):
    """Return True if this live channel belongs to the requested MEOS category."""
    genre_filter = _LIVE_GENRE_MAP.get(category)
    if genre_filter is None:
        return True  # "live" = everything
    raw_genre = _genre_text(channel)
    if isinstance(genre_filter, list):
        return any(kw in raw_genre for kw in genre_filter)
    return genre_filter in raw_genre


def _channel_name(channel):
    return (channel.get("name") or channel.get("title") or channel.get("slug") or "").strip()


def _load_channels():
    for url in _CHANNELS_URLS:
        data = _fetch_json(url)
        if not data:
            continue
        channels = data if isinstance(data, list) else data.get("data") or []
        if channels:
            return channels
    return []


def _iter_vod_categories(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("categories", "data", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _vod_stream(item):
    stitched = item.get("stitched") or {}
    urls = stitched.get("urls") or []
    for u in urls:
        if (u.get("type") or "").lower() == "hls" and u.get("url"):
            return u.get("url")
    for u in urls:
        if u.get("url"):
            return u.get("url")
    return ""


def _vod_matches(item, category, query, category_name=""):
    name = (item.get("name") or item.get("title") or "").lower()
    genre = (item.get("genre") or "").lower()
    media_type = (item.get("type") or "").lower()
    cat = (category_name or "").lower()
    summary = (item.get("summary") or item.get("description") or "").lower()
    haystack = "{} {} {} {} {}".format(name, genre, media_type, cat, summary)

    if query and query.lower() not in haystack:
        return False

    if not category or category == "live":
        return True
    if category == "movies":
        return media_type == "movie" or "movie" in cat
    if category == "tv":
        return media_type in ("series", "episode", "show") or "series" in cat or "tv" in cat
    if category == "docs":
        return "document" in haystack or "history" in haystack or "science" in haystack
    if category == "sports":
        return any(k in haystack for k in ["sport", "nfl", "nba", "nhl", "mlb", "ufc", "mma", "boxing", "racing"])
    return True


def _load_vod_items(category=None, query=None):
    payload = _fetch_json(_VOD_URL)
    if not payload:
        return []

    categories = _iter_vod_categories(payload)
    results = []
    for cat in categories:
        category_name = (cat.get("name") or cat.get("title") or "") if isinstance(cat, dict) else ""
        items = cat.get("items") if isinstance(cat, dict) else []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("_id") or item.get("id") or "")
            title = (item.get("name") or item.get("title") or "").strip()
            if not item_id or not title:
                continue
            if not _vod_matches(item, category, query, category_name=category_name):
                continue
            stream_url = _vod_stream(item)
            if not stream_url:
                continue
            genre = (item.get("genre") or category_name or "VOD").strip()
            results.append(
                {
                    "media_id": "plutovod::" + item_id,
                    "title": title,
                    "genre": genre,
                    "stream_url": stream_url,
                }
            )

    dedup = {}
    for row in results:
        dedup[row["media_id"]] = row
    return list(dedup.values())


def _best_stream(channel):
    urls = channel.get("stitcherUrls") or []
    if urls:
        url = urls[0].get("url", "")
        if url:
            return url
    # fallback: build stitcher URL manually
    slug = channel.get("slug") or channel.get("id") or ""
    if slug:
        return (
            "https://service-stitcher.clusters.pluto.tv/stitch/hls/channel/"
            + slug + "/master.m3u8?deviceDNT=1&deviceId=meos&deviceType=web"
            "&deviceMake=Chrome&deviceModel=web&deviceVersion=114.0"
            "&appName=plutotv&appVersion=5.8.1-lts&deviceLat=40.7128"
            "&deviceLon=-74.0060&deviceCountry=US&deviceZip=10001"
            "&deviceDMA=501&serverSideAds=false&includeExtendedEvents=false"
            "&jwt=undefined&content-type=application/x-mpegURL"
        )
    return ""


class PlutoTvProvider(BaseProvider):
    """
    Pluto TV — free, legal, ad-supported channels and on-demand content.
    No account or authentication required.
    """

    id = "pluto_tv"
    name = "Pluto TV"
    requires_oauth = False

    def get_catalog(self, auth_state, category=None, query=None, year=None, award=None, result=None):
        if category in ("movies", "tv", "docs", "sports") or (query and (not category or category != "live")):
            vod = _load_vod_items(category=category, query=query)
            vod.sort(key=lambda x: x["title"].lower())
            if vod:
                return [{"media_id": r["media_id"], "title": r["title"], "genre": r["genre"]} for r in vod[:300]]

        channels = _load_channels()
        if not channels:
            return []

        results = []
        for ch in channels:
            name = _channel_name(ch)
            if not name:
                continue

            if query:
                haystack = "{} {}".format(name.lower(), _genre_text(ch))
                if query.lower() not in haystack:
                    continue
            if category and category != "live":
                if not _channel_matches(ch, category):
                    continue

            stream_url = _best_stream(ch)
            if not stream_url:
                continue

            media_id = "pluto::" + str(ch.get("id") or ch.get("slug") or name)
            genre = _genre_text(ch) or "live tv"

            results.append({
                "media_id": media_id,
                "title": name,
                "genre": genre.title(),
                "_stream_url": stream_url,
            })

        results.sort(key=lambda x: x["title"].lower())
        return [{"media_id": r["media_id"], "title": r["title"], "genre": r["genre"]} for r in results]

    def check_entitlement(self, media_id, auth_state):
        return True, ""

    def resolve_playback(self, media_id, auth_state):
        if media_id.startswith("plutovod::"):
            item_id = media_id[len("plutovod::"):]
            items = _load_vod_items()
            selected = next((i for i in items if i["media_id"] == "plutovod::" + item_id), None)
            if not selected:
                return None
            return {
                "stream_url": selected["stream_url"],
                "title": selected["title"],
                "mime_type": "application/vnd.apple.mpegurl",
                "license_url": "",
            }

        if not media_id.startswith("pluto::"):
            return None

        channel_id = media_id[len("pluto::"):]
        channels = _load_channels()
        if not channels:
            return None

        ch = next(
            (
                c for c in channels
                if str(c.get("id") or c.get("slug") or "") == channel_id
                or _channel_name(c) == channel_id
            ),
            None,
        )

        if not ch:
            return None

        stream_url = _best_stream(ch)
        if not stream_url:
            return None

        return {
            "stream_url": stream_url,
            "title": _channel_name(ch) or channel_id,
            "mime_type": "application/vnd.apple.mpegurl",
            "license_url": "",
        }
