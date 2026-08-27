"""Verify Scrubs V2 / The Loop / Red Gratis / The Ghost priority-integration
rule matching in repository.meos/default.py, outside of Kodi (stubbed xbmc*).
"""

import os
import sys
import types

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

CASES = [
    ("Scrubs V2", "plugin.video.scrubsv2", "Scrubs V2"),
    ("The Loop", "plugin.video.theloop", "The Loop"),
    ("Red Gratis", "plugin.video.redgratis", "Red Gratis"),
    ("The Ghost", "plugin.video.ghost", "The Ghost"),
]

print("Rule matching (_find_addon_rule):")
for label, addon_id, addon_name in CASES:
    rule = meos._find_addon_rule(addon_id, addon_name)
    print("  {0:12s} id={1:28s} -> rule={2}".format(label, addon_id, rule.get("name") if rule else None))

print("\nPriority bootstrap specs (_auto_integrate_priority_specs):")
specs = meos._auto_integrate_priority_specs()
spec_names = [s["name"] for s in specs]
print("  ", spec_names)

print("\nToken matching (_addon_matches_tokens) against each spec:")
for label, addon_id, addon_name in CASES:
    matched = [s["name"] for s in specs if meos._addon_matches_tokens(addon_id, addon_name, s.get("tokens", []))]
    print("  {0:12s} matched specs = {1}".format(label, matched))

print("\nDeclared category paths (_addon_category_paths) sample (movies):")
for label, addon_id, addon_name in CASES:
    paths = meos._addon_category_paths(addon_id, addon_name, "movies")
    print("  {0:12s} movies paths = {1}".format(label, paths[:3]))

ok = all(meos._find_addon_rule(a, n) for _, a, n in CASES) and all(
    any(meos._addon_matches_tokens(a, n, s.get("tokens", [])) for s in specs) for _, a, n in CASES
)
print("\nRESULT:", "PASS - all 4 addons resolve a rule and a priority spec" if ok else "FAIL")
