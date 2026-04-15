"""File extraction utilities for upload handling."""

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Tuple


def extract_logs_zip(zip_bytes: bytes) -> Tuple[Path, Path]:
    """
    Extract logs ZIP to a temporary directory.

    Handles three possible structures:
    - extracted_root/projects/myapp/*.jsonl
    - extracted_root/myapp/*.jsonl
    - extracted_root/*.jsonl

    Returns: (temp_dir, projects_dir_with_logs)

    Note: Caller is responsible for cleaning up temp_dir when done.

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
    if logs_dir.exists():
        shutil.copytree(logs_dir, logs_dest, dirs_exist_ok=True)

    return project_dir


def merge_project_with_logs(project_path: str, zip_bytes: bytes, temp_root: Path) -> Path:
    """
    Copy project directory into temp_root, then overlay logs from ZIP.

    Handles the case where user provides both a local project path and a logs ZIP.
    Copies the project, extracts logs, and merges them into the project directory.

    Args:
        project_path: Path to the local project directory
        zip_bytes: Raw bytes of the logs ZIP file
        temp_root: Temporary directory to work in

    Returns:
        Path to the merged project directory

    Raises:
        ValueError: If project_path doesn't exist or no .jsonl files found in ZIP
    """
    project_input = Path(project_path).resolve()
    if not project_input.exists():
        raise ValueError(f"Project path does not exist: {project_path}")

    # Copy project files into temp_root/project
    merged_dir = temp_root / "project"
    shutil.copytree(str(project_input), str(merged_dir), dirs_exist_ok=True)

    # Extract logs ZIP to temp location
    zip_path = temp_root / "logs.zip"
    zip_path.write_bytes(zip_bytes)

    logs_extracted = temp_root / "logs_extracted"
    logs_extracted.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(logs_extracted)
    finally:
        zip_path.unlink()

    # Find logs directory in extracted ZIP
    logs_dir = _find_projects_dir(logs_extracted)

    # Verify we found logs
    jsonl_files = list(logs_dir.rglob("*.jsonl"))
    if not jsonl_files:
        raise ValueError("No .jsonl log files found in uploaded ZIP")

    # Merge logs into project
    logs_dest = merged_dir / "logs"
    if logs_dir.exists():
        shutil.copytree(str(logs_dir), str(logs_dest), dirs_exist_ok=True)

    # Clean up extracted logs
    shutil.rmtree(logs_extracted, ignore_errors=True)

    return merged_dir
