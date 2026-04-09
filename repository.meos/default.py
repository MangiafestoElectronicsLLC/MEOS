import sys

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

PROVIDERS = {provider.id: provider for provider in get_providers()}


def build_url(query):
    return BASE_URL + "?" + urlencode(query)


def get_auth_state(provider_id):
    return ADDON.getSetting("auth.{0}".format(provider_id))


def set_auth_state(provider_id, state):
    ADDON.setSetting("auth.{0}".format(provider_id), state)


def add_folder_item(label, query, art=None):
    item = xbmcgui.ListItem(label=label)
    item.setArt(art or {"thumb": "icon.png", "fanart": "fanart.jpg"})
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=True)


def add_playable_item(label, query, info=None, art=None):
    item = xbmcgui.ListItem(label=label)
    item.setArt(art or {"thumb": "icon.png", "fanart": "fanart.jpg"})
    item.setInfo("video", info or {"title": label})
    item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(HANDLE, build_url(query), item, isFolder=False)


def list_root():
    add_playable_item(
        "Quick Test Stream",
        {"action": "play_sample"},
        {"title": "Quick Test Stream", "genre": "Demo"},
    )
    add_folder_item("Official Integrations", {"action": "list_providers"})
    xbmcplugin.endOfDirectory(HANDLE)


def play_sample():
    stream_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
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

    message = "Open: {0}\nCode: {1}".format(payload["verification_uri"], payload["user_code"])
    xbmcgui.Dialog().ok("Connect Account", message)

    # This is a legal integration scaffold. Replace this with real token polling when wiring an official API.
    set_auth_state(provider.id, "connected")
    xbmcgui.Dialog().notification("MEOS", "Account marked connected", xbmcgui.NOTIFICATION_INFO, 2500)
    return True


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
    for item in catalog:
        add_playable_item(
            item["title"],
            {"action": "provider_play", "provider": provider.id, "media_id": item["media_id"]},
            {"title": item["title"], "genre": item.get("genre", "")},
        )
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
