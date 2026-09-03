# -*- coding: utf-8 -*-
"""Favorites: a flat, user-curated list of items (own content, scraper
results, or integration shortcuts) persisted as JSON in addon settings.
"""
from resources.lib.utils.settings import get_json_setting, set_json_setting

SETTING_ID = 'favorites_json'


def list_favorites():
    return get_json_setting(SETTING_ID, [])


def _item_key(item):
    return item.get('url') or item.get('title')


def add_favorite(item):
    favorites = list_favorites()
    key = _item_key(item)
    if any(_item_key(existing) == key for existing in favorites):
        return False
    favorites.append(item)
    set_json_setting(SETTING_ID, favorites)
    return True


def remove_favorite(key):
    favorites = list_favorites()
    new_favorites = [item for item in favorites if _item_key(item) != key]
    set_json_setting(SETTING_ID, new_favorites)
    return len(new_favorites) != len(favorites)


def is_favorite(key):
    return any(_item_key(item) == key for item in list_favorites())
