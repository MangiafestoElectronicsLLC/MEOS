# -*- coding: utf-8 -*-
"""Registry that aggregates all enabled metadata + stream scrapers."""
from resources.lib.scrapers.archive_org_scraper import ArchiveOrgScraper
from resources.lib.scrapers.custom_scraper import CustomScraper
from resources.lib.scrapers.tmdb_scraper import TMDBScraper
from resources.lib.utils import kodi
from resources.lib.utils.settings import get_json_setting, set_json_setting

CUSTOM_SETTING_ID = 'custom_scrapers_json'


def get_metadata_scrapers():
    scrapers = []
    if kodi.get_setting_bool('scraper_tmdb_enabled', True) and kodi.get_setting('scraper_tmdb_api_key', ''):
        scrapers.append(TMDBScraper())
    return scrapers


def get_stream_scrapers():
    scrapers = []
    if kodi.get_setting_bool('scraper_archiveorg_enabled', True):
        scrapers.append(ArchiveOrgScraper())
    for custom in list_custom_scrapers():
        scrapers.append(CustomScraper(custom['name'], custom['url_template']))
    return scrapers


def search_metadata(query):
    results = []
    for scraper in get_metadata_scrapers():
        try:
            results.extend(scraper.search(query))
        except Exception as exc:
            kodi.log('Metadata scraper {0} failed: {1}'.format(scraper.name, exc), kodi.LOGERROR)
    return results


def search_streams(query):
    results = []
    for scraper in get_stream_scrapers():
        try:
            results.extend(scraper.search(query))
        except Exception as exc:
            kodi.log('Stream scraper {0} failed: {1}'.format(scraper.name, exc), kodi.LOGERROR)
    return results


def list_custom_scrapers():
    return get_json_setting(CUSTOM_SETTING_ID, [])


def add_custom_scraper(name, url_template):
    name = (name or '').strip()
    url_template = (url_template or '').strip()
    if not name or not url_template:
        return False
    custom = list_custom_scrapers()
    if any(item['name'] == name for item in custom):
        return False
    custom.append({'name': name, 'url_template': url_template})
    set_json_setting(CUSTOM_SETTING_ID, custom)
    return True


def remove_custom_scraper(name):
    custom = list_custom_scrapers()
    new_custom = [item for item in custom if item['name'] != name]
    set_json_setting(CUSTOM_SETTING_ID, new_custom)
    return len(new_custom) != len(custom)
