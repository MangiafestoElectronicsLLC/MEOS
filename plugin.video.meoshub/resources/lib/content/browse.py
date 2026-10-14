# -*- coding: utf-8 -*-
"""Genre and holiday browsing for Movies / TV Shows.

Pure data + lookup logic (no Kodi UI calls). Results come from three kinds
of sources and are returned as plain dicts for ui.py to render:
  - archive.org      -> free public-domain, directly playable
  - TMDB (own key)   -> discovery metadata; selecting one searches the hub
  - integrations     -> matching items from the user's installed add-ons
"""
import datetime

from resources.lib.integrations import manager as integrations_manager
from resources.lib.scrapers.archive_org_scraper import ArchiveOrgScraper
from resources.lib.scrapers.tmdb_scraper import TMDBScraper
from resources.lib.utils import kodi

MEDIA_TYPES = (('movies', 'Movies'), ('tvshows', 'TV Shows'))
MAX_INTEGRATION_MATCHES = 60

# key, label, archive.org subject terms, TMDB movie genre id, TMDB tv genre id
GENRES = [
    ('action', 'Action', ['action'], 28, 10759),
    ('adventure', 'Adventure', ['adventure'], 12, 10759),
    ('animation', 'Animation / Cartoons', ['animation', 'cartoon'], 16, 16),
    ('comedy', 'Comedy', ['comedy'], 35, 35),
    ('crime', 'Crime', ['crime', 'film noir'], 80, 80),
    ('documentary', 'Documentary', ['documentary'], 99, 99),
    ('drama', 'Drama', ['drama'], 18, 18),
    ('family', 'Family / Kids', ['family', 'children'], 10751, 10762),
    ('fantasy', 'Fantasy', ['fantasy'], 14, 10765),
    ('horror', 'Horror', ['horror'], 27, 9648),
    ('mystery', 'Mystery', ['mystery'], 9648, 9648),
    ('romance', 'Romance', ['romance'], 10749, 18),
    ('scifi', 'Sci-Fi', ['science fiction', 'sci-fi'], 878, 10765),
    ('thriller', 'Thriller', ['thriller', 'suspense'], 53, 80),
    ('war', 'War', ['war'], 10752, 10768),
    ('western', 'Western', ['western'], 37, 37),
]

# key, label, search keywords, aliases (for typed search), window start (m, d), window end (m, d)
# A window of None means the date is computed (Easter) or moves too much to track.
HOLIDAYS = [
    ('christmas', 'Christmas', ['christmas', 'santa claus'], ['xmas', 'santa', 'noel', 'x-mas', 'december', 'yule'], (12, 1), (12, 26)),
    ('halloween', 'Halloween', ['halloween', 'trick or treat'], ['spooky', 'october', 'haunted', 'scary'], (10, 1), (10, 31)),
    ('thanksgiving', 'Thanksgiving', ['thanksgiving', 'turkey day'], ['turkey', 'pilgrims', 'november'], (11, 12), (11, 30)),
    ('easter', 'Easter', ['easter', 'easter bunny'], ['bunny', 'spring', 'resurrection'], None, None),
    ('valentines', "Valentine's Day", ['valentine', 'valentines'], ['valentine', 'valentines day', 'love', 'cupid', 'february'], (2, 1), (2, 14)),
    ('newyear', "New Year's", ['new year', 'new years eve'], ['nye', 'new years', 'new year eve', 'january'], (12, 27), (1, 3)),
    ('july4', 'Independence Day (4th of July)', ['independence day', 'fourth of july', '4th of july'], ['4th of july', 'july 4th', 'july', 'patriotic', 'america', 'usa', 'fourth'], (6, 20), (7, 5)),
    ('stpatricks', "St. Patrick's Day", ['st patrick', 'irish'], ['saint patricks', 'st pattys', 'leprechaun', 'ireland', 'march'], (3, 1), (3, 17)),
    ('hanukkah', 'Hanukkah', ['hanukkah', 'chanukah'], ['chanukah', 'menorah', 'jewish'], None, None),
    ('kwanzaa', 'Kwanzaa', ['kwanzaa'], [], (12, 26), (1, 1)),
    ('mothersday', "Mother's Day", ['mothers day', 'mother'], ['mom', 'mothers', 'mother'], (5, 1), (5, 14)),
    ('fathersday', "Father's Day", ['fathers day', 'father'], ['dad', 'fathers', 'father'], (6, 1), (6, 20)),
    ('memorialday', 'Memorial Day / Veterans Day', ['memorial day', 'veterans day', 'veteran'], ['veterans', 'memorial', 'military', 'soldier', 'armed forces'], (5, 20), (5, 31)),
    ('mlk', 'Martin Luther King Jr. Day', ['martin luther king', 'civil rights'], ['mlk', 'king day', 'black history'], (1, 10), (1, 20)),
    ('groundhog', 'Groundhog Day', ['groundhog day', 'groundhog'], ['groundhog'], (1, 25), (2, 2)),
]


def genre_label(genre_key):
    for key, label, _, _, _ in GENRES:
        if key == genre_key:
            return label
    return genre_key


def _genre(genre_key):
    for genre in GENRES:
        if genre[0] == genre_key:
            return genre
    return None


def _holiday(holiday_key):
    for holiday in HOLIDAYS:
        if holiday[0] == holiday_key:
            return holiday
    return None


def holiday_label(holiday_key):
    holiday = _holiday(holiday_key)
    return holiday[1] if holiday else holiday_key


def media_label(media_type):
    return 'TV Shows' if media_type == 'tvshows' else 'Movies'


def _easter_date(year):
    """Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return datetime.date(year, month, day + 1)


def _in_window(holiday, today):
    key, _, _, _, start, end = holiday
    if key == 'easter':
        easter = _easter_date(today.year)
        return easter - datetime.timedelta(days=21) <= today <= easter + datetime.timedelta(days=1)
    if not start or not end:
        # Hanukkah moves around the Hebrew calendar; treat all of December as in-season.
        return key == 'hanukkah' and today.month == 12
    start_md, end_md, today_md = start, end, (today.month, today.day)
    if start_md <= end_md:
        return start_md <= today_md <= end_md
    return today_md >= start_md or today_md <= end_md  # window wraps the new year


def current_holidays(today=None):
    """Holidays that are in season right now, as [(key, label)]."""
    today = today or datetime.date.today()
    return [(h[0], h[1]) for h in HOLIDAYS if _in_window(h, today)]


def all_holidays():
    return [(h[0], h[1]) for h in HOLIDAYS]


def match_holidays(query):
    """Holidays matching a typed query (name, keyword or alias, forgiving of
    case/punctuation), e.g. 'xmas' -> Christmas, '4th of july' -> Independence Day.
    """
    needle = ''.join(c for c in (query or '').lower() if c.isalnum() or c == ' ').strip()
    if len(needle) < 3:
        return []
    matches = []
    for key, label, keywords, aliases, _, _ in HOLIDAYS:
        terms = [label] + keywords + aliases
        for term in terms:
            normalized = ''.join(c for c in term.lower() if c.isalnum() or c == ' ')
            if needle == normalized or needle in normalized or (len(normalized) >= 4 and normalized in needle):
                matches.append((key, label))
                break
    return matches


# ---------------------------------------------------------------------------
# Result gathering
# ---------------------------------------------------------------------------

def _clean(term):
    return ''.join(c for c in term if c.isalnum() or c in " -'").strip()


def _archive(terms, media_type, page):
    if not kodi.get_setting_bool('scraper_archiveorg_enabled', True):
        return []
    try:
        return ArchiveOrgScraper().search_terms([_clean(t) for t in terms], media_type='movies', page=page)
    except Exception as exc:
        kodi.log('archive browse failed: {0}'.format(exc), kodi.LOGERROR)
        return []


def _tmdb_ready():
    return kodi.get_setting_bool('scraper_tmdb_enabled', True) and bool(kodi.get_setting('scraper_tmdb_api_key', ''))


def _integration_matches(media_type, terms):
    """Items in the user's integrated add-ons whose label mentions a term."""
    lowered = [t.lower() for t in terms if t]
    results = []
    for integration in integrations_manager.get_resolved_integrations():
        try:
            items = integration.get_category_items(media_type)
        except Exception as exc:
            kodi.log('browse: {0} failed: {1}'.format(integration.name, exc), kodi.LOGERROR)
            continue
        matched = 0
        for entry in items:
            label = (entry.get('label') or '').lower()
            if any(term in label for term in lowered):
                results.append({'integration': integration, 'entry': entry})
                matched += 1
                if matched >= MAX_INTEGRATION_MATCHES:
                    break
    return results


TMDB_LISTS = [
    ('popular', 'Popular'),
    ('top_rated', 'Top Rated'),
    ('trending', 'Trending This Week'),
    ('now', 'Now Playing / On The Air'),
]


def tmdb_ready():
    return _tmdb_ready()


def tmdb_list_results(media_type, kind, page=1):
    tmdb = TMDBScraper().listing(media_type, kind, page) if _tmdb_ready() else []
    return {'integration': [], 'free': [], 'tmdb': tmdb, 'has_more': bool(tmdb)}


def genre_results(media_type, genre_key, page=1, source='tmdb'):
    empty = {'integration': [], 'free': [], 'tmdb': [], 'has_more': False}
    if genre_key == '_all':
        subjects = ['television', 'tv series'] if media_type == 'tvshows' else ['feature film', 'movie']
        free = _archive(subjects, media_type, page)
        return {'integration': [], 'free': free, 'tmdb': [], 'has_more': len(free) >= 25}
    genre = _genre(genre_key)
    if not genre:
        return empty
    _, label, subjects, movie_id, tv_id = genre
    if source == 'free':
        terms = list(subjects) + (['television'] if media_type == 'tvshows' else [])
        free = _archive(terms, media_type, page)
        return {'integration': [], 'free': free, 'tmdb': [], 'has_more': len(free) >= 25}
    if source == 'addons':
        integration = _integration_matches(media_type, [label.split(' /')[0]]) if page == 1 else []
        return {'integration': integration, 'free': [], 'tmdb': [], 'has_more': False}
    tmdb = []
    if _tmdb_ready():
        tmdb = TMDBScraper().discover(media_type, genre_id=(tv_id if media_type == 'tvshows' else movie_id), page=page)
    return {'integration': [], 'free': [], 'tmdb': tmdb, 'has_more': bool(tmdb)}


def holiday_results(media_type, holiday_key, page=1):
    holiday = _holiday(holiday_key)
    if not holiday:
        return {'integration': [], 'free': [], 'tmdb': [], 'has_more': False}
    _, _, keywords, _, _, _ = holiday
    tmdb = []
    if _tmdb_ready():
        tmdb = TMDBScraper().discover_keyword(media_type, keywords[0], page=page)
    free = _archive(keywords, media_type, page)
    integration = _integration_matches(media_type, keywords) if page == 1 else []
    return {'integration': integration, 'free': free, 'tmdb': tmdb, 'has_more': bool(tmdb or len(free) >= 25)}
