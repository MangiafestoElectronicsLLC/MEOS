# -*- coding: utf-8 -*-
"""Tiny JSON disk cache with a TTL, used to avoid re-hitting network APIs
and re-browsing slow third-party add-ons on every menu load.
"""
import json
import os
import time

from resources.lib.utils import kodi

CACHE_DIR = 'cache'


def _cache_path(key):
    directory = kodi.ensure_dir(os.path.join(kodi.PROFILE_PATH, CACHE_DIR))
    safe_key = ''.join(c if c.isalnum() else '_' for c in key)
    return os.path.join(directory, safe_key + '.json')


def _ttl_seconds():
    minutes_by_index = {0: 15, 1: 60, 2: 240, 3: 1440}
    index = kodi.get_setting_int('cache_ttl_minutes', 1)
    return minutes_by_index.get(index, 60) * 60


def get(key, ttl_seconds=None):
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            payload = json.load(handle)
    except Exception:
        return None
    age = time.time() - payload.get('_ts', 0)
    if age > (ttl_seconds if ttl_seconds is not None else _ttl_seconds()):
        return None
    return payload.get('data')


def set(key, data):
    path = _cache_path(key)
    payload = {'_ts': time.time(), 'data': data}
    try:
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(payload, handle)
    except Exception as exc:
        kodi.log('cache.set failed for {0}: {1}'.format(key, exc), kodi.LOGERROR)


def clear():
    directory = kodi.ensure_dir(os.path.join(kodi.PROFILE_PATH, CACHE_DIR))
    for name in os.listdir(directory):
        try:
            os.remove(os.path.join(directory, name))
        except OSError:
            pass
