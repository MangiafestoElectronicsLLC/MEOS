from .base import BaseProvider


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
        "media_id": "movie_elephants_dream",
        "title": "Elephants Dream",
        "category": "movies",
        "genre": "Animation",
        "stream_url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "movie_subaru_outback",
        "title": "Subaru Outback (Demo)",
        "category": "movies",
        "genre": "Demo",
        "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "movie_tears_of_steel",
        "title": "Tears of Steel",
        "category": "movies",
        "genre": "Animation / Sci-Fi",
        "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "tv_for_bigger_blazes",
        "title": "For Bigger Blazes",
        "category": "tv",
        "genre": "TV",
        "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "tv_for_bigger_escape",
        "title": "For Bigger Escape",
        "category": "tv",
        "genre": "TV",
        "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "tv_for_bigger_fun",
        "title": "For Bigger Fun",
        "category": "tv",
        "genre": "TV",
        "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        "mime_type": "video/mp4",
    },
    {
        "media_id": "tv_for_bigger_joyrides",
        "title": "For Bigger Joyrides",
        "category": "tv",
        "genre": "TV",
        "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
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
        "media_id": "docs_we_are_go",
        "title": "We Are Go (Demo Documentary)",
        "category": "docs",
        "genre": "Documentary",
        "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoing.mp4",
        "mime_type": "video/mp4",
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
