# -*- coding: utf-8 -*-
"""Base classes for routing into other, already-installed Kodi add-ons.

MEOS Hub never imports or copies a third-party add-on's code. Instead it:
  1. Uses JSON-RPC to find the add-on that is actually installed on this
     device (ids/names vary between forks/builds, so we match loosely).
  2. Uses JSON-RPC (Files.GetDirectory) to browse that add-on's own
     plugin:// menu tree and find the sub-folder that matches a unified
     MEOS Hub category (Movies, TV Shows, ...).
  3. Hands back plain plugin:// URLs. Kodi's normal navigation takes care
     of actually invoking the target add-on when the user selects an item.
"""
from resources.lib.integrations.known_addons import CATEGORY_KEYWORDS
from resources.lib.utils import jsonrpc
from resources.lib.utils.settings import get_json_setting, set_json_setting

# Persisted addon_id -> {category: folder_url} cache so a resolved folder
# (via breadcrumbs or the generic BFS fallback) doesn't need to be
# re-discovered on every single menu open.
TARGET_CACHE_SETTING = 'integration_target_cache_json'

# BFS fallback bounds: keep any single "any add-on" scan fast and bounded,
# since add-ons can have arbitrarily deep/large menu trees.
BFS_MAX_DEPTH = 3
BFS_MAX_NODES = 40


def _get_target_cache():
    return get_json_setting(TARGET_CACHE_SETTING, {})


def _cache_target(addon_id, category, url):
    cache = _get_target_cache()
    cache.setdefault(addon_id, {})[category] = url
    set_json_setting(TARGET_CACHE_SETTING, cache)


def clear_target_cache(addon_id=None):
    """Drop cached folder resolutions, forcing a fresh BFS/breadcrumb scan.
    Called after enabling/removing an integration so stale targets never stick.
    """
    if addon_id is None:
        set_json_setting(TARGET_CACHE_SETTING, {})
        return
    cache = _get_target_cache()
    if cache.pop(addon_id, None) is not None:
        set_json_setting(TARGET_CACHE_SETTING, cache)


class IntegrationSpec(object):
    """Static description of an integration (built-in or user-added)."""

    def __init__(self, key, label, addon_id_guess, keywords, category_paths=None, builtin=True):
        self.key = key
        self.label = label
        self.addon_id_guess = addon_id_guess
        # Keywords used to find the real installed add-on id/name on this device.
        self.keywords = keywords
        # category -> list of breadcrumb paths to try, e.g.
        # {"movies": [["Movies"], ["Movies", "Movies"]]}
        self.category_paths = category_paths or {}
        self.builtin = builtin


class Integration(object):
    """A resolved integration: a spec bound to a real, installed add-on id."""

    def __init__(self, spec, installed_addon_id, installed_name=None):
        self.spec = spec
        self.addon_id = installed_addon_id
        self.name = installed_name or spec.label

    @property
    def root_url(self):
        return 'plugin://{0}/'.format(self.addon_id)

    def get_root_items(self):
        return jsonrpc.get_directory(self.root_url)

    def _navigate(self, breadcrumbs):
        """Walk a list of folder labels from the add-on root, one level at
        a time, returning (final_folder_url, items) at the end of the path
        (or (None, None) if any breadcrumb label could not be found).
        """
        current_url = self.root_url
        items = jsonrpc.get_directory(current_url)
        for label in breadcrumbs:
            match = None
            for entry in items:
                entry_label = (entry.get('label') or '').strip().lower()
                if entry_label == label.strip().lower():
                    match = entry
                    break
            if not match:
                return None, None
            current_url = match.get('file')
            if not current_url:
                return None, None
            items = jsonrpc.get_directory(current_url)
        return current_url, items

    def _bfs_find_category_folder(self, category):
        """Generic fallback: breadth-first search this add-on's own menu
        tree, scoring folder labels against unified-category keywords, so
        add-ons with no configured breadcrumb paths can still be matched.
        Bounded by BFS_MAX_DEPTH/BFS_MAX_NODES to keep it fast.
        """
        keywords = CATEGORY_KEYWORDS.get(category, [])
        if not keywords:
            return None
        queue = [(self.root_url, 0)]
        visited = set()
        best_url = None
        best_score = 0
        while queue and len(visited) < BFS_MAX_NODES:
            url, depth = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            for entry in jsonrpc.get_directory(url):
                label = (entry.get('label') or '').strip().lower()
                entry_url = entry.get('file')
                if not entry_url:
                    continue
                is_folder = entry.get('filetype') == 'directory' or entry_url.startswith('plugin://')
                if not is_folder:
                    continue
                score = sum(1 for keyword in keywords if keyword in label)
                if score > best_score:
                    best_score = score
                    best_url = entry_url
                if score > 0 and depth + 1 < BFS_MAX_DEPTH:
                    queue.append((entry_url, depth + 1))
        return best_url

    def get_category_items(self, category):
        """Return items for a unified category, in order of preference:
        1. A previously cached, resolved folder for this add-on+category.
        2. Each configured breadcrumb path, tried in order.
        3. A generic BFS keyword scan of the add-on's own menu tree, so
           add-ons with no configured breadcrumb paths still work.
        Any newly resolved folder is cached for next time.
        """
        cached_url = _get_target_cache().get(self.addon_id, {}).get(category)
        if cached_url:
            items = jsonrpc.get_directory(cached_url)
            if items:
                return items

        for breadcrumbs in self.spec.category_paths.get(category, []):
            folder_url, items = self._navigate(breadcrumbs)
            if items:
                _cache_target(self.addon_id, category, folder_url)
                return items

        discovered_url = self._bfs_find_category_folder(category)
        if discovered_url:
            items = jsonrpc.get_directory(discovered_url)
            if items:
                _cache_target(self.addon_id, category, discovered_url)
                return items

        return []
