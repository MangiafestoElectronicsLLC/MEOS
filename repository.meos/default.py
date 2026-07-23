import sys
import random
import json

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from providers import get_providers

try:
    from urllib import urlencode
    from urlparse import parse_qsl, urlparse, urlunparse
except ImportError:
    from urllib.parse import urlencode, parse_qsl, urlparse, urlunparse


ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]
DEFAULT_ART = {"thumb": "icon.png", "icon": "icon.png", "fanart": "fanart.jpg"}
DEFAULT_SAMPLE_STREAMS = [
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
]
PRIMARY_PROVIDER_ID = "archive_org"
MENU_CATEGORIES = [
    ("Movies", "movies"),
    ("TV Shows", "tv"),
    ("Cable TV", "cable"),
    ("PPV Events", "ppv"),
    ("Documentaries", "docs"),
    ("Live Channels", "live"),
    ("Sports", "sports"),
]
SPORT_TOPICS = [
    ("Live NFL", "NFL football"),
    ("Live NHL", "NHL hockey"),
    ("Live Basketball", "NBA basketball"),
    ("Live Baseball", "MLB baseball"),
    ("Live NCAA", "NCAA college sports"),
    ("Live Boxing", "boxing"),
    ("Live UFC", "UFC MMA"),
    ("Live Racing", "motorsport racing"),
    ("Live Horse Racing", "horse racing"),
]
AWARD_MENU = [
    ("Oscar Winners", "oscar", "winner"),
    ("Oscar Nominees", "oscar", "nominee"),
    ("Emmy Winners", "emmy", "winner"),
    ("Emmy Nominees", "emmy", "nominee"),
]
YEAR_MIN = 1927
YEAR_MAX = 2026
MAX_INTEGRATED_SCAN_DEPTH = 6
MAX_INTEGRATED_ITEMS_PER_ADDON = 800
MAX_INTEGRATED_TARGET_MATCHES = 8
MAX_VALIDATED_CACHE_ITEMS = 800
MAX_INTEGRATED_SEARCH_ITEMS_PER_ADDON = 160
MAX_INTEGRATED_SEARCH_TOTAL_ITEMS = 1200
VALIDATED_TARGETS_SETTING = "external_validated_targets"
VALIDATED_PROVIDER_SETTING = "provider_validated_items"
STREAM_VOTES_SETTING = "external_stream_votes"
MANUAL_FAVORITES_SETTING = "manual_favorites"
CUSTOM_INTEGRATED_TARGETS_SETTING = "integrated_custom_targets"
MAX_MANUAL_FAVORITES = 600
MAX_INTEGRATED_MENU_CACHE_ITEMS = 1200
MAX_INTEGRATED_BROWSE_SHORTCUTS_PER_ADDON = 4
VALIDATED_MARKER_UNICODE = "[COLOR limegreen][B]✔[/B][/COLOR] "
VALIDATED_MARKER_REJECTED = "[COLOR red][B]✘[/B][/COLOR] "
VALIDATED_MARKER_FALLBACK = "[COLOR limegreen][B]OK[/B][/COLOR] "
VALIDATED_MARKER_LEGACY = "[COLOR limegreen][B]v[/B][/COLOR] "
CUSTOM_MAPPED_MARKER = "[COLOR gold][B]Mapped[/B][/COLOR] "
VOTE_MARKER_UP = "[COLOR limegreen][B]👍[/B][/COLOR] "
VOTE_MARKER_DOWN = "[COLOR red][B]👎[/B][/COLOR] "
MIN_STREAM_VALIDATION_SECONDS = 10
VIDEO_ADDON_TYPES = ("xbmc.python.pluginsource", "xbmc.addon.video")
INTEGRATED_MENU_CACHE_SETTING = "integrated_menu_cache"
CATEGORY_HINTS = {
    "movies": ["movie", "movies", "film", "cinema", "one click movie", "1 click movie"],
    "tv": ["tv", "shows", "tv shows", "series", "episodes", "one click tv", "1 click tv"],
    "docs": ["doc", "docs", "documentary", "documentaries"],
    "cable": ["cable", "cable tv", "channels", "channel", "iptv", "broadcast", "local channels", "network tv", "live tv"],
    "ppv": ["ppv", "pay per view", "event", "events", "fight night", "boxing", "ufc", "mma", "wrestling"],
    "live": ["live", "channels", "channel", "iptv", "live tv", "local channels", "broadcast", "one click live", "1 click live"],
    "sports": ["sport", "sports", "nfl", "nba", "mlb", "ufc", "mma", "boxing", "wwe", "ppv", "pay per view"],
    "award": ["award", "awards", "oscar", "emmy", "winner", "nominee"],
}
ADDON_CATEGORY_RULES = [
    {
        "name": "scrubs",
        "id_contains": ["scrubsv2", "scrubs", "plugin.video.scrubs", "plugin.video.scrubsv2"],
        "label_contains": ["scrubs", "scrubs v2"],
        "paths": {
            "movies": [
                ["Movies"],
                ["Movie"],
                ["Scrubs", "Movies"],
                ["1 Click Movies"],
                ["One Click Movies"],
                ["My Movies"],
                ["Trending Movies"],
                ["Boxsets"],
            ],
            "tv": [
                ["TV Shows"],
                ["TV"],
                ["Scrubs", "TV Shows"],
                ["1 Click TV Shows"],
                ["One Click TV Shows"],
                ["My TV Shows"],
                ["New Episodes"],
            ],
            "cable": [["Live TV"], ["Channels"], ["Cable"], ["24/7"], ["24 7"], ["Mega List"]],
            "live": [["Live TV"], ["Channels"], ["24/7"], ["24 7"], ["Mega List"]],
            "sports": [["Sports"], ["Sports Zone"], ["Sports Zones"], ["Live Sports"], ["PPV"]],
            "ppv": [["PPV"], ["Pay Per View"], ["Events"], ["Fight Night"]],
        },
        "categories": {
            "movies": ["movies", "movie", "my movies", "new movies", "movie world", "boxsets", "1-click movies", "one click movies", "1 click movies", "trending movies", "film", "films", "debrid movies", "movies debrid"],
            "tv": ["tv shows", "tv", "my tv shows", "new episodes", "series", "episodes", "1-click tv shows", "one click tv shows", "1 click tv shows", "trending tv shows", "debrid tv", "tv debrid"],
            "cable": ["cable tv", "live tv", "live channels", "channels", "iptv", "network tv", "24/7", "mega list"],
            "ppv": ["ppv", "pay per view", "events", "fight night", "wrestling", "boxing", "ufc", "mma"],
            "live": ["live tv", "live channels", "channels", "iptv", "cable tv", "24/7", "mega list", "cable channels"],
            "sports": ["sports", "live sports", "sport", "sports zone", "sports zones", "nfl", "nba", "mlb", "nhl", "ufc", "boxing"],
            "docs": ["documentaries", "docs", "documentary"],
        },
    },
    {
        "name": "red gratis",
        "id_contains": ["redgratis", "red.gratis", "plugin.video.red", "plugin.video.redgratis", "plugin.video.red.gratis"],
        "label_contains": ["red gratis", "redgratis", "red"],
        "categories": {
            "movies": ["peliculas", "pelis", "movies", "cine", "estrenos", "boxsets"],
            "tv": ["series", "tv", "tv shows", "novelas", "episodios"],
            "cable": ["cable", "cable tv", "canales", "channels", "tv en vivo", "en vivo"],
            "ppv": ["ppv", "pay per view", "eventos", "event"],
            "live": ["tv en vivo", "en vivo", "live tv", "canales", "channels", "cable", "latino"],
            "sports": ["deportes", "sports", "eventos"],
            "docs": ["documentales", "documentaries", "docs"],
        },
    },
    {
        "name": "loop",
        "id_contains": ["theloop", "plugin.video.loop", "plugin.video.theloop", "plugin.video.the.loop"],
        "label_contains": ["loop", "the loop"],
        "paths": {
            "live": [["24/7"], ["24/7", "Mega List"], ["24/7", "Mega List", "Cable Channels"]],
            "cable": [["24/7", "Mega List", "Cable Channels"], ["24/7", "Mega List"]],
            "sports": [["24/7", "Mega List", "Sports Zone"], ["24/7", "Mega List", "Sports Zones"], ["24/7", "Sports Zone"]],
            "movies": [["Movies"], ["Movie"]],
            "tv": [["TV Shows"], ["TV"], ["Episodes"]],
        },
        "categories": {
            "movies": ["movies", "movie", "movie zone", "boxsets", "one click movies", "1-click movies"],
            "tv": ["tv shows", "shows", "series", "tv", "episodes"],
            "cable": ["cable tv", "channels", "live channels", "iptv", "network tv", "24/7", "mega list", "cable channels"],
            "ppv": ["ppv", "pay per view", "events", "fight night"],
            "live": ["live tv", "channels", "live channels", "iptv", "cable", "abc mega list", "mega list", "abc", "cable channels", "24/7"],
            "sports": ["sports", "live sports", "sport", "24/7 sports", "24/7", "sports area", "sports zone", "sports zones", "zone sports"],
            "docs": ["documentaries", "docs"],
        },
    },
    {
        "name": "tbmd",
        "id_contains": ["tbmd", "plugin.video.tbmd"],
        "label_contains": ["tbmd"],
        "paths": {
            "movies": [["Movies"], ["TBMD", "Movies"]],
            "tv": [["TV Shows"], ["TV"], ["TBMD", "TV Shows"]],
            "cable": [["24/7"], ["Channels"], ["Mega List"]],
            "live": [["24/7"], ["Mega List"], ["Live TV"]],
            "sports": [["Sports"], ["Sports Zone"], ["Sports Zones"]],
        },
        "categories": {
            "movies": ["movies", "movie", "films", "film", "within", "movie section"],
            "tv": ["tv shows", "tv", "shows", "series", "episodes", "within", "tv section"],
            "cable": ["cable", "channels", "live channels", "24/7", "mega list"],
            "ppv": ["ppv", "events", "fight night", "pay per view"],
            "live": ["live tv", "channels", "live channels", "24/7", "mega list"],
            "sports": ["sports", "sport", "live sports", "sports zone"],
            "docs": ["documentaries", "docs", "documentary"],
        },
    },
    {
        "name": "ghost",
        "id_contains": ["ghost", "plugin.video.ghost", "plugin.video.theghost", "plugin.video.the.ghost"],
        "label_contains": ["ghost", "the ghost"],
        "paths": {
            "movies": [["Movies"], ["Free", "Movies"], ["Free", "New Movies"], ["New Movies"]],
            "tv": [["TV Shows"], ["Shows"], ["Series"]],
            "cable": [["Live TV"], ["Channels"]],
            "live": [["Live TV"], ["Channels"]],
            "sports": [["Sports"], ["Sports Zone"], ["Sports Zones"]],
        },
        "categories": {
            "movies": ["movies", "movie", "1-click movies", "one click movies", "boxsets"],
            "tv": ["tv shows", "shows", "series", "1-click tv shows", "one click tv shows"],
            "cable": ["cable tv", "channels", "iptv", "live tv"],
            "ppv": ["ppv", "pay per view", "events", "boxing", "ufc"],
            "live": ["live tv", "channels", "live channels", "iptv", "cable"],
            "sports": ["sports", "sport", "live sports"],
            "docs": ["documentaries", "docs", "documentary"],
        },
    },
    {
        "name": "rising tides",
        "id_contains": ["risingtides", "rising.tides", "plugin.video.risingtides", "plugin.video.rising.tides"],
        "label_contains": ["rising tides", "risingtides"],
        "categories": {
            "movies": ["movies", "movie", "replays"],
            "tv": ["tv shows", "shows", "replays", "series"],
            "cable": ["cable tv", "channels", "live tv", "iptv"],
            "ppv": ["ppv events", "ppv", "pay per view", "fights", "replays"],
            "live": ["live tv", "channels", "live channels", "iptv", "cable", "ppv events"],
            "sports": ["sports", "live sports", "football", "basketball", "baseball", "hockey", "replays", "ppv events"],
            "docs": ["documentaries", "docs"],
        },
    },
    {
        "name": "the crew",
        "id_contains": ["thecrew", "crew", "plugin.video.thecrew", "plugin.video.the.crew"],
        "label_contains": ["the crew", "crew"],
        "categories": {
            "movies": ["movies", "movie", "1-click movies", "one click movies", "boxsets", "new movies"],
            "tv": ["tv shows", "shows", "series", "1-click tv shows", "one click tv shows", "new episodes"],
            "cable": ["cable tv", "channels", "iptv", "network tv", "live tv"],
            "ppv": ["ppv", "pay per view", "fights", "events", "ufc", "boxing"],
            "live": ["live tv", "channels", "live channels", "iptv", "cable", "tv"],
            "sports": ["sports", "sport", "live sports", "nfl", "nba", "mlb", "nhl", "ufc", "boxing"],
            "docs": ["documentaries", "docs", "kids"],
        },
    },
]

PROVIDERS = {provider.id: provider for provider in get_providers()}


def build_url(query):
    return BASE_URL + "?" + urlencode(query)


def get_auth_state(provider_id):
    return ADDON.getSetting("auth.{0}".format(provider_id))


def set_auth_state(provider_id, state):
    ADDON.setSetting("auth.{0}".format(provider_id), state)


def _setting_bool(setting_id, default=False):
    value = (ADDON.getSetting(setting_id) or "").strip().lower()
    if not value:
        return default
    return value in ("true", "1", "yes", "on")


def _json_rpc(method, params=None):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        payload["params"] = params

    try:
        response = xbmc.executeJSONRPC(json.dumps(payload))
        data = json.loads(response)
    except Exception as exc:
        xbmc.log("MEOS JSON-RPC failure ({0}): {1}".format(method, exc), xbmc.LOGWARNING)
        return None

    if data.get("error"):
        xbmc.log("MEOS JSON-RPC error ({0}): {1}".format(method, data.get("error")), xbmc.LOGWARNING)
        return None

    return data.get("result")


def _get_integrated_addon_ids():
    raw = (ADDON.getSetting("external_integrated_addons") or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []

    cleaned = []
    seen = set()
    for addon_id in data:
        if not addon_id:
            continue
        addon_id = str(addon_id).strip()
        if not addon_id or addon_id in seen:
            continue
        seen.add(addon_id)
        cleaned.append(addon_id)
    return cleaned


def _set_integrated_addon_ids(addon_ids):
    payload = []
    seen = set()
    for addon_id in addon_ids:
        if not addon_id:
            continue
        addon_id = str(addon_id).strip()
        if not addon_id or addon_id in seen:
            continue
        seen.add(addon_id)
        payload.append(addon_id)
    ADDON.setSetting("external_integrated_addons", json.dumps(payload))


def _get_integrated_menu_cache():
    return _get_json_object_list_setting(INTEGRATED_MENU_CACHE_SETTING)


def _set_integrated_menu_cache(rows):
    cleaned = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        addon_id = str(row.get("addon_id") or "").strip()
        category = str(row.get("category") or "").strip()
        target = str(row.get("target") or "").strip()
        if not addon_id or not category or not target:
            continue

        key = (addon_id.lower(), category.lower(), target.lower())
        if key in seen:
            continue
        seen.add(key)

        cleaned.append(
            {
                "addon_id": addon_id,
                "addon_name": str(row.get("addon_name") or addon_id).strip(),
                "category": category,
                "category_label": str(row.get("category_label") or category.title()).strip(),
                "target": target,
                "label": str(row.get("label") or target).strip(),
                "title": str(row.get("title") or "").strip(),
                "is_folder": bool(row.get("is_folder", True)),
                "thumb": str(row.get("thumb") or "").strip(),
                "fanart": str(row.get("fanart") or "").strip(),
                "custom_mapped": bool(row.get("custom_mapped", False)),
                "validated": bool(row.get("validated", False)),
            }
        )
        if len(cleaned) >= MAX_INTEGRATED_MENU_CACHE_ITEMS:
            break

    ADDON.setSetting(INTEGRATED_MENU_CACHE_SETTING, json.dumps(cleaned))


def _integrated_menu_cache_rows_for_addon(addon_id, addon_name, addon_row=None):
    rows = []
    if not addon_id:
        return rows

    for category_label, category in MENU_CATEGORIES:
        matches = _resolve_integrated_targets(addon_id, category, addon_name=addon_name)
        for match in matches:
            target = (match.get("target") or "").strip()
            if not target:
                continue
            rows.append(
                {
                    "addon_id": addon_id,
                    "addon_name": addon_name,
                    "category": category,
                    "category_label": category_label,
                    "target": target,
                    "label": match.get("matched_label") or "Match",
                    "title": addon_name,
                    "is_folder": bool(match.get("is_folder", True)),
                    "thumb": match.get("thumbnail") or (addon_row or {}).get("thumbnail") or "",
                    "fanart": match.get("fanart") or (addon_row or {}).get("fanart") or "",
                    "custom_mapped": bool(match.get("custom_mapped", False)),
                    "validated": _is_target_validated(target),
                }
            )

    return rows


def _refresh_integrated_menu_cache(addon_id, addon_name, addon_row=None):
    addon_id = (addon_id or "").strip()
    if not addon_id:
        return 0

    remaining = [row for row in _get_integrated_menu_cache() if (row.get("addon_id") or "").strip() != addon_id]
    new_rows = _integrated_menu_cache_rows_for_addon(addon_id, addon_name, addon_row=addon_row)
    remaining.extend(new_rows)
    _set_integrated_menu_cache(remaining)
    return len(new_rows)


def _sync_integrated_menu_cache(addon_ids=None):
    if addon_ids is None:
        addon_ids = _get_integrated_addon_ids()

    selected = []
    seen = set()
    for addon_id in addon_ids:
        addon_id = (addon_id or "").strip()
        if not addon_id or addon_id in seen:
            continue
        seen.add(addon_id)
        selected.append(addon_id)

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    refreshed_rows = []
    refreshed = 0

    for addon_id in selected:
        row = installed.get(addon_id)
        if not row:
            continue
        addon_name = row.get("name") or addon_id
        new_rows = _integrated_menu_cache_rows_for_addon(addon_id, addon_name, addon_row=row)
        refreshed_rows.extend(new_rows)
        refreshed += len(new_rows)

    _set_integrated_menu_cache(refreshed_rows)
    return refreshed


def _get_json_list_setting(setting_id):
    raw = (ADDON.getSetting(setting_id) or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return data


def _set_json_list_setting(setting_id, values):
    cleaned = []
    seen = set()
    for value in values:
        if not value:
            continue
        value = str(value).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
        if len(cleaned) >= MAX_VALIDATED_CACHE_ITEMS:
            break
    ADDON.setSetting(setting_id, json.dumps(cleaned))


def _get_json_object_list_setting(setting_id):
    raw = (ADDON.getSetting(setting_id) or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _set_json_object_list_setting(setting_id, values, max_items=MAX_MANUAL_FAVORITES):
    cleaned = []
    seen = set()
    for row in values:
        if not isinstance(row, dict):
            continue
        target = str(row.get("target") or "").strip()
        if not target:
            continue
        key = target.lower()
        if key in seen:
            continue
        seen.add(key)
        payload = {
            "target": target,
            "label": str(row.get("label") or target).strip(),
            "title": str(row.get("title") or "").strip(),
            "is_folder": bool(row.get("is_folder", True)),
            "thumb": str(row.get("thumb") or "").strip(),
            "fanart": str(row.get("fanart") or "").strip(),
        }
        cleaned.append(payload)
        if len(cleaned) >= max_items:
            break
    ADDON.setSetting(setting_id, json.dumps(cleaned))


def _addon_id_from_target(target):
    target = (target or "").strip()
    if not target:
        return ""
    if not target.startswith("plugin://"):
        return ""
    try:
        parsed = urlparse(target)
    except Exception:
        return ""
    return (parsed.netloc or "").strip()


def _get_custom_integrated_targets():
    raw_rows = _get_json_object_list_setting(CUSTOM_INTEGRATED_TARGETS_SETTING)
    cleaned = []
    seen = set()
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        addon_id = (row.get("addon_id") or "").strip()
        category = (row.get("category") or "").strip().lower()
        target = (row.get("target") or "").strip()
        if not addon_id or not category or not target:
            continue
        key = (addon_id.lower(), category, target.lower())
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(
            {
                "addon_id": addon_id,
                "category": category,
                "target": target,
                "label": (row.get("label") or "").strip(),
                "is_folder": bool(row.get("is_folder", True)),
                "thumb": (row.get("thumb") or "").strip(),
                "fanart": (row.get("fanart") or "").strip(),
                "custom_mapped": bool(row.get("custom_mapped", True)),
            }
        )
    return cleaned


def _set_custom_integrated_targets(rows):
    cleaned = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        addon_id = str(row.get("addon_id") or "").strip()
        category = str(row.get("category") or "").strip().lower()
        target = str(row.get("target") or "").strip()
        if not addon_id or not category or not target:
            continue

        key = (addon_id.lower(), category, target.lower())
        if key in seen:
            continue
        seen.add(key)

        cleaned.append(
            {
                "addon_id": addon_id,
                "category": category,
                "target": target,
                "label": str(row.get("label") or target).strip(),
                "is_folder": bool(row.get("is_folder", True)),
                "thumb": str(row.get("thumb") or "").strip(),
                "fanart": str(row.get("fanart") or "").strip(),
                "custom_mapped": bool(row.get("custom_mapped", True)),
            }
        )
        if len(cleaned) >= MAX_INTEGRATED_MENU_CACHE_ITEMS:
            break

    ADDON.setSetting(CUSTOM_INTEGRATED_TARGETS_SETTING, json.dumps(cleaned))


def _is_custom_integrated_target(addon_id, category, target):
    addon_id = (addon_id or "").strip().lower()
    category = (category or "").strip().lower()
    target = (target or "").strip().lower()
    if not addon_id or not category or not target:
        return False

    for row in _get_custom_integrated_targets():
        if (
            (row.get("addon_id") or "").strip().lower() == addon_id
            and (row.get("category") or "").strip().lower() == category
            and (row.get("target") or "").strip().lower() == target
        ):
            return True
    return False


def _set_custom_integrated_target(addon_id, category, target, label="", is_folder=True, thumb="", fanart=""):
    addon_id = (addon_id or "").strip()
    category = (category or "").strip().lower()
    target = (target or "").strip()
    if not addon_id or not category or not target:
        return False

    rows = _get_custom_integrated_targets()
    rows = [
        row
        for row in rows
        if not (
            (row.get("addon_id") or "").strip().lower() == addon_id.lower()
            and (row.get("category") or "").strip().lower() == category
            and (row.get("target") or "").strip().lower() == target.lower()
        )
    ]
    rows.insert(
        0,
        {
            "addon_id": addon_id,
            "category": category,
            "target": target,
            "label": (label or "").strip(),
            "is_folder": bool(is_folder),
            "thumb": (thumb or "").strip(),
            "fanart": (fanart or "").strip(),
            "custom_mapped": True,
        },
    )
    _set_custom_integrated_targets(rows)
    return True


def _remove_custom_integrated_target(addon_id, category, target):
    addon_id = (addon_id or "").strip().lower()
    category = (category or "").strip().lower()
    target = (target or "").strip().lower()
    if not addon_id or not category or not target:
        return False

    rows = _get_custom_integrated_targets()
    filtered = [
        row
        for row in rows
        if not (
            (row.get("addon_id") or "").strip().lower() == addon_id
            and (row.get("category") or "").strip().lower() == category
            and (row.get("target") or "").strip().lower() == target
        )
    ]
    if len(filtered) == len(rows):
        return False
    _set_custom_integrated_targets(filtered)
    return True


def _custom_targets_for_addon_category(addon_id, category):
    addon_id = (addon_id or "").strip().lower()
    category = (category or "").strip().lower()
    if not addon_id or not category:
        return []

    matches = []
    for row in _get_custom_integrated_targets():
        row_addon = (row.get("addon_id") or "").strip().lower()
        row_category = (row.get("category") or "").strip().lower()
        if row_addon != addon_id or row_category != category:
            continue
        target = (row.get("target") or "").strip()
        if not target:
            continue
        matches.append(
            {
                "target": target,
                "is_folder": bool(row.get("is_folder", True)),
                "matched_label": (row.get("label") or "").strip(),
                "thumbnail": (row.get("thumb") or "").strip(),
                "fanart": (row.get("fanart") or "").strip(),
                "custom_mapped": bool(row.get("custom_mapped", True)),
                "score": 5000,
            }
        )
    return matches


def _to_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _get_manual_favorites():
    return _get_json_object_list_setting(MANUAL_FAVORITES_SETTING)


def _set_manual_favorites(rows):
    _set_json_object_list_setting(MANUAL_FAVORITES_SETTING, rows, max_items=MAX_MANUAL_FAVORITES)


def _add_manual_favorite(target, label="", title="", is_folder=True, thumb="", fanart=""):
    target = (target or "").strip()
    if not target:
        return False

    row = {
        "target": target,
        "label": (label or title or target).strip(),
        "title": (title or "").strip(),
        "is_folder": bool(is_folder),
        "thumb": (thumb or "").strip(),
        "fanart": (fanart or "").strip(),
    }

    items = _get_manual_favorites()
    filtered = [existing for existing in items if (existing.get("target") or "").strip().lower() != target.lower()]
    filtered.insert(0, row)
    _set_manual_favorites(filtered)
    return True


def _remove_manual_favorite(target):
    target = (target or "").strip().lower()
    if not target:
        return False
    items = _get_manual_favorites()
    filtered = [row for row in items if (row.get("target") or "").strip().lower() != target]
    if len(filtered) == len(items):
        return False
    _set_manual_favorites(filtered)
    return True


def _get_validated_target_set():
    return set(_get_json_list_setting(VALIDATED_TARGETS_SETTING))


def _canonical_target(target):
    target = (target or "").strip()
    if not target:
        return ""

    if "://" not in target:
        return target

    try:
        parsed = urlparse(target)
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    except Exception:
        return target

    volatile_keys = {
        "_",
        "ts",
        "time",
        "timestamp",
        "token",
        "sig",
        "signature",
        "expires",
        "expiry",
        "session",
        "auth",
        "rnd",
        "random",
        "cache",
        "cachebuster",
    }

    filtered = []
    for key, value in query_pairs:
        if (key or "").strip().lower() in volatile_keys:
            continue
        filtered.append((key, value))

    filtered.sort(key=lambda row: ((row[0] or "").lower(), row[1] or ""))
    normalized_query = urlencode(filtered)
    return urlunparse(
        (
            (parsed.scheme or "").lower(),
            (parsed.netloc or "").lower(),
            parsed.path or "",
            parsed.params or "",
            normalized_query,
            "",
        )
    )


def _target_validation_keys(target):
    target = (target or "").strip()
    if not target:
        return []

    keys = [target]
    canonical = _canonical_target(target)
    if canonical and canonical not in keys:
        keys.append(canonical)

    if "://" in target:
        try:
            parsed = urlparse(target)
            no_query = urlunparse(
                (
                    (parsed.scheme or "").lower(),
                    (parsed.netloc or "").lower(),
                    parsed.path or "",
                    parsed.params or "",
                    "",
                    "",
                )
            )
            if no_query and no_query not in keys:
                keys.append(no_query)
        except Exception:
            pass

    return keys


def _is_target_validated(target):
    if not target:
        return False
    validated = _get_validated_target_set()
    for key in _target_validation_keys(target):
        if key in validated:
            return True
    return False


def _mark_target_validated(target):
    if not target:
        return
    values = _get_json_list_setting(VALIDATED_TARGETS_SETTING)
    for key in reversed(_target_validation_keys(target)):
        values.insert(0, key)
    _set_json_list_setting(VALIDATED_TARGETS_SETTING, values)


def _provider_validation_key(provider_id, media_id):
    return "{0}::{1}".format(provider_id or "", media_id or "")


def _is_provider_validated(provider_id, media_id):
    key = _provider_validation_key(provider_id, media_id)
    return bool(provider_id and media_id and key in set(_get_json_list_setting(VALIDATED_PROVIDER_SETTING)))


def _mark_provider_validated(provider_id, media_id):
    key = _provider_validation_key(provider_id, media_id)
    if not provider_id or not media_id:
        return
    values = _get_json_list_setting(VALIDATED_PROVIDER_SETTING)
    values.insert(0, key)
    _set_json_list_setting(VALIDATED_PROVIDER_SETTING, values)


def _validated_only_enabled():
    return _setting_bool("validated_only", False)


def _stream_validation_filter_mode():
    value = (ADDON.getSetting("stream_validation_filter") or "").strip().lower()

    enum_index_map = {
        "0": "all",
        "1": "working",
        "2": "nonworking",
    }
    if value in enum_index_map:
        mode = enum_index_map[value]
    else:
        mapping = {
            "all": "all",
            "show all": "all",
            "working": "working",
            "working only": "working",
            "validated": "working",
            "validated only": "working",
            "nonworking": "nonworking",
            "non-working": "nonworking",
            "non-working only": "nonworking",
            "down": "nonworking",
        }
        mode = mapping.get(value, "all")

    # Keep backward compatibility with the original toggle.
    if mode == "all" and _validated_only_enabled():
        return "working"
    return mode


def _stream_is_working(validated=False, vote=""):
    return bool(validated or (vote or "").strip().lower() == "up")


def _stream_is_nonworking(validated=False, vote=""):
    return bool((not validated) and (vote or "").strip().lower() == "down")


def _stream_visible_by_filter(validated=False, vote=""):
    mode = _stream_validation_filter_mode()
    if mode == "working":
        return _stream_is_working(validated=validated, vote=vote)
    if mode == "nonworking":
        return _stream_is_nonworking(validated=validated, vote=vote)
    return True


def _kodi_major_version():
    build = (xbmc.getInfoLabel("System.BuildVersion") or "").strip()
    if not build:
        return 0
    token = build.split(" ", 1)[0]
    try:
        return int(token.split(".", 1)[0])
    except Exception:
        return 0


def _validated_marker_override_setting():
    value = (ADDON.getSetting("validated_marker_override") or "").strip().lower()
    if not value:
        return "auto"

    enum_index_map = {
        "0": "auto",
        "1": "unicode",
        "2": "ok",
        "3": "legacy",
    }
    if value in enum_index_map:
        return enum_index_map[value]

    mapping = {
        "auto": "auto",
        "unicode": "unicode",
        "unicode check": "unicode",
        "check": "unicode",
        "checkmark": "unicode",
        "ok": "ok",
        "ok fallback": "ok",
        "fallback": "ok",
        "legacy": "legacy",
        "legacy v": "legacy",
        "v": "legacy",
    }
    return mapping.get(value, "auto")


def _validated_marker_for_runtime():
    override = _validated_marker_override_setting()
    if override == "unicode":
        return VALIDATED_MARKER_UNICODE
    if override == "ok":
        return VALIDATED_MARKER_FALLBACK
    if override == "legacy":
        return VALIDATED_MARKER_LEGACY

    # Kodi 18.x skins can miss glyph support for the check symbol.
    major = _kodi_major_version()
    if major and major <= 18:
        return VALIDATED_MARKER_FALLBACK
    return VALIDATED_MARKER_UNICODE


def _stream_vote_key(target="", provider_id="", media_id=""):
    provider_id = (provider_id or "").strip()
    media_id = (media_id or "").strip()
    if provider_id and media_id:
        return "provider://{0}/{1}".format(provider_id, media_id)
    target = (target or "").strip()
    if not target:
        return ""
    return _canonical_target(target) or target


def _get_stream_vote_rows():
    return _get_json_object_list_setting(STREAM_VOTES_SETTING)


def _set_stream_vote_rows(rows):
    _set_json_object_list_setting(STREAM_VOTES_SETTING, rows, max_items=MAX_VALIDATED_CACHE_ITEMS)


def _get_stream_vote(target="", provider_id="", media_id=""):
    key = _stream_vote_key(target=target, provider_id=provider_id, media_id=media_id)
    if not key:
        return ""
    for row in _get_stream_vote_rows():
        if (row.get("target") or "").strip() == key:
            vote = (row.get("vote") or "").strip().lower()
            if vote in ("up", "down"):
                return vote
            return ""
    return ""


def _set_stream_vote(target="", provider_id="", media_id="", vote=""):
    key = _stream_vote_key(target=target, provider_id=provider_id, media_id=media_id)
    vote = (vote or "").strip().lower()
    if not key:
        return False

    rows = [row for row in _get_stream_vote_rows() if (row.get("target") or "").strip() != key]
    if vote in ("up", "down"):
        rows.insert(0, {"target": key, "vote": vote})
    _set_stream_vote_rows(rows)
    return True


def _stream_status_marker(validated=False, vote=""):
    vote = (vote or "").strip().lower()
    if _stream_is_working(validated=validated, vote=vote):
        return _validated_marker_for_runtime()
    if vote == "down":
        return VALIDATED_MARKER_REJECTED
    return ""


def _stream_status_label(validated=False, vote=""):
    vote = (vote or "").strip().lower()
    if _stream_is_working(validated=validated, vote=vote):
        parts = ["Working"]
    elif _stream_is_nonworking(validated=validated, vote=vote):
        parts = ["Non-working"]
    else:
        parts = ["Unverified"]

    if vote == "up" and not validated:
        parts.append("Thumbs Up")
    elif vote == "down":
        parts.append("Thumbs Down")
    return " · ".join(parts)


def _integrated_target_status(target, is_folder=False):
    validated = _is_target_validated(target)
    vote = _get_stream_vote(target=target)

    # Folder targets may hold validated playable descendants.
    if is_folder and (not validated) and vote != "down":
        validated = _target_has_validated_descendant(target, max_depth=MAX_INTEGRATED_SCAN_DEPTH, max_items=160)

    return validated, vote


def _is_integration_bridge_title(title):
    normalized = " ".join(_normalize_label(title).split())
    if not normalized:
        return False

    if normalized.startswith("integrated "):
        return True

    bridge_tokens = [
        "open movies in",
        "open movie in",
        "open tv in",
        "open tv shows in",
        "open live in",
        "open live tv in",
        "open channels in",
        "open native add on",
        "open native addon",
    ]
    return any(token in normalized for token in bridge_tokens)


def _infer_category_from_text(text, default="live"):
    haystack = (text or "").strip()
    if not haystack:
        return default

    best_category = default
    best_score = 0
    for category_label, category in MENU_CATEGORIES:
        score = _score_keywords(haystack, CATEGORY_HINTS.get(category, []))
        if score > best_score:
            best_score = score
            best_category = category

    return best_category if best_score else default


def _category_tag_for_text(text, default="live"):
    category = _infer_category_from_text(text, default=default)
    for category_label, category_key in MENU_CATEGORIES:
        if category_key == category:
            return category_label
    return default.title()


def _integration_select_mode_setting():
    value = (ADDON.getSetting("integration_select_mode") or "").strip().lower()
    if not value:
        return "enabled"

    enum_index_map = {
        "0": "enabled",
        "1": "all",
    }
    if value in enum_index_map:
        return enum_index_map[value]

    mapping = {
        "enabled": "enabled",
        "enabled only": "enabled",
        "all": "all",
        "all available": "all",
        "available": "all",
    }
    return mapping.get(value, "enabled")


def _integration_include_disabled_from_setting():
    return _integration_select_mode_setting() == "all"


def _integration_mode_label():
    return "All available" if _integration_include_disabled_from_setting() else "Enabled only"


def _format_validated_label(label, validated):
    if not validated:
        return label
    label = label or ""
    marker = _validated_marker_for_runtime()
    if label.startswith(marker):
        return label
    if label.startswith(VALIDATED_MARKER_UNICODE):
        return label
    if label.startswith(VALIDATED_MARKER_FALLBACK):
        return label
    if label.startswith(VALIDATED_MARKER_LEGACY):
        return label
    return "{0}{1}".format(marker, label)


def _format_custom_mapped_label(label, custom_mapped=False):
    if not custom_mapped:
        return label
    label = label or ""
    if label.startswith(CUSTOM_MAPPED_MARKER):
        return label
    return "{0}{1}".format(CUSTOM_MAPPED_MARKER, label)


def _get_installed_video_addons(include_meos=False, include_disabled=True):
    meos_id = ADDON.getAddonInfo("id")

    rows = []
    seen = set()
    for addon_type in VIDEO_ADDON_TYPES:
        result = _json_rpc(
            "Addons.GetAddons",
            {
                "type": addon_type,
                "properties": ["name", "enabled", "thumbnail", "fanart", "version"],
            },
        )
        addons = (result or {}).get("addons") or []
        for addon in addons:
            addon_id = addon.get("addonid") or ""
            if not addon_id:
                continue
            if addon_id == meos_id and not include_meos:
                continue

            enabled = addon.get("enabled", True)
            if (not enabled) and (not include_disabled):
                continue
            if addon_id in seen:
                continue
            seen.add(addon_id)

            name = addon.get("name") or addon_id
            rows.append(
                {
                    "name": name,
                    "addon_id": addon_id,
                    "enabled": enabled,
                    "thumbnail": addon.get("thumbnail") or "",
                    "fanart": addon.get("fanart") or "",
                }
            )

    rows.sort(key=lambda item: item["name"].lower())
    return rows


def _normalize_label(text):
    text = (text or "").lower()
    return "".join(ch if ch.isalnum() else " " for ch in text)


def _score_category_match(label, category):
    normalized = " {0} ".format(_normalize_label(label))
    keywords = CATEGORY_HINTS.get(category, [])
    score = 0

    for keyword in keywords:
        normalized_keyword = _normalize_label(keyword).strip()
        if not normalized_keyword:
            continue
        token = " {0} ".format(normalized_keyword)
        if token in normalized:
            score += 10
            continue
        if normalized_keyword in normalized:
            score += 4

    return score


def _score_keywords(label, keywords):
    normalized = _normalize_label(label).strip()
    if not normalized:
        return 0

    wrapped = " {0} ".format(normalized)
    score = 0
    for keyword in keywords:
        token = _normalize_label(keyword).strip()
        if not token:
            continue
        wrapped_token = " {0} ".format(token)
        if normalized == token:
            score += 80
            continue
        if wrapped_token in wrapped:
            score += 40
            continue
        if token in normalized:
            score += 15
    return score


def _find_addon_rule(addon_id, addon_name):
    addon_id_norm = (addon_id or "").lower()
    addon_name_norm = (addon_name or "").lower()

    for rule in ADDON_CATEGORY_RULES:
        id_contains = [token.lower() for token in rule.get("id_contains", [])]
        label_contains = [token.lower() for token in rule.get("label_contains", [])]
        if any(token and token in addon_id_norm for token in id_contains):
            return rule
        if any(token and token in addon_name_norm for token in label_contains):
            return rule
    return None


def _addon_category_keywords(addon_id, addon_name, category):
    rule = _find_addon_rule(addon_id, addon_name)
    keywords = []
    if rule:
        keywords.extend(rule.get("categories", {}).get(category, []))
    keywords.extend(CATEGORY_HINTS.get(category, []))

    cleaned = []
    seen = set()
    for keyword in keywords:
        key = _normalize_label(keyword).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned.append(keyword)
    return cleaned


def _addon_category_paths(addon_id, addon_name, category):
    rule = _find_addon_rule(addon_id, addon_name)
    if not rule:
        return []

    paths = rule.get("paths", {}).get(category, [])
    cleaned = []
    seen = set()
    for path in paths:
        if not path:
            continue
        if isinstance(path, (str, unicode if "unicode" in globals() else str)):
            sequence = [path]
        else:
            sequence = []
            for step in path:
                if not step:
                    continue
                if isinstance(step, (str, unicode if "unicode" in globals() else str)):
                    sequence.append(step)
                else:
                    sequence.append(str(step))
        normalized = tuple(_normalize_label(step).strip() for step in sequence if _normalize_label(step).strip())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(sequence)
    return cleaned


def _match_path_step(entries, step_labels):
    if not entries:
        return None
    if isinstance(step_labels, (str,)):
        step_labels = [step_labels]

    best_entry = None
    best_score = 0
    for entry in entries:
        if entry.get("filetype") != "directory":
            continue
        label = entry.get("label") or entry.get("title") or ""
        score = _score_keywords(label, step_labels)
        if score > best_score:
            best_score = score
            best_entry = entry

    return best_entry


def _resolve_integrated_path_sequence(addon_id, sequence):
    root_target = "plugin://{0}/".format(addon_id)
    current_target = root_target
    current_entry = None

    for step in sequence:
        entries = _browse_directory_entries(current_target)
        if not entries:
            return None
        labels = step if isinstance(step, (list, tuple)) else [step]
        current_entry = _match_path_step(entries, labels)
        if not current_entry:
            return None
        current_target = current_entry.get("file") or ""
        if not current_target:
            return None

    return current_entry


def _resolve_integrated_targets(addon_id, category, addon_name=""):
    custom_matches = _custom_targets_for_addon_category(addon_id, category)
    if custom_matches:
        return custom_matches

    root_target = "plugin://{0}/".format(addon_id)
    exact_paths = _addon_category_paths(addon_id, addon_name, category)
    exact_results = []
    seen_targets = set()
    for sequence in exact_paths:
        resolved = _resolve_integrated_path_sequence(addon_id, sequence)
        if not resolved:
            continue
        target = resolved.get("file") or ""
        if not target or target in seen_targets:
            continue
        seen_targets.add(target)
        exact_results.append(
            {
                "target": target,
                "is_folder": resolved.get("filetype") == "directory",
                "matched_label": resolved.get("label") or resolved.get("title") or "",
                "thumbnail": resolved.get("thumbnail") or "",
                "fanart": resolved.get("fanart") or "",
                "score": 1000,
            }
        )
        if len(exact_results) >= MAX_INTEGRATED_TARGET_MATCHES:
            return exact_results

    if exact_results:
        return exact_results

    keywords = _addon_category_keywords(addon_id, addon_name, category)
    queue = [(root_target, 0)]
    visited_targets = set()
    candidates = []
    fallback_entries = []

    while queue:
        current_target, depth = queue.pop(0)
        if not current_target or current_target in visited_targets:
            continue
        visited_targets.add(current_target)

        entries = _browse_directory_entries(current_target)
        if not entries:
            continue
        if current_target == root_target:
            fallback_entries = entries

        for entry in entries:
            file_path = entry.get("file") or ""
            if not file_path:
                continue
            label = entry.get("label") or entry.get("title") or file_path
            score = _score_keywords(label, keywords)
            if score > 0:
                score += max(0, (MAX_INTEGRATED_SCAN_DEPTH - depth) * 5)
                candidates.append((score, depth, entry))

            if entry.get("filetype") == "directory" and depth < MAX_INTEGRATED_SCAN_DEPTH:
                queue.append((file_path, depth + 1))

    if candidates:
        candidates.sort(key=lambda row: (row[0], -row[1]), reverse=True)
        resolved = []
        seen_targets = set()
        for score, depth, entry in candidates:
            if score < 30 and resolved:
                continue
            target = entry.get("file") or ""
            if not target or target in seen_targets:
                continue
            seen_targets.add(target)
            resolved.append(
                {
                    "target": target,
                    "is_folder": entry.get("filetype") == "directory",
                    "matched_label": entry.get("label") or entry.get("title") or "",
                    "thumbnail": entry.get("thumbnail") or "",
                    "fanart": entry.get("fanart") or "",
                    "score": score,
                }
            )
            if len(resolved) >= MAX_INTEGRATED_TARGET_MATCHES:
                break
        if resolved:
            return resolved

    entries = fallback_entries
    if not entries:
        return [{"target": root_target, "is_folder": True, "matched_label": "", "thumbnail": "", "fanart": ""}]

    ranked_fallback = []
    for entry in entries:
        file_path = entry.get("file") or ""
        if not file_path:
            continue
        label = entry.get("label") or entry.get("title") or file_path
        category_score = _score_category_match(label, category)
        inferred_category = _infer_category_from_text("{0} {1}".format(label, file_path), default="")
        if category_score <= 0 and inferred_category != category:
            continue

        if inferred_category == category:
            category_score += 25
        ranked_fallback.append((category_score, entry))

    if not ranked_fallback:
        return [{"target": root_target, "is_folder": True, "matched_label": "", "thumbnail": "", "fanart": ""}]

    ranked_fallback.sort(key=lambda row: row[0], reverse=True)
    fallback_results = []
    seen_fallback = set()
    for _, entry in ranked_fallback:
        target = entry.get("file") or ""
        if not target or target in seen_fallback:
            continue
        seen_fallback.add(target)
        fallback_results.append(
            {
                "target": target,
                "is_folder": entry.get("filetype") == "directory",
                "matched_label": entry.get("label") or entry.get("title") or "",
                "thumbnail": entry.get("thumbnail") or "",
                "fanart": entry.get("fanart") or "",
            }
        )
        if len(fallback_results) >= MAX_INTEGRATED_TARGET_MATCHES:
            break

    if fallback_results:
        return fallback_results

    return [{"target": root_target, "is_folder": True, "matched_label": "", "thumbnail": "", "fanart": ""}]


def _browse_directory_entries(target):
    target = (target or "").strip()
    if not target:
        return []

    targets_to_try = []
    seen_targets = set()

    def _push_target(value):
        value = (value or "").strip()
        if not value or value in seen_targets:
            return
        seen_targets.add(value)
        targets_to_try.append(value)

    _push_target(target)

    parsed = urlparse(target)
    if parsed.scheme == "plugin" and parsed.netloc:
        path = parsed.path or "/"
        if not path.startswith("/"):
            path = "/" + path

        if not path.endswith("/"):
            _push_target(urlunparse((parsed.scheme, parsed.netloc, path + "/", parsed.params, parsed.query, parsed.fragment)))

        _push_target(urlunparse((parsed.scheme, parsed.netloc, "/", "", "", "")))

    request_profiles = [
        {"media": "files"},
        {"media": "video"},
        {},
    ]

    properties = ["label", "title", "file", "filetype", "thumbnail", "fanart", "plot"]

    for directory in targets_to_try:
        for profile in request_profiles:
            params = {
                "directory": directory,
                "properties": properties,
            }
            params.update(profile)
            result = _json_rpc("Files.GetDirectory", params)
            files = (result or {}).get("files") or []
            if not files:
                continue

            cleaned = []
            seen_files = set()
            for entry in files:
                file_path = (entry.get("file") or "").strip()
                if not file_path or file_path in seen_files:
                    continue
                if file_path in ("..", "."):
                    continue
                seen_files.add(file_path)
                cleaned.append(entry)

            if cleaned:
                return cleaned

    return []


def _resolve_integrated_target(addon_id, category, addon_name=""):
    return _resolve_integrated_targets(addon_id, category, addon_name=addon_name)[0]


def _title_key(text):
    normalized = _normalize_label(text)
    parts = [part for part in normalized.split() if part]
    return " ".join(parts)


def _iter_integrated_playables(target, max_depth, max_items):
    stack = [(target, 0)]
    visited = set()
    yielded = 0

    while stack and yielded < max_items:
        current_target, depth = stack.pop()
        if not current_target or current_target in visited:
            continue
        visited.add(current_target)

        entries = _browse_directory_entries(current_target)
        if not entries:
            continue

        for entry in entries:
            file_path = entry.get("file") or ""
            if not file_path:
                continue

            if entry.get("filetype") == "directory":
                if depth < max_depth:
                    stack.append((file_path, depth + 1))
                continue

            yielded += 1
            yield entry
            if yielded >= max_items:
                break


def _target_has_validated_descendant(target, max_depth=3, max_items=80):
    if _is_target_validated(target):
        return True

    for entry in _iter_integrated_playables(target, max_depth=max_depth, max_items=max_items):
        file_path = entry.get("file") or ""
        if file_path and _is_target_validated(file_path):
            return True
    return False


def _search_integrated_playables(target, query, max_depth=6, max_items=120):
    normalized_query = _normalize_label(query).strip()
    if not target or not normalized_query:
        return []

    results = []
    stack = [(target, 0)]
    visited = set()
    seen_targets = set()

    while stack and len(results) < max_items:
        current_target, depth = stack.pop()
        if not current_target or current_target in visited:
            continue
        visited.add(current_target)

        entries = _browse_directory_entries(current_target)
        if not entries:
            continue

        for entry in entries:
            file_path = entry.get("file") or ""
            if not file_path:
                continue

            label = entry.get("label") or entry.get("title") or file_path
            haystack = " {0} {1} ".format(_normalize_label(label), _normalize_label(file_path))

            if entry.get("filetype") == "directory":
                if depth < max_depth:
                    stack.append((file_path, depth + 1))
                continue

            if normalized_query in haystack and file_path not in seen_targets:
                results.append(entry)
                seen_targets.add(file_path)
                if len(results) >= max_items:
                    break

    return results


def add_integrated_category_items(category, seen_title_keys=None):
    selected = _get_integrated_addon_ids()
    if not selected:
        return 0

    if seen_title_keys is None:
        seen_title_keys = set()

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=False)}
    total_added = 0

    for addon_id in selected:
        row = installed.get(addon_id)
        if not row:
            continue

        addon_added = 0
        browse_shortcuts = 0
        browse_seen_targets = set()
        start_points = _resolve_integrated_targets(addon_id, category, addon_name=row.get("name", ""))
        for resolved in start_points:
            start_target = resolved.get("target") or "plugin://{0}/".format(addon_id)
            source_is_custom = bool(resolved.get("custom_mapped", False))

            if (
                resolved.get("is_folder", True)
                and start_target not in browse_seen_targets
                and browse_shortcuts < MAX_INTEGRATED_BROWSE_SHORTCUTS_PER_ADDON
            ):
                browse_seen_targets.add(start_target)
                browse_shortcuts += 1
                mapped_label = (resolved.get("matched_label") or category.title()).strip() or category.title()
                folder_validated, folder_vote = _integrated_target_status(start_target, is_folder=True)
                if _stream_visible_by_filter(validated=folder_validated, vote=folder_vote):
                    browse_label = _format_validated_label(
                        "[Integrated {0}] Browse {1}".format(row["name"], mapped_label),
                        folder_validated,
                    )
                    browse_label = _format_custom_mapped_label(browse_label, source_is_custom)
                    browse_art = {
                        "thumb": resolved.get("thumbnail") or row.get("thumbnail") or DEFAULT_ART["thumb"],
                        "icon": resolved.get("thumbnail") or row.get("thumbnail") or DEFAULT_ART["icon"],
                        "fanart": resolved.get("fanart") or row.get("fanart") or DEFAULT_ART["fanart"],
                    }
                    add_folder_item(
                        browse_label,
                        {"action": "external_browse", "target": start_target, "title": row["name"]},
                        art=browse_art,
                    )
                    total_added += 1
                    addon_added += 1

            if resolved.get("is_folder", True):
                playable_entries = _iter_integrated_playables(
                    start_target,
                    max_depth=MAX_INTEGRATED_SCAN_DEPTH,
                    max_items=MAX_INTEGRATED_ITEMS_PER_ADDON,
                )
            else:
                playable_entries = [{"file": start_target, "label": resolved.get("matched_label") or row["name"]}]

            for entry in playable_entries:
                target = entry.get("file") or ""
                if not target:
                    continue

                title = entry.get("label") or entry.get("title") or target
                if _is_integration_bridge_title(title):
                    continue
                title_key = _title_key(title)
                if title_key:
                    dedupe_key = "{0}:{1}".format(addon_id, title_key)
                else:
                    dedupe_key = "{0}:{1}".format(addon_id, target.lower())
                if dedupe_key and dedupe_key in seen_title_keys:
                    continue

                is_validated, vote = _integrated_target_status(target, is_folder=False)
                if not _stream_visible_by_filter(validated=is_validated, vote=vote):
                    continue

                if dedupe_key:
                    seen_title_keys.add(dedupe_key)

                label = _format_validated_label("[Integrated {0}] {1}".format(row["name"], title), is_validated)
                label = _format_custom_mapped_label(label, source_is_custom)
                art = {
                    "thumb": entry.get("thumbnail") or row.get("thumbnail") or DEFAULT_ART["thumb"],
                    "icon": entry.get("thumbnail") or row.get("thumbnail") or DEFAULT_ART["icon"],
                    "fanart": entry.get("fanart") or row.get("fanart") or DEFAULT_ART["fanart"],
                }
                add_validated_playable_item(
                    label,
                    {"action": "external_play", "target": target},
                    validated=is_validated,
                    info={"title": title, "genre": category.title()},
                    art=art,
                )
                add_vote_actions(
                    title,
                    {"target": target},
                    "external_browse",
                    {"return_target": start_target, "return_title": row["name"]},
                    art=art,
                )
                total_added += 1
                addon_added += 1

        # Some add-ons don't expose browsable items via Files.GetDirectory for deep plugin paths.
        # In that case, add one native shortcut so users still reach the correct section.
        if addon_added == 0 and start_points:
            fallback = start_points[0]
            fallback_target = fallback.get("target") or "plugin://{0}/".format(addon_id)
            fallback_label = fallback.get("matched_label") or category.title()
            art = {
                "thumb": fallback.get("thumbnail") or row.get("thumbnail") or DEFAULT_ART["thumb"],
                "icon": fallback.get("thumbnail") or row.get("thumbnail") or DEFAULT_ART["icon"],
                "fanart": fallback.get("fanart") or row.get("fanart") or DEFAULT_ART["fanart"],
            }
            add_folder_item(
                _format_custom_mapped_label(
                    "[Integrated {0}] Open {1} in {2}".format(category.title(), fallback_label, row["name"]),
                    source_is_custom,
                ),
                {"action": "external_native", "target": fallback_target},
                art=art,
            )
            total_added += 1

    return total_added


def _add_integrated_category_content(category, seen_title_keys=None):
    if seen_title_keys is None:
        seen_title_keys = set()
    return add_integrated_category_items(category, seen_title_keys=seen_title_keys)


def _add_cached_integrated_category_content(category, seen_title_keys=None):
    if seen_title_keys is None:
        seen_title_keys = set()

    selected = set(_get_integrated_addon_ids())
    if not selected:
        return 0

    cache = _get_integrated_menu_cache()
    cache.sort(
        key=lambda row: (
            (row.get("addon_name") or "").lower(),
            (row.get("label") or "").lower(),
            (row.get("target") or "").lower(),
        )
    )

    added = 0
    for row in cache:
        addon_id = (row.get("addon_id") or "").strip()
        if addon_id not in selected:
            continue

        row_category = (row.get("category") or "").strip().lower()
        if row_category != (category or "").strip().lower():
            continue

        target = row.get("target") or ""
        if not target:
            continue

        title = row.get("title") or row.get("label") or target
        title_key = _title_key(title)
        if title_key:
            dedupe_key = "{0}:{1}".format(addon_id, title_key)
        else:
            dedupe_key = "{0}:{1}".format(addon_id, target.lower())
        if dedupe_key in seen_title_keys:
            continue

        row_is_folder = bool(row.get("is_folder", True))
        cached_validated = bool(row.get("validated"))
        is_validated, vote = _integrated_target_status(target, is_folder=row_is_folder)
        is_validated = cached_validated or is_validated
        if not _stream_visible_by_filter(validated=is_validated, vote=vote):
            continue

        if dedupe_key:
            seen_title_keys.add(dedupe_key)

        addon_name = row.get("addon_name") or addon_id
        label = _format_validated_label("[Integrated {0}] {1}".format(addon_name, title), is_validated)
        label = _format_custom_mapped_label(label, bool(row.get("custom_mapped", False)))
        art = {
            "thumb": row.get("thumb") or DEFAULT_ART["thumb"],
            "icon": row.get("thumb") or DEFAULT_ART["icon"],
            "fanart": row.get("fanart") or DEFAULT_ART["fanart"],
        }

        if row_is_folder:
            add_folder_item(label, {"action": "external_browse", "target": target, "title": addon_name}, art=art)
        else:
            add_validated_playable_item(
                label,
                {"action": "external_play", "target": target},
                validated=is_validated,
                info={"title": title, "genre": category.title()},
                art=art,
            )

        add_vote_actions(
            title,
            {"target": target},
            "list_category",
            {"return_provider": "all", "return_category": category},
            art=art,
        )
        added += 1

    return added


def add_folder_item(label, query, art=None, context_items=None):
    item = xbmcgui.ListItem(label=label)
    item.setArt(art or DEFAULT_ART)
    if context_items:
        item.addContextMenuItems(context_items)
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=True)


def add_action_item(label, query, art=None, context_items=None):
    item = xbmcgui.ListItem(label=label)
    item.setArt(art or DEFAULT_ART)
    if context_items:
        item.addContextMenuItems(context_items)
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=False)


def add_playable_item(label, query, info=None, art=None, label2="", context_items=None):
    item = xbmcgui.ListItem(label=label)
    if label2:
        item.setLabel2(label2)
    item.setArt(art or DEFAULT_ART)
    if context_items:
        item.addContextMenuItems(context_items)
    item.setInfo("video", info or {"title": label})
    item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=False)


def add_validated_playable_item(label, query, validated=False, info=None, art=None, context_items=None):
    query = query or {}
    vote = _get_stream_vote(
        target=query.get("target", ""),
        provider_id=query.get("provider", ""),
        media_id=query.get("media_id", ""),
    )
    marker = _stream_status_marker(validated=validated, vote=vote)
    if marker:
        label = "{0}{1}".format(marker, label)

    video_info = dict(info or {"title": label})
    video_info.setdefault("mediatype", "video")
    video_info.setdefault("plotoutline", _stream_status_label(validated=validated, vote=vote))
    if _stream_is_working(validated=validated, vote=vote):
        video_info["playcount"] = 1
    add_playable_item(
        label,
        query,
        info=video_info,
        art=art,
        label2=_stream_status_label(validated=validated, vote=vote).upper(),
        context_items=context_items,
    )


def add_vote_actions(label, query, return_action, return_args=None, art=None):
    return_args = return_args or {}
    base = {
        "action": "vote_stream",
        "return_action": return_action,
        "label": label,
        "target": query.get("target", ""),
        "provider": query.get("provider", ""),
        "media_id": query.get("media_id", ""),
        "return_target": return_args.get("return_target", ""),
        "return_title": return_args.get("return_title", ""),
        "return_provider": return_args.get("return_provider", ""),
        "return_media_id": return_args.get("return_media_id", ""),
        "return_category": return_args.get("return_category", ""),
        "return_query": return_args.get("return_query", ""),
        "return_mode": return_args.get("return_mode", ""),
    }

    add_action_item("Thumbs Up: {0}".format(label), dict(base, vote="up"), art=art)
    add_action_item("Thumbs Down: {0}".format(label), dict(base, vote="down"), art=art)


def _validate_stream_after_play(target="", provider_id="", media_id="", title=""):
    key = _stream_vote_key(target=target, provider_id=provider_id, media_id=media_id)
    if not key:
        return

    if provider_id and media_id:
        if _is_provider_validated(provider_id, media_id) or _get_stream_vote(provider_id=provider_id, media_id=media_id) == "down":
            return
    else:
        if _is_target_validated(target) or _get_stream_vote(target=target) == "down":
            return

    player = xbmc.Player()
    saw_playback = False
    for _ in range(MIN_STREAM_VALIDATION_SECONDS):
        xbmc.sleep(1000)
        if player.isPlaying():
            saw_playback = True
            continue
        if saw_playback:
            _set_stream_vote(target=target, provider_id=provider_id, media_id=media_id, vote="down")
            display = title or media_id or target or "Stream"
            xbmcgui.Dialog().notification(
                "MEOS",
                "{0} marked non-working".format(display),
                xbmcgui.NOTIFICATION_WARNING,
                1800,
            )
            return

    if not saw_playback:
        return

    if provider_id and media_id:
        _mark_provider_validated(provider_id, media_id)
        display = title or media_id
    else:
        _mark_target_validated(target)
        display = title or target

    _set_stream_vote(target=target, provider_id=provider_id, media_id=media_id, vote="up")

    xbmcgui.Dialog().notification("MEOS", "{0} validated".format(display), xbmcgui.NOTIFICATION_INFO, 1800)


def list_root():
    add_folder_item("One-Click Live TV", {"action": "list_category", "provider": "all", "category": "live"})
    add_folder_item("One-Click Movies", {"action": "list_category", "provider": "all", "category": "movies"})
    add_folder_item("One-Click TV Shows", {"action": "list_category", "provider": "all", "category": "tv"})
    add_folder_item("Cable TV", {"action": "list_category", "provider": "all", "category": "cable"})
    add_folder_item("PPV Events", {"action": "list_category", "provider": "all", "category": "ppv"})
    add_folder_item("Sports Hub", {"action": "sports_menu"})
    add_folder_item("Manual Favorites", {"action": "favorites_menu"})
    add_folder_item("Integrate Other Add-ons", {"action": "integration_menu"})
    for label, category in MENU_CATEGORIES:
        add_folder_item(label, {"action": "list_category", "provider": "all", "category": category})
    add_folder_item("Awards", {"action": "awards_menu"})
    add_folder_item("Installed Add-ons Hub", {"action": "external_addons"})
    add_folder_item("Search All", {"action": "search_all"})
    add_folder_item("Settings", {"action": "open_settings"})
    xbmcplugin.endOfDirectory(HANDLE)


def _scan_context_items_for_target(target, title="", label="", is_folder=True):
    target = (target or "").strip()
    if not target:
        return []

    addon_id = _addon_id_from_target(target)
    if not addon_id:
        return []

    return [
        (
            "MEOS: Scan This Add-on For Content",
            "RunPlugin({0})".format(build_url({"action": "integration_scan_addon", "addon_id": addon_id})),
        ),
        (
            "MEOS: Scan This Folder To Add",
            "RunPlugin({0})".format(
                build_url(
                    {
                        "action": "integration_scan_folder",
                        "target": target,
                        "title": title,
                        "label": label or title or target,
                        "is_folder": "true" if bool(is_folder) else "false",
                        "return_target": target,
                        "return_title": title,
                    }
                )
            ),
        ),
    ]


def list_external_search_prompt(target, title="Add-on"):
    if not target:
        xbmcgui.Dialog().notification("MEOS", "Missing add-on target", xbmcgui.NOTIFICATION_ERROR, 3000)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    keyboard = xbmc.Keyboard("", "Search in {0}".format(title or "Add-on"))
    keyboard.doModal()
    if not keyboard.isConfirmed():
        list_external_browse(target, title)
        return

    query = keyboard.getText().strip()
    if not query:
        list_external_browse(target, title)
        return

    list_external_search_results(target, title, query)


def list_external_search_results(target, title="Add-on", query=""):
    target = (target or "").strip()
    query = (query or "").strip()
    if not target or not query:
        xbmcgui.Dialog().notification("MEOS", "Missing search target or query", xbmcgui.NOTIFICATION_ERROR, 3000)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    xbmcplugin.setPluginCategory(HANDLE, "Search: {0}".format(title or "Add-on"))
    add_folder_item("Search Again", {"action": "external_search_prompt", "target": target, "title": title})
    add_action_item(
        "Add Current Folder to Favorites",
        {
            "action": "favorite_add",
            "target": target,
            "label": "[{0}] {1}".format(_category_tag_for_text("{0} {1}".format(title, target)), title or "Add-on"),
            "title": title or "Add-on",
            "is_folder": "true",
            "return_action": "external_search_results",
            "return_target": target,
            "return_title": title,
            "return_query": query,
        },
    )
    add_action_item("Open Native Add-on Page", {"action": "external_native", "target": target})

    matches = _search_integrated_playables(target, query)
    if not matches:
        xbmcgui.Dialog().notification("MEOS", "No matching items found", xbmcgui.NOTIFICATION_INFO, 2500)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    for entry in matches:
        file_path = entry.get("file") or ""
        if not file_path:
            continue

        raw_label = entry.get("label") or entry.get("title") or file_path
        category_label = _category_tag_for_text("{0} {1} {2}".format(title or "", raw_label, file_path))
        label = "[{0}] {1}".format(category_label, raw_label)
        is_validated = _is_target_validated(file_path)
        label = _format_validated_label(label, is_validated)
        art = {
            "thumb": entry.get("thumbnail") or DEFAULT_ART["thumb"],
            "icon": entry.get("thumbnail") or DEFAULT_ART["icon"],
            "fanart": entry.get("fanart") or DEFAULT_ART["fanart"],
        }

        if entry.get("filetype") == "directory":
            add_action_item(
                "Add to Favorites: {0}".format(label),
                {
                    "action": "favorite_add",
                    "target": file_path,
                    "label": label,
                    "title": title,
                    "is_folder": "true",
                    "thumb": entry.get("thumbnail") or "",
                    "fanart": entry.get("fanart") or "",
                    "return_action": "external_search_results",
                    "return_target": target,
                    "return_title": title,
                    "return_query": query,
                },
            )
            add_folder_item(label, {"action": "external_browse", "target": file_path, "title": title}, art=art)
            add_vote_actions(
                raw_label,
                {"target": file_path},
                "external_search_results",
                {"return_target": target, "return_title": title, "return_query": query},
                art=art,
            )
        else:
            add_action_item(
                "Add to Favorites: {0}".format(label),
                {
                    "action": "favorite_add",
                    "target": file_path,
                    "label": label,
                    "title": title,
                    "is_folder": "false",
                    "thumb": entry.get("thumbnail") or "",
                    "fanart": entry.get("fanart") or "",
                    "return_action": "external_search_results",
                    "return_target": target,
                    "return_title": title,
                    "return_query": query,
                },
            )
            add_validated_playable_item(
                label,
                {"action": "external_play", "target": file_path},
                validated=is_validated,
                info={"title": raw_label},
                art=art,
            )
            add_vote_actions(
                raw_label,
                {"target": file_path},
                "external_search_results",
                {"return_target": target, "return_title": title, "return_query": query},
                art=art,
            )
            continue

        add_vote_actions(
            raw_label,
            {"target": file_path},
            "external_search_results",
            {"return_target": target, "return_title": title, "return_query": query},
            art=art,
        )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_sources(category):
    """Show one folder per provider that supports this category."""
    xbmcplugin.setPluginCategory(HANDLE, category.title())
    for provider in sorted(PROVIDERS.values(), key=lambda p: p.name.lower()):
        add_folder_item(
            provider.name,
            {"action": "list_category", "provider": provider.id, "category": category},
        )
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_sports_menu():
    xbmcplugin.setPluginCategory(HANDLE, "Sports Hub")
    for label, query in SPORT_TOPICS:
        add_folder_item(label, {"action": "sport_topic", "query": query})
    xbmcplugin.endOfDirectory(HANDLE)


def list_sport_topic(query):
    xbmcplugin.setPluginCategory(HANDLE, "Sports: {}".format(query))
    seen = set()
    found = 0
    for provider in sorted(PROVIDERS.values(), key=lambda p: p.name.lower()):
        auth_state = get_auth_state(provider.id)
        catalog = provider.get_catalog(auth_state, category="sports", query=query)
        for item in catalog:
            key = (provider.id, item.get("media_id", ""))
            if key in seen:
                continue
            seen.add(key)
            label = "[{}] {}".format(provider.name, item["title"])
            add_playable_item(
                label,
                {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
                {"title": item["title"], "genre": item.get("genre", "Sports")},
            )
            add_vote_actions(
                item["title"],
                {"provider": provider.id, "media_id": item["media_id"]},
                "sport_topic",
                {"return_query": query},
            )
            found += 1

    if not found:
        xbmcgui.Dialog().notification("MEOS", "No legal sports streams found for this filter", xbmcgui.NOTIFICATION_INFO, 3000)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_awards_menu():
    xbmcplugin.setPluginCategory(HANDLE, "Awards")
    for label, award, result in AWARD_MENU:
        add_folder_item(
            label,
            {"action": "awards_years", "award": award, "result": result, "sort": "desc"},
        )
    xbmcplugin.endOfDirectory(HANDLE)


def list_award_years(award, result, sort="desc"):
    if award not in ("oscar", "emmy") or result not in ("winner", "nominee"):
        xbmcgui.Dialog().notification("MEOS", "Invalid award filter", xbmcgui.NOTIFICATION_ERROR, 2500)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    current_sort = "desc" if sort != "asc" else "asc"
    next_sort = "asc" if current_sort == "desc" else "desc"
    sort_label = "Year: Newest First" if current_sort == "desc" else "Year: Oldest First"

    xbmcplugin.setPluginCategory(HANDLE, "{} {}".format(award.title(), result.title()))
    add_folder_item(
        "Sort: {}".format(sort_label),
        {"action": "awards_years", "award": award, "result": result, "sort": next_sort},
    )

    years = list(range(YEAR_MIN, YEAR_MAX + 1))
    years.sort(reverse=(current_sort == "desc"))
    for year in years:
        add_folder_item(
            str(year),
            {
                "action": "list_award_year",
                "provider": PRIMARY_PROVIDER_ID,
                "award": award,
                "result": result,
                "year": str(year),
            },
        )
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE)


def play_sample():
    configured_stream = ADDON.getSetting("sample_stream_url").strip()
    if configured_stream:
        stream_url = configured_stream
    else:
        stream_url = random.choice(DEFAULT_SAMPLE_STREAMS)
    item = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)


def list_providers():
    for provider in sorted(PROVIDERS.values(), key=lambda p: p.name.lower()):
        label = provider.name
        if provider.requires_oauth and not get_auth_state(provider.id):
            label += " (connect account)"
        add_folder_item(label, {"action": "provider_catalog", "provider": provider.id})
    xbmcplugin.endOfDirectory(HANDLE)


def connect_provider(provider):
    payload = provider.start_device_authorization()
    if not payload:
        xbmcgui.Dialog().ok("Connect Account", "Provider does not support device authorization yet.")
        return False

    verification_uri = payload.get("verification_uri") or ADDON.getSetting("partner_auth_url")
    user_code = payload.get("user_code") or "MEOS-0000"

    message = "Open: {0}\nCode: {1}".format(verification_uri, user_code)
    xbmcgui.Dialog().ok("Connect Account", message)

    # This scaffold keeps legal integration boundaries while allowing manual verification in test environments.
    confirmed = xbmcgui.Dialog().yesno(
        "MEOS",
        "Did you complete account linking on the website?",
        "This enables your linked provider features.",
        yeslabel="Yes",
        nolabel="No",
    )
    if confirmed:
        set_auth_state(provider.id, "connected")
        xbmcgui.Dialog().notification("MEOS", "Account connected", xbmcgui.NOTIFICATION_INFO, 2500)
        return True

    xbmcgui.Dialog().notification("MEOS", "Account not connected", xbmcgui.NOTIFICATION_WARNING, 2500)
    return False


def list_provider_catalog(provider_id):
    provider = PROVIDERS.get(provider_id)
    if not provider:
        xbmcgui.Dialog().notification("MEOS", "Unknown provider", xbmcgui.NOTIFICATION_ERROR, 2500)
        return

    auth_state = get_auth_state(provider.id)
    if provider.requires_oauth and not auth_state:
        add_folder_item("Connect account", {"action": "provider_auth", "provider": provider.id})
        xbmcplugin.endOfDirectory(HANDLE)
        return

    catalog = provider.get_catalog(auth_state)
    if not catalog:
        xbmcgui.Dialog().notification("MEOS", "No content available for this provider", xbmcgui.NOTIFICATION_INFO, 3000)
        add_folder_item("No content available", {"action": "list_providers"})
        xbmcplugin.endOfDirectory(HANDLE)
        return

    for item in catalog:
        add_playable_item(
            item["title"],
            {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
            {"title": item["title"], "genre": item.get("genre", "")},
        )
        add_vote_actions(
            item["title"],
            {"provider": provider.id, "media_id": item["media_id"]},
            "provider_catalog",
            {"return_provider": provider.id},
        )
    xbmcplugin.endOfDirectory(HANDLE)


def list_category(provider_id, category):
    if provider_id == "all":
        seen_titles = set()
        found = 0
        selected_integrated = _get_integrated_addon_ids()

        _sync_integrated_menu_cache()

        if category in ("movies", "tv", "live", "sports") and selected_integrated:
            add_action_item(
                "Rescan Integrated Add-ons Now",
                {
                    "action": "integration_rescan_category",
                    "return_provider": provider_id,
                    "return_category": category,
                },
            )

        seen = set()
        for provider in sorted(PROVIDERS.values(), key=lambda p: p.name.lower()):
            auth_state = get_auth_state(provider.id)
            catalog = provider.get_catalog(auth_state, category=category)
            for item in catalog:
                key = (provider.id, item.get("media_id", ""))
                if key in seen:
                    continue
                title_key = _title_key(item.get("title", ""))
                if title_key and title_key in seen_titles:
                    continue
                is_validated = _is_provider_validated(provider.id, item.get("media_id", ""))
                vote = _get_stream_vote(provider_id=provider.id, media_id=item.get("media_id", ""))
                if not _stream_visible_by_filter(validated=is_validated, vote=vote):
                    continue
                seen.add(key)
                if title_key:
                    seen_titles.add(title_key)
                label = _format_validated_label("[{0}] {1}".format(provider.name, item["title"]), is_validated)
                add_validated_playable_item(
                    label,
                    {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
                    validated=is_validated,
                    info={"title": item["title"], "genre": item.get("genre", "")},
                )
                add_vote_actions(
                    label,
                    {"provider": provider.id, "media_id": item["media_id"]},
                    "list_category",
                    {
                        "return_provider": provider_id,
                        "return_category": category,
                    },
                )
                found += 1

        found += _add_integrated_category_content(category, seen_title_keys=seen_titles)
        found += _add_cached_integrated_category_content(category, seen_title_keys=seen_titles)

        add_folder_item("Relevant Integrated Add-ons", {"action": "integration_menu"})

        if not found:
            xbmcgui.Dialog().notification("MEOS", "No items in this category", xbmcgui.NOTIFICATION_INFO, 2500)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    provider = PROVIDERS.get(provider_id)
    if not provider:
        xbmcgui.Dialog().notification("MEOS", "Unknown provider", xbmcgui.NOTIFICATION_ERROR, 2500)
        return

    auth_state = get_auth_state(provider.id)
    catalog = provider.get_catalog(auth_state, category=category)
    if not catalog:
        xbmcgui.Dialog().notification("MEOS", "No items in this category", xbmcgui.NOTIFICATION_INFO, 2500)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    for item in catalog:
        is_validated = _is_provider_validated(provider.id, item.get("media_id", ""))
        vote = _get_stream_vote(provider_id=provider.id, media_id=item.get("media_id", ""))
        if not _stream_visible_by_filter(validated=is_validated, vote=vote):
            continue
        add_validated_playable_item(
            _format_validated_label(item["title"], is_validated),
            {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
            validated=is_validated,
            info={"title": item["title"], "genre": item.get("genre", "")},
        )
        add_vote_actions(
            item["title"],
            {"provider": provider.id, "media_id": item["media_id"]},
            "list_category",
            {
                "return_provider": provider_id,
                "return_category": category,
            },
        )
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_award_year(provider_id, award, result, year):
    provider = PROVIDERS.get(provider_id)
    if not provider:
        xbmcgui.Dialog().notification("MEOS", "Unknown provider", xbmcgui.NOTIFICATION_ERROR, 2500)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    auth_state = get_auth_state(provider.id)
    catalog = provider.get_catalog(
        auth_state,
        category="award",
        query=None,
        year=year,
        award=award,
        result=result,
    )
    if not catalog:
        xbmcgui.Dialog().notification("MEOS", "No award items for this year", xbmcgui.NOTIFICATION_INFO, 2500)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    for item in catalog:
        add_playable_item(
            item["title"],
            {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
            {"title": item["title"], "genre": item.get("genre", "")},
        )
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_external_addons():
    xbmcplugin.setPluginCategory(HANDLE, "Installed Video Add-ons")
    include_meos = _setting_bool("external_include_meos", False)
    include_disabled = _setting_bool("external_include_disabled", False)
    rows = _get_installed_video_addons(include_meos=include_meos, include_disabled=include_disabled)

    if not rows:
        xbmcgui.Dialog().notification("MEOS", "No installed video add-ons found", xbmcgui.NOTIFICATION_INFO, 3000)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    for addon in rows:
        label = addon["name"] if addon.get("enabled", True) else "[DISABLED] {0}".format(addon["name"])
        addon_id = addon["addon_id"]
        target = "plugin://{0}/".format(addon_id)
        art = {
            "thumb": addon.get("thumbnail") or DEFAULT_ART["thumb"],
            "icon": addon.get("thumbnail") or DEFAULT_ART["icon"],
            "fanart": addon.get("fanart") or DEFAULT_ART["fanart"],
        }
        add_folder_item(label, {"action": "external_browse", "target": target, "title": label}, art=art)

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_integration_menu():
    xbmcplugin.setPluginCategory(HANDLE, "Integrate Other Add-ons")
    selected = _get_integrated_addon_ids()

    add_folder_item("Select Installed Add-ons", {"action": "integration_picker"})
    add_folder_item("Integrate All ({0})".format(_integration_mode_label()), {"action": "integration_select_all"})
    add_folder_item("Custom Integration Targets", {"action": "integration_custom_targets"})
    add_folder_item("Integrated Add-ons (Cached View)", {"action": "integration_cached_menu"})
    add_folder_item("Auto-Build Favorites from Top Matches", {"action": "favorites_autobuild"})
    add_folder_item("Integration Inspector", {"action": "integration_inspector"})
    add_folder_item("Clear Integrated Add-ons", {"action": "integration_clear"})

    if not selected:
        add_folder_item("No integrated add-ons selected", {"action": "integration_picker"})
        xbmcplugin.endOfDirectory(HANDLE)
        return

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    for addon_id in selected:
        row = installed.get(addon_id)
        label = row["name"] if row else addon_id
        if row and not row.get("enabled", True):
            label = "[DISABLED] {0}".format(label)
        add_folder_item(
            "Integrated: {0}".format(label),
            {"action": "external_browse", "target": "plugin://{0}/".format(addon_id), "title": label},
        )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_integration_picker():
    rows = _get_installed_video_addons(include_meos=False, include_disabled=True)
    if not rows:
        xbmcgui.Dialog().notification("MEOS", "No video add-ons available", xbmcgui.NOTIFICATION_INFO, 3000)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    xbmcplugin.setPluginCategory(HANDLE, "Select Add-ons to Integrate")
    selected_existing = _get_integrated_addon_ids()
    selected_set = set(selected_existing)

    add_folder_item("Done", {"action": "integration_menu"})
    add_folder_item("Select All ({0})".format(_integration_mode_label()), {"action": "integration_select_all"})
    add_folder_item("Clear Integrated Add-ons", {"action": "integration_clear"})

    for item in rows:
        addon_id = item["addon_id"]
        checked = "[x]" if addon_id in selected_set else "[ ]"
        art = {
            "thumb": item.get("thumbnail") or DEFAULT_ART["thumb"],
            "icon": item.get("thumbnail") or DEFAULT_ART["icon"],
            "fanart": item.get("fanart") or DEFAULT_ART["fanart"],
        }
        addon_label = item["name"]
        if not item.get("enabled", True):
            addon_label = "[DISABLED] {0}".format(addon_label)
        add_folder_item(
            "{0} {1}".format(checked, addon_label),
            {"action": "integration_toggle", "addon_id": addon_id},
            art=art,
        )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def toggle_integrated_addon(addon_id):
    addon_id = (addon_id or "").strip()
    if not addon_id:
        xbmcgui.Dialog().notification("MEOS", "Missing add-on id", xbmcgui.NOTIFICATION_ERROR, 2500)
        list_integration_picker()
        return

    selected = _get_integrated_addon_ids()
    if addon_id in selected:
        selected = [value for value in selected if value != addon_id]
        notice = "Removed integrated add-on"
    else:
        selected.append(addon_id)
        notice = "Added integrated add-on"

    _set_integrated_addon_ids(selected)
    _sync_integrated_menu_cache(selected)
    xbmcgui.Dialog().notification("MEOS", notice, xbmcgui.NOTIFICATION_INFO, 2000)
    list_integration_picker()


def select_all_integrated_addons(include_disabled=False):
    rows = _get_installed_video_addons(include_meos=False, include_disabled=include_disabled)
    if not rows:
        xbmcgui.Dialog().notification("MEOS", "No video add-ons available", xbmcgui.NOTIFICATION_INFO, 3000)
        list_integration_menu()
        return

    addon_ids = [row.get("addon_id") for row in rows if row.get("addon_id")]
    mode_label = "all available" if include_disabled else "enabled"
    _set_integrated_addon_ids(addon_ids)
    _sync_integrated_menu_cache(addon_ids)
    auto_build_enabled = _setting_bool("integrate_all_auto_build_favorites", False)
    if auto_build_enabled:
        favorites_before = len(_get_manual_favorites())
        for addon_id in addon_ids:
            row = next((item for item in rows if item.get("addon_id") == addon_id), None)
            addon_name = (row or {}).get("name") or addon_id
            for category_label, category in MENU_CATEGORIES:
                matches = _resolve_integrated_targets(addon_id, category, addon_name=addon_name)
                if not matches:
                    continue
                top = matches[0]
                target = (top.get("target") or "").strip()
                if not target:
                    continue
                _add_manual_favorite(
                    target,
                    label="[{0}] {1} - {2}".format(category_label, addon_name, top.get("matched_label") or "Top Match"),
                    title=addon_name,
                    is_folder=bool(top.get("is_folder", True)),
                    thumb=top.get("thumbnail") or (row or {}).get("thumbnail") or "",
                    fanart=top.get("fanart") or (row or {}).get("fanart") or "",
                )
        favorites_after = len(_get_manual_favorites())
        added_count = max(0, favorites_after - favorites_before)
        xbmcgui.Dialog().notification(
            "MEOS",
            "Integrated {0} {1} add-ons, auto-built {2} favorites".format(len(addon_ids), mode_label, added_count),
            xbmcgui.NOTIFICATION_INFO,
            3000,
        )
    else:
        xbmcgui.Dialog().notification(
            "MEOS",
            "Integrated {0} {1} add-ons".format(len(addon_ids), mode_label),
            xbmcgui.NOTIFICATION_INFO,
            2500,
        )
    list_integration_menu()


def clear_integrated_addons():
    confirmed = xbmcgui.Dialog().yesno(
        "MEOS",
        "Clear all integrated add-ons?",
        yeslabel="Clear",
        nolabel="Cancel",
    )
    if not confirmed:
        list_integration_menu()
        return

    _set_integrated_addon_ids([])
    _set_integrated_menu_cache([])
    xbmcgui.Dialog().notification("MEOS", "Integrated add-ons cleared", xbmcgui.NOTIFICATION_INFO, 2500)
    list_integration_menu()


def list_integration_inspector():
    xbmcplugin.setPluginCategory(HANDLE, "Integration Inspector")
    add_folder_item("Manual Favorites", {"action": "favorites_menu"})
    add_folder_item("Integrated Add-ons (Cached View)", {"action": "integration_cached_menu"})

    selected = _get_integrated_addon_ids()
    if not selected:
        add_folder_item("No integrated add-ons selected", {"action": "integration_picker"})
        xbmcplugin.endOfDirectory(HANDLE)
        return

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    for addon_id in selected:
        row = installed.get(addon_id)
        addon_name = row["name"] if row else addon_id
        if row and not row.get("enabled", True):
            addon_name = "[DISABLED] {0}".format(addon_name)
        add_folder_item(
            "Inspect: {0}".format(addon_name),
            {"action": "integration_audit_addon", "addon_id": addon_id},
        )
        add_folder_item(
            "Manual Browse & Search: {0}".format(addon_name),
            {"action": "external_browse", "target": "plugin://{0}/".format(addon_id), "title": addon_name},
        )
        add_action_item(
            "Scan This Add-on Now: {0}".format(addon_name),
            {"action": "integration_scan_addon", "addon_id": addon_id},
        )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_integration_addon_audit(addon_id):
    addon_id = (addon_id or "").strip()
    if not addon_id:
        xbmcgui.Dialog().notification("MEOS", "Missing add-on id", xbmcgui.NOTIFICATION_ERROR, 2500)
        list_integration_inspector()
        return

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    row = installed.get(addon_id)
    addon_name = row["name"] if row else addon_id
    root_target = "plugin://{0}/".format(addon_id)

    xbmcplugin.setPluginCategory(HANDLE, "Inspect: {0}".format(addon_name))
    add_folder_item("Open Add-on Root", {"action": "external_browse", "target": root_target, "title": addon_name})
    add_folder_item("Manual Browse & Search", {"action": "external_browse", "target": root_target, "title": addon_name})
    add_folder_item("Search Within Add-on", {"action": "external_search_prompt", "target": root_target, "title": addon_name})
    add_action_item(
        "Scan This Add-on Now",
        {"action": "integration_scan_addon", "addon_id": addon_id},
    )
    add_folder_item("Coverage Report", {"action": "integration_audit_report", "addon_id": addon_id})
    add_action_item(
        "Add Root to Favorites",
        {
            "action": "favorite_add",
            "target": root_target,
            "label": "[{0}] Root".format(addon_name),
            "title": addon_name,
            "is_folder": "true",
            "thumb": (row or {}).get("thumbnail", ""),
            "fanart": (row or {}).get("fanart", ""),
            "return_action": "integration_audit_addon",
            "return_addon_id": addon_id,
        },
    )

    for category_label, category in MENU_CATEGORIES:
        targets = _resolve_integrated_targets(addon_id, category, addon_name=addon_name)
        if not targets:
            continue
        for match in targets:
            target = match.get("target") or root_target
            matched_label = match.get("matched_label") or "Best Match"
            is_folder = bool(match.get("is_folder", True))

            label = "[{0}] {1} -> {2}".format(category_label, addon_name, matched_label)
            art = {
                "thumb": match.get("thumbnail") or (row or {}).get("thumbnail") or DEFAULT_ART["thumb"],
                "icon": match.get("thumbnail") or (row or {}).get("thumbnail") or DEFAULT_ART["icon"],
                "fanart": match.get("fanart") or (row or {}).get("fanart") or DEFAULT_ART["fanart"],
            }

            if is_folder:
                add_folder_item(label, {"action": "external_browse", "target": target, "title": addon_name}, art=art)
            else:
                add_validated_playable_item(
                    label,
                    {"action": "external_play", "target": target},
                    validated=_is_target_validated(target),
                    info={"title": label, "genre": category_label},
                    art=art,
                )

            add_action_item(
                "Add to Favorites: {0}".format(label),
                {
                    "action": "favorite_add",
                    "target": target,
                    "label": label,
                    "title": addon_name,
                    "is_folder": "true" if is_folder else "false",
                    "thumb": art.get("thumb", ""),
                    "fanart": art.get("fanart", ""),
                    "return_action": "integration_audit_addon",
                    "return_addon_id": addon_id,
                },
            )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def scan_integrated_addon_now(addon_id):
    addon_id = (addon_id or "").strip()
    if not addon_id:
        xbmcgui.Dialog().notification("MEOS", "Missing add-on id", xbmcgui.NOTIFICATION_ERROR, 2500)
        list_integration_inspector()
        return

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    row = installed.get(addon_id)
    if not row:
        xbmcgui.Dialog().notification("MEOS", "Add-on is not installed", xbmcgui.NOTIFICATION_WARNING, 2500)
        list_integration_inspector()
        return

    favorites = _get_manual_favorites()
    existing_targets = set((item.get("target") or "").strip().lower() for item in favorites)
    addon_name = row["name"]
    cache_added = _refresh_integrated_menu_cache(addon_id, addon_name, addon_row=row)
    added = 0

    for cached_row in _integrated_menu_cache_rows_for_addon(addon_id, addon_name, addon_row=row):
        target = cached_row.get("target") or ""
        if not target or target.lower() in existing_targets:
            continue
        if _add_manual_favorite(
            target,
            label="[{0}] {1} - {2}".format(
                cached_row.get("category_label") or "Category",
                addon_name,
                cached_row.get("label") or "Match",
            ),
            title=addon_name,
            is_folder=bool(cached_row.get("is_folder", True)),
            thumb=cached_row.get("thumb") or "",
            fanart=cached_row.get("fanart") or "",
        ):
            existing_targets.add(target.lower())
            added += 1

    xbmcgui.Dialog().notification(
        "MEOS",
        "Refreshed cache for {0} ({1} entries) and added {2} favorites".format(addon_name, cache_added, added),
        xbmcgui.NOTIFICATION_INFO,
        3000,
    )
    list_integrated_addons_cache()


def list_integrated_addons_cache(addon_id="", category=""):
    addon_id = (addon_id or "").strip().lower()
    category = (category or "").strip().lower()
    cache = _get_integrated_menu_cache()
    if addon_id:
        cache = [row for row in cache if (row.get("addon_id") or "").strip().lower() == addon_id]
    if category:
        cache = [row for row in cache if (row.get("category") or "").strip().lower() == category]

    xbmcplugin.setPluginCategory(HANDLE, "Integrated Add-ons")
    add_folder_item("Refresh Cached Integrated Add-ons", {"action": "integration_cached_refresh"})
    add_folder_item("Back to Integration Menu", {"action": "integration_menu"})

    if not cache:
        add_folder_item("No cached integrated add-ons yet", {"action": "integration_inspector"})
        xbmcplugin.endOfDirectory(HANDLE)
        return

    if not addon_id and not category:
        counts = {}
        for row in cache:
            key = (row.get("category") or "").strip().lower() or "other"
            counts[key] = counts.get(key, 0) + 1

        for category_label, category_key in MENU_CATEGORIES:
            count = counts.get(category_key, 0)
            if not count:
                continue
            add_folder_item(
                "[{0}] Cached ({1})".format(category_label, count),
                {"action": "integration_cached_menu", "category": category_key},
            )
        other_count = counts.get("other", 0)
        if other_count:
            add_folder_item(
                "[Other] Cached ({0})".format(other_count),
                {"action": "integration_cached_menu", "category": "other"},
            )
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    cache.sort(
        key=lambda row: (
            (row.get("addon_name") or "").lower(),
            (row.get("label") or "").lower(),
            (row.get("target") or "").lower(),
        )
    )

    for row in cache:
        target = row.get("target") or ""
        if not target:
            continue
        category_label = row.get("category_label") or "Category"
        addon_name = row.get("addon_name") or row.get("addon_id") or "Add-on"
        label = "[{0}] {1} - {2}".format(category_label, addon_name, row.get("label") or "Match")
        art = {
            "thumb": row.get("thumb") or DEFAULT_ART["thumb"],
            "icon": row.get("thumb") or DEFAULT_ART["icon"],
            "fanart": row.get("fanart") or DEFAULT_ART["fanart"],
        }

        if row.get("is_folder", True):
            add_folder_item(
                label,
                {"action": "external_browse", "target": target, "title": addon_name},
                art=art,
                context_items=_scan_context_items_for_target(target, title=addon_name, label=row.get("label") or label, is_folder=True),
            )
        else:
            add_validated_playable_item(
                label,
                {"action": "external_play", "target": target},
                validated=bool(row.get("validated")) or _is_target_validated(target),
                info={"title": label, "genre": category_label},
                art=art,
                context_items=_scan_context_items_for_target(target, title=addon_name, label=row.get("label") or label, is_folder=False),
            )
            add_vote_actions(
                row.get("label") or label,
                {"target": target},
                "integration_cached_menu",
                {"return_category": category},
                art=art,
            )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def refresh_integrated_addons_cache():
    selected = _get_integrated_addon_ids()
    if not selected:
        xbmcgui.Dialog().notification("MEOS", "No integrated add-ons selected", xbmcgui.NOTIFICATION_INFO, 2500)
        list_integrated_addons_cache()
        return

    refreshed = _sync_integrated_menu_cache(selected)

    xbmcgui.Dialog().notification(
        "MEOS",
        "Refreshed integrated add-on cache ({0} entries)".format(refreshed),
        xbmcgui.NOTIFICATION_INFO,
        3000,
    )
    list_integrated_addons_cache()


def rescan_integrated_for_category(return_provider="all", return_category="movies"):
    selected = _get_integrated_addon_ids()
    return_provider = (return_provider or "all").strip() or "all"
    return_category = (return_category or "movies").strip() or "movies"

    if not selected:
        xbmcgui.Dialog().notification("MEOS", "No integrated add-ons selected", xbmcgui.NOTIFICATION_INFO, 2500)
        list_category(return_provider, return_category)
        return

    refreshed = _sync_integrated_menu_cache(selected)
    xbmcgui.Dialog().notification(
        "MEOS",
        "Rescanned integrated add-ons ({0} entries)".format(refreshed),
        xbmcgui.NOTIFICATION_INFO,
        2500,
    )
    list_category(return_provider, return_category)


def scan_integrated_folder_action(target, title="", label="", is_folder="true", return_target="", return_title=""):
    target = (target or "").strip()
    title = (title or "").strip()
    label = (label or "").strip() or target
    return_target = (return_target or "").strip() or target
    return_title = (return_title or "").strip() or title

    addon_id = _addon_id_from_target(target)
    if not addon_id or not target:
        xbmcgui.Dialog().notification("MEOS", "Could not detect integrated add-on from target", xbmcgui.NOTIFICATION_WARNING, 2400)
        list_external_browse(return_target, return_title or "Add-on")
        return

    inferred_category = _infer_category_from_text("{0} {1} {2}".format(title, label, target), default="live")
    mapped = _set_custom_integrated_target(
        addon_id,
        inferred_category,
        target,
        label=label,
        is_folder=_to_bool(is_folder, True),
    )

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    row = installed.get(addon_id)
    addon_name = (row or {}).get("name") or addon_id
    refreshed = _refresh_integrated_menu_cache(addon_id, addon_name, addon_row=row)

    if mapped:
        xbmcgui.Dialog().notification(
            "MEOS",
            "Mapped folder to {0} and scanned {1} entries".format(inferred_category.title(), refreshed),
            xbmcgui.NOTIFICATION_INFO,
            2600,
        )
    else:
        xbmcgui.Dialog().notification("MEOS", "Folder scan mapping failed", xbmcgui.NOTIFICATION_WARNING, 2400)

    list_external_browse(return_target, return_title or addon_name)


def list_integration_audit_report(addon_id):
    addon_id = (addon_id or "").strip()
    if not addon_id:
        xbmcgui.Dialog().notification("MEOS", "Missing add-on id", xbmcgui.NOTIFICATION_ERROR, 2500)
        list_integration_inspector()
        return

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    row = installed.get(addon_id)
    addon_name = row["name"] if row else addon_id

    xbmcplugin.setPluginCategory(HANDLE, "Coverage: {0}".format(addon_name))
    add_folder_item("Back to Add-on Inspector", {"action": "integration_audit_addon", "addon_id": addon_id})

    for category_label, category in MENU_CATEGORIES:
        targets = _resolve_integrated_targets(addon_id, category, addon_name=addon_name)
        if not targets:
            add_action_item("{0}: no target match".format(category_label), {"action": "integration_audit_addon", "addon_id": addon_id})
            continue

        playable_count = 0
        folders = 0
        sample_target = targets[0].get("target") or "plugin://{0}/".format(addon_id)
        for target_info in targets:
            target = target_info.get("target") or ""
            if not target:
                continue
            if target_info.get("is_folder", True):
                folders += 1
                for _ in _iter_integrated_playables(target, max_depth=MAX_INTEGRATED_SCAN_DEPTH, max_items=80):
                    playable_count += 1
                    if playable_count >= 200:
                        break
            else:
                playable_count += 1
            if playable_count >= 200:
                break

        status = "{0}: targets {1}, folders {2}, playable hits {3}".format(
            category_label,
            len(targets),
            folders,
            playable_count,
        )
        add_folder_item(
            status,
            {"action": "external_browse", "target": sample_target, "title": addon_name},
        )
        add_action_item(
            "Add {0} sample target to Favorites".format(category_label),
            {
                "action": "favorite_add",
                "target": sample_target,
                "label": "[{0}] {1} sample".format(category_label, addon_name),
                "title": addon_name,
                "is_folder": "true",
                "thumb": (row or {}).get("thumbnail", ""),
                "fanart": (row or {}).get("fanart", ""),
                "return_action": "integration_audit_report",
                "return_addon_id": addon_id,
            },
        )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_manual_favorites():
    xbmcplugin.setPluginCategory(HANDLE, "Manual Favorites")
    favorites = _get_manual_favorites()

    add_folder_item("Add Favorite by Path/URL", {"action": "favorite_add_prompt"})
    add_folder_item("Add from Integrated Add-ons", {"action": "favorite_add_integrated_menu"})
    add_folder_item("Auto-Build from Integrated Add-ons", {"action": "favorites_autobuild"})
    add_folder_item("Integration Inspector", {"action": "integration_inspector"})
    if favorites:
        add_folder_item("Clear Favorites", {"action": "favorite_clear"})

    if not favorites:
        add_folder_item("No favorites yet", {"action": "favorite_add_prompt"})
        xbmcplugin.endOfDirectory(HANDLE)
        return

    for row in favorites:
        target = row.get("target") or ""
        if not target:
            continue
        label = row.get("label") or target
        is_folder = bool(row.get("is_folder", True))
        art = {
            "thumb": row.get("thumb") or DEFAULT_ART["thumb"],
            "icon": row.get("thumb") or DEFAULT_ART["icon"],
            "fanart": row.get("fanart") or DEFAULT_ART["fanart"],
        }

        if is_folder:
            add_folder_item("[Folder] {0}".format(label), {"action": "external_browse", "target": target, "title": row.get("title") or label}, art=art)
        else:
            add_validated_playable_item(
                "[Playable] {0}".format(label),
                {"action": "external_play", "target": target},
                validated=_is_target_validated(target),
                info={"title": label},
                art=art,
            )

        add_action_item("Remove: {0}".format(label), {"action": "favorite_remove", "target": target})

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_favorite_add_from_integrated_menu():
    xbmcplugin.setPluginCategory(HANDLE, "Add Favorite from Integrated Add-ons")
    selected = _get_integrated_addon_ids()
    if not selected:
        add_folder_item("No integrated add-ons selected", {"action": "integration_picker"})
        xbmcplugin.endOfDirectory(HANDLE)
        return

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    for addon_id in selected:
        row = installed.get(addon_id)
        addon_name = row["name"] if row else addon_id
        if row and not row.get("enabled", True):
            addon_name = "[DISABLED] {0}".format(addon_name)
        add_folder_item(
            "{0}".format(addon_name),
            {"action": "favorite_add_integrated_addon", "addon_id": addon_id},
        )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_favorite_add_from_integrated_addon(addon_id):
    addon_id = (addon_id or "").strip()
    if not addon_id:
        xbmcgui.Dialog().notification("MEOS", "Missing add-on id", xbmcgui.NOTIFICATION_ERROR, 2500)
        list_favorite_add_from_integrated_menu()
        return

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    row = installed.get(addon_id)
    addon_name = row["name"] if row else addon_id
    root_target = "plugin://{0}/".format(addon_id)

    xbmcplugin.setPluginCategory(HANDLE, "Add from: {0}".format(addon_name))
    add_action_item(
        "Add Root to Favorites",
        {
            "action": "favorite_add",
            "target": root_target,
            "label": "[{0}] Root".format(addon_name),
            "title": addon_name,
            "is_folder": "true",
            "thumb": (row or {}).get("thumbnail", ""),
            "fanart": (row or {}).get("fanart", ""),
            "return_action": "favorite_add_integrated_addon",
            "return_addon_id": addon_id,
        },
    )

    for category_label, category in MENU_CATEGORIES:
        targets = _resolve_integrated_targets(addon_id, category, addon_name=addon_name)
        if not targets:
            add_action_item("{0}: no match".format(category_label), {"action": "favorite_add_integrated_menu"})
            continue

        for match in targets:
            target = match.get("target") or root_target
            matched_label = match.get("matched_label") or "Top Match"
            is_folder = bool(match.get("is_folder", True))
            label = "[{0}] {1}".format(category_label, matched_label)
            art = {
                "thumb": match.get("thumbnail") or (row or {}).get("thumbnail") or DEFAULT_ART["thumb"],
                "icon": match.get("thumbnail") or (row or {}).get("thumbnail") or DEFAULT_ART["icon"],
                "fanart": match.get("fanart") or (row or {}).get("fanart") or DEFAULT_ART["fanart"],
            }

            add_action_item(
                "Add to Favorites: {0}".format(label),
                {
                    "action": "favorite_add",
                    "target": target,
                    "label": "[{0}] {1} - {2}".format(category_label, addon_name, matched_label),
                    "title": addon_name,
                    "is_folder": "true" if is_folder else "false",
                    "thumb": art.get("thumb", ""),
                    "fanart": art.get("fanart", ""),
                    "return_action": "favorite_add_integrated_addon",
                    "return_addon_id": addon_id,
                },
            )

            if is_folder:
                add_folder_item(
                    "Browse: {0}".format(label),
                    {"action": "external_browse", "target": target, "title": addon_name},
                    art=art,
                )
            else:
                add_validated_playable_item(
                    "Play: {0}".format(_format_validated_label(label, _is_target_validated(target))),
                    {"action": "external_play", "target": target},
                    validated=_is_target_validated(target),
                    info={"title": label, "genre": category_label},
                    art=art,
                )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def add_manual_favorite_prompt():
    target_kb = xbmc.Keyboard("", "Favorite Path or URL")
    target_kb.doModal()
    if not target_kb.isConfirmed():
        list_manual_favorites()
        return

    target = target_kb.getText().strip()
    if not target:
        xbmcgui.Dialog().notification("MEOS", "Favorite path is empty", xbmcgui.NOTIFICATION_WARNING, 2500)
        list_manual_favorites()
        return

    label_kb = xbmc.Keyboard(target, "Favorite Label")
    label_kb.doModal()
    label = target
    if label_kb.isConfirmed():
        label = (label_kb.getText() or "").strip() or target

    default_is_folder = target.startswith("plugin://") or target.endswith("/")
    is_folder = xbmcgui.Dialog().yesno(
        "MEOS",
        "Treat this favorite as a folder?",
        "Choose No to store as a direct playable.",
        yeslabel="Folder",
        nolabel="Playable",
    )
    if not is_folder and default_is_folder:
        is_folder = False
    elif is_folder and not default_is_folder:
        is_folder = True

    if _add_manual_favorite(target, label=label, title=label, is_folder=is_folder):
        xbmcgui.Dialog().notification("MEOS", "Favorite added", xbmcgui.NOTIFICATION_INFO, 2000)
    else:
        xbmcgui.Dialog().notification("MEOS", "Could not add favorite", xbmcgui.NOTIFICATION_ERROR, 2500)
    list_manual_favorites()


def add_manual_favorite_from_action(
    target,
    label="",
    title="",
    is_folder="true",
    thumb="",
    fanart="",
    return_action="favorites_menu",
    return_target="",
    return_title="",
    return_addon_id="",
    return_query="",
):
    added = _add_manual_favorite(
        target,
        label=label,
        title=title,
        is_folder=_to_bool(is_folder, True),
        thumb=thumb,
        fanart=fanart,
    )
    if added:
        xbmcgui.Dialog().notification("MEOS", "Added to favorites", xbmcgui.NOTIFICATION_INFO, 1800)
    else:
        xbmcgui.Dialog().notification("MEOS", "Favorite target missing", xbmcgui.NOTIFICATION_WARNING, 2200)

    if return_action == "external_browse":
        list_external_browse(return_target, return_title)
        return
    if return_action == "integration_audit_addon":
        list_integration_addon_audit(return_addon_id)
        return
    if return_action == "integration_audit_report":
        list_integration_audit_report(return_addon_id)
        return
    if return_action == "favorite_add_integrated_addon":
        list_favorite_add_from_integrated_addon(return_addon_id)
        return
    if return_action == "external_search_results":
        list_external_search_results(return_target, return_title, return_query)
        return
    list_manual_favorites()


def remove_manual_favorite_action(target):
    if _remove_manual_favorite(target):
        xbmcgui.Dialog().notification("MEOS", "Favorite removed", xbmcgui.NOTIFICATION_INFO, 1800)
    else:
        xbmcgui.Dialog().notification("MEOS", "Favorite not found", xbmcgui.NOTIFICATION_WARNING, 2200)
    list_manual_favorites()


def clear_manual_favorites():
    rows = _get_manual_favorites()
    if not rows:
        list_manual_favorites()
        return

    confirmed = xbmcgui.Dialog().yesno(
        "MEOS",
        "Clear all manual favorites?",
        yeslabel="Clear",
        nolabel="Cancel",
    )
    if not confirmed:
        list_manual_favorites()
        return

    _set_manual_favorites([])
    xbmcgui.Dialog().notification("MEOS", "Favorites cleared", xbmcgui.NOTIFICATION_INFO, 2200)
    list_manual_favorites()


def auto_build_favorites_from_integrated():
    selected = _get_integrated_addon_ids()
    if not selected:
        xbmcgui.Dialog().notification("MEOS", "No integrated add-ons selected", xbmcgui.NOTIFICATION_INFO, 2500)
        list_integration_menu()
        return

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    favorites = _get_manual_favorites()
    existing_targets = set((row.get("target") or "").strip().lower() for row in favorites)

    added = 0
    for addon_id in selected:
        row = installed.get(addon_id)
        addon_name = row["name"] if row else addon_id

        for category_label, category in MENU_CATEGORIES:
            matches = _resolve_integrated_targets(addon_id, category, addon_name=addon_name)
            if not matches:
                continue

            top = matches[0]
            target = (top.get("target") or "").strip()
            if not target or target.lower() in existing_targets:
                continue

            label_suffix = top.get("matched_label") or "Top Match"
            is_folder = bool(top.get("is_folder", True))
            if _add_manual_favorite(
                target,
                label="[{0}] {1} - {2}".format(category_label, addon_name, label_suffix),
                title=addon_name,
                is_folder=is_folder,
                thumb=top.get("thumbnail") or (row or {}).get("thumbnail") or "",
                fanart=top.get("fanart") or (row or {}).get("fanart") or "",
            ):
                existing_targets.add(target.lower())
                added += 1

    xbmcgui.Dialog().notification(
        "MEOS",
        "Auto-build added {0} favorites".format(added),
        xbmcgui.NOTIFICATION_INFO,
        3000,
    )
    list_manual_favorites()


def add_integrated_addon_shortcuts(category):
    selected = _get_integrated_addon_ids()
    if not selected:
        return

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    category_label = (category or "Library").title()

    for addon_id in selected:
        row = installed.get(addon_id)
        if not row:
            continue

        resolved = _resolve_integrated_target(addon_id, category, addon_name=row.get("name", ""))
        target = resolved["target"]
        matched_label = resolved.get("matched_label") or ""

        label = "[Integrated {0}] {1}".format(category_label, row["name"])
        if not row.get("enabled", True):
            label = "[DISABLED] {0}".format(label)
        elif matched_label:
            label = "{0} - {1}".format(label, matched_label)

        art = {
            "thumb": resolved.get("thumbnail") or row.get("thumbnail") or row.get("fanart") or DEFAULT_ART["thumb"],
            "icon": resolved.get("thumbnail") or row.get("thumbnail") or DEFAULT_ART["icon"],
            "fanart": resolved.get("fanart") or row.get("fanart") or DEFAULT_ART["fanart"],
        }
        if resolved.get("is_folder", True):
            add_folder_item(
                label,
                {"action": "external_browse", "target": target, "title": row["name"]},
                art=art,
            )
        else:
            add_validated_playable_item(
                label,
                {"action": "external_play", "target": target},
                validated=_is_target_validated(target),
                info={"title": label},
                art=art,
            )


def list_external_browse(target, title="Add-on"):
    if not target:
        xbmcgui.Dialog().notification("MEOS", "Missing add-on target", xbmcgui.NOTIFICATION_ERROR, 3000)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    xbmcplugin.setPluginCategory(HANDLE, "Integrated: {0}".format(title or "Add-on"))

    add_action_item(
        "Open Native Add-on Page",
        {"action": "external_native", "target": target},
    )
    add_action_item(
        "Add This Folder to Favorites",
        {
            "action": "favorite_add",
            "target": target,
            "label": "[{0}] Current Folder".format(_category_tag_for_text("{0} {1}".format(title or "Add-on", target))),
            "title": title or "Add-on",
            "is_folder": "true",
            "return_action": "external_browse",
            "return_target": target,
            "return_title": title,
        },
    )
    add_folder_item("Search This Add-on", {"action": "external_search_prompt", "target": target, "title": title})
    addon_id = _addon_id_from_target(target)
    if addon_id:
        add_action_item(
            "Scan This Integrated Add-on For Content",
            {"action": "integration_scan_addon", "addon_id": addon_id},
        )
        add_action_item(
            "Scan This Folder To Add Into MEOS",
            {
                "action": "integration_scan_folder",
                "target": target,
                "title": title,
                "label": title,
                "is_folder": "true",
                "return_target": target,
                "return_title": title,
            },
        )
        add_folder_item(
            "Set This Folder as Integrated Target",
            {
                "action": "integration_set_target_menu",
                "addon_id": addon_id,
                "target": target,
                "title": title,
                "label": title,
                "is_folder": "true",
                "return_target": target,
                "return_title": title,
            },
        )
    add_vote_actions(
        title or "Add-on",
        {"target": target},
        "external_browse",
        {"return_target": target, "return_title": title},
    )

    files = _browse_directory_entries(target)

    if not files:
        xbmcgui.Dialog().notification("MEOS", "No items found for this add-on", xbmcgui.NOTIFICATION_INFO, 3000)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    for entry in files:
        file_path = entry.get("file") or ""
        if not file_path:
            continue

        label = entry.get("label") or entry.get("title") or file_path
        is_validated = _is_target_validated(file_path)
        label = _format_validated_label(label, is_validated)
        art = {
            "thumb": entry.get("thumbnail") or DEFAULT_ART["thumb"],
            "icon": entry.get("thumbnail") or DEFAULT_ART["icon"],
            "fanart": entry.get("fanart") or DEFAULT_ART["fanart"],
        }

        if entry.get("filetype") == "directory":
            if addon_id:
                add_action_item(
                    "Map to MEOS: {0}".format(label),
                    {
                        "action": "integration_set_target_menu",
                        "addon_id": addon_id,
                        "target": file_path,
                        "title": title,
                        "label": entry.get("label") or entry.get("title") or file_path,
                        "is_folder": "true",
                        "thumb": entry.get("thumbnail") or "",
                        "fanart": entry.get("fanart") or "",
                        "return_target": target,
                        "return_title": title,
                    },
                    art=art,
                )
            add_action_item(
                "Add to Favorites: {0}".format(label),
                {
                    "action": "favorite_add",
                    "target": file_path,
                    "label": label,
                    "title": title,
                    "is_folder": "true",
                    "thumb": entry.get("thumbnail") or "",
                    "fanart": entry.get("fanart") or "",
                    "return_action": "external_browse",
                    "return_target": target,
                    "return_title": title,
                },
            )
            scan_context = _scan_context_items_for_target(
                file_path,
                title=title,
                label=entry.get("label") or entry.get("title") or file_path,
                is_folder=True,
            )
            add_folder_item(
                label,
                {"action": "external_browse", "target": file_path, "title": title},
                art=art,
                context_items=scan_context,
            )
            add_vote_actions(
                label,
                {"target": file_path},
                "external_browse",
                {"return_target": target, "return_title": title},
                art=art,
            )
        else:
            if addon_id:
                add_action_item(
                    "Map to MEOS: {0}".format(label),
                    {
                        "action": "integration_set_target_menu",
                        "addon_id": addon_id,
                        "target": file_path,
                        "title": title,
                        "label": entry.get("label") or entry.get("title") or file_path,
                        "is_folder": "false",
                        "thumb": entry.get("thumbnail") or "",
                        "fanart": entry.get("fanart") or "",
                        "return_target": target,
                        "return_title": title,
                    },
                    art=art,
                )
            add_action_item(
                "Add to Favorites: {0}".format(label),
                {
                    "action": "favorite_add",
                    "target": file_path,
                    "label": label,
                    "title": title,
                    "is_folder": "false",
                    "thumb": entry.get("thumbnail") or "",
                    "fanart": entry.get("fanart") or "",
                    "return_action": "external_browse",
                    "return_target": target,
                    "return_title": title,
                },
            )
            add_validated_playable_item(
                label,
                {"action": "external_play", "target": file_path},
                validated=is_validated,
                info={"title": label},
                art=art,
                context_items=_scan_context_items_for_target(
                    file_path,
                    title=title,
                    label=entry.get("label") or entry.get("title") or file_path,
                    is_folder=False,
                ),
            )
            add_vote_actions(
                label,
                {"target": file_path},
                "external_browse",
                {"return_target": target, "return_title": title},
                art=art,
            )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def play_external_item(target):
    if not target:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    if target.startswith("plugin://"):
        xbmc.executebuiltin('PlayMedia("{0}")'.format(target.replace('"', '%22')))
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        _validate_stream_after_play(target=target)
        return

    item = xbmcgui.ListItem(path=target)
    item.setArt(DEFAULT_ART)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)
    _validate_stream_after_play(target=target)


def list_custom_integration_targets(addon_id=""):
    addon_id = (addon_id or "").strip().lower()
    rows = _get_custom_integrated_targets()
    if addon_id:
        rows = [row for row in rows if (row.get("addon_id") or "").strip().lower() == addon_id]

    xbmcplugin.setPluginCategory(HANDLE, "Custom Integration Targets")
    add_folder_item("Back to Integration Menu", {"action": "integration_menu"})

    if not rows:
        add_folder_item("No custom targets saved", {"action": "integration_menu"})
        xbmcplugin.endOfDirectory(HANDLE)
        return

    rows.sort(
        key=lambda row: (
            (row.get("addon_id") or "").lower(),
            (row.get("category") or "").lower(),
            (row.get("label") or "").lower(),
            (row.get("target") or "").lower(),
        )
    )

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
    category_labels = {key: label for (label, key) in MENU_CATEGORIES}

    for row in rows:
        target = row.get("target") or ""
        if not target:
            continue
        row_addon_id = (row.get("addon_id") or "").strip()
        addon_name = (installed.get(row_addon_id) or {}).get("name") or row_addon_id
        category = (row.get("category") or "").strip().lower()
        category_label = category_labels.get(category, category.title() or "Category")
        mapped_label = (row.get("label") or "").strip() or target
        label = _format_custom_mapped_label("[{0}] {1} - {2}".format(category_label, addon_name, mapped_label), True)
        art = {
            "thumb": row.get("thumb") or (installed.get(row_addon_id) or {}).get("thumbnail") or DEFAULT_ART["thumb"],
            "icon": row.get("thumb") or (installed.get(row_addon_id) or {}).get("thumbnail") or DEFAULT_ART["icon"],
            "fanart": row.get("fanart") or (installed.get(row_addon_id) or {}).get("fanart") or DEFAULT_ART["fanart"],
        }

        if bool(row.get("is_folder", True)):
            add_folder_item(label, {"action": "external_browse", "target": target, "title": addon_name}, art=art)
        else:
            add_validated_playable_item(
                label,
                {"action": "external_play", "target": target},
                validated=_is_target_validated(target),
                info={"title": label, "genre": category_label},
                art=art,
            )

        add_action_item(
            "Remove Mapping: {0}".format(label),
            {
                "action": "integration_remove_target",
                "addon_id": row_addon_id,
                "category": category,
                "target": target,
                "return_addon_id": addon_id,
            },
        )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_integration_set_target_menu(addon_id, target, title="", label="", is_folder="true", thumb="", fanart="", return_target="", return_title=""):
    addon_id = (addon_id or "").strip()
    target = (target or "").strip()
    title = (title or "").strip() or addon_id or "Add-on"
    label = (label or "").strip() or target
    return_target = (return_target or "").strip() or target
    return_title = (return_title or "").strip() or title

    if not addon_id or not target:
        xbmcgui.Dialog().notification("MEOS", "Missing integration mapping target", xbmcgui.NOTIFICATION_WARNING, 2200)
        list_external_browse(return_target, return_title)
        return

    xbmcplugin.setPluginCategory(HANDLE, "Set Integration Target")
    add_folder_item("Back", {"action": "external_browse", "target": return_target, "title": return_title})
    add_folder_item("Custom Integration Targets", {"action": "integration_custom_targets", "addon_id": addon_id})

    for category_label, category in MENU_CATEGORIES:
        add_action_item(
            "Use This {0} for {1}".format("Folder" if _to_bool(is_folder, True) else "Playable", category_label),
            {
                "action": "integration_set_target",
                "addon_id": addon_id,
                "category": category,
                "target": target,
                "title": title,
                "label": label,
                "is_folder": "true" if _to_bool(is_folder, True) else "false",
                "thumb": thumb,
                "fanart": fanart,
                "return_target": return_target,
                "return_title": return_title,
            },
        )

    xbmcplugin.endOfDirectory(HANDLE)


def set_custom_integration_target_action(addon_id, category, target, title="", label="", is_folder="true", thumb="", fanart="", return_target="", return_title=""):
    addon_id = (addon_id or "").strip()
    category = (category or "").strip().lower()
    target = (target or "").strip()
    title = (title or "").strip() or addon_id or "Add-on"
    label = (label or "").strip() or title or target
    is_folder_value = _to_bool(is_folder, True)
    return_target = (return_target or "").strip() or target
    return_title = (return_title or "").strip() or title

    if not addon_id:
        addon_id = _addon_id_from_target(target)
    if not addon_id or not category or not target:
        xbmcgui.Dialog().notification("MEOS", "Missing custom integration mapping values", xbmcgui.NOTIFICATION_WARNING, 2200)
        list_external_browse(return_target, return_title)
        return

    if _set_custom_integrated_target(
        addon_id,
        category,
        target,
        label=label,
        is_folder=is_folder_value,
        thumb=thumb,
        fanart=fanart,
    ):
        installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
        row = installed.get(addon_id)
        addon_name = (row or {}).get("name") or addon_id
        _refresh_integrated_menu_cache(addon_id, addon_name, addon_row=row)
        xbmcgui.Dialog().notification("MEOS", "Custom integration target saved", xbmcgui.NOTIFICATION_INFO, 2200)
    else:
        xbmcgui.Dialog().notification("MEOS", "Could not save custom target", xbmcgui.NOTIFICATION_WARNING, 2200)

    list_external_browse(return_target, return_title)


def remove_custom_integration_target_action(addon_id, category, target, return_addon_id=""):
    removed = _remove_custom_integrated_target(addon_id, category, target)
    if removed:
        addon_id_clean = (addon_id or "").strip()
        installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=True)}
        row = installed.get(addon_id_clean)
        addon_name = (row or {}).get("name") or addon_id_clean
        _refresh_integrated_menu_cache(addon_id_clean, addon_name, addon_row=row)
        xbmcgui.Dialog().notification("MEOS", "Custom integration target removed", xbmcgui.NOTIFICATION_INFO, 2000)
    else:
        xbmcgui.Dialog().notification("MEOS", "Custom integration target not found", xbmcgui.NOTIFICATION_WARNING, 2200)

    list_custom_integration_targets(return_addon_id)


def open_external_native(target):
    if not target:
        xbmcgui.Dialog().notification("MEOS", "Missing add-on target", xbmcgui.NOTIFICATION_ERROR, 3000)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    xbmc.executebuiltin('ActivateWindow(Videos,"{0}",return)'.format(target.replace('"', '%22')))
    xbmcplugin.endOfDirectory(HANDLE)


def vote_stream_action(
    vote,
    target="",
    provider="",
    media_id="",
    label="",
    return_action="favorites_menu",
    return_target="",
    return_title="",
    return_provider="",
    return_media_id="",
    return_category="",
    return_query="",
    return_mode="",
):
    if _set_stream_vote(target=target, provider_id=provider, media_id=media_id, vote=vote):
        xbmcgui.Dialog().notification("MEOS", "Vote saved", xbmcgui.NOTIFICATION_INFO, 1800)
    else:
        xbmcgui.Dialog().notification("MEOS", "Vote target missing", xbmcgui.NOTIFICATION_WARNING, 2200)

    if return_action == "external_browse":
        list_external_browse(return_target, return_title)
        return
    if return_action == "external_search_results":
        list_external_search_results(return_target, return_title, return_query)
        return
    if return_action == "provider_catalog":
        list_provider_catalog(return_provider or provider)
        return
    if return_action == "list_category":
        list_category(return_provider, return_category)
        return
    if return_action == "sport_topic":
        list_sport_topic(return_query or "sports")
        return
    if return_action == "search_all":
        search_catalog()
        return
    if return_action == "search_all_results":
        list_search_all_results(return_query, mode=return_mode or "all")
        return
    list_manual_favorites()


def list_search_all_menu():
    xbmcplugin.setPluginCategory(HANDLE, "Search All")
    add_folder_item("Search Everything (Providers + Integrated)", {"action": "search_all_prompt", "mode": "all"})
    add_folder_item("Search Providers Only", {"action": "search_all_prompt", "mode": "providers"})
    add_folder_item("Search Integrated Add-ons Only", {"action": "search_all_prompt", "mode": "integrated"})
    xbmcplugin.endOfDirectory(HANDLE)


def search_all_prompt(mode="all"):
    keyboard = xbmc.Keyboard("", "Search MEOS")
    keyboard.doModal()
    if not keyboard.isConfirmed():
        xbmcplugin.endOfDirectory(HANDLE)
        return

    query = keyboard.getText().strip()
    if not query:
        xbmcplugin.endOfDirectory(HANDLE)
        return

    list_search_all_results(query, mode=mode)


def _search_integrated_addons(query):
    query = (query or "").strip()
    if not query:
        return []

    selected = _get_integrated_addon_ids()
    if not selected:
        return []

    installed = {item["addon_id"]: item for item in _get_installed_video_addons(include_meos=False, include_disabled=False)}
    results = []
    seen_targets = set()

    for addon_id in selected:
        row = installed.get(addon_id)
        if not row:
            continue

        addon_name = row.get("name") or addon_id
        start_targets = []
        seen_starts = set()

        def _add_start_target(value):
            value = (value or "").strip()
            if not value or value in seen_starts:
                return
            seen_starts.add(value)
            start_targets.append(value)

        _add_start_target("plugin://{0}/".format(addon_id))

        for _, category in MENU_CATEGORIES:
            matches = _resolve_integrated_targets(addon_id, category, addon_name=addon_name)
            for match in matches:
                _add_start_target(match.get("target") or "")

        addon_count = 0
        for start_target in start_targets:
            matched_rows = _search_integrated_playables(
                start_target,
                query,
                max_depth=MAX_INTEGRATED_SCAN_DEPTH,
                max_items=80,
            )
            for entry in matched_rows:
                file_path = (entry.get("file") or "").strip()
                if not file_path or file_path in seen_targets:
                    continue
                seen_targets.add(file_path)

                payload = dict(entry)
                payload["_addon_id"] = addon_id
                payload["_addon_name"] = addon_name
                results.append(payload)
                addon_count += 1

                if addon_count >= MAX_INTEGRATED_SEARCH_ITEMS_PER_ADDON:
                    break
                if len(results) >= MAX_INTEGRATED_SEARCH_TOTAL_ITEMS:
                    return results

            if addon_count >= MAX_INTEGRATED_SEARCH_ITEMS_PER_ADDON:
                break

    return results


def list_search_all_results(query, mode="all", provider_id=None):
    query = (query or "").strip()
    mode = (mode or "all").strip().lower() or "all"
    if mode not in ("all", "providers", "integrated"):
        mode = "all"

    if not query:
        xbmcgui.Dialog().notification("MEOS", "Search query is empty", xbmcgui.NOTIFICATION_WARNING, 2200)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    xbmcplugin.setPluginCategory(HANDLE, "Search: {0}".format(query))
    add_folder_item("Search Again", {"action": "search_all_prompt", "mode": mode})

    found = 0

    if mode in ("all", "providers"):
        targets = [PROVIDERS[provider_id]] if provider_id and provider_id in PROVIDERS else list(PROVIDERS.values())
        for provider in targets:
            auth_state = get_auth_state(provider.id)
            catalog = provider.get_catalog(auth_state, query=query)
            for item in catalog:
                label = "[{0}] {1}".format(provider.name, item["title"])
                is_validated = _is_provider_validated(provider.id, item.get("media_id", ""))
                vote = _get_stream_vote(provider_id=provider.id, media_id=item.get("media_id", ""))
                if not _stream_visible_by_filter(validated=is_validated, vote=vote):
                    continue
                add_validated_playable_item(
                    label,
                    {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
                    validated=is_validated,
                    info={"title": item["title"], "genre": item.get("genre", "")},
                )
                add_vote_actions(
                    item["title"],
                    {"provider": provider.id, "media_id": item["media_id"]},
                    "search_all_results",
                    {"return_query": query, "return_mode": mode},
                )
                found += 1

    if mode in ("all", "integrated"):
        integrated_matches = _search_integrated_addons(query)
        for entry in integrated_matches:
            file_path = (entry.get("file") or "").strip()
            if not file_path:
                continue

            raw_label = entry.get("label") or entry.get("title") or file_path
            addon_name = entry.get("_addon_name") or entry.get("_addon_id") or "Add-on"
            label = "[Integrated {0}] {1}".format(addon_name, raw_label)
            is_validated, vote = _integrated_target_status(file_path, is_folder=entry.get("filetype") == "directory")
            if not _stream_visible_by_filter(validated=is_validated, vote=vote):
                continue

            art = {
                "thumb": entry.get("thumbnail") or DEFAULT_ART["thumb"],
                "icon": entry.get("thumbnail") or DEFAULT_ART["icon"],
                "fanart": entry.get("fanart") or DEFAULT_ART["fanart"],
            }
            context_items = _scan_context_items_for_target(
                file_path,
                title=addon_name,
                label=raw_label,
                is_folder=entry.get("filetype") == "directory",
            )

            if entry.get("filetype") == "directory":
                add_folder_item(
                    _format_validated_label(label, is_validated),
                    {"action": "external_browse", "target": file_path, "title": addon_name},
                    art=art,
                    context_items=context_items,
                )
            else:
                add_validated_playable_item(
                    _format_validated_label(label, is_validated),
                    {"action": "external_play", "target": file_path},
                    validated=is_validated,
                    info={"title": raw_label, "genre": "Integrated"},
                    art=art,
                    context_items=context_items,
                )

            add_vote_actions(
                raw_label,
                {"target": file_path},
                "search_all_results",
                {"return_query": query, "return_mode": mode},
                art=art,
            )
            found += 1

    if not found:
        xbmcgui.Dialog().notification("MEOS", "No results found", xbmcgui.NOTIFICATION_INFO, 2500)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def search_catalog(provider_id=None):
    # Backward-compatible provider-only search entrypoint.
    search_all_prompt(mode="providers")


def open_settings():
    ADDON.openSettings()
    xbmcplugin.endOfDirectory(HANDLE)


def play_provider_item(provider_id, media_id):
    provider = PROVIDERS.get(provider_id)
    if not provider:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    auth_state = get_auth_state(provider.id)
    entitled, reason = provider.check_entitlement(media_id, auth_state)
    if not entitled:
        xbmcgui.Dialog().notification("MEOS", reason, xbmcgui.NOTIFICATION_WARNING, 3500)
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    playback = provider.resolve_playback(media_id, auth_state)
    if not playback or not playback.get("stream_url"):
        xbmcgui.Dialog().notification("MEOS", "Provider playback not configured", xbmcgui.NOTIFICATION_ERROR, 3500)
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    item = xbmcgui.ListItem(path=playback["stream_url"])
    item.setArt(DEFAULT_ART)
    item.setInfo("video", {"title": playback.get("title", media_id)})
    item.setContentLookup(False)

    mime_type = playback.get("mime_type", "").strip()
    if mime_type:
        item.setMimeType(mime_type)

    if playback.get("license_url"):
        item.setProperty("inputstream", "inputstream.adaptive")
        item.setProperty("inputstream.adaptive.manifest_type", playback.get("manifest_type", "mpd"))
        item.setProperty("inputstream.adaptive.license_type", playback.get("license_type", "com.widevine.alpha"))
        item.setProperty(
            "inputstream.adaptive.license_key",
            "{0}|{1}|R{{SSM}}|".format(playback["license_url"], playback.get("license_headers", "")),
        )

    xbmcplugin.setResolvedUrl(HANDLE, True, item)
    _validate_stream_after_play(provider_id=provider.id, media_id=media_id, title=playback.get("title", media_id))


def router(params):
    action = params.get("action")
    if not action:
        list_root()
        return

    if action == "play_sample":
        play_sample()
        return

    if action == "list_providers":
        list_providers()
        return

    if action == "list_category":
        list_category(params.get("provider", ""), params.get("category", ""))
        return

    if action == "sports_menu":
        list_sports_menu()
        return

    if action == "sport_topic":
        list_sport_topic(params.get("query", "sports"))
        return

    if action == "awards_menu":
        list_awards_menu()
        return

    if action == "awards_years":
        list_award_years(params.get("award", ""), params.get("result", ""), params.get("sort", "desc"))
        return

    if action == "list_award_year":
        list_award_year(
            params.get("provider", PRIMARY_PROVIDER_ID),
            params.get("award", ""),
            params.get("result", ""),
            params.get("year", ""),
        )
        return

    if action == "list_sources":
        list_sources(params.get("category", ""))
        return

    if action == "external_addons":
        list_external_addons()
        return

    if action == "integration_menu":
        list_integration_menu()
        return

    if action == "integration_inspector":
        list_integration_inspector()
        return

    if action == "integration_cached_menu":
        list_integrated_addons_cache(params.get("addon_id", ""), params.get("category", ""))
        return

    if action == "integration_cached_refresh":
        refresh_integrated_addons_cache()
        return

    if action == "integration_custom_targets":
        list_custom_integration_targets(params.get("addon_id", ""))
        return

    if action == "integration_set_target_menu":
        list_integration_set_target_menu(
            params.get("addon_id", ""),
            params.get("target", ""),
            params.get("title", ""),
            label=params.get("label", ""),
            is_folder=params.get("is_folder", "true"),
            thumb=params.get("thumb", ""),
            fanart=params.get("fanart", ""),
            return_target=params.get("return_target", ""),
            return_title=params.get("return_title", ""),
        )
        return

    if action == "integration_set_target":
        set_custom_integration_target_action(
            params.get("addon_id", ""),
            params.get("category", ""),
            params.get("target", ""),
            title=params.get("title", ""),
            label=params.get("label", ""),
            is_folder=params.get("is_folder", "true"),
            thumb=params.get("thumb", ""),
            fanart=params.get("fanart", ""),
            return_target=params.get("return_target", ""),
            return_title=params.get("return_title", ""),
        )
        return

    if action == "integration_remove_target":
        remove_custom_integration_target_action(
            params.get("addon_id", ""),
            params.get("category", ""),
            params.get("target", ""),
            return_addon_id=params.get("return_addon_id", ""),
        )
        return

    if action == "integration_rescan_category":
        rescan_integrated_for_category(
            params.get("return_provider", "all"),
            params.get("return_category", "movies"),
        )
        return

    if action == "integration_picker":
        list_integration_picker()
        return

    if action == "integration_toggle":
        toggle_integrated_addon(params.get("addon_id", ""))
        return

    if action == "integration_audit_addon":
        list_integration_addon_audit(params.get("addon_id", ""))
        return

    if action == "integration_audit_report":
        list_integration_audit_report(params.get("addon_id", ""))
        return

    if action == "integration_scan_addon":
        scan_integrated_addon_now(params.get("addon_id", ""))
        return

    if action == "integration_scan_folder":
        scan_integrated_folder_action(
            params.get("target", ""),
            title=params.get("title", ""),
            label=params.get("label", ""),
            is_folder=params.get("is_folder", "true"),
            return_target=params.get("return_target", ""),
            return_title=params.get("return_title", ""),
        )
        return

    if action == "integration_select_all":
        select_all_integrated_addons(include_disabled=_integration_include_disabled_from_setting())
        return

    if action == "integration_clear":
        clear_integrated_addons()
        return

    if action == "favorites_menu":
        list_manual_favorites()
        return

    if action == "favorite_add_prompt":
        add_manual_favorite_prompt()
        return

    if action == "favorite_add_integrated_menu":
        list_favorite_add_from_integrated_menu()
        return

    if action == "favorite_add_integrated_addon":
        list_favorite_add_from_integrated_addon(params.get("addon_id", ""))
        return

    if action == "favorite_add":
        add_manual_favorite_from_action(
            params.get("target", ""),
            label=params.get("label", ""),
            title=params.get("title", ""),
            is_folder=params.get("is_folder", "true"),
            thumb=params.get("thumb", ""),
            fanart=params.get("fanart", ""),
            return_action=params.get("return_action", "favorites_menu"),
            return_target=params.get("return_target", ""),
            return_title=params.get("return_title", ""),
            return_addon_id=params.get("return_addon_id", ""),
            return_query=params.get("return_query", ""),
        )
        return

    if action == "favorite_remove":
        remove_manual_favorite_action(params.get("target", ""))
        return

    if action == "favorite_clear":
        clear_manual_favorites()
        return

    if action == "favorites_autobuild":
        auto_build_favorites_from_integrated()
        return

    if action == "external_browse":
        list_external_browse(params.get("target", ""), params.get("title", "Add-on"))
        return

    if action == "external_search_prompt":
        list_external_search_prompt(params.get("target", ""), params.get("title", "Add-on"))
        return

    if action == "external_search_results":
        list_external_search_results(
            params.get("target", ""),
            params.get("title", "Add-on"),
            params.get("query", ""),
        )
        return

    if action == "vote_stream":
        vote_stream_action(
            params.get("vote", ""),
            target=params.get("target", ""),
            provider=params.get("provider", ""),
            media_id=params.get("media_id", ""),
            label=params.get("label", ""),
            return_action=params.get("return_action", "favorites_menu"),
            return_target=params.get("return_target", ""),
            return_title=params.get("return_title", ""),
            return_provider=params.get("return_provider", ""),
            return_media_id=params.get("return_media_id", ""),
            return_category=params.get("return_category", ""),
            return_query=params.get("return_query", ""),
            return_mode=params.get("return_mode", ""),
        )
        return

    if action == "external_play":
        play_external_item(params.get("target", ""))
        return

    if action == "external_native":
        open_external_native(params.get("target", ""))
        return

    if action == "search_all":
        list_search_all_menu()
        return

    if action == "search_all_prompt":
        search_all_prompt(params.get("mode", "all"))
        return

    if action == "search_all_results":
        list_search_all_results(
            params.get("query", ""),
            mode=params.get("mode", "all"),
        )
        return

    if action == "search":
        search_catalog(params.get("provider"))
        return

    if action == "open_settings":
        open_settings()
        return

    if action == "provider_auth":
        provider = PROVIDERS.get(params.get("provider", ""))
        if provider:
            connect_provider(provider)
        list_provider_catalog(params.get("provider", ""))
        return

    if action == "provider_catalog":
        list_provider_catalog(params.get("provider", ""))
        return

    if action == "provider_play":
        play_provider_item(params.get("provider", ""), params.get("media_id", ""))
        return

    xbmc.log("MEOS: unknown action {0}".format(action), xbmc.LOGWARNING)
    list_root()


router(dict(parse_qsl(sys.argv[2][1:])))
