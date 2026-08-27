from .base import BaseProvider


# Every entry below was probed and confirmed to return a playable stream.
# Google's gtv-videos-bucket demo files now return HTTP 403 and were removed.
CATALOG = [
    {
        "media_id": "movie_big_buck_bunny",
        "title": "Big Buck Bunny",
        "category": "movies",
        "genre": "Animation",
        "stream_url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "mime_type": "application/vnd.apple.mpegurl",
    },
    {
        "media_id": "movie_his_girl_friday",
        "title": "His Girl Friday (1940)",
        "category": "movies",
        "genre": "Comedy",
        "stream_url": "https://archive.org/download/his_girl_friday/his_girl_friday.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "movie_reefer_madness",
        "title": "Reefer Madness (1938)",
        "category": "movies",
        "genre": "Drama",
        "stream_url": "https://archive.org/download/reefer_madness1938/reefer_madness1938.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "tv_google_blender_archive",
        "title": "Big Buck Bunny (Internet Archive Mirror)",
        "category": "tv",
        "genre": "Animation",
        "stream_url": "https://archive.org/download/BigBuckBunny_328/BigBuckBunny_512kb.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "tv_elephants_dream_archive",
        "title": "Elephants Dream (Internet Archive Mirror)",
        "category": "tv",
        "genre": "Animation",
        "stream_url": "https://archive.org/download/ElephantsDream/ed_1024_512kb.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "tv_chaplin_floorwalker",
        "title": "Charlie Chaplin: The Floorwalker (1916)",
        "category": "tv",
        "genre": "Classic Comedy",
        "stream_url": "https://archive.org/download/CC_1916_05_15_TheFloorwalker/CC_1916_05_15_TheFloorwalker_512kb.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "docs_duck_and_cover",
        "title": "Duck and Cover (1951)",
        "category": "docs",
        "genre": "Documentary",
        "stream_url": "https://archive.org/download/DuckandC1951/DuckandC1951.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "docs_nazi_concentration_camps",
        "title": "Nazi Concentration Camps (1945)",
        "category": "docs",
        "genre": "Documentary",
        "stream_url": "https://archive.org/download/nazi_concentration_camps/nazi_concentration_camps.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "live_test_channel",
        "title": "MEOS Live Test Channel",
        "category": "live",
        "genre": "Live",
        "stream_url": "https://test-streams.mux.dev/test_001/stream.m3u8",
        "mime_type": "application/vnd.apple.mpegurl",
    },
    {
        "media_id": "sports_test_feed",
        "title": "MEOS Sports Test Feed",
        "category": "sports",
        "genre": "Sports",
        "stream_url": "https://test-streams.mux.dev/dai-discontinuity-deltatre/manifest.m3u8",
        "mime_type": "application/vnd.apple.mpegurl",
    },
    {
        "media_id": "sports_tears_of_steel_trailer",
        "title": "Sports Showcase Clip",
        "category": "sports",
        "genre": "Sports",
        "stream_url": "https://test-streams.mux.dev/pts_shift/master.m3u8",
        "mime_type": "application/vnd.apple.mpegurl",
    },
    {
        "media_id": "cable_test_channel",
        "title": "MEOS Cable Test Channel",
        "category": "cable",
        "genre": "Cable TV",
        "stream_url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "mime_type": "application/vnd.apple.mpegurl",
    },
    {
        "media_id": "cable_patriotic_popeye",
        "title": "Patriotic Popeye (1957)",
        "category": "cable",
        "genre": "Classic Cartoons",
        "stream_url": "https://archive.org/download/popeye_patriotic_popeye/popeye_patriotic_popeye_512kb.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "ppv_test_event",
        "title": "MEOS PPV Test Event",
        "category": "ppv",
        "genre": "PPV",
        "stream_url": "https://test-streams.mux.dev/test_001/stream.m3u8",
        "mime_type": "application/vnd.apple.mpegurl",
    },
]


class OfficialPartnerProvider(BaseProvider):
    """
    MEOS Demo content provider.

    Provides a curated set of publicly accessible, royalty-free demo streams
    sourced from Google's sample media bucket and Mux test streams.
    All items are free and legal to stream.
    """

    id = "official_partner"
    name = "MEOS Demo"
    requires_oauth = False

    def start_device_authorization(self):
        return {
            "verification_uri": "https://www.mangiafestoelectronics.com/",
            "user_code": "MEOS-DEMO",
        }

    def get_catalog(self, auth_state, category=None, query=None, year=None, award=None, result=None):
        items = CATALOG

        if category and category != "award":
            items = [item for item in items if item.get("category") == category]

        if query:
            q = query.lower().strip()
            items = [item for item in items if q in item.get("title", "").lower()]

        return [{"media_id": item["media_id"], "title": item["title"], "genre": item["genre"]} for item in items]

    def check_entitlement(self, media_id, auth_state):
        return True, ""

    def resolve_playback(self, media_id, auth_state):
        selected = next((item for item in CATALOG if item["media_id"] == media_id), None)
        if not selected:
            return None

        return {
            "stream_url": selected["stream_url"],
            "title": selected["title"],
            "mime_type": selected.get("mime_type", ""),
            "license_url": "",
        }
