# -*- coding: utf-8 -*-
"""Thin wrapper around Kodi's JSON-RPC API.

Used to discover installed add-ons and to browse their plugin:// directories
without ever importing or copying their source code (routing only).
"""
import json

import xbmc


def execute(method, params=None):
    """Run a JSON-RPC method and return the parsed 'result' dict (or {})."""
    payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': method,
        'params': params or {},
    }
    try:
        raw = xbmc.executeJSONRPC(json.dumps(payload))
        response = json.loads(raw)
    except Exception:
        return {}
    return response.get('result', {}) or {}


def get_installed_addons(content='video', enabled_only=False):
    """Return a list of {addonid, name, enabled} dicts for video add-ons."""
    params = {
        'type': 'xbmc.python.pluginsource',
        'content': content,
        'properties': ['name', 'enabled', 'path'],
    }
    if enabled_only:
        params['enabled'] = True
    result = execute('Addons.GetAddons', params)
    return result.get('addons', []) or []


def is_addon_installed(addon_id):
    for addon in get_installed_addons():
        if addon.get('addonid') == addon_id:
            return True
    return False


def find_addon_by_keywords(keywords, enabled_only=True):
    """Best-effort match: find an installed add-on whose id/name contains
    any of the given keywords (case-insensitive). Real-world add-on ids and
    display names vary a lot between builds/forks, so exact-id matching
    alone is unreliable.
    """
    keywords = [k.lower() for k in keywords]
    for addon in get_installed_addons(enabled_only=enabled_only):
        haystack = '{0} {1}'.format(addon.get('addonid', ''), addon.get('name', '')).lower()
        for keyword in keywords:
            if keyword and keyword in haystack:
                return addon
    return None


def get_directory(plugin_url):
    """List the contents of a plugin:// directory. Returns a list of file dicts."""
    params = {
        'directory': plugin_url,
        'media': 'video',
        'properties': ['title', 'file', 'thumbnail', 'art', 'plot', 'year', 'genre'],
    }
    result = execute('Files.GetDirectory', params)
    return result.get('files', []) or []
