from .base import BaseProvider


class OfficialPartnerProvider(BaseProvider):
    id = "official_partner"
    name = "Official Partner Demo"
    requires_oauth = True

    def start_device_authorization(self):
        return {
            "verification_uri": "https://partner.example.com/device",
            "user_code": "MEOS-1234",
        }

    def get_catalog(self, auth_state):
        return [
            {
                "media_id": "partner_demo_1",
                "title": "Partner Licensed Demo",
                "genre": "Demo",
            }
        ]

    def check_entitlement(self, media_id, auth_state):
        if auth_state != "connected":
            return False, "Connect account before playback"
        return True, ""

    def resolve_playback(self, media_id, auth_state):
        if auth_state != "connected":
            return None

        # Replace these with official playback endpoints from your licensed provider.
        return {
            "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "license_url": "",
            "license_type": "com.widevine.alpha",
            "manifest_type": "mpd",
            "license_headers": "",
        }
