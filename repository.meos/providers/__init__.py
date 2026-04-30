from .archive_org import ArchiveOrgProvider


def get_providers():
    return [
        ArchiveOrgProvider(),
    ]
