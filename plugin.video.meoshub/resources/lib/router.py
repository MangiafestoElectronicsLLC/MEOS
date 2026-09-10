# -*- coding: utf-8 -*-
"""Parses the plugin:// URL Kodi invokes us with and dispatches to ui.py.

Kodi calls default.py with argv = [base_url, handle, '?query=string'].
"""
try:
    from urllib.parse import parse_qsl
except ImportError:  # pragma: no cover
    from urlparse import parse_qsl

from resources.lib import ui


def _dispatch(action, params):
    if action in ('', None, 'main'):
        return ui.list_main_menu()
    if action == 'category':
        return ui.list_category(params['category'])
    if action == 'archive_search':
        return ui.archive_search(params['category'])
    if action == 'integrations':
        return ui.list_integrations_menu()
    if action == 'integration_menu':
        return ui.list_integration_menu(params['key'])
    if action == 'integration_category':
        return ui.list_integration_category(params['key'], params['category'])
    if action == 'integration_add_custom':
        return ui.integration_add_custom()
    if action == 'integration_remove_custom':
        return ui.integration_remove_custom(params['addon_id'])
    if action == 'integration_discover':
        return ui.list_discover_addons()
    if action == 'integration_auto_toggle':
        return ui.integration_auto_toggle(params['addon_id'])
    if action == 'search':
        return ui.do_search()
    if action == 'favorites':
        return ui.list_favorites()
    if action == 'favorite_add':
        return ui.favorite_add(
            params.get('title', ''), params.get('url', ''), params.get('poster', ''),
            params.get('plot', ''), params.get('year', ''), params.get('source', ''),
        )
    if action == 'favorite_remove':
        return ui.favorite_remove(params.get('key', ''))
    if action == 'settings':
        return ui.settings_menu()
    if action == 'settings_categories':
        return ui.settings_categories_menu()
    if action == 'toggle_category':
        return ui.toggle_category(params['category'])
    if action == 'settings_integrations':
        return ui.settings_integrations_menu()
    if action == 'integration_toggle':
        return ui.integration_toggle(params['key'])
    if action == 'settings_scrapers':
        return ui.settings_scrapers_menu()
    if action == 'scraper_toggle_tmdb':
        return ui.scraper_toggle_tmdb()
    if action == 'scraper_toggle_archiveorg':
        return ui.scraper_toggle_archiveorg()
    if action == 'scraper_set_tmdb_key':
        return ui.scraper_set_tmdb_key()
    if action == 'scraper_add_custom':
        return ui.scraper_add_custom()
    if action == 'scraper_remove_custom':
        return ui.scraper_remove_custom(params['name'])
    if action == 'settings_theme':
        return ui.settings_theme_menu()
    if action == 'settings_importexport':
        return ui.settings_importexport_menu()
    if action == 'io_import_sources':
        return ui.io_import_sources()
    if action == 'io_export_integrations':
        return ui.io_export_integrations()
    if action == 'io_export_scrapers':
        return ui.io_export_scrapers()
    if action == 'io_export_favorites':
        return ui.io_export_favorites()
    if action == 'open_kodi_settings':
        return ui.open_kodi_settings()
    if action == 'play':
        return ui.play_item(params['url'])

    return ui.list_main_menu()


def run(argv):
    base_url = argv[0]
    handle = int(argv[1])
    query_string = argv[2][1:] if len(argv) > 2 and argv[2] else ''
    params = dict(parse_qsl(query_string))

    ui.init(base_url, handle)
    _dispatch(params.get('action', ''), params)
