import os
import uuid
import datetime
from typing import Optional
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SyncOutput:
    username: str
    output_dirpath: str
    run_at: str = field(default_factory=lambda: datetime.datetime.utcnow().date().isoformat())
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ref_min_dt: Optional[str] = None
    ref_max_dt: Optional[str] = None

    @property
    def sync_compressed_filename(self):
        maxmin_ext = f"_{self.ref_max_dt}_{self.ref_min_dt}" if self.ref_min_dt and self.ref_max_dt else ""
        return f"{self.username}_{self.run_at}_{self.run_id}{maxmin_ext}.zip"

    @property
    def sync_compressed_filepath(self):
        return os.path.join(self.output_dirpath, self.sync_compressed_filename)

    @property
    def username_dirpath(self):
        return os.path.join(self.output_dirpath, self.username)

    def precheck(self):
        if not os.path.exists(self.output_dirpath):
            raise FileNotFoundError(f"Output directory not found: {self.output_dirpath}")
        if not os.path.exists(self.username_dirpath):
            raise FileNotFoundError(f"Output directory not found: {self.username_dirpath}")
    
    def zip(self) -> str:
        from fred.somea.utils.misc import zip_directory
        self.precheck()
        return zip_directory(
            source_dir=self.username_dirpath,
            output_path=self.sync_compressed_filepath,
            include_root=False,
        )


class SyncInterface:
    
    @classmethod
    def auto(cls, **kwargs) -> 'SyncInterface':
        if getattr(cls, "_auto", None):
            return cls._auto(**kwargs)
        raise NotImplementedError

    def sync(self, **kwargs) -> SyncOutput:
        if getattr(self, "_sync", None):
            out = self._sync(**kwargs)
            out.precheck()
            out.zip()
            return out
        raise NotImplementedError

    def close(self, **kwargs):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
