from .official_partner import OfficialPartnerProvider
from .youtube_official import YouTubeOfficialProvider


def get_providers():
    return [
        OfficialPartnerProvider(),
        YouTubeOfficialProvider(),
    ]
