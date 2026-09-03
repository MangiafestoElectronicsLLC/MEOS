# -*- coding: utf-8 -*-
"""Unified search across free/legal streams, metadata scrapers, integrated
add-ons, and favorites. Results are combined into a single flat list, each
tagged with its source so the UI can show where a result came from.
"""
from resources.lib.content import favorites as favorites_content
from resources.lib.integrations import manager as integrations_manager
from resources.lib.scrapers import manager as scrapers_manager
from resources.lib.utils import kodi

# Unified categories that make sense to text-search inside integrated add-ons.
# Live TV/Networks/PPV menus are usually channel lists, not searchable catalogs.
SEARCHABLE_INTEGRATION_CATEGORIES = ('movies', 'tvshows')
MAX_INTEGRATION_MATCHES_PER_ADDON = 20


def _search_integrations(query):
    query_lower = query.lower()
    results = []
    for integration in integrations_manager.get_resolved_integrations():
        for category in SEARCHABLE_INTEGRATION_CATEGORIES:
            try:
                items = integration.get_category_items(category)
            except Exception as exc:
                kodi.log('Integration search failed for {0}: {1}'.format(integration.name, exc), kodi.LOGERROR)
                continue
            matched = 0
            for entry in items:
                label = (entry.get('label') or '').strip()
                if query_lower in label.lower():
                    results.append({
                        'title': label,
                        'url': entry.get('file', ''),
                        'poster': (entry.get('art') or {}).get('poster', '') or entry.get('thumbnail', ''),
                        'plot': entry.get('plot', ''),
                        'year': str(entry.get('year', '') or ''),
                        'source': integration.name,
                        'is_addon_route': True,
                        'is_folder': entry.get('filetype') == 'directory',
                    })
                    matched += 1
                    if matched >= MAX_INTEGRATION_MATCHES_PER_ADDON:
                        break
    return results


def _search_favorites(query):
    query_lower = query.lower()
    results = []
    for item in favorites_content.list_favorites():
        if query_lower in (item.get('title') or '').lower():
            merged = dict(item)
            merged.setdefault('source', 'favorites')
            results.append(merged)
    return results


def unified_search(query):
    if not query:
        return []

    results = []
    results.extend(_search_favorites(query))

    for entry in scrapers_manager.search_metadata(query):
        merged = dict(entry)
        merged['is_addon_route'] = False
        results.append(merged)

    for entry in scrapers_manager.search_streams(query):
        merged = dict(entry)
        merged['is_addon_route'] = False
        results.append(merged)

    results.extend(_search_integrations(query))
    return results
