# -*- coding: utf-8 -*-
"""Built-in integration specs for the add-ons required by the spec.

Real-world add-on ids and internal menu wording vary between forks and
Kodi builds, so each spec ships several best-effort breadcrumb paths and
keyword hints. Users can always fine-tune coverage via
"Settings -> Integrations -> Manage Custom Add-ons" if a path guess misses,
or simply rely on the automatic root-folder fallback.
"""

MOVIE_PATHS = [
    ['Movies'],
    ['Movies', 'Movies'],
    ['Movies', 'TMDB'],
    ['Movies', 'Movies', 'TMDB'],
]

TVSHOW_PATHS = [
    ['TV Shows'],
    ['TV Shows', 'TV Shows'],
    ['TV Shows', 'TMDB'],
    ['TV Shows', 'TV Shows', 'TMDB'],
    ['Shows'],
]

LIVE_PATHS = [
    ['Live TV'],
    ['Live', 'Channels'],
    ['Cable'],
    ['Live TV', 'Channels'],
]

SPORTS_PATHS = [
    ['Sports'],
    ['Live', 'Sports'],
    ['Sports', 'Live'],
]

PPV_PATHS = [
    ['PPV'],
    ['Pay Per View'],
    ['Sports', 'PPV'],
]

NETWORK_PATHS = [
    ['Networks'],
    ['TV Networks'],
    ['Channels'],
]

BUILTIN_INTEGRATIONS = [
    {
        'key': 'scrubsv2',
        'label': 'Scrubs V2',
        'addon_id_guess': 'plugin.video.scrubsv2',
        'keywords': ['scrubsv2', 'scrubs v2', 'scrubs'],
        'category_paths': {
            'movies': MOVIE_PATHS,
            'tvshows': TVSHOW_PATHS,
            'sports': SPORTS_PATHS,
            'ppv': PPV_PATHS,
            'livetv': LIVE_PATHS,
            'networks': NETWORK_PATHS,
        },
    },
    {
        'key': 'theloop',
        'label': 'The Loop',
        'addon_id_guess': 'plugin.video.theloop',
        'keywords': ['theloop', 'the loop', 'loop'],
        'category_paths': {
            'movies': MOVIE_PATHS,
            'tvshows': TVSHOW_PATHS,
            'sports': SPORTS_PATHS,
            'ppv': PPV_PATHS,
            'livetv': LIVE_PATHS,
            'networks': NETWORK_PATHS,
        },
    },
    {
        'key': 'ghost',
        'label': 'Ghost',
        'addon_id_guess': 'plugin.video.ghost',
        'keywords': ['ghost'],
        'category_paths': {
            'movies': MOVIE_PATHS,
            'tvshows': TVSHOW_PATHS,
            'sports': SPORTS_PATHS,
            'ppv': PPV_PATHS,
            'livetv': LIVE_PATHS,
            'networks': NETWORK_PATHS,
        },
    },
    {
        'key': 'thecrew',
        'label': 'The Crew',
        'addon_id_guess': 'plugin.video.thecrew',
        'keywords': ['thecrew', 'the crew', 'crew'],
        'category_paths': {
            'movies': MOVIE_PATHS,
            'tvshows': TVSHOW_PATHS,
            'sports': SPORTS_PATHS,
            'ppv': PPV_PATHS,
            'livetv': LIVE_PATHS,
            'networks': NETWORK_PATHS,
        },
    },
    {
        'key': 'youtube',
        'label': 'YouTube',
        'addon_id_guess': 'plugin.video.youtube',
        'keywords': ['youtube', 'you tube'],
        'category_paths': {
            'movies': [['Movies'], ['Playlists'], ['Popular right now']],
            'tvshows': [['Shows'], ['Subscriptions'], ['Playlists']],
            'sports': [['Sports'], ['Search']],
            'ppv': [['Live'], ['Search']],
            'livetv': [['Live'], ['Search']],
            'networks': [['Channels'], ['Subscriptions'], ['Playlists']],
        },
    },
]

# Settings id (bool) that toggles each built-in integration on/off.
BUILTIN_TOGGLE_SETTING = {
    'scrubsv2': 'integration_scrubsv2_enabled',
    'theloop': 'integration_theloop_enabled',
    'ghost': 'integration_ghost_enabled',
    'thecrew': 'integration_thecrew_enabled',
    'youtube': 'integration_youtube_enabled',
}
