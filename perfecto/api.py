"""
Perfecto Cloud REST API — Complete Wrapper
==========================================
Covers every major Perfecto command category:
  - Handsets (device inventory)
  - Executions (session lifecycle)
  - Voice / VoLTE
  - Network
  - Application
  - Device utilities (screenshot, log, info)
  - Media (recording)
  - Repository (file upload/download)
  - Reporting
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


class PerfectoAPIError(Exception):
    def __init__(self, message: str, status_code: int = 0, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class PerfectoAPI:
    """
    Perfecto REST API client.

    Args:
        base_url:  API Gateway base URL, e.g. 'https://api.mycompany.com/perfecto'
        token:     Auth token (passed as Authorization: Bearer <token>)
        timeout:   Request timeout in seconds (default 60)
    """

    def __init__(self, base_url: str, token: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Session with automatic retry on transient failures
        self._session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[
                500,
                502,
                503,
                504])
        self._session.mount("https://", HTTPAdapter(max_retries=retry))

    # ─────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────

    def _get(self,
             endpoint: str,
             params: dict[str,
                          Any] | None = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        log.debug("GET %s params=%s", url, params)
        resp = self._session.get(
            url,
            headers=self.headers,
            params=params or {},
            timeout=self.timeout)
        if not resp.ok:
            raise PerfectoAPIError(
                f"GET {endpoint} failed [{resp.status_code}]: {resp.text[:300]}",
                resp.status_code,
                resp.text,
            )
        return resp.json()

    def _post(
            self,
            endpoint: str,
            data: dict | None = None,
            params: dict | None = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        log.debug("POST %s data=%s", url, data)
        resp = self._session.post(
            url,
            headers=self.headers,
            json=data or {},
            params=params or {},
            timeout=self.timeout,
        )
        if not resp.ok:
            raise PerfectoAPIError(
                f"POST {endpoint} failed [{resp.status_code}]: {resp.text[:300]}",
                resp.status_code,
                resp.text,
            )
        return resp.json()

    def _cmd(
        self,
        execution_id: str,
        command: str,
        subcommand: str,
        extras: dict | None = None,
    ) -> dict:
        """Shortcut for execution command calls."""
        params = {
            "operation": "command",
            "executionId": execution_id,
            "command": command,
            "subcommand": subcommand,
        }
        if extras:
            params.update(extras)
        return self._get("executions", params)

    # ─────────────────────────────────────────────────────────────────────
    # 1. HANDSETS — Device Inventory
    # ─────────────────────────────────────────────────────────────────────

    def list_devices(
        self,
        os: Optional[str] = None,
        model: Optional[str] = None,
        operator: Optional[str] = None,
        os_version: Optional[str] = None,
        location: Optional[str] = None,
        phone_number: Optional[str] = None,
        status: Optional[str] = "Available",
        in_use: bool = False,
    ) -> list[dict]:
        """
        List devices from the Perfecto inventory.

        Args:
            os:          'Android' or 'iOS'
            model:       Device model (e.g. 'iPhone 15 Pro', 'Galaxy S24')
            operator:    Carrier name (e.g. 'AT&T', 'Verizon', 'T-Mobile')
            os_version:  OS version string (e.g. '17.2', '14')
            location:    Lab location filter
            phone_number: Filter by assigned phone number
            status:      'Available' | 'Busy' | 'Disconnected' (default: 'Available')
            in_use:      Include devices currently in use (default: False)

        Returns:
            List of device dicts with id, model, os, carrier, phoneNumber, status.
        """
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if not in_use:
            params["inUse"] = "false"
        if os:
            params["os"] = os
        if model:
            params["model"] = model
        if operator:
            params["operator"] = operator
        if os_version:
            params["osVersion"] = os_version
        if location:
            params["location"] = location
        if phone_number:
            params["phoneNumber"] = phone_number

        result = self._get("handsets", params)
        handsets = result.get("handsets", result.get("items", []))
        return [self._normalize_device(h) for h in handsets]

    def get_device_info(self, device_id: str) -> dict:
        """Get full properties of a specific device."""
        result = self._get("handsets", {"deviceId": device_id})
        items = result.get("handsets", result.get("items", []))
        return self._normalize_device(items[0]) if items else {}

    def _normalize_device(self, raw: dict) -> dict:
        return {
            "device_id": raw.get("deviceId", raw.get("id", "")),
            "model": raw.get("model", ""),
            "os": raw.get("os", ""),
            "os_version": raw.get("osVersion", ""),
            "operator": raw.get("operator", raw.get("carrier", "")),
            "phone_number": raw.get("phoneNumber", ""),
            "status": raw.get("status", ""),
            "location": raw.get("location", ""),
            "description": raw.get("description", ""),
        }

    # ─────────────────────────────────────────────────────────────────────
    # 2. EXECUTIONS — Session Lifecycle
    # ─────────────────────────────────────────────────────────────────────

    def open_session(self, device_id: str) -> str:
        """
        Reserve a device and open an execution session.

        Returns:
            execution_id (str) — required for all command calls.
        """
        result = self._get(
            "executions", {
                "operation": "open", "deviceId": device_id})
        exec_id = result.get("executionId", result.get("id", ""))
        if not exec_id:
            raise PerfectoAPIError(
                f"open_session: no executionId in response: {result}"
            )
        log.info("Opened session %s for device %s", exec_id, device_id)
        return exec_id

    def close_session(self, execution_id: str) -> dict:
        """Release a reserved device and close the session."""
        result = self._get(
            "executions", {"operation": "close", "executionId": execution_id}
        )
        log.info("Closed session %s", execution_id)
        return result

    def get_session_status(self, execution_id: str) -> dict:
        """Get current session status and metadata."""
        return self._get(
            "executions", {"operation": "status", "executionId": execution_id}
        )

    def list_active_sessions(self) -> list[dict]:
        """List all currently open executions for this account."""
        result = self._get("executions", {"operation": "list"})
        return result.get("executions", result.get("items", []))

    # ─────────────────────────────────────────────────────────────────────
    # 3. DEVICE UTILITIES
    # ─────────────────────────────────────────────────────────────────────

    def get_device_properties(self, execution_id: str) -> dict:
        """Return device hardware/software properties (model, OS, IMEI, etc.)."""
        return self._cmd(execution_id, "device", "info")

    def take_screenshot(
            self,
            execution_id: str,
            key: Optional[str] = None) -> dict:
        """
        Capture a screenshot of the device screen.

        Args:
            key: Optional artifact key/filename in repository.

        Returns:
            Dict with 'repositoryKey' pointing to the saved screenshot.
        """
        extras = {}
        if key:
            extras["param.key"] = key
        return self._cmd(execution_id, "device", "screenshot", extras)

    def get_device_log(
            self,
            execution_id: str,
            log_type: str = "device") -> dict:
        """
        Download device logs.

        Args:
            log_type: 'device' (logcat/syslog) | 'vitals' | 'network'
        """
        return self._cmd(
            execution_id, "device", "log", {
                "param.type": log_type})

    def clear_app_data(self, execution_id: str, package: str) -> dict:
        """Clear application data/cache for a given package."""
        return self._cmd(
            execution_id, "device", "clear", {"param.packageName": package}
        )

    def reboot_device(self, execution_id: str) -> dict:
        """Reboot the device (use sparingly — takes ~60 seconds)."""
        return self._cmd(execution_id, "device", "reboot")

    def set_device_location(
        self, execution_id: str, latitude: float, longitude: float
    ) -> dict:
        """Inject a fake GPS location."""
        return self._cmd(
            execution_id,
            "device",
            "location.set",
            {
                "param.lat": str(latitude),
                "param.lng": str(longitude),
            },
        )

    # ─────────────────────────────────────────────────────────────────────
    # 4. VOICE / VoLTE
    # ─────────────────────────────────────────────────────────────────────

    def voice_call(self, execution_id: str, phone_number: str) -> dict:
        """
        Initiate a voice/VoLTE call.

        Args:
            phone_number: E.164 format recommended (e.g. '+12125551234')
        """
        return self._cmd(
            execution_id, "voice", "call", {"param.phoneNumber": phone_number}
        )

    def voice_answer(self, execution_id: str) -> dict:
        """Answer an incoming call on the device."""
        return self._cmd(execution_id, "voice", "answer")

    def voice_end(self, execution_id: str) -> dict:
        """End / hang up the active call."""
        return self._cmd(execution_id, "voice", "end")

    def voice_hold(self, execution_id: str) -> dict:
        """Place the active call on hold."""
        return self._cmd(execution_id, "voice", "hold")

    def voice_resume(self, execution_id: str) -> dict:
        """Resume a held call."""
        return self._cmd(execution_id, "voice", "resume")

    def voice_mute(self, execution_id: str) -> dict:
        """Mute the microphone on the active call."""
        return self._cmd(execution_id, "voice", "mute")

    def voice_unmute(self, execution_id: str) -> dict:
        """Unmute the microphone."""
        return self._cmd(execution_id, "voice", "unmute")

    def voice_send_dtmf(self, execution_id: str, digits: str) -> dict:
        """
        Send DTMF tones during a call.

        Args:
            digits: String of digits/symbols to send (e.g. '1#23*')
        """
        return self._cmd(
            execution_id, "voice", "sendDtmf", {
                "param.digits": digits})

    def voice_get_status(self, execution_id: str) -> str:
        """
        Get current call state.

        Returns:
            One of: 'idle', 'ringing', 'active', 'held', 'failed'
        """
        result = self._cmd(execution_id, "voice", "getStatus")
        return str(
            result.get(
                "returnValue",
                result.get(
                    "status",
                    "unknown"))).lower()

    def voice_conference_add(self, execution_id: str) -> dict:
        """Merge held + active calls into a conference (3-way)."""
        return self._cmd(execution_id, "voice", "merge")

    def voice_transfer(self, execution_id: str, phone_number: str) -> dict:
        """Blind transfer the active call to another number."""
        return self._cmd(
            execution_id, "voice", "transfer", {
                "param.phoneNumber": phone_number})

    def voice_wait_for_state(
        self,
        execution_id: str,
        target_state: str,
        timeout_sec: int = 30,
        poll_interval: float = 2.0,
    ) -> bool:
        """
        Poll voice_get_status until it matches target_state or timeout expires.

        Args:
            target_state: e.g. 'active', 'ringing', 'idle'
            timeout_sec:  Max seconds to wait

        Returns:
            True if target state was reached, False if timed out.
        """
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            current = self.voice_get_status(execution_id)
            if current == target_state.lower():
                return True
            time.sleep(poll_interval)
        return False

    # ─────────────────────────────────────────────────────────────────────
    # 5. NETWORK
    # ─────────────────────────────────────────────────────────────────────

    def network_get_info(self, execution_id: str) -> dict:
        """
        Return current network details.

        Returns dict with: networkType, signalStrength, operator, roaming, wifi, imsi.
        """
        return self._cmd(execution_id, "network", "info")

    def network_set_airplane_mode(
            self,
            execution_id: str,
            enable: bool) -> dict:
        """Toggle airplane mode on or off."""
        return self._cmd(
            execution_id,
            "network",
            "airplaneMode",
            {"param.mode": "on" if enable else "off"},
        )

    def network_set_wifi(self, execution_id: str, enable: bool) -> dict:
        """Enable or disable WiFi."""
        return self._cmd(
            execution_id, "network", "wifi", {
                "param.mode": "on" if enable else "off"})

    def network_set_data(self, execution_id: str, enable: bool) -> dict:
        """Enable or disable cellular data."""
        return self._cmd(
            execution_id, "network", "data", {
                "param.mode": "on" if enable else "off"})

    def network_set_type(self, execution_id: str, network_type: str) -> dict:
        """
        Force a specific network type.

        Args:
            network_type: '5G' | 'LTE' | '3G' | '2G' | 'Auto'
        """
        return self._cmd(
            execution_id, "network", "type", {
                "param.type": network_type})

    def network_get_signal_strength(self, execution_id: str) -> dict:
        """Get current signal strength (RSRP/RSRQ for LTE)."""
        return self._cmd(execution_id, "network", "signal")

    # ─────────────────────────────────────────────────────────────────────
    # 6. APPLICATION MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────

    def app_install(self, execution_id: str, repository_key: str) -> dict:
        """
        Install an app from the Perfecto repository.

        Args:
            repository_key: Path in the Perfecto repo (e.g. 'PUBLIC:apps/myapp.apk')
        """
        return self._cmd(
            execution_id, "application", "install", {
                "param.file": repository_key})

    def app_open(self, execution_id: str, app_identifier: str) -> dict:
        """
        Launch an installed application.

        Args:
            app_identifier: Package name (Android) or bundle ID (iOS)
        """
        return self._cmd(
            execution_id, "application", "open", {
                "param.identifier": app_identifier})

    def app_close(self, execution_id: str, app_identifier: str) -> dict:
        """Close / force-stop an application."""
        return self._cmd(
            execution_id, "application", "close", {
                "param.identifier": app_identifier})

    def app_uninstall(self, execution_id: str, app_identifier: str) -> dict:
        """Uninstall an application."""
        return self._cmd(
            execution_id,
            "application",
            "uninstall",
            {"param.identifier": app_identifier},
        )

    def app_get_info(self, execution_id: str, app_identifier: str) -> dict:
        """Get version, install state, and other metadata for an app."""
        return self._cmd(
            execution_id, "application", "info", {
                "param.identifier": app_identifier})

    def app_clean_data(self, execution_id: str, app_identifier: str) -> dict:
        """Clear app data and cache (Android only)."""
        return self._cmd(
            execution_id, "application", "clean", {
                "param.identifier": app_identifier})

    # ─────────────────────────────────────────────────────────────────────
    # 7. MEDIA — Recording
    # ─────────────────────────────────────────────────────────────────────

    def recording_start(self, execution_id: str) -> dict:
        """Start video recording of the device screen."""
        return self._cmd(execution_id, "monitor", "start")

    def recording_stop(self, execution_id: str) -> dict:
        """
        Stop screen recording.

        Returns:
            Dict with 'repositoryKey' for the saved video.
        """
        return self._cmd(execution_id, "monitor", "stop")

    def recording_get(self, execution_id: str, key: str) -> bytes:
        """Download a recording artifact as raw bytes."""
        url = f"{self.base_url}/repositories/media/{key}"
        resp = self._session.get(url, headers=self.headers, timeout=120)
        resp.raise_for_status()
        return resp.content

    # ─────────────────────────────────────────────────────────────────────
    # 8. REPOSITORY — File Management
    # ─────────────────────────────────────────────────────────────────────

    def repo_list(self, folder: str = "PUBLIC") -> dict:
        """List files in the Perfecto repository."""
        return self._get("repositories/media",
                         {"operation": "list", "folder": folder})

    def repo_upload(self, local_path: str, repo_key: str) -> dict:
        """
        Upload a local file to the Perfecto repository.

        Args:
            local_path: Path to local file
            repo_key:   Destination key e.g. 'PUBLIC:apps/myapp.apk'
        """
        url = f"{self.base_url}/repositories/media/{repo_key}"
        with open(local_path, "rb") as f:
            resp = self._session.post(
                url,
                headers={
                    "Perfecto-Authorization": self.headers["Perfecto-Authorization"]},
                files={
                    "file": f},
                timeout=300,
            )
        resp.raise_for_status()
        return resp.json()

    def repo_download(self, repo_key: str, local_path: str) -> str:
        """
        Download a file from the Perfecto repository.

        Returns:
            local_path where the file was saved.
        """
        url = f"{self.base_url}/repositories/media/{repo_key}"
        resp = self._session.get(
            url,
            headers=self.headers,
            stream=True,
            timeout=120)
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return local_path

    def repo_delete(self, repo_key: str) -> dict:
        """Delete a file from the Perfecto repository."""
        url = f"{self.base_url}/repositories/media/{repo_key}"
        resp = self._session.delete(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return {"deleted": repo_key}

    # ─────────────────────────────────────────────────────────────────────
    # 9. REPORTING
    # ─────────────────────────────────────────────────────────────────────

    def report_get_execution(self, execution_id: str) -> dict:
        """Fetch the full execution report (steps, artifacts, pass/fail)."""
        return self._get(
            "executions", {"operation": "status", "executionId": execution_id}
        )

    def report_download_artifact(
        self, execution_id: str, artifact_type: str = "video"
    ) -> dict:
        """
        Get download URL for an execution artifact.

        Args:
            artifact_type: 'video' | 'image' | 'log'
        """
        return self._cmd(
            execution_id, "report", "artifact", {"param.type": artifact_type}
        )

    def report_set_custom_field(
            self,
            execution_id: str,
            name: str,
            value: str) -> dict:
        """Tag an execution with a custom field (visible in Perfecto Reporting)."""
        return self._cmd(
            execution_id,
            "report",
            "custom.field",
            {
                "param.name": name,
                "param.value": value,
            },
        )

    # ─────────────────────────────────────────────────────────────────────
    # 10. TIMER UTILITIES
    # ─────────────────────────────────────────────────────────────────────

    def wait(self, seconds: float) -> None:
        """Simple blocking wait — use sparingly; prefer voice_wait_for_state."""
        time.sleep(seconds)
