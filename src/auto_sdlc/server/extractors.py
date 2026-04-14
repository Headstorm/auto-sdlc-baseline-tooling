"""File extraction utilities for upload handling."""

import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple


def extract_logs_zip(zip_bytes: bytes) -> Tuple[Path, Path]:
    """
    Extract logs ZIP to a temporary directory.

    Handles three possible structures:
    - extracted_root/projects/myapp/*.jsonl
    - extracted_root/myapp/*.jsonl
    - extracted_root/*.jsonl

    Returns: (temp_dir, projects_dir_with_logs)

    Raises: ValueError if no .jsonl files found
    """
    temp_dir = tempfile.mkdtemp(prefix="auto_sdlc_logs_")
    temp_path = Path(temp_dir)

    try:
        # Extract ZIP
        zip_path = temp_path / "upload.zip"
        zip_path.write_bytes(zip_bytes)

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(temp_path)

        zip_path.unlink()

        # Find .jsonl files
        jsonl_files = list(temp_path.rglob("*.jsonl"))
        if not jsonl_files:
            raise ValueError("No .jsonl log files found in upload")

        # Find best projects directory
        projects_dir = _find_projects_dir(temp_path)

        return temp_path, projects_dir

    except Exception as e:
        # Clean up on error
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _find_projects_dir(extracted_root: Path) -> Path:
    """
    Find the directory containing .jsonl files.

    Returns the highest-level directory that contains all .jsonl files.
    """
    jsonl_files = list(extracted_root.rglob("*.jsonl"))
    if not jsonl_files:
        return extracted_root

    # Prefer a directory named "projects" if found
    for f in jsonl_files:
        for parent in f.parents:
            if parent.name == "projects" and parent != extracted_root:
                return parent

    # Fall back to first jsonl file's parent
    first = jsonl_files[0]
    return first.parent


def create_project_structure(logs_dir: Path, temp_root: Path) -> Path:
    """
    Create a minimal project structure for report generation.

    Copies logs directory to a new project directory structure.

    Returns: path to the project directory
    """
    project_dir = temp_root / "project"
    project_dir.mkdir(parents=True, exist_ok=True)

    logs_dest = project_dir / "logs"

    # Copy logs
    import shutil
    if logs_dir.exists():
        shutil.copytree(logs_dir, logs_dest, dirs_exist_ok=True)

    return project_dir
