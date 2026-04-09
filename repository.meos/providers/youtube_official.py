from .base import BaseProvider


class YouTubeOfficialProvider(BaseProvider):
    id = "youtube_official"
    name = "YouTube Official API"
    requires_oauth = False

    def get_catalog(self, auth_state):
        return [
            {
                "media_id": "youtube_setup_required",
                "title": "Configure YouTube Data API source",
                "genre": "Setup",
            }
        ]

    def check_entitlement(self, media_id, auth_state):
        return True, ""

    def resolve_playback(self, media_id, auth_state):
        # Intentionally empty until a real API key + legal playlist/channel integration is configured.
        return None
