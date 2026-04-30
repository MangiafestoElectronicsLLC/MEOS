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
]


class OfficialPartnerProvider(BaseProvider):
    id = "official_partner"
    name = "MEOS"
    requires_oauth = False

    def start_device_authorization(self):
        return {
            "verification_uri": "https://www.mangiafestoelectronics.com/",
            "user_code": "MEOS-DEMO",
        }

    def get_catalog(self, auth_state, category=None, query=None):
        items = CATALOG

        if category:
            items = [item for item in items if item.get("category") == category]

        if query:
            q = query.lower().strip()
            items = [item for item in items if q in item.get("title", "").lower()]

        return [{"media_id": item["media_id"], "title": item["title"], "genre": item["genre"]} for item in items]

    def check_entitlement(self, media_id, auth_state):
        return True, ""

    def resolve_playback(self, media_id, auth_state):
        if auth_state != "connected":
            return None

        selected = next((item for item in CATALOG if item["media_id"] == media_id), None)
        if not selected:
            return None

        # Replace these with official playback endpoints from your licensed provider.
        return {
            "stream_url": selected["stream_url"],
            "title": selected["title"],
            "mime_type": selected.get("mime_type", ""),
            "license_url": "",
            "license_type": "com.widevine.alpha",
            "manifest_type": "mpd",
            "license_headers": "",
        }
