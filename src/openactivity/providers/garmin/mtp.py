"""MTP (Media Transfer Protocol) device access for newer Garmin watches.

Newer Garmin devices (Forerunner 265/965, Fenix 7+, Venu 3, etc.) use MTP
instead of USB mass storage. macOS has no native MTP support, so we use
libmtp command-line tools to access the device.

Requires: libmtp (brew install libmtp on macOS, apt install libmtp-dev on Linux)
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


class MTPError(Exception):
    """Error communicating with MTP device."""


def is_libmtp_available() -> bool:
    """Check if libmtp tools are installed."""
    return shutil.which("mtp-files") is not None


def get_install_command() -> str:
    """Get the platform-appropriate install command for libmtp."""
    system = platform.system()
    if system == "Darwin":
        return "brew install libmtp"
    elif system == "Linux":
        return "sudo apt install libmtp-dev mtp-tools"
    else:
        return "Install libmtp from https://libmtp.sourceforge.net/"


def detect_garmin_device() -> dict | None:
    """Detect a connected Garmin MTP device.

    Returns:
        Dict with device info (model, serial), or None if not found
    """
    if not is_libmtp_available():
        return None

    try:
        result = subprocess.run(
            ["mtp-detect"],
            capture_output=True, text=True, timeout=15,
        )
        output = result.stdout + result.stderr

        if "091e" not in output.lower() and "garmin" not in output.lower():
            return None

        info = {"vendor": "Garmin"}

        model_match = re.search(r"Model:\s*(.+)", output)
        if model_match:
            info["model"] = model_match.group(1).strip()

        serial_match = re.search(r"Serial number:\s*(.+)", output)
        if serial_match:
            info["serial"] = serial_match.group(1).strip()

        return info
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def _parse_mtp_files_output(output: str) -> list[dict]:
    """Parse mtp-files output into structured file entries.

    Each entry in mtp-files output looks like:
       File ID: 33554435
       Filename: 2025-09-09-06-52-32.fit
       File size 149050 (0x...) bytes
       Parent ID: 16777239
       ...
    """
    entries = []
    current = {}

    for line in output.splitlines():
        line = line.strip()

        if line.startswith("File ID:"):
            if current:
                entries.append(current)
            current = {"file_id": int(line.split(":", 1)[1].strip())}
        elif line.startswith("Filename:"):
            current["filename"] = line.split(":", 1)[1].strip()
        elif line.startswith("File size"):
            match = re.match(r"File size (\d+)", line)
            if match:
                current["size"] = int(match.group(1))
        elif line.startswith("Parent ID:"):
            current["parent_id"] = int(line.split(":", 1)[1].strip())

    if current:
        entries.append(current)

    return entries


def _find_activity_folder_id(entries: list[dict], folders_output: str) -> int | None:
    """Find the folder ID for the Activity folder on the device."""
    for line in folders_output.splitlines():
        line = line.strip()
        # Format: "16777239\t  Activity" or similar
        if "Activity" in line or "activity" in line:
            match = re.match(r"(\d+)", line)
            if match:
                return int(match.group(1))
    return None


def list_activity_files() -> list[dict]:
    """List all FIT activity files on the connected Garmin device.

    Returns:
        List of dicts with file_id, filename, size for each activity FIT file
    """
    if not is_libmtp_available():
        raise MTPError("libmtp not installed")

    # Get folder listing to find Activity folder ID
    try:
        folders_result = subprocess.run(
            ["mtp-folders"],
            capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired as e:
        raise MTPError("Timed out communicating with device") from e

    activity_folder_id = _find_activity_folder_id([], folders_result.stdout)
    if activity_folder_id is None:
        raise MTPError("Activity folder not found on device")

    # Get full file listing
    try:
        files_result = subprocess.run(
            ["mtp-files"],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired as e:
        raise MTPError("Timed out listing files on device") from e

    all_files = _parse_mtp_files_output(files_result.stdout)

    # Filter to FIT files in Activity folder
    activity_files = [
        f for f in all_files
        if f.get("parent_id") == activity_folder_id
        and f.get("filename", "").lower().endswith(".fit")
    ]

    return activity_files


def download_activity_files(
    file_list: list[dict],
    dest_dir: Path,
    *,
    progress_callback: callable | None = None,
) -> int:
    """Download FIT files from the device via MTP.

    Args:
        file_list: List of file dicts from list_activity_files()
        dest_dir: Directory to save downloaded FIT files
        progress_callback: Optional callback(current, total, filename) for progress

    Returns:
        Number of files successfully downloaded
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0

    for i, file_info in enumerate(file_list):
        file_id = file_info["file_id"]
        filename = file_info["filename"]
        dest_path = dest_dir / filename

        if progress_callback:
            progress_callback(i + 1, len(file_list), filename)

        try:
            subprocess.run(
                ["mtp-getfile", str(file_id), str(dest_path)],
                capture_output=True, text=True, timeout=30,
            )
            if dest_path.exists() and dest_path.stat().st_size > 0:
                downloaded += 1
        except (subprocess.SubprocessError, OSError):
            continue

    return downloaded


def download_all_activities(dest_dir: Path | None = None, *, progress_callback=None) -> Path:
    """Download all activity FIT files from the connected Garmin device.

    Args:
        dest_dir: Directory to save files. If None, uses a temp directory.
        progress_callback: Optional callback(current, total, filename)

    Returns:
        Path to directory containing downloaded FIT files
    """
    if dest_dir is None:
        dest_dir = Path(tempfile.mkdtemp(prefix="garmin_activities_"))

    activity_files = list_activity_files()

    if not activity_files:
        raise MTPError("No activity files found on device")

    download_activity_files(
        activity_files, dest_dir, progress_callback=progress_callback,
    )

    return dest_dir
