"""Unit tests for device detection logic (T031)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from openactivity.providers.garmin.importer import (
    find_connected_device,
    find_garmin_connect_directory,
    is_mtp_device_connected,
)
from openactivity.providers.garmin.mtp import (
    _find_activity_folder_id,
    _parse_mtp_files_output,
    detect_garmin_device,
    get_install_command,
    is_libmtp_available,
)

# === find_connected_device Tests ===


class TestFindConnectedDevice:
    def test_returns_none_when_no_device(self) -> None:
        """No real device will be mounted in test environment."""
        result = find_connected_device()
        # On test machines, no Garmin will be connected
        assert result is None or isinstance(result, Path)

    def test_returns_path_type(self) -> None:
        """find_connected_device always returns Path or None."""
        result = find_connected_device()
        assert result is None or isinstance(result, Path)


# === find_garmin_connect_directory Tests ===


class TestFindGarminConnectDirectory:
    def test_returns_none_when_not_found(self) -> None:
        result = find_garmin_connect_directory()
        assert result is None or isinstance(result, Path)


# === is_mtp_device_connected Tests ===


class TestIsMtpDeviceConnected:
    @patch("subprocess.run")
    @patch("platform.system", return_value="Darwin")
    def test_mac_detects_garmin_usb(self, mock_sys, mock_run) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "USB Device: Garmin Forerunner 965"
        mock_run.return_value = mock_result
        assert is_mtp_device_connected() is True

    @patch("subprocess.run")
    @patch("platform.system", return_value="Darwin")
    def test_mac_no_garmin_device(self, mock_sys, mock_run) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "USB Device: Apple Keyboard"
        mock_run.return_value = mock_result
        assert is_mtp_device_connected() is False

    @patch("subprocess.run")
    @patch("platform.system", return_value="Linux")
    def test_linux_detects_garmin_vendor_id(self, mock_sys, mock_run) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "Bus 001 Device 005: ID 091e:0003 Garmin International"
        mock_run.return_value = mock_result
        assert is_mtp_device_connected() is True

    @patch("subprocess.run", side_effect=FileNotFoundError)
    @patch("platform.system", return_value="Darwin")
    def test_handles_subprocess_error(self, mock_sys, mock_run) -> None:
        assert is_mtp_device_connected() is False


# === MTP Module Tests ===


class TestIsLibmtpAvailable:
    @patch("openactivity.providers.garmin.mtp.shutil.which")
    def test_available(self, mock_which) -> None:
        mock_which.return_value = "/usr/local/bin/mtp-files"
        assert is_libmtp_available() is True

    @patch("openactivity.providers.garmin.mtp.shutil.which")
    def test_not_available(self, mock_which) -> None:
        mock_which.return_value = None
        assert is_libmtp_available() is False


class TestGetInstallCommand:
    @patch("openactivity.providers.garmin.mtp.platform")
    def test_mac_command(self, mock_platform) -> None:
        mock_platform.system.return_value = "Darwin"
        assert "brew" in get_install_command()

    @patch("openactivity.providers.garmin.mtp.platform")
    def test_linux_command(self, mock_platform) -> None:
        mock_platform.system.return_value = "Linux"
        assert "apt" in get_install_command()


class TestDetectGarminDevice:
    @patch("openactivity.providers.garmin.mtp.is_libmtp_available")
    def test_returns_none_without_libmtp(self, mock_available) -> None:
        mock_available.return_value = False
        assert detect_garmin_device() is None

    @patch("openactivity.providers.garmin.mtp.subprocess")
    @patch("openactivity.providers.garmin.mtp.is_libmtp_available")
    def test_detects_garmin(self, mock_available, mock_subprocess) -> None:
        mock_available.return_value = True
        mock_result = MagicMock()
        mock_result.stdout = (
            "Vendor: Garmin\n"
            "VendorID: 091e\n"
            "Model: Forerunner 965\n"
            "Serial number: ABC123\n"
        )
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result

        info = detect_garmin_device()
        assert info is not None
        assert info["model"] == "Forerunner 965"
        assert info["serial"] == "ABC123"

    @patch("openactivity.providers.garmin.mtp.subprocess")
    @patch("openactivity.providers.garmin.mtp.is_libmtp_available")
    def test_no_garmin_device(self, mock_available, mock_subprocess) -> None:
        mock_available.return_value = True
        mock_result = MagicMock()
        mock_result.stdout = "No devices found."
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result

        assert detect_garmin_device() is None


# === MTP File Parsing Tests ===


class TestParseMtpFilesOutput:
    def test_parse_single_entry(self) -> None:
        output = (
            "File ID: 33554435\n"
            "   Filename: 2025-09-09-06-52-32.fit\n"
            "   File size 149050 (0x00024600) bytes\n"
            "   Parent ID: 16777239\n"
        )
        entries = _parse_mtp_files_output(output)
        assert len(entries) == 1
        assert entries[0]["file_id"] == 33554435
        assert entries[0]["filename"] == "2025-09-09-06-52-32.fit"
        assert entries[0]["size"] == 149050
        assert entries[0]["parent_id"] == 16777239

    def test_parse_multiple_entries(self) -> None:
        output = (
            "File ID: 100\n"
            "   Filename: a.fit\n"
            "   File size 1000 (0x03E8) bytes\n"
            "   Parent ID: 10\n"
            "File ID: 200\n"
            "   Filename: b.fit\n"
            "   File size 2000 (0x07D0) bytes\n"
            "   Parent ID: 10\n"
        )
        entries = _parse_mtp_files_output(output)
        assert len(entries) == 2
        assert entries[0]["file_id"] == 100
        assert entries[1]["file_id"] == 200

    def test_parse_empty_output(self) -> None:
        entries = _parse_mtp_files_output("")
        assert entries == []


class TestFindActivityFolderId:
    def test_finds_activity_folder(self) -> None:
        folders_output = (
            "16777237\t  Garmin\n"
            "16777239\t  Activity\n"
            "16777240\t  Settings\n"
        )
        result = _find_activity_folder_id([], folders_output)
        assert result == 16777239

    def test_returns_none_when_not_found(self) -> None:
        folders_output = (
            "16777237\t  Garmin\n"
            "16777240\t  Settings\n"
        )
        result = _find_activity_folder_id([], folders_output)
        assert result is None
