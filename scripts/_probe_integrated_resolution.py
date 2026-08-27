"""End-to-end simulation of MEOS's integrated-addon resolution against a fake
plugin whose menu structure matches what the user reported for their real
Gratis Red / Ghost installs: Movies -> Movies -> TMDB -> In Theaters -> films.

This exercises the real _resolve_integrated_targets / _iter_integrated_playables
code paths from repository.meos/default.py without needing a live Kodi/addon.
"""

import os
import sys
import types
from urllib.parse import urlparse, parse_qsl

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON_DIR = os.path.join(REPO_ROOT, "repository.meos")


def _install_kodi_stubs():
    xbmc = types.ModuleType("xbmc")
    xbmc.LOGWARNING = 3
    xbmc.LOGERROR = 4
    xbmc.LOGINFO = 1
    xbmc.LOGDEBUG = 0
    xbmc.log = lambda msg, level=1: None
    xbmc.executebuiltin = lambda cmd: None
    xbmc.getInfoLabel = lambda *a, **k: ""

    xbmcaddon = types.ModuleType("xbmcaddon")

    class _Addon(object):
        def __init__(self, addon_id=None):
            self._settings = {}

        def getSetting(self, key):
            return self._settings.get(key, "")

        def setSetting(self, key, value):
            self._settings[key] = value

        def getAddonInfo(self, key):
            return ""

        def getLocalizedString(self, code):
            return ""

    xbmcaddon.Addon = _Addon

    xbmcgui = types.ModuleType("xbmcgui")

    class _ListItem(object):
        def __init__(self, *a, **k):
            pass

        def setArt(self, *a, **k):
            pass

        def setInfo(self, *a, **k):
            pass

        def setProperty(self, *a, **k):
            pass

        def addContextMenuItems(self, *a, **k):
            pass

    class _Dialog(object):
        def notification(self, *a, **k):
            pass

        def yesno(self, *a, **k):
            return False

        def input(self, *a, **k):
            return ""

    xbmcgui.ListItem = _ListItem
    xbmcgui.Dialog = _Dialog
    xbmcgui.NOTIFICATION_INFO = 1
    xbmcgui.NOTIFICATION_ERROR = 2

    xbmcplugin = types.ModuleType("xbmcplugin")
    xbmcplugin.addDirectoryItem = lambda *a, **k: None
    xbmcplugin.endOfDirectory = lambda *a, **k: None
    xbmcplugin.setContent = lambda *a, **k: None
    xbmcplugin.addSortMethod = lambda *a, **k: None
    xbmcplugin.SORT_METHOD_LABEL = 1

    for name, module in (
        ("xbmc", xbmc),
        ("xbmcaddon", xbmcaddon),
        ("xbmcgui", xbmcgui),
        ("xbmcplugin", xbmcplugin),
    ):
        sys.modules[name] = module


_install_kodi_stubs()
sys.argv = ["plugin://plugin.video.meos/", "1", ""]
sys.path.insert(0, ADDON_DIR)

import default as meos  # noqa: E402

ADDON_ID = "plugin.video.fakegratis"
ROOT = "plugin://{0}/".format(ADDON_ID)

# Fake filesystem: Movies -> Movies -> TMDB -> In Theaters -> 12 movies.
FAKE_TREE = {
    ROOT: [
        {"file": ROOT + "?m=account", "label": "My Account", "filetype": "file"},
        {"file": ROOT + "Movies/", "label": "Movies", "filetype": "directory"},
        {"file": ROOT + "TV%20Shows/", "label": "TV Shows", "filetype": "directory"},
        {"file": ROOT + "Search/", "label": "Search", "filetype": "directory"},
        {"file": ROOT + "Settings/", "label": "Settings", "filetype": "directory"},
    ],
    ROOT + "Movies/": [
        {"file": ROOT + "Movies/Movies/", "label": "Movies", "filetype": "directory"},
        {"file": ROOT + "Movies/Boxsets/", "label": "Boxsets", "filetype": "directory"},
    ],
    ROOT + "Movies/Movies/": [
        {"file": ROOT + "Movies/Movies/TMDB/", "label": "TMDB", "filetype": "directory"},
    ],
    ROOT + "Movies/Movies/TMDB/": [
        {"file": ROOT + "Movies/Movies/TMDB/InTheaters/", "label": "In Theaters", "filetype": "directory"},
        {"file": ROOT + "Movies/Movies/TMDB/Popular/", "label": "Popular", "filetype": "directory"},
    ],
    ROOT + "Movies/Movies/TMDB/InTheaters/": [
        {"file": ROOT + "play?id={0}".format(i), "label": "Fake Movie {0}".format(i), "filetype": "file"}
        for i in range(12)
    ],
    ROOT + "Movies/Movies/TMDB/Popular/": [
        {"file": ROOT + "play?id=p{0}".format(i), "label": "Fake Popular Movie {0}".format(i), "filetype": "file"}
        for i in range(5)
    ],
}


def fake_json_rpc(method, params):
    if method != "Files.GetDirectory":
        return {}
    directory = (params or {}).get("directory") or ""
    files = FAKE_TREE.get(directory)
    if files is None:
        # Try without trailing slash / with trailing slash.
        alt = directory[:-1] if directory.endswith("/") else directory + "/"
        files = FAKE_TREE.get(alt)
    if files is None:
        return {"files": []}
    return {"files": [dict(f) for f in files]}


meos._json_rpc = fake_json_rpc

print("Resolving 'movies' targets for fake Gratis Red-style addon...")
targets = meos._resolve_integrated_targets(ADDON_ID, "movies", addon_name="Gratis Red")
if not targets:
    print("RESULT: FAIL - no targets resolved at all")
    sys.exit(1)

for t in targets[:5]:
    print("  candidate: score={0} folder={1} label={2!r} target={3}".format(
        t.get("score"), t.get("is_folder"), t.get("matched_label"), t.get("target")))

total_playables = 0
seen_titles = set()
for t in targets:
    start = t.get("target")
    if not t.get("is_folder", True):
        total_playables += 1
        continue
    for entry in meos._iter_integrated_playables(start, max_depth=meos.MAX_INTEGRATED_SCAN_DEPTH, max_items=meos.MAX_INTEGRATED_ITEMS_PER_ADDON):
        title = entry.get("label") or entry.get("file")
        if title in seen_titles:
            continue
        seen_titles.add(title)
        total_playables += 1

print("\nTotal distinct playable movie entries discovered: {0}".format(total_playables))
print("RESULT:", "PASS" if total_playables >= 12 else "FAIL - expected at least 12 fake movies")
