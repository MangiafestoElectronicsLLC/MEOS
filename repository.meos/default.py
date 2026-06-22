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
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import urlencode, parse_qsl


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
MAX_INTEGRATED_SCAN_DEPTH = 2
MAX_INTEGRATED_ITEMS_PER_ADDON = 120
CATEGORY_HINTS = {
    "movies": ["movie", "movies", "film", "cinema", "one click movie", "1 click movie"],
    "tv": ["tv", "shows", "tv shows", "series", "episodes", "one click tv", "1 click tv"],
    "docs": ["doc", "docs", "documentary", "documentaries"],
    "live": ["live", "channels", "iptv", "live tv", "one click live", "1 click live"],
    "sports": ["sport", "sports", "nfl", "nba", "mlb", "ufc", "mma", "boxing", "wwe"],
    "award": ["award", "awards", "oscar", "emmy", "winner", "nominee"],
}

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


def _browse_directory_entries(target):
    result = _json_rpc(
        "Files.GetDirectory",
        {
            "directory": target,
            "media": "files",
            "properties": ["title", "file", "filetype", "thumbnail", "fanart", "plot"],
        },
    )
    return (result or {}).get("files") or []


def _resolve_integrated_target(addon_id, category):
    root_target = "plugin://{0}/".format(addon_id)
    entries = _browse_directory_entries(root_target)
    if not entries:
        return {"target": root_target, "is_folder": True, "matched_label": ""}

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
        return {"target": root_target, "is_folder": True, "matched_label": ""}

    return {
        "target": best.get("file") or root_target,
        "is_folder": best.get("filetype") == "directory",
        "matched_label": best.get("label") or best.get("title") or "",
    }


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

        resolved = _resolve_integrated_target(addon_id, category)
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
            if dedupe_key:
                seen_title_keys.add(dedupe_key)

            label = "[Integrated {0}] {1}".format(row["name"], title)
            art = {
                "thumb": entry.get("thumbnail") or row.get("thumbnail") or DEFAULT_ART["thumb"],
                "icon": entry.get("thumbnail") or row.get("thumbnail") or DEFAULT_ART["icon"],
                "fanart": entry.get("fanart") or row.get("fanart") or DEFAULT_ART["fanart"],
            }
            add_playable_item(
                label,
                {"action": "external_play", "target": target},
                {"title": title, "genre": category.title()},
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


def add_playable_item(label, query, info=None, art=None):
    item = xbmcgui.ListItem(label=label)
    item.setArt(art or DEFAULT_ART)
    item.setInfo("video", info or {"title": label})
    item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=False)


def list_root():
    add_folder_item("One-Click Live TV", {"action": "list_category", "provider": "all", "category": "live"})
    add_folder_item("One-Click Movies", {"action": "list_category", "provider": "all", "category": "movies"})
    add_folder_item("Sports Hub", {"action": "sports_menu"})
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
                seen.add(key)
                title_key = _title_key(item.get("title", ""))
                if title_key and title_key in seen_titles:
                    continue
                if title_key:
                    seen_titles.add(title_key)
                label = "[{}] {}".format(provider.name, item["title"])
                add_playable_item(
                    label,
                    {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
                    {"title": item["title"], "genre": item.get("genre", "")},
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
        add_playable_item(
            item["title"],
            {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
            {"title": item["title"], "genre": item.get("genre", "")},
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


def pick_integrated_addons():
    rows = _get_installed_video_addons(include_meos=False, include_disabled=False)
    if not rows:
        xbmcgui.Dialog().notification("MEOS", "No enabled video add-ons available", xbmcgui.NOTIFICATION_INFO, 3000)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    selected_existing = set(_get_integrated_addon_ids())
    labels = [item["name"] for item in rows]
    preselect = [index for index, item in enumerate(rows) if item["addon_id"] in selected_existing]

    selected_indexes = xbmcgui.Dialog().multiselect(
        "Select Add-ons to Integrate",
        labels,
        preselect=preselect,
    )
    if selected_indexes is None:
        xbmcplugin.endOfDirectory(HANDLE)
        return

    chosen_ids = [rows[index]["addon_id"] for index in selected_indexes if 0 <= index < len(rows)]
    _set_integrated_addon_ids(chosen_ids)
    xbmcgui.Dialog().notification("MEOS", "Integrated add-ons updated", xbmcgui.NOTIFICATION_INFO, 2500)
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

        resolved = _resolve_integrated_target(addon_id, category)
        target = resolved["target"]
        matched_label = resolved.get("matched_label") or ""

        label = "[Integrated {0}] {1}".format(category_label, row["name"])
        if not row.get("enabled", True):
            label = "[DISABLED] {0}".format(label)
        elif matched_label:
            label = "{0} - {1}".format(label, matched_label)

        art = {
            "thumb": row.get("thumbnail") or DEFAULT_ART["thumb"],
            "icon": row.get("thumbnail") or DEFAULT_ART["icon"],
            "fanart": row.get("fanart") or DEFAULT_ART["fanart"],
        }
        if resolved.get("is_folder", True):
            add_folder_item(
                label,
                {"action": "external_browse", "target": target, "title": row["name"]},
                art=art,
            )
        else:
            add_playable_item(
                label,
                {"action": "external_play", "target": target},
                {"title": label},
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
        art = {
            "thumb": entry.get("thumbnail") or DEFAULT_ART["thumb"],
            "icon": entry.get("thumbnail") or DEFAULT_ART["icon"],
            "fanart": entry.get("fanart") or DEFAULT_ART["fanart"],
        }

        if entry.get("filetype") == "directory":
            add_folder_item(label, {"action": "external_browse", "target": file_path, "title": title}, art=art)
        else:
            add_playable_item(label, {"action": "external_play", "target": file_path}, {"title": label}, art=art)

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def play_external_item(target):
    if not target:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    if target.startswith("plugin://"):
        xbmc.executebuiltin('PlayMedia("{0}")'.format(target.replace('"', '%22')))
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    item = xbmcgui.ListItem(path=target)
    item.setArt(DEFAULT_ART)
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

    if action == "integration_picker":
        pick_integrated_addons()
        return

    if action == "integration_clear":
        clear_integrated_addons()
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
