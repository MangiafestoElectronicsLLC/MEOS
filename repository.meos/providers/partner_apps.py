"""
MEOS — Official free-service launchers.

Tubi, Crackle, Kanopy, Hoopla and Rakuten TV Free are legitimate free
services, but their catalogs are only available through their own
authenticated/DRM-protected apps.  MEOS therefore does NOT scrape them.
Instead it hands playback off to the service's official Kodi add-on when the
user has it installed, so ads, DRM and library entitlements are respected.
"""

import xbmc
import xbmcaddon

from .base import BaseProvider


# service key -> (display name, Kodi add-on id, launch path, MEOS categories)
_SERVICES = {
    "tubi": {
        "title": "Tubi (Free, ad-supported)",
        "addon_id": "plugin.video.tubitv",
        "path": "plugin://plugin.video.tubitv/",
        "genre": "Free Movies & TV",
        "categories": ["movies", "tv", "docs", "live", "cable"],
    },
    "crackle": {
        "title": "Crackle (Free, ad-supported)",
        "addon_id": "plugin.video.crackle",
        "path": "plugin://plugin.video.crackle/",
        "genre": "Free Movies & TV",
        "categories": ["movies", "tv"],
    },
    "kanopy": {
        "title": "Kanopy (Free with library card)",
        "addon_id": "plugin.video.kanopy",
        "path": "plugin://plugin.video.kanopy/",
        "genre": "Library Streaming",
        "categories": ["movies", "docs"],
    },
    "hoopla": {
        "title": "Hoopla Digital (Free with library card)",
        "addon_id": "plugin.video.hoopla",
        "path": "plugin://plugin.video.hoopla/",
        "genre": "Library Streaming",
        "categories": ["movies", "tv", "docs"],
    },
    "rakuten": {
        "title": "Rakuten TV Free",
        "addon_id": "plugin.video.rakuten",
        "path": "plugin://plugin.video.rakuten/",
        "genre": "Free Movies & TV",
        "categories": ["movies", "tv"],
    },
}


def _is_installed(addon_id):
    try:
        xbmcaddon.Addon(addon_id)
        return True
    except Exception:
        return False


class PartnerAppsProvider(BaseProvider):
    """Deep-links into officially published free-service Kodi add-ons."""

    id = "partner_apps"
    name = "MEOS Free Services"
    requires_oauth = False

    def get_catalog(self, auth_state, category=None, query=None, year=None, award=None, result=None):
        rows = []
        for key, service in _SERVICES.items():
            if category and category not in service["categories"]:
                continue
            if query and query.strip().lower() not in service["title"].lower():
                continue
            if not _is_installed(service["addon_id"]):
                continue
            rows.append({
                "media_id": "app::" + key,
                "title": service["title"],
                "genre": service["genre"],
            })
        rows.sort(key=lambda x: x["title"].lower())
        return rows

    def check_entitlement(self, media_id, auth_state):
        key = media_id[len("app::"):] if media_id.startswith("app::") else ""
        service = _SERVICES.get(key)
        if not service:
            return False, "Unknown free service"
        if not _is_installed(service["addon_id"]):
            return False, "Install the official {} add-on first".format(service["title"])
        # These services are browsed in their own add-on, so open it instead of resolving a stream.
        xbmc.executebuiltin("ActivateWindow(Videos,{},return)".format(service["path"]))
        return False, "Opening {}".format(service["title"])

    def resolve_playback(self, media_id, auth_state):
        return None
