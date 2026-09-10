# -*- coding: utf-8 -*-
"""All screen-building logic for MEOS Hub lives here.

router.py only parses the plugin:// URL and calls into these functions.
Keeping all xbmcgui/xbmcplugin calls in one module makes the rest of the
codebase (integrations/scrapers/content) fully Kodi-API-free and testable.
"""
try:
    from urllib.parse import urlencode
except ImportError:  # pragma: no cover
    from urllib import urlencode

import xbmcgui
import xbmcplugin

from resources.lib.content import categories as categories_content
from resources.lib.content import favorites as favorites_content
from resources.lib.content import importexport
from resources.lib.content import search as search_content
from resources.lib.integrations import base as integrations_base
from resources.lib.integrations import manager as integrations_manager
from resources.lib.integrations.known_addons import BUILTIN_TOGGLE_SETTING
from resources.lib.scrapers import manager as scrapers_manager
from resources.lib.scrapers.archive_org_scraper import ArchiveOrgScraper
from resources.lib.utils import kodi

BASE_URL = ''
HANDLE = -1

THEME_ICONS = {
    0: 'DefaultAddonVideo.png',   # Default
    1: 'DefaultAddonVideo.png',   # Dark (same icon set, kept simple/beginner-friendly)
    2: 'DefaultAddonVideo.png',   # Light
}


def init(base_url, handle):
    global BASE_URL, HANDLE
    BASE_URL = base_url
    HANDLE = handle


def build_url(**params):
    return '{0}?{1}'.format(BASE_URL, urlencode(params))


def _content_type():
    xbmcplugin.setContent(HANDLE, 'videos')


def _finish(sort=True):
    if sort:
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def add_folder(label, action, icon=None, plot=None, **params):
    list_item = xbmcgui.ListItem(label=label)
    art_icon = icon or 'DefaultFolder.png'
    list_item.setArt({'icon': art_icon, 'thumb': art_icon})
    if plot:
        _set_info(list_item, {'plot': plot})
    url = build_url(action=action, **params)
    xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)


def _set_info(list_item, info):
    try:
        video_info_tag = list_item.getVideoInfoTag()
        if info.get('title'):
            video_info_tag.setTitle(info['title'])
        if info.get('plot'):
            video_info_tag.setPlot(info['plot'])
        if info.get('genre'):
            video_info_tag.setGenres([info['genre']] if isinstance(info['genre'], str) else info['genre'])
        if info.get('year'):
            try:
                video_info_tag.setYear(int(info['year']))
            except (TypeError, ValueError):
                pass
        video_info_tag.setMediaType('video')
    except AttributeError:
        # Older Kodi (pre-20) without getVideoInfoTag()
        list_item.setInfo('video', info)


def add_playable(title, url, poster='', fanart='', plot='', year='', is_addon_route=False, source=''):
    list_item = xbmcgui.ListItem(label=title)
    list_item.setArt({'icon': poster or 'DefaultVideo.png', 'thumb': poster or 'DefaultVideo.png', 'fanart': fanart or poster})
    _set_info(list_item, {'title': title, 'plot': plot, 'year': year, 'genre': source})
    list_item.setProperty('IsPlayable', 'true')

    if is_addon_route:
        # Hand off directly to the other add-on's own plugin:// URL; Kodi
        # will invoke that add-on's default.py exactly as if the user had
        # opened it directly (true routing, no code copied).
        target_url = url
    else:
        target_url = build_url(action='play', url=url)

    context_menu = [(
        'Add to Favorites',
        'RunPlugin({0})'.format(build_url(action='favorite_add', title=title, url=url, poster=poster, plot=plot, year=year, source=source)),
    )]
    list_item.addContextMenuItems(context_menu)

    xbmcplugin.addDirectoryItem(HANDLE, target_url, list_item, isFolder=False)


def add_addon_folder(title, url, poster=''):
    list_item = xbmcgui.ListItem(label=title)
    list_item.setArt({'icon': poster or 'DefaultFolder.png', 'thumb': poster or 'DefaultFolder.png'})
    xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def list_main_menu():
    _content_type()
    for key, label in categories_content.enabled_categories():
        add_folder(label, 'category', category=key)
    add_folder('Addon Integrations', 'integrations')
    add_folder('Search', 'search')
    add_folder('Favorites', 'favorites')
    add_folder('Settings', 'settings')
    _finish(sort=False)


# ---------------------------------------------------------------------------
# Categories (Movies / TV Shows / Networks / Sports / PPV / Live TV)
# ---------------------------------------------------------------------------

def list_category(category):
    _content_type()
    label = categories_content.label_for(category)

    media_type = categories_content.CATEGORY_MEDIA_TYPE.get(category)
    if media_type and kodi.get_setting_bool('scraper_archiveorg_enabled', True):
        add_folder('Search free public-domain {0} (archive.org)'.format(label), 'archive_search', category=category)

    sources = categories_content.get_integration_sources(category)
    any_items = False
    for integration, items in sources:
        any_items = True
        for entry in items[:kodi.get_setting_int('items_per_page', 50) or 50]:
            _add_integration_entry(integration, entry)

    if not any_items and not media_type:
        add_folder(
            'No sources configured for {0} yet - open Settings to add one'.format(label),
            'settings',
        )
    _finish()


def _add_integration_entry(integration, entry):
    label = entry.get('label') or 'Untitled'
    file_url = entry.get('file', '')
    is_folder = entry.get('filetype') == 'directory'
    thumb = entry.get('thumbnail', '') or (entry.get('art') or {}).get('poster', '')
    if is_folder or not file_url:
        add_addon_folder('[{0}] {1}'.format(integration.name, label), file_url or integration.root_url, thumb)
    else:
        add_playable(
            title='[{0}] {1}'.format(integration.name, label),
            url=file_url,
            poster=thumb,
            plot=entry.get('plot', ''),
            year=str(entry.get('year', '') or ''),
            is_addon_route=True,
            source=integration.name,
        )


def archive_search(category):
    query = kodi.input_text('Search free public-domain {0}'.format(categories_content.label_for(category)))
    _content_type()
    if query:
        scraper = ArchiveOrgScraper()
        media_type = categories_content.CATEGORY_MEDIA_TYPE.get(category, 'movies')
        for entry in scraper.search(query, media_type=media_type):
            add_playable(
                title=entry['title'],
                url='archive:' + entry['identifier'],
                poster=entry.get('poster', ''),
                plot=entry.get('plot', ''),
                year=entry.get('year', ''),
                source='archive.org',
            )
    _finish()


# ---------------------------------------------------------------------------
# Integrations
# ---------------------------------------------------------------------------

def list_integrations_menu():
    _content_type()
    for spec in integrations_manager.get_all_specs():
        toggle_id = BUILTIN_TOGGLE_SETTING.get(spec.key)
        enabled = kodi.get_setting_bool(toggle_id, True) if toggle_id else True
        integration = integrations_manager.resolve(spec) if enabled else None
        status = 'installed' if integration else ('disabled' if not enabled else 'not installed')
        label = '{0} ({1})'.format(spec.label, status)
        if integration:
            add_folder(label, 'integration_menu', key=spec.key)
        else:
            add_folder(label, 'settings_integrations')
    add_folder('+ Add Your Own Add-on', 'integration_add_custom')
    add_folder('Discover All Installed Add-ons', 'integration_discover')
    _finish(sort=False)


def _find_spec(key):
    for spec in integrations_manager.get_all_specs():
        if spec.key == key:
            return spec
    return None


def list_integration_menu(key):
    spec = _find_spec(key)
    _content_type()
    if not spec:
        _finish()
        return
    for cat_key, cat_label in categories_content.CATEGORIES:
        add_folder(cat_label, 'integration_category', key=key, category=cat_key)
    _finish(sort=False)


def list_integration_category(key, category):
    spec = _find_spec(key)
    _content_type()
    if spec:
        integration = integrations_manager.resolve(spec)
        if integration:
            items = integration.get_category_items(category)
            for entry in items:
                _add_integration_entry(integration, entry)
            if not items:
                add_folder('No "{0}" content found in this add-on'.format(categories_content.label_for(category)), 'integration_menu', key=key)
    _finish()


def integration_add_custom():
    addon_id = kodi.input_text('Enter the exact add-on id (e.g. plugin.video.example)')
    if addon_id:
        label = kodi.input_text('Display name (optional)', default=addon_id)
        if integrations_manager.add_custom_integration(addon_id, label or addon_id):
            kodi.notify('Added {0}'.format(label or addon_id))
        else:
            kodi.notify('Already added or invalid add-on id')


def integration_remove_custom(addon_id):
    if integrations_manager.remove_custom_integration(addon_id):
        integrations_base.clear_target_cache(addon_id)
        kodi.notify('Removed integration')


def list_discover_addons():
    """List every installed video add-on that isn't already a built-in or
    custom integration, so any of them can be added as an integration with
    a single click (no need to know/type its exact add-on id).
    """
    _content_type()
    discoverable = integrations_manager.get_discoverable_addons()
    enabled_ids = set(integrations_manager.get_auto_enabled_ids())
    if not discoverable:
        add_folder('No other installed video add-ons found', 'integrations')
    for addon in discoverable:
        addon_id = addon.get('addonid')
        name = addon.get('name') or addon_id
        status = 'Integrated - select to remove' if addon_id in enabled_ids else 'Select to integrate'
        add_folder('{0}: {1}'.format(name, status), 'integration_auto_toggle', addon_id=addon_id)
    add_folder('<< Back to Integrations', 'integrations')
    _finish(sort=False)


def integration_auto_toggle(addon_id):
    enabled_ids = set(integrations_manager.get_auto_enabled_ids())
    new_state = addon_id not in enabled_ids
    integrations_manager.set_auto_enabled(addon_id, new_state)
    integrations_base.clear_target_cache(addon_id)
    kodi.notify('Integrated' if new_state else 'Removed from integrations')
    list_discover_addons()


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def do_search():
    query = kodi.input_text('Search MEOS Hub (free content, add-ons, metadata)')
    _content_type()
    if query:
        results = search_content.unified_search(query)
        if not results:
            add_folder('No results for "{0}"'.format(query), 'search')
        for entry in results:
            add_playable(
                title='{0} ({1})'.format(entry.get('title', ''), entry.get('source', '')),
                url=entry.get('url', ''),
                poster=entry.get('poster', ''),
                plot=entry.get('plot', ''),
                year=entry.get('year', ''),
                is_addon_route=bool(entry.get('is_addon_route')),
                source=entry.get('source', ''),
            )
    _finish()


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------

def list_favorites():
    _content_type()
    favorites = favorites_content.list_favorites()
    if not favorites:
        add_folder('No favorites yet - add some from any item\'s context menu', 'favorites')
    for item in favorites:
        list_item_url = item.get('url', '')
        list_item = xbmcgui.ListItem(label=item.get('title', 'Untitled'))
        list_item.setArt({'icon': item.get('poster') or 'DefaultVideo.png'})
        _set_info(list_item, {'plot': item.get('plot', ''), 'year': item.get('year', '')})
        list_item.setProperty('IsPlayable', 'true')
        list_item.addContextMenuItems([(
            'Remove from Favorites',
            'RunPlugin({0})'.format(build_url(action='favorite_remove', key=list_item_url or item.get('title', ''))),
        )])
        target = list_item_url if str(list_item_url).startswith('plugin://') else build_url(action='play', url=list_item_url)
        xbmcplugin.addDirectoryItem(HANDLE, target, list_item, isFolder=False)
    _finish()


def favorite_add(title, url, poster='', plot='', year='', source=''):
    item = {'title': title, 'url': url, 'poster': poster, 'plot': plot, 'year': year, 'source': source}
    if favorites_content.add_favorite(item):
        kodi.notify('Added to Favorites')
    else:
        kodi.notify('Already in Favorites')


def favorite_remove(key):
    if favorites_content.remove_favorite(key):
        kodi.notify('Removed from Favorites')


# ---------------------------------------------------------------------------
# Settings (in-addon menus, in addition to the native Kodi settings dialog)
# ---------------------------------------------------------------------------

def settings_menu():
    _content_type()
    add_folder('Toggle Categories', 'settings_categories')
    add_folder('Manage Integrations', 'settings_integrations')
    add_folder('Manage Scrapers', 'settings_scrapers')
    add_folder('Change UI Theme', 'settings_theme')
    add_folder('Import / Export', 'settings_importexport')
    add_folder('Open Kodi Add-on Settings', 'open_kodi_settings')
    _finish(sort=False)


def settings_categories_menu():
    _content_type()
    for key, label in categories_content.CATEGORIES:
        enabled = kodi.get_setting_bool(categories_content.CATEGORY_TOGGLE_SETTING[key], True)
        add_folder('{0}: {1}'.format(label, 'ON' if enabled else 'OFF'), 'toggle_category', category=key)
    _finish(sort=False)


def toggle_category(category):
    setting_id = categories_content.CATEGORY_TOGGLE_SETTING.get(category)
    if setting_id:
        current = kodi.get_setting_bool(setting_id, True)
        kodi.set_setting(setting_id, not current)


def settings_integrations_menu():
    _content_type()
    for spec in integrations_manager.get_all_specs():
        toggle_id = BUILTIN_TOGGLE_SETTING.get(spec.key)
        if toggle_id:
            enabled = kodi.get_setting_bool(toggle_id, True)
            add_folder('{0}: {1}'.format(spec.label, 'ON' if enabled else 'OFF'), 'integration_toggle', key=spec.key)
        elif spec.key.startswith(integrations_manager.AUTO_KEY_PREFIX):
            add_folder('{0} (discovered) - remove'.format(spec.label), 'integration_auto_toggle', addon_id=spec.addon_id_guess)
        else:
            add_folder('{0} (custom) - remove'.format(spec.label), 'integration_remove_custom', addon_id=spec.addon_id_guess)
    add_folder('+ Add Your Own Add-on', 'integration_add_custom')
    add_folder('Discover All Installed Add-ons', 'integration_discover')
    _finish(sort=False)


def integration_toggle(key):
    toggle_id = BUILTIN_TOGGLE_SETTING.get(key)
    if toggle_id:
        current = kodi.get_setting_bool(toggle_id, True)
        kodi.set_setting(toggle_id, not current)


def settings_scrapers_menu():
    _content_type()
    tmdb_enabled = kodi.get_setting_bool('scraper_tmdb_enabled', True)
    add_folder('TMDB metadata: {0}'.format('ON' if tmdb_enabled else 'OFF'), 'scraper_toggle_tmdb')
    add_folder('Set TMDB API Key', 'scraper_set_tmdb_key')
    archive_enabled = kodi.get_setting_bool('scraper_archiveorg_enabled', True)
    add_folder('archive.org free streams: {0}'.format('ON' if archive_enabled else 'OFF'), 'scraper_toggle_archiveorg')
    for custom in scrapers_manager.list_custom_scrapers():
        add_folder('{0} (custom) - remove'.format(custom['name']), 'scraper_remove_custom', name=custom['name'])
    add_folder('+ Add Custom Scraper', 'scraper_add_custom')
    _finish(sort=False)


def scraper_toggle_tmdb():
    current = kodi.get_setting_bool('scraper_tmdb_enabled', True)
    kodi.set_setting('scraper_tmdb_enabled', not current)


def scraper_toggle_archiveorg():
    current = kodi.get_setting_bool('scraper_archiveorg_enabled', True)
    kodi.set_setting('scraper_archiveorg_enabled', not current)


def scraper_set_tmdb_key():
    key = kodi.input_text('Enter your free TMDB API key', default=kodi.get_setting('scraper_tmdb_api_key', ''))
    if key:
        kodi.set_setting('scraper_tmdb_api_key', key)
        kodi.notify('TMDB API key saved')


def scraper_add_custom():
    name = kodi.input_text('Scraper name')
    if not name:
        return
    url_template = kodi.input_text('URL template (must contain {query})')
    if scrapers_manager.add_custom_scraper(name, url_template):
        kodi.notify('Added scraper "{0}"'.format(name))
    else:
        kodi.notify('Could not add scraper (missing name/url or duplicate)')


def scraper_remove_custom(name):
    if scrapers_manager.remove_custom_scraper(name):
        kodi.notify('Removed scraper "{0}"'.format(name))


def settings_theme_menu():
    themes = ['Default', 'Dark', 'Light']
    current = kodi.get_setting_int('theme', 0)
    choice = kodi.select_dialog('Choose UI Theme', ['{0}{1}'.format(t, ' (current)' if i == current else '') for i, t in enumerate(themes)])
    if choice >= 0:
        kodi.set_setting('theme', choice)
        kodi.notify('Theme set to {0}'.format(themes[choice]))


def settings_importexport_menu():
    _content_type()
    add_folder('Import Content Sources (CSV/XLSX)', 'io_import_sources')
    add_folder('Export Integrated Add-on List', 'io_export_integrations')
    add_folder('Export Custom Scrapers', 'io_export_scrapers')
    add_folder('Export Favorites', 'io_export_favorites')
    _finish(sort=False)


def _export_folder():
    return kodi.get_setting('io_export_folder', 'special://temp/meoshub_exports')


def io_import_sources():
    file_path = kodi.browse_file('Select a CSV or XLSX file', '.csv|.xlsx')
    if not file_path:
        return
    local_path = kodi.translate_path(file_path)
    added, skipped = importexport.import_sources(local_path)
    kodi.notify('Imported {0} item(s), skipped {1}'.format(added, skipped))


def io_export_integrations():
    path = importexport.export_integrations(_export_folder())
    kodi.notify('Exported to {0}'.format(path))


def io_export_scrapers():
    path = importexport.export_scrapers(_export_folder())
    kodi.notify('Exported to {0}'.format(path))


def io_export_favorites():
    path = importexport.export_favorites(_export_folder())
    kodi.notify('Exported to {0}'.format(path))


def open_kodi_settings():
    kodi.open_addon_settings()


# ---------------------------------------------------------------------------
# Playback
# ---------------------------------------------------------------------------

def play_item(url):
    resolved_url = url
    if url.startswith('archive:'):
        identifier = url.split(':', 1)[1]
        resolved_url = ArchiveOrgScraper().resolve(identifier)

    list_item = xbmcgui.ListItem(path=resolved_url)
    is_valid = bool(resolved_url)
    if is_valid:
        list_item.setProperty('IsPlayable', 'true')
    xbmcplugin.setResolvedUrl(HANDLE, is_valid, list_item)
    if not is_valid:
        kodi.notify('Could not resolve a playable stream for this item')
