from .archive_org import ArchiveOrgProvider
from .pluto_tv import PlutoTvProvider


def get_providers():
    return [
        ArchiveOrgProvider(),
        PlutoTvProvider(),
    ]
