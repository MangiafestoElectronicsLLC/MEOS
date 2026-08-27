"""
MEOS — Public media & public domain feeds provider.

Sources are US government / public domain / openly licensed collections that
may be redistributed freely:
  - NASA (live TV plus the NASA archive collection)
  - C-SPAN congressional coverage (US government works, hosted on archive.org)
  - PBS-affiliated public media programs released to the public domain
  - Prelinger Archives and other US government film collections

All items resolve through official archive.org endpoints or the publishers'
own public HLS feeds.
"""

import json

import xbmc

try:
    from urllib.request import urlopen, Request
    from urllib.parse import quote_plus, quote
except ImportError:
    from urllib import urlopen, quote_plus, quote
    from urllib2 import Request

from .base import BaseProvider


_SEARCH_URL = "https://archive.org/advancedsearch.php"
_META_URL = "https://archive.org/metadata/{}"
_DL_URL = "https://archive.org/download/{}/{}"
_ROWS = 80

_LIVE_CATALOG = [
    {
        "media_id": "pubfeed_live::nasa_public",
        "title": "NASA TV Public Channel (Live)",
        "genre": "Public Media / Live",
        "stream_url": "https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master.m3u8",
    },
    {
        "media_id": "pubfeed_live::nasa_media",
        "title": "NASA TV Media Channel (Live)",
        "genre": "Public Media / Live",
        "stream_url": "https://ntv2.akamaized.net/hls/live/2014075/NASA-NTV2-HLS/master.m3u8",
    },
]

# archive.org queries for openly redistributable public media collections
_COLLECTION_QUERIES = {
    "docs": (
        "(collection:nasa OR collection:c-span OR collection:prelinger "
        "OR collection:usgovfilms OR collection:pbs) AND mediatype:movies"
    ),
    "movies": "(collection:prelinger OR collection:usgovfilms) AND mediatype:movies",
    "tv": "(collection:c-span OR collection:pbs) AND mediatype:movies",
    "cable": "(collection:c-span OR collection:pbs OR collection:nasa) AND mediatype:movies",
    "sports": "(collection:usgovfilms OR collection:prelinger) AND subject:sports AND mediatype:movies",
}

_DEFAULT_QUERY = _COLLECTION_QUERIES["docs"]
_SCOPE = (
    "(collection:nasa OR collection:c-span OR collection:prelinger "
    "OR collection:usgovfilms OR collection:pbs)"
)


def _fetch_json(url):
    try:
        req = Request(url, headers={"User-Agent": "MEOS-Kodi/1.0"})
        resp = urlopen(req, timeout=15)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        xbmc.log("MEOS [public feeds] fetch error: {}".format(exc), xbmc.LOGWARNING)
        return None


def _search(query):
    url = (
        _SEARCH_URL
        + "?q=" + quote_plus(query)
        + "&fl[]=identifier&fl[]=title&fl[]=year&fl[]=collection"
        + "&rows=" + str(_ROWS)
        + "&page=1&sort[]=downloads+desc&output=json"
    )
    data = _fetch_json(url)
    if not data:
        return []

    rows = []
    for doc in data.get("response", {}).get("docs") or []:
        identifier = (doc.get("identifier") or "").strip()
        if not identifier:
            continue
        title = (doc.get("title") or identifier).strip()
        year = doc.get("year") or ""
        collection = doc.get("collection")
        if isinstance(collection, list):
            collection = collection[0] if collection else ""
        rows.append({
            "media_id": "pubfeed::" + identifier,
            "title": "{} ({})".format(title, year) if year else title,
            "genre": str(collection or "Public Media").replace("_", " ").title(),
        })
    return rows


_PLAYABLE_EXTS = (".mp4", ".m4v", ".mkv", ".webm", ".avi", ".mov", ".mpg", ".mpeg", ".ogv")
_MIME_BY_EXT = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mpg": "video/mpeg",
    ".mpeg": "video/mpeg",
    ".ogv": "video/ogg",
}


def _best_video_file(files):
    names = [f.get("name", "") for f in files]
    mp4 = [n for n in names if n.lower().endswith(".mp4")]
    if mp4:
        return mp4[0]
    other = [n for n in names if n.lower().endswith(_PLAYABLE_EXTS)]
    return other[0] if other else None


def _resolve_archive_stream(identifier):
    meta = _fetch_json(_META_URL.format(identifier))
    if not meta:
        return "", ""
    chosen = _best_video_file(meta.get("files") or [])
    if not chosen:
        return "", ""
    lowered = chosen.lower()
    mime = next((m for ext, m in _MIME_BY_EXT.items() if lowered.endswith(ext)), "")
    return _DL_URL.format(identifier, quote(chosen, safe=".-_~()")), mime


class PublicFeedsProvider(BaseProvider):
    """PBS / NASA / C-SPAN / public domain government collections."""

    id = "public_feeds"
    name = "MEOS Public Media"
    requires_oauth = False

    def get_catalog(self, auth_state, category=None, query=None, year=None, award=None, result=None):
        if query:
            escaped = query.replace('"', "")
            search_query = (
                "{} AND mediatype:movies AND "
                '(title:"{}" OR subject:"{}" OR description:"{}")'
            ).format(_SCOPE, escaped, escaped, escaped)
            return _search(search_query)

        if category == "live":
            return [
                {"media_id": ch["media_id"], "title": ch["title"], "genre": ch["genre"]}
                for ch in _LIVE_CATALOG
            ]

        return _search(_COLLECTION_QUERIES.get(category or "docs", _DEFAULT_QUERY))

    def check_entitlement(self, media_id, auth_state):
        return True, ""

    def resolve_playback(self, media_id, auth_state):
        if media_id.startswith("pubfeed_live::"):
            channel = next((c for c in _LIVE_CATALOG if c["media_id"] == media_id), None)
            if not channel:
                return None
            return {
                "stream_url": channel["stream_url"],
                "title": channel["title"],
                "mime_type": "application/vnd.apple.mpegurl",
                "license_url": "",
            }

        if media_id.startswith("pubfeed::"):
            identifier = media_id[len("pubfeed::"):]
            stream_url, mime_type = _resolve_archive_stream(identifier)
            if not stream_url:
                return None
            return {
                "stream_url": stream_url,
                "title": identifier,
                "mime_type": mime_type,
                "license_url": "",
            }

        return None
