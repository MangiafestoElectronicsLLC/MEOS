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
from resources.lib.utils import jsonrpc


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
        a time, returning the directory listing at the end of the path
        (or None if any breadcrumb label could not be found).
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
                return None
            current_url = match.get('file')
            if not current_url:
                return None
            items = jsonrpc.get_directory(current_url)
        return items

    def get_category_items(self, category):
        """Return (folder_url, items) for a unified category, trying each
        configured breadcrumb path until one resolves to a non-empty
        listing. Falls back to the add-on root if nothing matches.
        """
        for breadcrumbs in self.spec.category_paths.get(category, []):
            items = self._navigate(breadcrumbs)
            if items:
                return items
        return []
