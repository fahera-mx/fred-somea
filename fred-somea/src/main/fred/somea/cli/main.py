from fred.cli.interface import AbstractCLI


class CLI(AbstractCLI):

    @property
    def version(self):
        from fred.somea.version import version
        return version.value

    @property
    def social_media_catalog(self):
        from fred.somea.sync.catalog import SyncCatalog

        return [sm.name for sm in SyncCatalog]

    def local_sync(self, social_media: str, **kwargs):
        from fred.somea.sync.catalog import SyncCatalog

        with SyncCatalog[social_media.upper()].auto(**kwargs) as sync:
            return sync
