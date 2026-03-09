import os
from typing import Optional
from dataclasses import dataclass

from instaloader import Instaloader
from instaloader.instaloadercontext import InstaloaderContext
from instaloader.structures import Profile

from fred.settings import logger_manager
from fred.somea.sync.interface import SyncInterface, SyncOutput
from fred.somea.settings import SOMEA_DIRNAME

logger = logger_manager.get_logger(__name__)


@dataclass
class SyncInstagram(SyncInterface):
    username: str
    output_dirpath: str
    instaloader: Instaloader

    @property
    def context(self) -> InstaloaderContext:
        return self.instaloader.context

    @property
    def profile(self) -> Profile:
        return Profile.from_username(
            context=self.context,
            username=self.username,
        )

    def close(self, **kwargs):
        self.instaloader.close()

    @classmethod
    def _auto(
        cls,
        username: str,
        output_dirpath: Optional[str] = None,
        include_videos: bool = False,
        compress_json: bool = False,
        **instaloader_configs
    ) -> 'SyncInstagram':
        if output_dirpath is None:
            output_dirpath = os.path.join(os.getcwd(), SOMEA_DIRNAME)
        if not os.path.exists(output_dirpath):
            os.makedirs(output_dirpath)
        instaloader = Instaloader(
            dirname_pattern=os.path.join(output_dirpath, "{target}"),
            download_videos=include_videos,
            compress_json=compress_json,
            **instaloader_configs
        )
        return cls(
            username=username,
            output_dirpath=output_dirpath,
            instaloader=instaloader,
        )

    def _sync(
        self,
        # By default download profile picture and posts
        exclude_profile_pic: bool = False,
        exclude_posts: bool = False,
        # Optionally include tags, igtv, highlights, stories, and reels
        include_tagged: bool = False,
        include_igtv: bool = False,
        include_highlights: bool = False,
        include_stories: bool = False,
        include_reels: bool = False,
        # Fast update is expected as default
        disable_fast_update: bool = False,
        # Number of items downloaded is variable
        max_count: Optional[int] = None,
        # Additiona arguments
        raise_if_error: bool = False,
        **kwargs,
    ) -> SyncOutput:
        try:
            self.instaloader.download_profiles(
                profiles={self.profile, },
                profile_pic=not exclude_profile_pic,
                posts=not exclude_posts,
                tagged=include_tagged,
                igtv=include_igtv,
                highlights=include_highlights,
                stories=include_stories,
                fast_update=not disable_fast_update,
                reels=include_reels,
                max_count=max_count,
                **kwargs,
            )
        except Exception as e:
            logger.error("Error while processing profile {self.profile}: {e}")
            if raise_if_error:
                raise
        return SyncOutput(
            username=self.username,
            output_dirpath=self.output_dirpath,
            # TODO: Eventually add ref_min_dt & ref_max_dt
        )
