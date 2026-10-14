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


def check_holidays_and_genres():
    import datetime
    import tools.kodi_mocks as kodi_mocks
    kodi_mocks.install()

    from resources.lib import router
    from resources.lib.content import browse
    from resources.lib.scrapers import archive_org_scraper

    assert ('christmas', 'Christmas') in browse.match_holidays('xmas')
    assert ('july4', 'Independence Day (4th of July)') in browse.match_holidays('4th of July')
    assert ('halloween', 'Halloween') in browse.match_holidays('HALLOWEEN')
    assert browse.match_holidays('zz') == []
    assert 'christmas' in [k for k, _ in browse.current_holidays(datetime.date(2026, 12, 10))]
    assert 'newyear' in [k for k, _ in browse.current_holidays(datetime.date(2027, 1, 1))]
    assert 'easter' in [k for k, _ in browse.current_holidays(datetime.date(2026, 4, 3))]
    assert 'halloween' not in [k for k, _ in browse.current_holidays(datetime.date(2026, 12, 10))]

    archive_org_scraper.ArchiveOrgScraper._get_json = lambda self, url: {
        'response': {'docs': [{'identifier': 'demo-id', 'title': 'Demo Holiday Film', 'year': 1950}]}
    }
    queries = [
        'category&category=movies', 'category&category=tvshows', 'category_all&category=movies',
        'genre&media=movies&genre=horror', 'genre&media=tvshows&genre=comedy',
        'genre&media=movies&genre=horror&source=free', 'genre&media=tvshows&genre=_all&source=free',
        'genres&media=movies&source=tmdb', 'tmdb_menu&media=movies', 'tmdb_list&media=tvshows&kind=top_rated',
        'free_menu&media=tvshows', 'category&category=livetv', 'channel_groups&category=sports',
        'holidays', 'holidays&media=movies', 'holiday&holiday=christmas',
        'holiday&holiday=christmas&media=movies', 'holiday&holiday=halloween&media=tvshows',
    ]
    for query in queries:
        kodi_mocks.DIRECTORY_ITEMS[:] = []
        router.run(['plugin://plugin.video.meoshub', '1', '?action=' + query])
        assert kodi_mocks.DIRECTORY_ITEMS, 'no items for ' + query
    assert any('Demo Holiday Film' in str(item) for item in kodi_mocks.DIRECTORY_ITEMS)

    from resources.lib.content import livetv
    sample = '#EXTM3U\n#EXTINF:-1 tvg-logo="http://x/l.png" group-title="News",Demo News\nhttp://example.com/a.m3u8\n'
    parsed = livetv.parse_m3u(sample)
    assert parsed == [{'name': 'Demo News', 'url': 'http://example.com/a.m3u8', 'logo': 'http://x/l.png', 'group': 'News'}]
    livetv._fetch = lambda url: parsed
    kodi_mocks.DIRECTORY_ITEMS[:] = []
    router.run(['plugin://plugin.video.meoshub', '1', '?action=channels&group=news'])
    assert any(i['label'] == 'Demo News' for i in kodi_mocks.DIRECTORY_ITEMS)


def check_bootstrap_defaults():
    import tools.kodi_mocks as kodi_mocks
    kodi_mocks.install()

    from resources.lib.integrations import bootstrap, manager
    calls = []
    bootstrap.xbmc.executebuiltin = lambda cmd: calls.append(cmd)
    keys = [s.key for s in manager.builtin_specs()]
    for expected in ('redgratis', 'ghost', 'theloop', 'risingtides'):
        assert expected in keys, expected
    summary = bootstrap.ensure_defaults(force=True)
    assert 'InstallAddon(plugin.video.redgratis)' in calls, calls
    assert 'Red Gratis' in summary['install_requested']
    calls[:] = []
    bootstrap.ensure_defaults()
    assert not calls, 'should not retry automatically'


def main():
    check('Default integrations bootstrap', check_bootstrap_defaults)
    check('XML files are well-formed', check_xml_files)
    check('All Python files compile', check_python_compiles)
    check('Router builds core screens without crashing', check_router_smoke_test)
    check('Genre/holiday browsing and holiday search work', check_holidays_and_genres)
    check('Nested third-party content is merged as playable items', check_nested_integration_content)

    print('')
    if FAILURES:
        print('{0} check(s) FAILED: {1}'.format(len(FAILURES), ', '.join(FAILURES)))
        sys.exit(1)
    print('All checks passed.')
    sys.exit(0)


if __name__ == '__main__':
    main()
