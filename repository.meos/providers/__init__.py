from .archive_org import ArchiveOrgProvider
from .official_partner import OfficialPartnerProvider
from .pluto_tv import PlutoTvProvider


def get_providers():
    return [
        ArchiveOrgProvider(),
        OfficialPartnerProvider(),
        PlutoTvProvider(),
    ]
