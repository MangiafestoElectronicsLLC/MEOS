# -*- coding: utf-8 -*-
"""Base interfaces for metadata and free-stream scrapers.

A "metadata scraper" enriches items with posters/fanart/plot/genre/year.
A "stream scraper" finds actual playable, legal free content (e.g. public
domain movies on archive.org).
"""


class MetadataScraper(object):
    name = 'base-metadata'

    def search(self, query):
        """Return a list of dicts: title, year, plot, poster, fanart, genre."""
        raise NotImplementedError


class StreamScraper(object):
    name = 'base-stream'

    def search(self, query):
        """Return a list of dicts: title, url, poster, plot, year (playable)."""
        raise NotImplementedError
