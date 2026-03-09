import enum

from fred.somea.sync.interface import SyncInterface
from fred.somea.sync._instagram import SyncInstagram


class SyncCatalog(enum.Enum):
    INSTAGRAM = SyncInstagram

    def auto(self, **kwargs) -> SyncInterface:
        return self.value.auto(**kwargs)
