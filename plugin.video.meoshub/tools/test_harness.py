# -*- coding: utf-8 -*-
"""Offline validation + smoke-test harness for MEOS Hub.

Run with:  python tools/test_harness.py
No Kodi installation is required - this uses tools/kodi_mocks.py to stand
in for xbmc/xbmcgui/xbmcplugin/xbmcaddon/xbmcvfs.

Checks performed:
  1. addon.xml and resources/settings.xml are well-formed XML.
  2. Every .py file in the add-on compiles cleanly.
  3. The router can build the main menu and every category/search/settings
     screen without raising an exception.
"""
import os
import py_compile
import sys
import xml.etree.ElementTree as ET

ADDON_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ADDON_ROOT)

FAILURES = []


def check(label, func):
    try:
        func()
        print('[PASS] {0}'.format(label))
    except Exception as exc:  # noqa: BLE001 - harness must report, not raise
        print('[FAIL] {0}: {1}'.format(label, exc))
        FAILURES.append(label)


def check_xml_files():
    for relative_path in ('addon.xml', os.path.join('resources', 'settings.xml')):
        ET.parse(os.path.join(ADDON_ROOT, relative_path))


def check_python_compiles():
    for dirpath, dirnames, filenames in os.walk(ADDON_ROOT):
        dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git')]
        for filename in filenames:
            if filename.endswith('.py'):
                py_compile.compile(os.path.join(dirpath, filename), doraise=True)


def check_router_smoke_test():
    import tools.kodi_mocks as kodi_mocks
    kodi_mocks.install()

    from resources.lib import router

    actions = [
        '',
        'category&category=movies',
        'category&category=tvshows',
        'integrations',
        'integration_discover',
        'favorites',
        'settings',
        'settings_categories',
        'settings_integrations',
        'settings_scrapers',
        'settings_importexport',
    ]
    for action_query in actions:
        kodi_mocks.DIRECTORY_ITEMS[:] = []
        router.run(['plugin://plugin.video.meoshub', '1', '?action=' + action_query.split('&', 1)[0] +
                    ('&' + action_query.split('&', 1)[1] if '&' in action_query else '')])


def main():
    check('XML files are well-formed', check_xml_files)
    check('All Python files compile', check_python_compiles)
    check('Router builds core screens without crashing', check_router_smoke_test)

    print('')
    if FAILURES:
        print('{0} check(s) FAILED: {1}'.format(len(FAILURES), ', '.join(FAILURES)))
        sys.exit(1)
    print('All checks passed.')
    sys.exit(0)


if __name__ == '__main__':
    main()
