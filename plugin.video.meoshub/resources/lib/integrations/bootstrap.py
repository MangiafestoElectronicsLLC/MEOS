# -*- coding: utf-8 -*-
"""Make the default integrations work out of the box.

For every built-in integration (Red Gratis, Ghost, The Loop, Rising Tides,
...) this makes sure the real add-on is usable:
  - already installed and enabled   -> nothing to do (it is integrated)
  - installed but disabled          -> enable it via JSON-RPC
  - not installed                   -> ask Kodi to install it from the
                                       repositories the user already has

MEOS Hub never bundles or downloads third-party code itself; installing
goes through Kodi's own InstallAddon, so it only works when one of the
user's repositories provides the add-on. Each missing add-on is attempted
once automatically (so users are not nagged); the Settings menu entry
"Install / refresh default add-ons" retries on demand.
"""
import xbmc

from resources.lib.integrations import manager as integrations_manager
from resources.lib.utils import jsonrpc, kodi
from resources.lib.utils.settings import get_json_setting, set_json_setting

ATTEMPTED_SETTING = 'bootstrap_attempted_json'


def _installed_ids(enabled_only=False):
    return set(a.get('addonid') for a in jsonrpc.get_installed_addons(enabled_only=enabled_only))


def ensure_defaults(force=False):
    """Returns {'enabled': [...], 'install_requested': [...], 'ready': [...]} (labels)."""
    summary = {'enabled': [], 'install_requested': [], 'ready': []}
    attempted = get_json_setting(ATTEMPTED_SETTING, [])
    all_ids = _installed_ids()
    enabled_ids = _installed_ids(enabled_only=True)

    for spec in integrations_manager.builtin_specs():
        toggle = integrations_manager.BUILTIN_TOGGLE_SETTING.get(spec.key)
        if toggle and not kodi.get_setting_bool(toggle, True):
            continue
        if jsonrpc.find_addon_by_keywords(spec.keywords) or spec.addon_id_guess in enabled_ids:
            summary['ready'].append(spec.label)
            continue
        if spec.addon_id_guess in all_ids:
            jsonrpc.execute('Addons.SetAddonEnabled', {'addonid': spec.addon_id_guess, 'enabled': True})
            summary['enabled'].append(spec.label)
            continue
        if force or spec.addon_id_guess not in attempted:
            xbmc.executebuiltin('InstallAddon({0})'.format(spec.addon_id_guess))
            summary['install_requested'].append(spec.label)
            if spec.addon_id_guess not in attempted:
                attempted.append(spec.addon_id_guess)
    set_json_setting(ATTEMPTED_SETTING, attempted)
    return summary
