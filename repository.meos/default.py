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
MAX_INTEGRATED_ITEMS_PER_ADDON = 300
MAX_INTEGRATED_TARGET_MATCHES = 8
MAX_VALIDATED_CACHE_ITEMS = 800
VALIDATED_TARGETS_SETTING = "external_validated_targets"
VALIDATED_PROVIDER_SETTING = "provider_validated_items"
MANUAL_FAVORITES_SETTING = "manual_favorites"
MAX_MANUAL_FAVORITES = 600
VALIDATED_MARKER_UNICODE = "[COLOR limegreen][B]✔[/B][/COLOR] "
VALIDATED_MARKER_FALLBACK = "[COLOR limegreen][B]OK[/B][/COLOR] "
VALIDATED_MARKER_LEGACY = "[COLOR limegreen][B]v[/B][/COLOR] "
CATEGORY_HINTS = {
    "movies": ["movie", "movies", "film", "cinema", "one click movie", "1 click movie"],
    "tv": ["tv", "shows", "tv shows", "series", "episodes", "one click tv", "1 click tv"],
    "docs": ["doc", "docs", "documentary", "documentaries"],
    "live": ["live", "channels", "channel", "iptv", "live tv", "cable", "cable tv", "local channels", "broadcast", "one click live", "1 click live"],
    "sports": ["sport", "sports", "nfl", "nba", "mlb", "ufc", "mma", "boxing", "wwe"],
    "award": ["award", "awards", "oscar", "emmy", "winner", "nominee"],
}
ADDON_CATEGORY_RULES = [
    {
        "name": "scrubs",
        "id_contains": ["scrubsv2", "scrubs", "plugin.video.scrubs", "plugin.video.scrubsv2"],
        "label_contains": ["scrubs", "scrubs v2"],
        "categories": {
            "movies": ["movies", "my movies", "new movies", "movie world", "boxsets", "1-click movies", "one click movies", "trending movies"],
            "tv": ["tv shows", "my tv shows", "new episodes", "series", "episodes", "1-click tv shows", "one click tv shows", "trending tv shows"],
            "live": ["live tv", "live channels", "channels", "iptv", "cable tv"],
            "sports": ["sports", "live sports", "sport"],
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
            "live": ["tv en vivo", "en vivo", "live tv", "canales", "channels", "cable", "latino"],
            "sports": ["deportes", "sports", "eventos"],
            "docs": ["documentales", "documentaries", "docs"],
        },
    },
    {
        "name": "loop",
        "id_contains": ["theloop", "plugin.video.loop", "plugin.video.theloop", "plugin.video.the.loop"],
        "label_contains": ["loop", "the loop"],
        "categories": {
            "movies": ["movies", "movie", "movie zone"],
            "tv": ["tv shows", "shows", "series", "tv"],
            "live": ["live tv", "channels", "live channels", "iptv", "cable", "abc mega list", "mega list", "abc", "cable channels"],
            "sports": ["sports", "live sports", "sport", "24/7 sports", "24/7", "sports area", "sports zone", "zone sports"],
            "docs": ["documentaries", "docs"],
        },
    },
    {
        "name": "ghost",
        "id_contains": ["ghost", "plugin.video.ghost", "plugin.video.theghost", "plugin.video.the.ghost"],
        "label_contains": ["ghost", "the ghost"],
        "categories": {
            "movies": ["movies", "movie", "1-click movies", "one click movies", "boxsets"],
            "tv": ["tv shows", "shows", "series", "1-click tv shows", "one click tv shows"],
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


def _get_installed_video_addons(include_meos=False, include_disabled=True):
    result = _json_rpc(
        "Addons.GetAddons",
        {
            "type": "xbmc.python.pluginsource",
            "properties": ["name", "enabled", "thumbnail", "fanart", "version"],
        },
    )
    addons = (result or {}).get("addons") or []
    meos_id = ADDON.getAddonInfo("id")

    rows = []
    for addon in addons:
        addon_id = addon.get("addonid") or ""
        if not addon_id:
            continue
        if addon_id == meos_id and not include_meos:
            continue

        enabled = addon.get("enabled", True)
        if (not enabled) and (not include_disabled):
            continue

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


def _resolve_integrated_targets(addon_id, category, addon_name=""):
    root_target = "plugin://{0}/".format(addon_id)
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
                }
            )
            if len(resolved) >= MAX_INTEGRATED_TARGET_MATCHES:
                break
        if resolved:
            return resolved

    entries = fallback_entries
    if not entries:
        return [{"target": root_target, "is_folder": True, "matched_label": "", "thumbnail": "", "fanart": ""}]

    best = None
    best_score = 0
    for entry in entries:
        file_path = entry.get("file") or ""
        if not file_path:
            continue
        label = entry.get("label") or entry.get("title") or file_path
        score = _score_category_match(label, category)
        if score > best_score:
            best_score = score
            best = entry

    if not best:
        return [{"target": root_target, "is_folder": True, "matched_label": "", "thumbnail": "", "fanart": ""}]

    return [
        {
            "target": best.get("file") or root_target,
            "is_folder": best.get("filetype") == "directory",
            "matched_label": best.get("label") or best.get("title") or "",
            "thumbnail": best.get("thumbnail") or "",
            "fanart": best.get("fanart") or "",
        }
    ]


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
        start_points = _resolve_integrated_targets(addon_id, category, addon_name=row.get("name", ""))
        for resolved in start_points:
            start_target = resolved.get("target") or "plugin://{0}/".format(addon_id)

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
                dedupe_key = _title_key(title)
                if dedupe_key and dedupe_key in seen_title_keys:
                    continue

                is_validated = _is_target_validated(target)
                if _validated_only_enabled() and not is_validated:
                    continue

                if dedupe_key:
                    seen_title_keys.add(dedupe_key)

                label = _format_validated_label("[Integrated {0}] {1}".format(row["name"], title), is_validated)
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
                "[Integrated {0}] Open {1} in {2}".format(category.title(), fallback_label, row["name"]),
                {"action": "external_native", "target": fallback_target},
                art=art,
            )
            total_added += 1

    return total_added


def add_folder_item(label, query, art=None):
    item = xbmcgui.ListItem(label=label)
    item.setArt(art or DEFAULT_ART)
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=True)


def add_action_item(label, query, art=None):
    item = xbmcgui.ListItem(label=label)
    item.setArt(art or DEFAULT_ART)
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=False)


def add_playable_item(label, query, info=None, art=None, label2=""):
    item = xbmcgui.ListItem(label=label)
    if label2:
        item.setLabel2(label2)
    item.setArt(art or DEFAULT_ART)
    item.setInfo("video", info or {"title": label})
    item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=False)


def add_validated_playable_item(label, query, validated=False, info=None, art=None):
    video_info = dict(info or {"title": label})
    video_info.setdefault("mediatype", "video")
    if validated:
        video_info.setdefault("plotoutline", "Validated working stream")
    else:
        video_info.setdefault("plotoutline", "Not validated yet")
    if validated:
        video_info["playcount"] = 1
    add_playable_item(
        label,
        query,
        info=video_info,
        art=art,
        label2="VALIDATED" if validated else "UNVERIFIED",
    )


def list_root():
    add_folder_item("One-Click Live TV", {"action": "list_category", "provider": "all", "category": "live"})
    add_folder_item("One-Click Movies", {"action": "list_category", "provider": "all", "category": "movies"})
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
    xbmcplugin.endOfDirectory(HANDLE)


def list_category(provider_id, category):
    validated_only = _validated_only_enabled()
    if provider_id == "all":
        add_integrated_addon_shortcuts(category)
        seen_titles = set()
        found = add_integrated_category_items(category, seen_title_keys=seen_titles)

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
                if validated_only and not is_validated:
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
                found += 1

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
        if validated_only and not is_validated:
            continue
        add_validated_playable_item(
            _format_validated_label(item["title"], is_validated),
            {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
            validated=is_validated,
            info={"title": item["title"], "genre": item.get("genre", "")},
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
    xbmcgui.Dialog().notification("MEOS", "Integrated add-ons cleared", xbmcgui.NOTIFICATION_INFO, 2500)
    list_integration_menu()


def list_integration_inspector():
    xbmcplugin.setPluginCategory(HANDLE, "Integration Inspector")
    add_folder_item("Manual Favorites", {"action": "favorites_menu"})

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
            "label": "[{0}] Current Folder".format(title or "Add-on"),
            "title": title or "Add-on",
            "is_folder": "true",
            "return_action": "external_browse",
            "return_target": target,
            "return_title": title,
        },
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
            add_folder_item(label, {"action": "external_browse", "target": file_path, "title": title}, art=art)
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
            )

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def play_external_item(target):
    if not target:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    if target.startswith("plugin://"):
        _mark_target_validated(target)
        xbmc.executebuiltin('PlayMedia("{0}")'.format(target.replace('"', '%22')))
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    item = xbmcgui.ListItem(path=target)
    item.setArt(DEFAULT_ART)
    _mark_target_validated(target)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)


def open_external_native(target):
    if not target:
        xbmcgui.Dialog().notification("MEOS", "Missing add-on target", xbmcgui.NOTIFICATION_ERROR, 3000)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    xbmc.executebuiltin('ActivateWindow(Videos,"{0}",return)'.format(target.replace('"', '%22')))
    xbmcplugin.endOfDirectory(HANDLE)


def search_catalog(provider_id=None):
    keyboard = xbmc.Keyboard("", "Search MEOS")
    keyboard.doModal()
    if not keyboard.isConfirmed():
        xbmcplugin.endOfDirectory(HANDLE)
        return

    query = keyboard.getText().strip()
    if not query:
        xbmcplugin.endOfDirectory(HANDLE)
        return

    targets = [PROVIDERS[provider_id]] if provider_id and provider_id in PROVIDERS else list(PROVIDERS.values())
    found = 0
    for provider in targets:
        auth_state = get_auth_state(provider.id)
        catalog = provider.get_catalog(auth_state, query=query)
        for item in catalog:
            label = "[{}] {}".format(provider.name, item["title"])
            add_playable_item(
                label,
                {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
                {"title": item["title"], "genre": item.get("genre", "")},
            )
            found += 1
    if not found:
        xbmcgui.Dialog().notification("MEOS", "No results found", xbmcgui.NOTIFICATION_INFO, 2500)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


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

    _mark_provider_validated(provider.id, media_id)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)


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

    if action == "external_play":
        play_external_item(params.get("target", ""))
        return

    if action == "external_native":
        open_external_native(params.get("target", ""))
        return

    if action == "search_all":
        search_catalog()
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
