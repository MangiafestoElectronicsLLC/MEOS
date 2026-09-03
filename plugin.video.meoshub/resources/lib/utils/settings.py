# -*- coding: utf-8 -*-
"""Helpers for storing structured (JSON) data inside addon text settings.

Kodi settings only store strings, so lists/dicts (custom integrations,
custom scrapers, favorites) are kept as JSON blobs in hidden text settings.
"""
import json

from resources.lib.utils import kodi


def get_json_setting(setting_id, default=None):
    raw = kodi.get_setting(setting_id, '')
    if not raw:
        return default if default is not None else []
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default if default is not None else []


def set_json_setting(setting_id, value):
    kodi.set_setting(setting_id, json.dumps(value))
