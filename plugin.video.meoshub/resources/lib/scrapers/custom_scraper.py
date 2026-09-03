# -*- coding: utf-8 -*-
"""User-defined custom scrapers.

A custom scraper is just a name + a URL template containing a {query}
placeholder that must return a JSON array of objects. MEOS Hub maps common
field names (title/name, url/link, poster/thumb/image, plot/description,
year) onto its own internal item format, so most simple JSON APIs work
out of the box without any code changes.
"""
import json

try:
    from urllib.parse import quote
    from urllib.request import urlopen
except ImportError:  # pragma: no cover
    from urllib import quote
    from urllib2 import urlopen

from resources.lib.scrapers.base import StreamScraper
from resources.lib.utils import kodi

FIELD_ALIASES = {
    'title': ('title', 'name'),
    'url': ('url', 'link', 'stream'),
    'poster': ('poster', 'thumb', 'image', 'icon'),
    'plot': ('plot', 'description', 'summary'),
    'year': ('year', 'date'),
}


def _first_present(entry, aliases):
    for key in aliases:
        if key in entry and entry[key]:
            return entry[key]
    return ''


class CustomScraper(StreamScraper):
    def __init__(self, name, url_template):
        self.name = name
        self.url_template = url_template

    def search(self, query):
        if not self.url_template or '{query}' not in self.url_template:
            return []
        url = self.url_template.replace('{query}', quote(query or ''))
        try:
            response = urlopen(url, timeout=8)
            data = json.loads(response.read().decode('utf-8'))
        except Exception as exc:
            kodi.log('CustomScraper "{0}" failed: {1}'.format(self.name, exc), kodi.LOGERROR)
            return []

        if isinstance(data, dict):
            data = data.get('results') or data.get('items') or []
        if not isinstance(data, list):
            return []

        results = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            results.append({
                'title': _first_present(entry, FIELD_ALIASES['title']),
                'url': _first_present(entry, FIELD_ALIASES['url']),
                'poster': _first_present(entry, FIELD_ALIASES['poster']),
                'plot': _first_present(entry, FIELD_ALIASES['plot']),
                'year': str(_first_present(entry, FIELD_ALIASES['year'])),
                'source': self.name,
            })
        return [item for item in results if item['title'] and item['url']]
