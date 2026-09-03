# -*- coding: utf-8 -*-
"""Free, legal public-domain streams from the Internet Archive (archive.org).

Uses only archive.org's public, documented APIs:
  - advancedsearch.php  -> find items matching a query
  - metadata/<id>       -> discover the actual playable file for an item
"""
import json

try:
    from urllib.parse import urlencode
    from urllib.request import urlopen
except ImportError:  # pragma: no cover
    from urllib import urlencode
    from urllib2 import urlopen

from resources.lib.scrapers.base import StreamScraper
from resources.lib.utils import cache, kodi

PLAYABLE_EXTENSIONS = ('.mp4', '.m4v', '.ogv', '.webm')


class ArchiveOrgScraper(StreamScraper):
    name = 'archive.org'

    def __init__(self, api_base=None):
        self.api_base = (api_base or kodi.get_setting('scraper_archiveorg_api_base', 'https://archive.org')).rstrip('/')

    def _get_json(self, url):
        try:
            response = urlopen(url, timeout=8)
            return json.loads(response.read().decode('utf-8'))
        except Exception as exc:
            kodi.log('ArchiveOrgScraper request failed: {0}'.format(exc), kodi.LOGERROR)
            return {}

    def _resolve_stream_url(self, identifier):
        data = self._get_json('{0}/metadata/{1}'.format(self.api_base, identifier))
        server = data.get('server')
        directory = data.get('dir')
        for file_info in data.get('files', []) or []:
            name = file_info.get('name', '')
            if name.lower().endswith(PLAYABLE_EXTENSIONS):
                if server and directory:
                    return 'https://{0}{1}/{2}'.format(server, directory, name)
                return '{0}/download/{1}/{2}'.format(self.api_base, identifier, name)
        return ''

    def search(self, query, media_type='movies', max_results=25):
        if not query:
            return []
        cache_key = 'archiveorg_search_{0}_{1}'.format(media_type, query)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        params = {
            'q': 'mediatype:({0}) AND title:({1})'.format(media_type, query),
            'fl[]': ['identifier', 'title', 'year', 'description'],
            'rows': str(max_results),
            'output': 'json',
        }
        url = '{0}/advancedsearch.php?{1}'.format(self.api_base, urlencode(params, doseq=True))
        data = self._get_json(url)
        docs = data.get('response', {}).get('docs', []) or []

        results = []
        for doc in docs:
            identifier = doc.get('identifier')
            if not identifier:
                continue
            results.append({
                'title': doc.get('title', identifier),
                'year': str(doc.get('year', '')),
                'plot': doc.get('description', '') if isinstance(doc.get('description', ''), str) else '',
                'identifier': identifier,
                'poster': '{0}/services/img/{1}'.format(self.api_base, identifier),
                'source': 'archive.org',
                # Resolved lazily (only when the user actually plays it) to
                # avoid one extra HTTP request per search result.
                'url': '',
            })
        cache.set(cache_key, results)
        return results

    def resolve(self, identifier):
        """Resolve a lazy archive.org search result into a real stream URL."""
        cache_key = 'archiveorg_stream_' + identifier
        cached = cache.get(cache_key)
        if cached:
            return cached
        url = self._resolve_stream_url(identifier)
        if url:
            cache.set(cache_key, url)
        return url
