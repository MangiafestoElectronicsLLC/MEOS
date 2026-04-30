"""
MEOS — Internet Archive & Free Legal Streams provider.

Sources used:
  - Internet Archive (archive.org)  — public domain / Creative Commons films,
    classic TV, documentaries, short films, sports.  Completely free and legal.
    API docs: https://archive.org/advancedsearch.php
  - NASA TV HLS — US government / public domain live channel.

We do NOT use any unofficial scrapers, pirate sites, or bypassed paywalls.
"""

import json
import re

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

# Archive.org search queries per UI category
_CATEGORY_QUERY = {
    "movies": "(collection:feature_films OR subject:feature film OR subject:cinema) AND mediatype:movies",
    "tv": "(subject:television OR subject:sitcom OR subject:cartoon OR subject:series) AND mediatype:movies",
    "docs": "(subject:documentary OR description:documentary) AND mediatype:movies",
    "sports": "(subject:sports OR subject:baseball OR subject:football OR subject:boxing OR subject:wrestling) AND mediatype:movies",
}

# Hardcoded free legal live channels
_LIVE_CATALOG = [
    {
        "media_id": "live_nasa_tv",
        "title": "NASA TV (Live — Public Domain)",
        "genre": "Science / Live",
        "stream_url": "https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master.m3u8",
        "mime_type": "application/vnd.apple.mpegurl",
    },
    {
        "media_id": "live_dw_english",
        "title": "DW News English (Live)",
        "genre": "News / Live",
        "stream_url": "https://dwamdstream102.akamaized.net/hls/live/2015533/dwstream102/index.m3u8",
        "mime_type": "application/vnd.apple.mpegurl",
    },
    {
        "media_id": "live_france24_en",
        "title": "France 24 English (Live)",
        "genre": "News / Live",
        "stream_url": "https://static.france24.com/live/F24_EN_LO_HLS/live_web.m3u8",
        "mime_type": "application/vnd.apple.mpegurl",
    },
]

_ROWS_PER_PAGE = 80

_AWARD_TERMS = {
    ("oscar", "winner"): [
        "academy award winner",
        "oscar winner",
        "academy award-winning",
    ],
    ("oscar", "nominee"): [
        "academy award nominee",
        "oscar nominee",
        "academy award nominated",
    ],
    ("emmy", "winner"): [
        "emmy award winner",
        "primetime emmy winner",
        "emmy-winning",
    ],
    ("emmy", "nominee"): [
        "emmy award nominee",
        "primetime emmy nominee",
        "emmy-nominated",
    ],
}


def _fetch_json(url):
    try:
        req = Request(url, headers={"User-Agent": "MEOS-Kodi/1.0"})
        resp = urlopen(req, timeout=15)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        xbmc.log("MEOS [archive.org] fetch error: {}".format(exc), xbmc.LOGWARNING)
        return None


def _search_archive(query, rows=_ROWS_PER_PAGE, page=1):
    url = (
        _SEARCH_URL
        + "?q=" + quote_plus(query)
        + "&fl[]=identifier&fl[]=title&fl[]=year"
        + "&rows=" + str(rows)
        + "&page=" + str(page)
        + "&sort[]=downloads+desc"
        + "&output=json"
    )
    data = _fetch_json(url)
    if not data:
        return []

    docs = data.get("response", {}).get("docs") or []
    results = []
    for doc in docs:
        identifier = (doc.get("identifier") or "").strip()
        if not identifier:
            continue
        title = (doc.get("title") or identifier).strip()
        year = (doc.get("year") or "")
        display = "{} ({})".format(title, year) if year else title
        results.append({
            "media_id": "archive::" + identifier,
            "title": display,
            "genre": "Archive",
        })
    return results


def _normalize_query(text):
    cleaned = (text or "").strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _query_candidates(raw_query):
    """Generate safer search candidates from user-entered text."""
    original = (raw_query or "").strip()
    normalized = _normalize_query(original)
    without_year = re.sub(r"\b(19|20)\d{2}\b", "", normalized).strip()

    candidates = []
    for value in (original, normalized, without_year):
        if value and value not in candidates:
            candidates.append(value)

    if normalized.startswith("the "):
        alt = normalized[4:].strip()
        if alt and alt not in candidates:
            candidates.append(alt)

    return candidates


def _free_text_archive_query(term):
    escaped = term.replace('"', "")
    return (
        "(mediatype:movies OR mediatype:audio) AND "
        "(title:\"{0}\" OR subject:\"{0}\" OR description:\"{0}\")"
    ).format(escaped)


def _build_award_query(award, result, year):
    terms = _AWARD_TERMS.get((award, result), [])
    if not terms:
        return ""
    term_query = " OR ".join('subject:"{}" OR description:"{}" OR title:"{}"'.format(t, t, t) for t in terms)
    return "mediatype:movies AND year:{} AND ({})".format(year, term_query)


def _best_video_file(files):
    """Pick the most playback-compatible video file from Archive.org metadata."""
    mp4_h264 = []
    mp4_any = []
    ogv = []
    for f in files:
        name = f.get("name", "")
        fmt = (f.get("format") or "").lower()
        if name.lower().endswith(".mp4"):
            if "h.264" in fmt or "mpeg4" in fmt or "mp4" in fmt:
                mp4_h264.append(name)
            else:
                mp4_any.append(name)
        elif name.lower().endswith(".ogv"):
            ogv.append(name)

    for candidates in (mp4_h264, mp4_any, ogv):
        if candidates:
            return candidates[0]
    return None


def _resolve_stream_url(identifier):
    meta = _fetch_json(_META_URL.format(identifier))
    if not meta:
        return None, ""
    files = meta.get("files") or []
    chosen = _best_video_file(files)
    if not chosen:
        return None, ""
    mime = "video/mp4" if chosen.lower().endswith(".mp4") else "video/ogg"
    return _DL_URL.format(identifier, quote(chosen, safe=".-_~()")), mime


class ArchiveOrgProvider(BaseProvider):
    """
    Primary MEOS content provider.

    Movies, TV, Documentaries, Sports: sourced from Internet Archive
    (public domain + Creative Commons licensed works).

    Live Channels: hardcoded free legal streams (NASA TV, DW, France 24).
    """

    id = "archive_org"
    name = "MEOS Archive"
    requires_oauth = False

    def get_catalog(self, auth_state, category=None, query=None, year=None, award=None, result=None):
        if category == "live":
            return [
                {"media_id": ch["media_id"], "title": ch["title"], "genre": ch["genre"]}
                for ch in _LIVE_CATALOG
            ]

        if category == "award" and year and award and result:
            award_query = _build_award_query(award, result, year)
            if not award_query:
                return []
            return _search_archive(award_query)

        if query:
            for candidate in _query_candidates(query):
                results = _search_archive(_free_text_archive_query(candidate))
                if results:
                    return results
            return []

        archive_query = _CATEGORY_QUERY.get(category or "movies", _CATEGORY_QUERY["movies"])
        return _search_archive(archive_query)

    def check_entitlement(self, media_id, auth_state):
        return True, ""

    def resolve_playback(self, media_id, auth_state):
        # Live channel
        if media_id.startswith("live_"):
            ch = next((c for c in _LIVE_CATALOG if c["media_id"] == media_id), None)
            if not ch:
                return None
            return {
                "stream_url": ch["stream_url"],
                "title": ch["title"],
                "mime_type": ch.get("mime_type", ""),
                "license_url": "",
            }

        # Internet Archive item — resolve the actual file URL at play time
        if media_id.startswith("archive::"):
            identifier = media_id[len("archive::"):]
            stream_url, mime_type = _resolve_stream_url(identifier)
            if not stream_url:
                return None
            return {
                "stream_url": stream_url,
                "title": identifier,
                "mime_type": mime_type,
                "license_url": "",
            }

        return None
