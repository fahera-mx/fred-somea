"""Unit tests for fred.somea.sync._instagram.SyncInstagram.

All tests use mocks — no real network or Instaloader calls are made.
"""
import os
from unittest.mock import MagicMock, patch, call

import pytest

from fred.somea.sync._instagram import SyncInstagram
from fred.somea.sync.interface import SyncOutput
from fred.somea.settings import SOMEA_DIRNAME


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_instaloader_cls():
    """Return a MagicMock that acts as the Instaloader class."""
    return MagicMock(name="Instaloader")


# ---------------------------------------------------------------------------
# SyncInstagram._auto
# ---------------------------------------------------------------------------

class TestSyncInstagramAuto:

    @patch("fred.somea.sync._instagram.Instaloader")
    def test_default_dirpath_is_cwd_somea(self, mock_il_cls, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        expected_dir = str(tmp_path / SOMEA_DIRNAME)

        instance = SyncInstagram.auto(username="johndoe")

        assert instance.output_dirpath == expected_dir
        assert os.path.isdir(expected_dir)

    @patch("fred.somea.sync._instagram.Instaloader")
    def test_custom_dirpath_is_used(self, mock_il_cls, tmp_path):
        custom = str(tmp_path / "custom_dir")

        instance = SyncInstagram.auto(username="johndoe", output_dirpath=custom)

        assert instance.output_dirpath == custom
        assert os.path.isdir(custom)

    @patch("fred.somea.sync._instagram.Instaloader")
    def test_dirname_pattern_set_correctly(self, mock_il_cls, tmp_path):
        custom = str(tmp_path / "out")

        SyncInstagram.auto(username="johndoe", output_dirpath=custom)

        _, kwargs = mock_il_cls.call_args
        assert kwargs["dirname_pattern"] == os.path.join(custom, "{target}")

    @patch("fred.somea.sync._instagram.Instaloader")
    def test_include_videos_forwarded(self, mock_il_cls, tmp_path):
        SyncInstagram.auto(username="u", output_dirpath=str(tmp_path), include_videos=True)

        _, kwargs = mock_il_cls.call_args
        assert kwargs["download_videos"] is True

    @patch("fred.somea.sync._instagram.Instaloader")
    def test_compress_json_forwarded(self, mock_il_cls, tmp_path):
        SyncInstagram.auto(username="u", output_dirpath=str(tmp_path), compress_json=True)

        _, kwargs = mock_il_cls.call_args
        assert kwargs["compress_json"] is True

    @patch("fred.somea.sync._instagram.Instaloader")
    def test_username_stored_on_instance(self, mock_il_cls, tmp_path):
        instance = SyncInstagram.auto(username="alice", output_dirpath=str(tmp_path))

        assert instance.username == "alice"


# ---------------------------------------------------------------------------
# SyncInstagram._sync
# ---------------------------------------------------------------------------

class TestSyncInstagramSync:

    def _make_instance(self, tmp_path) -> SyncInstagram:
        mock_il = MagicMock()
        return SyncInstagram(
            username="bob",
            output_dirpath=str(tmp_path),
            instaloader=mock_il,
        )

    @patch("fred.somea.sync._instagram.Profile")
    def test_sync_returns_sync_output(self, mock_profile_cls, tmp_path):
        instance = self._make_instance(tmp_path)

        out = instance._sync()

        assert isinstance(out, SyncOutput)
        assert out.username == "bob"
        assert out.output_dirpath == str(tmp_path)

    @patch("fred.somea.sync._instagram.Profile")
    def test_sync_calls_download_profiles(self, mock_profile_cls, tmp_path):
        instance = self._make_instance(tmp_path)
        mock_profile = MagicMock()
        mock_profile_cls.from_username.return_value = mock_profile

        instance._sync()

        instance.instaloader.download_profiles.assert_called_once()
        call_kwargs = instance.instaloader.download_profiles.call_args[1]
        assert call_kwargs["profiles"] == {mock_profile}

    @patch("fred.somea.sync._instagram.Profile")
    def test_sync_exclude_posts(self, mock_profile_cls, tmp_path):
        instance = self._make_instance(tmp_path)

        instance._sync(exclude_posts=True)

        call_kwargs = instance.instaloader.download_profiles.call_args[1]
        assert call_kwargs["posts"] is False

    @patch("fred.somea.sync._instagram.Profile")
    def test_sync_fast_update_default_true(self, mock_profile_cls, tmp_path):
        instance = self._make_instance(tmp_path)

        instance._sync()

        call_kwargs = instance.instaloader.download_profiles.call_args[1]
        assert call_kwargs["fast_update"] is True

    @patch("fred.somea.sync._instagram.Profile")
    def test_sync_disable_fast_update(self, mock_profile_cls, tmp_path):
        instance = self._make_instance(tmp_path)

        instance._sync(disable_fast_update=True)

        call_kwargs = instance.instaloader.download_profiles.call_args[1]
        assert call_kwargs["fast_update"] is False
