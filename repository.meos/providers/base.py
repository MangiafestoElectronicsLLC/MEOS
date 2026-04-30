class BaseProvider:
    id = "base"
    name = "Base Provider"
    requires_oauth = False

    def start_device_authorization(self):
        return None

    def get_catalog(self, auth_state, category=None, query=None):
        return []

    def check_entitlement(self, media_id, auth_state):
        return True, ""

    def resolve_playback(self, media_id, auth_state):
        return None
