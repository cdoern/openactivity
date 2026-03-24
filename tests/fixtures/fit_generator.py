"""Generate valid FIT binary files for testing.

Creates minimal but valid FIT files that fitparse can read,
with configurable sport type, distance, duration, heart rate, etc.
"""

from __future__ import annotations

import io
import struct
from datetime import datetime
from pathlib import Path

# FIT epoch is Dec 31, 1989 00:00:00 UTC
FIT_EPOCH = 631065600


def garmin_timestamp(dt: datetime) -> int:
    """Convert a Python datetime to a Garmin FIT timestamp."""
    return int(dt.timestamp()) - FIT_EPOCH


def fit_crc(data: bytes) -> int:
    """Compute CRC-16 for FIT data."""
    crc = 0
    crc_table = [
        0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
        0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400,
    ]
    for byte in data:
        tmp = crc_table[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ crc_table[byte & 0xF]
        tmp = crc_table[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ crc_table[(byte >> 4) & 0xF]
    return crc


def write_fit_file(
    path: Path | str,
    sport: str = "running",
    distance: float = 5000.0,
    elapsed: int = 1800,
    moving: int = 1750,
    avg_hr: int = 150,
    max_hr: int = 175,
    avg_speed: float = 2.78,
    start_time: datetime | None = None,
    total_ascent: int = 120,
) -> Path:
    """Write a valid FIT file with session data.

    Args:
        path: Output file path
        sport: Sport type (running, cycling, swimming, walking, hiking)
        distance: Total distance in meters
        elapsed: Elapsed time in seconds
        moving: Moving time in seconds
        avg_hr: Average heart rate in bpm
        max_hr: Max heart rate in bpm
        avg_speed: Average speed in m/s
        start_time: Activity start time
        total_ascent: Total elevation gain in meters

    Returns:
        Path to the written file
    """
    if start_time is None:
        start_time = datetime(2026, 3, 20, 7, 30, 0)

    path = Path(path)
    data_buf = io.BytesIO()

    # Definition message for file_id (mesg_num=0)
    data_buf.write(struct.pack("B", 0x40))  # definition, local msg 0
    data_buf.write(struct.pack("BB", 0, 0))  # reserved, arch (little-endian)
    data_buf.write(struct.pack("<H", 0))  # global mesg num = file_id
    data_buf.write(struct.pack("B", 2))  # num fields
    data_buf.write(struct.pack("BBB", 0, 1, 0))  # type (enum, 1 byte)
    data_buf.write(struct.pack("BBB", 4, 4, 134))  # time_created (uint32, 4 bytes)

    # Data message for file_id
    data_buf.write(struct.pack("B", 0x00))  # data, local msg 0
    data_buf.write(struct.pack("B", 4))  # type=4 (activity)
    data_buf.write(struct.pack("<I", garmin_timestamp(start_time)))

    # Definition message for session (mesg_num=18)
    data_buf.write(struct.pack("B", 0x41))  # definition, local msg 1
    data_buf.write(struct.pack("BB", 0, 0))  # reserved, arch
    data_buf.write(struct.pack("<H", 18))  # global mesg num = session
    data_buf.write(struct.pack("B", 9))  # num fields
    data_buf.write(struct.pack("BBB", 2, 4, 134))   # start_time (uint32)
    data_buf.write(struct.pack("BBB", 5, 1, 0))     # sport (enum)
    data_buf.write(struct.pack("BBB", 9, 4, 134))   # total_distance (uint32)
    data_buf.write(struct.pack("BBB", 7, 4, 134))   # total_elapsed_time (uint32)
    data_buf.write(struct.pack("BBB", 8, 4, 134))   # total_timer_time (uint32)
    data_buf.write(struct.pack("BBB", 22, 2, 132))  # total_ascent (uint16)
    data_buf.write(struct.pack("BBB", 14, 2, 132))  # avg_speed (uint16)
    data_buf.write(struct.pack("BBB", 16, 1, 2))    # avg_heart_rate (uint8)
    data_buf.write(struct.pack("BBB", 17, 1, 2))    # max_heart_rate (uint8)

    # Data message for session
    data_buf.write(struct.pack("B", 0x01))  # data, local msg 1
    data_buf.write(struct.pack("<I", garmin_timestamp(start_time)))

    sport_map = {
        "running": 1, "cycling": 2, "swimming": 5,
        "walking": 11, "hiking": 17,
    }
    data_buf.write(struct.pack("B", sport_map.get(sport, 0)))
    data_buf.write(struct.pack("<I", int(distance * 100)))
    data_buf.write(struct.pack("<I", int(elapsed * 1000)))
    data_buf.write(struct.pack("<I", int(moving * 1000)))
    data_buf.write(struct.pack("<H", total_ascent))
    data_buf.write(struct.pack("<H", int(avg_speed * 1000)))
    data_buf.write(struct.pack("B", avg_hr))
    data_buf.write(struct.pack("B", max_hr))

    data = data_buf.getvalue()

    # FIT file header (14 bytes)
    header_size = 14
    protocol_version = 0x20
    profile_version = 2132
    header = struct.pack(
        "<BBHI4s",
        header_size, protocol_version, profile_version,
        len(data), b".FIT",
    )
    header_crc = fit_crc(header)
    header += struct.pack("<H", header_crc)

    file_content = header + data
    file_crc = fit_crc(file_content)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(file_content)
        f.write(struct.pack("<H", file_crc))

    return path


def write_non_activity_fit_file(path: Path | str) -> Path:
    """Write a valid FIT file that is NOT an activity (no session message).

    This creates a FIT file with only a file_id message (type=device_settings),
    so parsing it should return None.
    """
    path = Path(path)
    data_buf = io.BytesIO()

    # Definition message for file_id (mesg_num=0)
    data_buf.write(struct.pack("B", 0x40))
    data_buf.write(struct.pack("BB", 0, 0))
    data_buf.write(struct.pack("<H", 0))
    data_buf.write(struct.pack("B", 2))
    data_buf.write(struct.pack("BBB", 0, 1, 0))  # type
    data_buf.write(struct.pack("BBB", 4, 4, 134))  # time_created

    # Data message for file_id - type=2 (settings), not 4 (activity)
    data_buf.write(struct.pack("B", 0x00))
    data_buf.write(struct.pack("B", 2))  # type=settings
    ts = garmin_timestamp(datetime(2026, 3, 20, 7, 30, 0))
    data_buf.write(struct.pack("<I", ts))

    data = data_buf.getvalue()

    header_size = 14
    header = struct.pack(
        "<BBHI4s", header_size, 0x20, 2132, len(data), b".FIT",
    )
    header_crc = fit_crc(header)
    header += struct.pack("<H", header_crc)

    file_content = header + data
    file_crc = fit_crc(file_content)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(file_content)
        f.write(struct.pack("<H", file_crc))

    return path


def write_corrupted_fit_file(path: Path | str) -> Path:
    """Write a file that looks like FIT but is corrupted."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        # Write a partial FIT header with garbage data
        f.write(b"\x0e\x20\x54\x08")  # partial header
        f.write(b"\x00\x00\x00\x00")
        f.write(b".FIT")
        f.write(b"\xff\xff")  # bad CRC
        f.write(b"\x00\x01\x02\x03\x04\x05")  # garbage
    return path


def write_empty_fit_file(path: Path | str) -> Path:
    """Write a minimal FIT file with valid header but no data records."""
    path = Path(path)
    data = b""

    header_size = 14
    header = struct.pack(
        "<BBHI4s", header_size, 0x20, 2132, len(data), b".FIT",
    )
    header_crc = fit_crc(header)
    header += struct.pack("<H", header_crc)

    file_content = header + data
    file_crc = fit_crc(file_content)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(file_content)
        f.write(struct.pack("<H", file_crc))

    return path
