# -*- coding: utf-8 -*-
"""Free live channels (cable-style) from public M3U playlists.

Uses the community iptv-org category playlists (publicly listed free
channels) plus any M3U URL/file the user adds in Settings. Nothing is
bundled; playlists are fetched on demand and cached.
"""
try:
    from urllib.request import urlopen
except ImportError:  # pragma: no cover
    from urllib2 import urlopen

from resources.lib.utils import cache, kodi

IPTV_BASE = 'https://iptv-org.github.io/iptv/categories/{0}.m3u'

# key, label
CHANNEL_GROUPS = [
    ('news', 'News'),
    ('sports', 'Sports'),
    ('movies', 'Movies'),
    ('entertainment', 'Entertainment'),
    ('comedy', 'Comedy'),
    ('series', 'Series / TV Shows'),
    ('classic', 'Classic TV'),
    ('kids', 'Kids'),
    ('animation', 'Animation'),
    ('documentary', 'Documentary'),
    ('music', 'Music'),
    ('family', 'Family'),
    ('lifestyle', 'Lifestyle'),
    ('cooking', 'Cooking'),
    ('travel', 'Travel'),
    ('science', 'Science'),
    ('religious', 'Religious'),
    ('weather', 'Weather'),
    ('general', 'General'),
]

CUSTOM_PLAYLIST_SETTING = 'custom_m3u_url'
MAX_CHANNELS = 600


def group_label(key):
    for k, label in CHANNEL_GROUPS:
        if k == key:
            return label
    return key


def parse_m3u(text):
    """Parse M3U text into [{'name','url','logo','group'}]."""
    channels = []
    name = logo = group = ''
    for raw in (text or '').splitlines():
        line = raw.strip()
        if line.startswith('#EXTINF'):
            logo = _attr(line, 'tvg-logo')
            group = _attr(line, 'group-title')
            name = line.rsplit(',', 1)[1].strip() if ',' in line else ''
        elif line and not line.startswith('#'):
            if line.startswith(('http://', 'https://', 'rtmp://', 'plugin://')):
                channels.append({'name': name or line, 'url': line, 'logo': logo, 'group': group})
            name = logo = group = ''
    return channels


def _attr(line, attr):
    marker = attr + '="'
    start = line.find(marker)
    if start < 0:
        return ''
    start += len(marker)
    end = line.find('"', start)
    return line[start:end] if end > start else ''


def _fetch(url):
    cache_key = 'm3u_' + url
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        text = urlopen(url, timeout=12).read().decode('utf-8', 'replace')
    except Exception as exc:
        kodi.log('playlist fetch failed ({0}): {1}'.format(url, exc), kodi.LOGERROR)
        return []
    channels = parse_m3u(text)[:MAX_CHANNELS]
    if channels:
        cache.set(cache_key, channels)
    return channels


def group_channels(key):
    return sorted(_fetch(IPTV_BASE.format(key)), key=lambda c: c['name'].lower())


def custom_channels():
    url = kodi.get_setting(CUSTOM_PLAYLIST_SETTING, '').strip()
    if not url:
        return []
    if not url.startswith(('http://', 'https://')):
        try:
            with open(kodi.translate_path(url), 'r', encoding='utf-8', errors='replace') as handle:
                return parse_m3u(handle.read())[:MAX_CHANNELS]
        except Exception as exc:
            kodi.log('custom playlist read failed: {0}'.format(exc), kodi.LOGERROR)
            return []
    return _fetch(url)
