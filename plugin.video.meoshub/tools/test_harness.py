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


def check_nested_integration_content():
    import tools.kodi_mocks as kodi_mocks
    kodi_mocks.install()

    from resources.lib.integrations.base import Integration, IntegrationSpec
    from resources.lib.integrations import base as integration_base

    integration_base.set_json_setting(integration_base.TARGET_CACHE_SETTING, {})
    root = 'plugin://plugin.video.thirdparty/'
    movies = root + 'movies'
    nested_movies = movies + '/movies'
    kodi_mocks.JSONRPC_RESPONSES['Files.GetDirectory'] = {
        'files': [{'label': 'Movies', 'file': movies, 'filetype': 'directory'}]
    }
    directory_responses = {
        movies: {'files': [{'label': 'Movies', 'file': nested_movies, 'filetype': 'directory'}]},
        nested_movies: {'files': [{'label': 'Example Movie', 'file': root + 'play/1', 'filetype': 'file'}]},
    }

    original_responses = dict(kodi_mocks.JSONRPC_RESPONSES)

    def execute_nested(request_json):
        import json
        request = json.loads(request_json)
        if request.get('method') == 'Files.GetDirectory':
            directory = request.get('params', {}).get('directory')
            result = directory_responses.get(directory, kodi_mocks.JSONRPC_RESPONSES['Files.GetDirectory'])
            return json.dumps({'jsonrpc': '2.0', 'id': 1, 'result': result})
        return kodi_mocks._execute_json_rpc(request_json)

    kodi_mocks.xbmc.executeJSONRPC = execute_nested
    try:
        spec = IntegrationSpec('custom:test', 'Third Party', 'plugin.video.thirdparty', [],
                               category_paths={'movies': [['Movies'], ['Movies', 'Movies']]}, builtin=False)
        items = Integration(spec, 'plugin.video.thirdparty', 'Third Party').get_category_items('movies')
        assert [item.get('label') for item in items] == ['Example Movie']
        assert items[0].get('_meos_is_folder') is False
    finally:
        kodi_mocks.JSONRPC_RESPONSES.clear()
        kodi_mocks.JSONRPC_RESPONSES.update(original_responses)
        kodi_mocks.xbmc.executeJSONRPC = kodi_mocks._execute_json_rpc


def main():
    check('XML files are well-formed', check_xml_files)
    check('All Python files compile', check_python_compiles)
    check('Router builds core screens without crashing', check_router_smoke_test)
    check('Nested third-party content is merged as playable items', check_nested_integration_content)

    print('')
    if FAILURES:
        print('{0} check(s) FAILED: {1}'.format(len(FAILURES), ', '.join(FAILURES)))
        sys.exit(1)
    print('All checks passed.')
    sys.exit(0)


if __name__ == '__main__':
    main()
