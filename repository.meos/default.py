import sys
import random

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

PROVIDERS = {provider.id: provider for provider in get_providers()}


def build_url(query):
    return BASE_URL + "?" + urlencode(query)


def get_auth_state(provider_id):
    return ADDON.getSetting("auth.{0}".format(provider_id))


def set_auth_state(provider_id, state):
    ADDON.setSetting("auth.{0}".format(provider_id), state)


def add_folder_item(label, query, art=None):
    item = xbmcgui.ListItem(label=label)
    item.setArt(art or DEFAULT_ART)
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=True)


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
    for label, category in MENU_CATEGORIES:
        add_folder_item(label, {"action": "list_category", "provider": "all", "category": category})
    add_folder_item("Awards", {"action": "awards_menu"})
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
        found = 0
        seen = set()
        for provider in sorted(PROVIDERS.values(), key=lambda p: p.name.lower()):
            auth_state = get_auth_state(provider.id)
            catalog = provider.get_catalog(auth_state, category=category)
            for item in catalog:
                key = (provider.id, item.get("media_id", ""))
                if key in seen:
                    continue
                seen.add(key)
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
