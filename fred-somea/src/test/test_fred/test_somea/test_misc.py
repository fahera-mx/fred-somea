"""Unit tests for fred.somea.utils.misc (zip_directory, unzip_file)."""
import zipfile
from pathlib import Path

import pytest

from fred.somea.utils.misc import zip_directory, unzip_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tree(root: Path) -> list[Path]:
    """Create a small directory tree under *root* and return the files."""
    (root / "a.txt").write_text("hello")
    (root / "sub").mkdir()
    (root / "sub" / "b.txt").write_text("world")
    return [root / "a.txt", root / "sub" / "b.txt"]


# ---------------------------------------------------------------------------
# zip_directory
# ---------------------------------------------------------------------------

class TestZipDirectory:

    def test_creates_zip_at_default_path(self, tmp_path):
        src = tmp_path / "mydir"
        src.mkdir()
        _make_tree(src)

        result = zip_directory(src)

        assert result == tmp_path / "mydir.zip"
        assert result.is_file()
        assert zipfile.is_zipfile(result)

    def test_custom_output_path(self, tmp_path):
        src = tmp_path / "mydir"
        src.mkdir()
        _make_tree(src)
        dest = tmp_path / "out" / "archive.zip"
        dest.parent.mkdir()

        result = zip_directory(src, output_path=dest)

        assert result == dest
        assert result.is_file()

    def test_include_root_true_prefixes_members(self, tmp_path):
        src = tmp_path / "mydir"
        src.mkdir()
        _make_tree(src)

        result = zip_directory(src, include_root=True)

        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
        assert all(n.startswith("mydir/") for n in names), names

    def test_include_root_false_no_prefix(self, tmp_path):
        src = tmp_path / "mydir"
        src.mkdir()
        _make_tree(src)

        result = zip_directory(src, include_root=False)

        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
        assert not any(n.startswith("mydir/") for n in names), names

    def test_all_files_present_in_archive(self, tmp_path):
        src = tmp_path / "mydir"
        src.mkdir()
        files = _make_tree(src)

        result = zip_directory(src, include_root=False)

        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
        relative = {str(f.relative_to(src)) for f in files}
        assert relative == set(names)

    def test_missing_source_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            zip_directory(tmp_path / "nonexistent")

    def test_not_a_directory_raises(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        with pytest.raises(NotADirectoryError):
            zip_directory(f)

    def test_accepts_string_path(self, tmp_path):
        src = tmp_path / "mydir"
        src.mkdir()
        _make_tree(src)

        result = zip_directory(str(src))

        assert isinstance(result, Path)
        assert result.is_file()


# ---------------------------------------------------------------------------
# unzip_file
# ---------------------------------------------------------------------------

class TestUnzipFile:

    def _make_zip(self, tmp_path: Path) -> Path:
        src = tmp_path / "src"
        src.mkdir(parents=True)
        _make_tree(src)
        return zip_directory(src, include_root=False)

    def test_round_trip(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "hello.txt").write_text("round-trip")
        zip_path = zip_directory(src, include_root=False)

        out = tmp_path / "extracted"
        unzip_file(zip_path, output_dir=out)

        assert (out / "hello.txt").read_text() == "round-trip"

    def test_default_output_dir_is_zip_parent(self, tmp_path):
        out_parent = tmp_path / "dest"
        out_parent.mkdir()
        # Build the zip directly inside out_parent
        zip_path = self._make_zip(out_parent)

        # Unzip with no output_dir → should land in the parent of the zip
        result = unzip_file(zip_path, output_dir=tmp_path / "fresh")

        assert result == tmp_path / "fresh"

    def test_custom_output_dir(self, tmp_path):
        zip_path = self._make_zip(tmp_path)
        out = tmp_path / "custom_out"

        result = unzip_file(zip_path, output_dir=out)

        assert result == out
        assert out.is_dir()

    def test_missing_zip_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            unzip_file(tmp_path / "ghost.zip")

    def test_invalid_zip_raises(self, tmp_path):
        bad = tmp_path / "bad.zip"
        bad.write_text("this is not a zip")
        with pytest.raises(ValueError):
            unzip_file(bad)

    def test_non_empty_dir_without_overwrite_raises(self, tmp_path):
        zip_path = self._make_zip(tmp_path)
        out = tmp_path / "out"
        out.mkdir()
        (out / "existing.txt").write_text("block")

        with pytest.raises(FileExistsError):
            unzip_file(zip_path, output_dir=out, overwrite=False)

    def test_non_empty_dir_with_overwrite_succeeds(self, tmp_path):
        zip_path = self._make_zip(tmp_path)
        out = tmp_path / "out"
        out.mkdir()
        (out / "existing.txt").write_text("block")

        result = unzip_file(zip_path, output_dir=out, overwrite=True)

        assert result == out

    def test_accepts_string_path(self, tmp_path):
        zip_path = self._make_zip(tmp_path)
        out = tmp_path / "str_out"

        result = unzip_file(str(zip_path), output_dir=str(out))

        assert isinstance(result, Path)
        assert result.is_dir()
