from .archive_org import ArchiveOrgProvider
from .fast_channels import FastChannelsProvider
from .official_partner import OfficialPartnerProvider
from .partner_apps import PartnerAppsProvider
from .pluto_tv import PlutoTvProvider
from .public_feeds import PublicFeedsProvider


def get_providers():
    return [
        ArchiveOrgProvider(),
        OfficialPartnerProvider(),
        PlutoTvProvider(),
        FastChannelsProvider(),
        PublicFeedsProvider(),
        PartnerAppsProvider(),
    ]
