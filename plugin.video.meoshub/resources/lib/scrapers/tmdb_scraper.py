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

    @staticmethod
    def _to_results(data, media_type):
        results = []
        for entry in data.get('results', []) or []:
            date = entry.get('release_date') or entry.get('first_air_date') or ''
            poster = entry.get('poster_path')
            backdrop = entry.get('backdrop_path')
            results.append({
                'title': entry.get('title') or entry.get('name') or '',
                'year': date[:4] if date else '',
                'plot': entry.get('overview', ''),
                'poster': IMAGE_BASE + poster if poster else '',
                'fanart': FANART_BASE + backdrop if backdrop else '',
                'genre': '',
                'media_type': 'tv' if media_type == 'tvshows' else 'movie',
                'source': 'tmdb',
            })
        return [r for r in results if r['title']]

    def discover(self, media_type, genre_id=None, keyword_ids=None, page=1):
        """Browse popular titles by TMDB genre and/or keyword ids."""
        if not self.api_key:
            return []
        kind = 'tv' if media_type == 'tvshows' else 'movie'
        params = {'sort_by': 'popularity.desc', 'include_adult': 'false', 'page': page}
        if genre_id:
            params['with_genres'] = genre_id
        if keyword_ids:
            params['with_keywords'] = '|'.join(str(k) for k in keyword_ids)
        cache_key = 'tmdb_discover_{0}_{1}_{2}_{3}'.format(kind, genre_id, params.get('with_keywords', ''), page)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        results = self._to_results(self._get('/discover/' + kind, params), media_type)
        cache.set(cache_key, results)
        return results

    def listing(self, media_type, kind, page=1):
        """Standard TMDB lists: popular, top_rated, trending, now."""
        if not self.api_key:
            return []
        tv = media_type == 'tvshows'
        paths = {
            'popular': '/tv/popular' if tv else '/movie/popular',
            'top_rated': '/tv/top_rated' if tv else '/movie/top_rated',
            'trending': '/trending/tv/week' if tv else '/trending/movie/week',
            'now': '/tv/on_the_air' if tv else '/movie/now_playing',
        }
        path = paths.get(kind, paths['popular'])
        cache_key = 'tmdb_list_{0}_{1}'.format(path, page)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        results = self._to_results(self._get(path, {'page': page}), media_type)
        cache.set(cache_key, results)
        return results

    def discover_keyword(self, media_type, keyword, page=1):
        """Browse titles tagged with a TMDB keyword (e.g. 'christmas')."""
        if not self.api_key or not keyword:
            return []
        cache_key = 'tmdb_kwids_' + keyword
        ids = cache.get(cache_key, ttl_seconds=30 * 24 * 3600)
        if ids is None:
            data = self._get('/search/keyword', {'query': keyword})
            ids = [k['id'] for k in (data.get('results') or [])[:5] if k.get('id')]
            if ids:
                cache.set(cache_key, ids)
        if not ids:
            return []
        return self.discover(media_type, keyword_ids=ids, page=page)

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
