import zipfile
from pathlib import Path


def zip_directory(
    source_dir: str | Path,
    output_path: str | Path | None = None,
    *,
    include_root: bool = True,
) -> Path:
    """Compress a directory into a ZIP archive.

    Args:
        source_dir: Path to the directory to compress.
        output_path: Destination for the ZIP file.  Defaults to
            ``<source_dir>.zip`` placed next to the source directory.
        include_root: When *True* (default) the top-level directory name is
            preserved inside the archive so that extracting it recreates the
            original folder.  When *False* the contents of the directory are
            placed at the archive root.

    Returns:
        The resolved :class:`~pathlib.Path` of the created ZIP file.

    Raises:
        NotADirectoryError: If *source_dir* does not point to a directory.
        FileNotFoundError: If *source_dir* does not exist.
    """
    source_dir = Path(source_dir).resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {source_dir}")

    if output_path is None:
        output_path = source_dir.parent / f"{source_dir.name}.zip"
    output_path = Path(output_path).resolve()

    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                arcname = (
                    Path(source_dir.name) / file_path.relative_to(source_dir)
                    if include_root
                    else file_path.relative_to(source_dir)
                )
                zf.write(file_path, arcname)

    return output_path


def unzip_file(
    zip_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Extract a ZIP archive to a directory.

    Args:
        zip_path: Path to the ``.zip`` file to extract.
        output_dir: Destination directory for the extracted contents.
            Defaults to the parent directory of the ZIP file.
        overwrite: When *True*, existing files at the destination are
            overwritten.  When *False* (default) a :class:`FileExistsError`
            is raised if the output directory already exists and is non-empty.

    Returns:
        The resolved :class:`~pathlib.Path` of the extraction directory.

    Raises:
        FileNotFoundError: If *zip_path* does not exist.
        ValueError: If *zip_path* is not a valid ZIP file.
        FileExistsError: If *output_dir* is non-empty and *overwrite* is
            *False*.
    """
    zip_path = Path(zip_path).resolve()

    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Not a valid ZIP file: {zip_path}")

    if output_dir is None:
        output_dir = zip_path.parent
    output_dir = Path(output_dir).resolve()

    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Output directory is non-empty: {output_dir}. "
            "Pass overwrite=True to extract anyway."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, mode="r") as zf:
        zf.extractall(output_dir)

    return output_dir
