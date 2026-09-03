# -*- coding: utf-8 -*-
"""Small, dependency-free helpers around the Kodi Python API.

Every other module in MEOS Hub should go through this module instead of
importing xbmc/xbmcgui/xbmcplugin/xbmcaddon/xbmcvfs directly. This keeps the
rest of the codebase easy to read and easy to unit test (see tools/kodi_mocks.py).
"""
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_PATH = ADDON.getAddonInfo('path')
ADDON_ICON = ADDON.getAddonInfo('icon')
PROFILE_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')) if hasattr(xbmcvfs, 'translatePath') else xbmc.translatePath(ADDON.getAddonInfo('profile'))

LOGDEBUG = xbmc.LOGDEBUG
LOGINFO = getattr(xbmc, 'LOGINFO', xbmc.LOGNOTICE if hasattr(xbmc, 'LOGNOTICE') else xbmc.LOGDEBUG)
LOGERROR = xbmc.LOGERROR


def log(message, level=LOGDEBUG):
    """Write a line to kodi.log, prefixed with the add-on id."""
    xbmc.log('[{0}] {1}'.format(ADDON_ID, message), level=level)


def translate_path(path):
    if hasattr(xbmcvfs, 'translatePath'):
        return xbmcvfs.translatePath(path)
    return xbmc.translatePath(path)


def ensure_dir(path):
    path = translate_path(path)
    if not xbmcvfs.exists(path):
        xbmcvfs.mkdirs(path)
    return path


def get_setting(setting_id, default=''):
    value = ADDON.getSetting(setting_id)
    if value is None or value == '':
        return default
    return value


def set_setting(setting_id, value):
    ADDON.setSetting(setting_id, str(value))


def get_setting_bool(setting_id, default=False):
    value = ADDON.getSetting(setting_id)
    if value in (None, ''):
        return default
    return str(value).lower() == 'true'


def get_setting_int(setting_id, default=0):
    value = ADDON.getSetting(setting_id)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def notify(message, heading=None, icon=xbmcgui.NOTIFICATION_INFO, time_ms=4000):
    xbmcgui.Dialog().notification(heading or ADDON_NAME, message, icon, time_ms)


def ok_dialog(message, heading=None):
    xbmcgui.Dialog().ok(heading or ADDON_NAME, message)


def yesno_dialog(message, heading=None):
    return xbmcgui.Dialog().yesno(heading or ADDON_NAME, message)


def input_text(heading, default=''):
    keyboard_default = default or ''
    result = xbmcgui.Dialog().input(heading, defaultt=keyboard_default)
    return result or ''


def select_dialog(heading, options):
    return xbmcgui.Dialog().select(heading, options)


def multiselect_dialog(heading, options, preselect=None):
    return xbmcgui.Dialog().multiselect(heading, options, preselect=preselect or [])


def browse_file(heading, mask=''):
    return xbmcgui.Dialog().browse(1, heading, 'files', mask)


def browse_folder(heading):
    return xbmcgui.Dialog().browse(3, heading, 'files')


def open_addon_settings():
    ADDON.openSettings()


def localize(string_id, *args):
    text = ADDON.getLocalizedString(string_id)
    if args:
        return text.format(*args)
    return text
