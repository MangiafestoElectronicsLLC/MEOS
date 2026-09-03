# -*- coding: utf-8 -*-
"""Minimal, headless stand-ins for the Kodi Python API modules.

These let tools/test_harness.py import and exercise MEOS Hub's router/ui
code on a plain desktop Python interpreter, without a running Kodi.
They are NOT used by the add-on itself inside Kodi.
"""
import json
import sys
import types

LOGDEBUG = 0
LOGINFO = 1
LOGNOTICE = 1
LOGERROR = 3


class FakeInfoTag(object):
    def setTitle(self, *_):
        pass

    def setPlot(self, *_):
        pass

    def setGenres(self, *_):
        pass

    def setYear(self, *_):
        pass

    def setMediaType(self, *_):
        pass


class FakeListItem(object):
    def __init__(self, label='', path=''):
        self.label = label
        self.path = path
        self.art = {}
        self.info = {}
        self.properties = {}
        self.context_menu = []

    def setArt(self, art):
        self.art.update(art)

    def setInfo(self, media_type, info):
        self.info.update(info)

    def setProperty(self, key, value):
        self.properties[key] = value

    def addContextMenuItems(self, items):
        self.context_menu.extend(items)

    def getVideoInfoTag(self):
        return FakeInfoTag()


class FakeDialog(object):
    def notification(self, *args, **kwargs):
        pass

    def ok(self, *args, **kwargs):
        return True

    def yesno(self, *args, **kwargs):
        return True

    def input(self, heading, defaultt=''):
        return defaultt

    def select(self, heading, options):
        return 0 if options else -1

    def multiselect(self, heading, options, preselect=None):
        return list(preselect or [])

    def browse(self, *args, **kwargs):
        return ''


xbmc = types.ModuleType('xbmc')
xbmc.LOGDEBUG = LOGDEBUG
xbmc.LOGINFO = LOGINFO
xbmc.LOGNOTICE = LOGNOTICE
xbmc.LOGERROR = LOGERROR
xbmc.log = lambda message, level=LOGDEBUG: print('[xbmc.log] {0}'.format(message))
xbmc.translatePath = lambda path: path.replace('special://temp/', '/tmp/').replace('special://profile/', '/tmp/profile/')


# Canned JSON-RPC responses. Override JSONRPC_RESPONSES from a test to
# simulate specific installed add-ons / directory listings.
JSONRPC_RESPONSES = {
    'Addons.GetAddons': {'addons': []},
    'Files.GetDirectory': {'files': []},
}


def _execute_json_rpc(request_json):
    request = json.loads(request_json)
    method = request.get('method')
    result = JSONRPC_RESPONSES.get(method, {})
    return json.dumps({'jsonrpc': '2.0', 'id': request.get('id', 1), 'result': result})


xbmc.executeJSONRPC = _execute_json_rpc

xbmcgui = types.ModuleType('xbmcgui')
xbmcgui.ListItem = FakeListItem
xbmcgui.Dialog = FakeDialog
xbmcgui.NOTIFICATION_INFO = 'info'
xbmcgui.NOTIFICATION_ERROR = 'error'

xbmcplugin = types.ModuleType('xbmcplugin')
xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE = 1
DIRECTORY_ITEMS = []


def _add_directory_item(handle, url, list_item, isFolder=False):
    DIRECTORY_ITEMS.append({'handle': handle, 'url': url, 'label': list_item.label, 'is_folder': isFolder})
    return True


def _end_of_directory(handle, succeeded=True, updateListing=False, cacheToDiscEmpty=False):
    pass


def _set_resolved_url(handle, succeeded, list_item):
    DIRECTORY_ITEMS.append({'handle': handle, 'url': list_item.path, 'label': 'resolved', 'is_folder': False, 'resolved': succeeded})


xbmcplugin.addDirectoryItem = _add_directory_item
xbmcplugin.endOfDirectory = _end_of_directory
xbmcplugin.setResolvedUrl = _set_resolved_url
xbmcplugin.setContent = lambda handle, content: None
xbmcplugin.addSortMethod = lambda handle, method: None

xbmcaddon = types.ModuleType('xbmcaddon')

FAKE_SETTINGS = {}
FAKE_ADDON_INFO = {
    'id': 'plugin.video.meoshub',
    'name': 'MEOS Hub',
    'path': '.',
    'icon': 'icon.png',
    'profile': 'special://profile/addon_data/plugin.video.meoshub/',
}


class FakeAddon(object):
    def getAddonInfo(self, key):
        return FAKE_ADDON_INFO.get(key, '')

    def getSetting(self, setting_id):
        return FAKE_SETTINGS.get(setting_id, '')

    def setSetting(self, setting_id, value):
        FAKE_SETTINGS[setting_id] = value

    def getLocalizedString(self, string_id):
        return str(string_id)

    def openSettings(self):
        pass


xbmcaddon.Addon = FakeAddon

xbmcvfs = types.ModuleType('xbmcvfs')
xbmcvfs.translatePath = xbmc.translatePath
xbmcvfs.exists = lambda path: __import__('os').path.exists(path)
xbmcvfs.mkdirs = lambda path: __import__('os').makedirs(path, exist_ok=True)


def install():
    """Register the fake modules so `import xbmc` etc. resolve to these."""
    sys.modules['xbmc'] = xbmc
    sys.modules['xbmcgui'] = xbmcgui
    sys.modules['xbmcplugin'] = xbmcplugin
    sys.modules['xbmcaddon'] = xbmcaddon
    sys.modules['xbmcvfs'] = xbmcvfs
