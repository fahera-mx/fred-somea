"""Unit tests for fred.somea.sync.interface (SyncOutput, SyncInterface)."""
import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fred.somea.sync.interface import SyncOutput, SyncInterface


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_output(tmp_path: Path, create_username_dir: bool = True, **kwargs) -> SyncOutput:
    username = kwargs.pop("username", "testuser")
    out = SyncOutput(username=username, output_dirpath=str(tmp_path), **kwargs)
    if create_username_dir:
        (tmp_path / username).mkdir(exist_ok=True)
    return out


# ---------------------------------------------------------------------------
# SyncOutput – field defaults
# ---------------------------------------------------------------------------

class TestSyncOutputDefaults:

    def test_run_at_is_today_iso(self, tmp_path):
        out = _make_output(tmp_path)
        today = datetime.datetime.utcnow().date().isoformat()
        assert out.run_at == today

    def test_run_id_is_32_char_hex(self, tmp_path):
        out = _make_output(tmp_path)
        assert len(out.run_id) == 32
        assert all(c in "0123456789abcdef" for c in out.run_id)

    def test_ref_dates_default_to_none(self, tmp_path):
        out = _make_output(tmp_path)
        assert out.ref_min_dt is None
        assert out.ref_max_dt is None

    def test_frozen_prevents_mutation(self, tmp_path):
        out = _make_output(tmp_path)
        with pytest.raises(Exception):  # FrozenInstanceError (dataclasses)
            out.username = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SyncOutput – properties
# ---------------------------------------------------------------------------

class TestSyncOutputProperties:

    def test_compressed_filename_no_dates(self, tmp_path):
        out = _make_output(tmp_path, username="alice")
        name = out.sync_compressed_filename
        assert name.startswith("alice_")
        assert name.endswith(".zip")
        assert "_None" not in name

    def test_compressed_filename_with_both_dates(self, tmp_path):
        out = _make_output(tmp_path, username="alice",
                           ref_min_dt="2024-01-01", ref_max_dt="2024-01-31")
        name = out.sync_compressed_filename
        assert "_2024-01-31_2024-01-01" in name

    def test_compressed_filename_only_min_date_no_ext(self, tmp_path):
        # Only one of the two date fields set → no date extension
        out = _make_output(tmp_path, username="alice", ref_min_dt="2024-01-01")
        name = out.sync_compressed_filename
        assert "2024-01-01" not in name

    def test_compressed_filepath(self, tmp_path):
        out = _make_output(tmp_path, username="alice")
        expected = str(tmp_path / out.sync_compressed_filename)
        assert out.sync_compressed_filepath == expected

    def test_username_dirpath(self, tmp_path):
        out = _make_output(tmp_path, username="alice")
        assert out.username_dirpath == str(tmp_path / "alice")


# ---------------------------------------------------------------------------
# SyncOutput – precheck
# ---------------------------------------------------------------------------

class TestSyncOutputPrecheck:

    def test_precheck_missing_output_dir(self, tmp_path):
        out = SyncOutput(username="u", output_dirpath=str(tmp_path / "ghost"))
        with pytest.raises(FileNotFoundError, match="Output directory not found"):
            out.precheck()

    def test_precheck_missing_username_dir(self, tmp_path):
        out = SyncOutput(username="u", output_dirpath=str(tmp_path))
        # username subdir intentionally NOT created
        with pytest.raises(FileNotFoundError, match="Output directory not found"):
            out.precheck()

    def test_precheck_ok(self, tmp_path):
        out = _make_output(tmp_path, username="u")
        out.precheck()  # should not raise


# ---------------------------------------------------------------------------
# SyncOutput – zip
# ---------------------------------------------------------------------------

class TestSyncOutputZip:

    def test_zip_delegates_to_zip_directory(self, tmp_path):
        out = _make_output(tmp_path, username="u")
        with patch("fred.somea.sync.interface.SyncOutput.precheck"):
            with patch("fred.somea.utils.misc.zip_directory") as mock_zip:
                mock_zip.return_value = Path(out.sync_compressed_filepath)
                out.zip()

        mock_zip.assert_called_once_with(
            source_dir=out.username_dirpath,
            output_path=out.sync_compressed_filepath,
            include_root=False,
        )

    def test_zip_calls_precheck_first(self, tmp_path):
        out = _make_output(tmp_path, username="u")
        call_order = []
        with patch.object(SyncOutput, "precheck", side_effect=lambda: call_order.append("precheck")):
            def _zip_side_effect(**kw):
                call_order.append("zip")
                return Path("x.zip")
            with patch("fred.somea.utils.misc.zip_directory", side_effect=_zip_side_effect):
                out.zip()
        assert call_order == ["precheck", "zip"]


# ---------------------------------------------------------------------------
# SyncInterface – dispatch
# ---------------------------------------------------------------------------

class TestSyncInterfaceDispatch:

    def test_auto_dispatches_to_auto(self):
        class Concrete(SyncInterface):
            @classmethod
            def _auto(cls, **kwargs):
                return "from_auto"

        assert Concrete.auto() == "from_auto"

    def test_auto_raises_without_auto(self):
        with pytest.raises(NotImplementedError):
            SyncInterface.auto()

    def test_sync_dispatches_to_sync(self, tmp_path):
        mock_out = MagicMock(spec=SyncOutput)

        class Concrete(SyncInterface):
            def _sync(self, **kwargs):
                return mock_out

            def close(self, **kwargs):
                pass

        instance = Concrete()
        result = instance.sync()

        mock_out.precheck.assert_called_once()
        mock_out.zip.assert_called_once()
        assert result is mock_out

    def test_sync_raises_without_sync(self):
        class Concrete(SyncInterface):
            def close(self, **kwargs):
                pass

        with pytest.raises(NotImplementedError):
            Concrete().sync()

    def test_context_manager_calls_close(self):
        closed = []

        class Concrete(SyncInterface):
            def close(self, **kwargs):
                closed.append(True)

        with Concrete():
            pass

        assert closed == [True]
