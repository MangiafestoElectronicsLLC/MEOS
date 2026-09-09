from .base import BaseProvider


CATALOG = [
    {
        "media_id": "yt_nasa",
        "title": "YouTube: NASA Official Channel",
        "category": "docs",
        "genre": "Science",
        "stream_url": "plugin://plugin.video.youtube/channel/UCLA_DiR1FfKNvjuUpBHmylQ/",
    },
    {
        "media_id": "yt_pbs_space_time",
        "title": "YouTube: PBS Space Time",
        "category": "docs",
        "genre": "Education",
        "stream_url": "plugin://plugin.video.youtube/channel/UC7_gcs09iThXybpVgjHZ_7g/",
    },
    {
        "media_id": "yt_ted_ed",
        "title": "YouTube: TED-Ed",
        "category": "tv",
        "genre": "Education",
        "stream_url": "plugin://plugin.video.youtube/channel/UCsooa4yRKGN_zEE8iknghZA/",
    },
    {
        "media_id": "yt_library_of_congress",
        "title": "YouTube: Library of Congress",
        "category": "docs",
        "genre": "Public Archive",
        "stream_url": "plugin://plugin.video.youtube/channel/UCe2Tgs-0S3qgOa4n2Us2Jzg/",
    },
    {
        "media_id": "yt_internet_archive",
        "title": "YouTube: Internet Archive",
        "category": "docs",
        "genre": "Public Archive",
        "stream_url": "plugin://plugin.video.youtube/channel/UCHQW5B6dN-B9qP5zd1HUL6w/",
    },
]


class YouTubeOfficialProvider(BaseProvider):
    id = "youtube_official"
    name = "YouTube Free Official Channels"
    requires_oauth = False

    def get_catalog(self, auth_state, category=None, query=None, year=None, award=None, result=None):
        items = CATALOG

        if category:
            items = [item for item in items if item.get("category") == category]

        if query:
            normalized_query = query.lower().strip()
            items = [item for item in items if normalized_query in item.get("title", "").lower()]

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
            "mime_type": "",
            "license_url": "",
        }
