# -*- coding: utf-8 -*-
"""Resolves configured integrations to real, installed add-ons and merges
their category listings into MEOS Hub's own menus.
"""
from resources.lib.integrations.base import Integration, IntegrationSpec
from resources.lib.integrations.known_addons import BUILTIN_INTEGRATIONS, BUILTIN_TOGGLE_SETTING
from resources.lib.utils import jsonrpc, kodi
from resources.lib.utils.settings import get_json_setting, set_json_setting

CUSTOM_SETTING_ID = 'custom_integrations_json'


def _builtin_specs():
    return [
        IntegrationSpec(
            key=item['key'],
            label=item['label'],
            addon_id_guess=item['addon_id_guess'],
            keywords=item['keywords'],
            category_paths=item['category_paths'],
            builtin=True,
        )
        for item in BUILTIN_INTEGRATIONS
    ]


def _custom_specs():
    specs = []
    for item in get_json_setting(CUSTOM_SETTING_ID, []):
        specs.append(IntegrationSpec(
            key='custom:' + item['addon_id'],
            label=item.get('label') or item['addon_id'],
            addon_id_guess=item['addon_id'],
            keywords=[item['addon_id']],
            category_paths=item.get('category_paths') or {
                'movies': [['Movies']],
                'tvshows': [['TV Shows']],
                'sports': [['Sports']],
                'ppv': [['PPV']],
                'livetv': [['Live TV']],
                'networks': [['Networks']],
            },
            builtin=False,
        ))
    return specs


def get_enabled_specs():
    """All specs the user currently wants active (built-in toggles + custom)."""
    enabled = []
    for spec in _builtin_specs():
        toggle_id = BUILTIN_TOGGLE_SETTING.get(spec.key)
        if not toggle_id or kodi.get_setting_bool(toggle_id, True):
            enabled.append(spec)
    enabled.extend(_custom_specs())
    return enabled


def get_all_specs():
    """Built-in + custom specs regardless of enabled state (for the manage screen)."""
    return _builtin_specs() + _custom_specs()


def resolve(spec):
    """Try to bind a spec to a real installed add-on. Returns Integration or None."""
    if jsonrpc.is_addon_installed(spec.addon_id_guess):
        return Integration(spec, spec.addon_id_guess, spec.label)
    match = jsonrpc.find_addon_by_keywords(spec.keywords)
    if match:
        return Integration(spec, match['addonid'], match.get('name', spec.label))
    return None


def get_resolved_integrations():
    """Resolved (installed) integrations only, for building menus/category merges."""
    resolved = []
    for spec in get_enabled_specs():
        integration = resolve(spec)
        if integration:
            resolved.append(integration)
    return resolved


def get_category_items_for_all(category):
    """Merge category listings from every resolved integration.

    Returns a list of (integration, items) tuples so the UI layer can tag
    each result with its source add-on.
    """
    results = []
    for integration in get_resolved_integrations():
        items = integration.get_category_items(category)
        if items:
            results.append((integration, items))
    return results


def add_custom_integration(addon_id, label=None):
    addon_id = (addon_id or '').strip()
    if not addon_id:
        return False
    custom = get_json_setting(CUSTOM_SETTING_ID, [])
    if any(item['addon_id'] == addon_id for item in custom):
        return False
    custom.append({'addon_id': addon_id, 'label': label or addon_id})
    set_json_setting(CUSTOM_SETTING_ID, custom)
    return True


def remove_custom_integration(addon_id):
    custom = get_json_setting(CUSTOM_SETTING_ID, [])
    new_custom = [item for item in custom if item['addon_id'] != addon_id]
    set_json_setting(CUSTOM_SETTING_ID, new_custom)
    return len(new_custom) != len(custom)


def list_custom_integrations():
    return get_json_setting(CUSTOM_SETTING_ID, [])
