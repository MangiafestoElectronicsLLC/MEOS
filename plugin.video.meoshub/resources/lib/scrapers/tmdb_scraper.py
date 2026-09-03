# -*- coding: utf-8 -*-
"""TMDB metadata scraper (legal, official API - requires a free user API key).

No API key ships with MEOS Hub. Users add their own free TMDB key under
Settings -> Scrapers -> TMDB API Key.
"""
import json

try:
    from urllib.parse import urlencode
    from urllib.request import urlopen
except ImportError:  # pragma: no cover - Python 2 fallback for old Kodi builds
    from urllib import urlencode
    from urllib2 import urlopen

from resources.lib.scrapers.base import MetadataScraper
from resources.lib.utils import cache, kodi

IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'
FANART_BASE = 'https://image.tmdb.org/t/p/w1280'


class TMDBScraper(MetadataScraper):
    name = 'tmdb'

    def __init__(self, api_key=None, api_base=None):
        self.api_key = api_key or kodi.get_setting('scraper_tmdb_api_key', '')
        self.api_base = (api_base or kodi.get_setting('scraper_tmdb_api_base', 'https://api.themoviedb.org/3')).rstrip('/')

    def _get(self, path, params):
        if not self.api_key:
            return {}
        params = dict(params)
        params['api_key'] = self.api_key
        url = '{0}{1}?{2}'.format(self.api_base, path, urlencode(params))
        try:
            response = urlopen(url, timeout=8)
            return json.loads(response.read().decode('utf-8'))
        except Exception as exc:
            kodi.log('TMDBScraper request failed: {0}'.format(exc), kodi.LOGERROR)
            return {}

    def search(self, query):
        if not self.api_key or not query:
            return []
        cache_key = 'tmdb_search_' + query
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._get('/search/multi', {'query': query, 'include_adult': 'false'})
        results = []
        for entry in data.get('results', []) or []:
            media_type = entry.get('media_type')
            if media_type not in ('movie', 'tv'):
                continue
            title = entry.get('title') or entry.get('name') or ''
            date = entry.get('release_date') or entry.get('first_air_date') or ''
            poster = entry.get('poster_path')
            backdrop = entry.get('backdrop_path')
            results.append({
                'title': title,
                'year': date[:4] if date else '',
                'plot': entry.get('overview', ''),
                'poster': IMAGE_BASE + poster if poster else '',
                'fanart': FANART_BASE + backdrop if backdrop else '',
                'genre': '',
                'media_type': media_type,
                'source': 'tmdb',
            })
        cache.set(cache_key, results)
        return results
