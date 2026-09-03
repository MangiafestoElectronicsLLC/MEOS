# -*- coding: utf-8 -*-
"""Unified category definitions and category-page content assembly."""
from resources.lib.integrations import manager as integrations_manager
from resources.lib.utils import kodi

CATEGORIES = [
    ('movies', 'Movies'),
    ('tvshows', 'TV Shows'),
    ('networks', 'Networks'),
    ('sports', 'Sports'),
    ('ppv', 'PPV'),
    ('livetv', 'Live TV / Cable'),
]

CATEGORY_TOGGLE_SETTING = {
    'movies': 'cat_movies_enabled',
    'tvshows': 'cat_tvshows_enabled',
    'networks': 'cat_networks_enabled',
    'sports': 'cat_sports_enabled',
    'ppv': 'cat_ppv_enabled',
    'livetv': 'cat_livetv_enabled',
}

# Free stream scraper media-type hint per unified category (archive.org
# mediatype values). Categories with no sensible free-content mapping are
# left to integrations only.
CATEGORY_MEDIA_TYPE = {
    'movies': 'movies',
    'tvshows': 'movies',  # archive.org has no dedicated tv mediatype; movies covers most public-domain TV.
}


def label_for(category):
    for key, label in CATEGORIES:
        if key == category:
            return label
    return category


def enabled_categories():
    return [(key, label) for key, label in CATEGORIES if kodi.get_setting_bool(CATEGORY_TOGGLE_SETTING[key], True)]


def get_integration_sources(category):
    """[(Integration, items)] for every installed/enabled integration that
    has content under this unified category.
    """
    return integrations_manager.get_category_items_for_all(category)
