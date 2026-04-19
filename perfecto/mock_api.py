"""
Mock Perfecto API — Simulation Mode
=====================================
Mimics PerfectoAPI with realistic stateful responses.
No real Perfecto credentials needed.

Used by:
    python run_skill.py --skill Hold_Resume --simulate
"""

from __future__ import annotations

import time
import uuid
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Simulated device inventory
# ─────────────────────────────────────────────────────────────────────────────

_DEVICES = [
    {
        "device_id": "SIM-ANDROID-001",
        "model": "Samsung Galaxy S24",
        "os": "Android",
        "os_version": "14",
        "operator": "AT&T",
        "phone_number": "+12125550101",
        "status": "Available",
        "location": "US-Lab-1",
    },
    {
        "device_id": "SIM-ANDROID-002",
        "model": "Google Pixel 8",
        "os": "Android",
        "os_version": "14",
        "operator": "Verizon",
        "phone_number": "+12125550102",
        "status": "Available",
        "location": "US-Lab-1",
    },
    {
        "device_id": "SIM-ANDROID-003",
        "model": "Samsung Galaxy S23",
        "os": "Android",
        "os_version": "13",
        "operator": "T-Mobile",
        "phone_number": "+12125550103",
        "status": "Available",
        "location": "US-Lab-1",
    },
    {
        "device_id": "SIM-IOS-001",
        "model": "iPhone 15 Pro",
        "os": "iOS",
        "os_version": "17.4",
        "operator": "AT&T",
        "phone_number": "+12125550201",
        "status": "Available",
        "location": "US-Lab-1",
    },
    {
        "device_id": "SIM-IOS-002",
        "model": "iPhone 14",
        "os": "iOS",
        "os_version": "17.2",
        "operator": "Verizon",
        "phone_number": "+12125550202",
        "status": "Available",
        "location": "US-Lab-1",
    },
]


class MockPerfectoAPI:
    """
    Stateful simulation of PerfectoAPI.
    Tracks call state per execution ID so voice_wait_for_state
    returns realistic responses based on prior actions.
    """

    def __init__(self):
        # execution_id → {device_id, call_state, network_type, muted}
        self._sessions: dict[str, dict] = {}
        self._reserved: set[str] = set()

    # ── Internal helpers ────────────────────────────────────────────────────

    def _session(self, execution_id: str) -> dict:
        if execution_id not in self._sessions:
            raise RuntimeError(f"Unknown execution_id: {execution_id}")
        return self._sessions[execution_id]

    def _device_for_exec(self, execution_id: str) -> dict:
        s = self._session(execution_id)
        return next(d for d in _DEVICES if d["device_id"] == s["device_id"])

    @staticmethod
    def _ok(extra: dict | None = None) -> dict:
        result = {"status": "Success", "simulatedMode": True}
        if extra:
            result.update(extra)
        return result

    # ── 1. Device inventory ─────────────────────────────────────────────────

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
        time.sleep(0.2)
        devices = [d for d in _DEVICES if d["device_id"] not in self._reserved]
        if os:
            devices = [d for d in devices if d["os"].lower() == os.lower()]
        if operator:
            devices = [d for d in devices if operator.lower()
                       in d["operator"].lower()]
        if model:
            devices = [
                d for d in devices if model.lower() in d["model"].lower()]
        return devices

    # ── 2. Sessions ─────────────────────────────────────────────────────────

    def open_session(self, device_id: str) -> str:
        """Reserve a device and return its execution ID (used by DevicePool)."""
        time.sleep(0.3)
        exec_id = f"SIM-EXEC-{uuid.uuid4().hex[:8].upper()}"
        self._sessions[exec_id] = {
            "device_id": device_id,
            "call_state": "idle",
            "network_type": "LTE",
            "muted": False,
            "airplane_mode": False,
        }
        self._reserved.add(device_id)
        return exec_id

    def close_session(self, execution_id: str) -> dict:
        """Release a device session (used by DevicePool)."""
        time.sleep(0.2)
        if execution_id in self._sessions:
            device_id = self._sessions[execution_id]["device_id"]
            self._reserved.discard(device_id)
            del self._sessions[execution_id]
        return self._ok()

    # Aliases for any direct callers
    def open_execution(self, device_id: str) -> dict:
        exec_id = self.open_session(device_id)
        return self._ok({"executionId": exec_id, "deviceId": device_id})

    def close_execution(self, execution_id: str) -> dict:
        return self.close_session(execution_id)

    def get_execution_status(self, execution_id: str) -> dict:
        s = self._session(execution_id)
        return self._ok({"state": "running", "callState": s["call_state"]})

    # ── 3. Device utilities ─────────────────────────────────────────────────

    def take_screenshot(
            self,
            execution_id: str,
            key: Optional[str] = None) -> dict:
        time.sleep(0.3)
        return self._ok(
            {
                "screenshotUrl": f"https://sim.perfecto.io/screenshots/{execution_id}.png",
                "key": key or f"{execution_id}.png",
            })

    def get_device_log(self, execution_id: str) -> dict:
        time.sleep(0.2)
        return self._ok(
            {"log": "[SIM] Device log — IMS registered, LTE attached, VoLTE enabled"}
        )

    def reboot_device(self, execution_id: str) -> dict:
        time.sleep(0.5)
        return self._ok()

    def get_device_info(self, execution_id: str) -> dict:
        d = self._device_for_exec(execution_id)
        return self._ok(
            {
                "deviceId": d["deviceId"],
                "model": d["model"],
                "os": d["os"],
                "osVersion": d["osVersion"],
                "phoneNumber": d["phoneNumber"],
                "batteryLevel": 85,
                "imsRegistered": True,
            }
        )

    # ── 4. VoLTE / Voice ─────────────────────────────────────────────────────

    def voice_call(self, execution_id: str, phone_number: str) -> dict:
        time.sleep(0.3)
        s = self._session(execution_id)
        s["call_state"] = "ringing"
        s["dialed_number"] = phone_number
        return self._ok({"callState": "ringing", "dialedNumber": phone_number})

    def voice_answer(self, execution_id: str) -> dict:
        time.sleep(0.2)
        s = self._session(execution_id)
        s["call_state"] = "active"
        return self._ok({"callState": "active"})

    def voice_end(self, execution_id: str) -> dict:
        time.sleep(0.2)
        s = self._session(execution_id)
        s["call_state"] = "idle"
        return self._ok({"callState": "idle"})

    def voice_hold(self, execution_id: str) -> dict:
        time.sleep(0.2)
        s = self._session(execution_id)
        s["call_state"] = "held"
        return self._ok({"callState": "held"})

    def voice_resume(self, execution_id: str) -> dict:
        time.sleep(0.2)
        s = self._session(execution_id)
        s["call_state"] = "active"
        return self._ok({"callState": "active"})

    def voice_mute(self, execution_id: str) -> dict:
        time.sleep(0.1)
        s = self._session(execution_id)
        s["muted"] = True
        return self._ok({"muted": True})

    def voice_unmute(self, execution_id: str) -> dict:
        time.sleep(0.1)
        s = self._session(execution_id)
        s["muted"] = False
        return self._ok({"muted": False})

    def voice_send_dtmf(self, execution_id: str, digits: str) -> dict:
        time.sleep(0.1 * len(digits))
        return self._ok({"digitsSent": digits})

    def voice_merge_conference(self, execution_id: str) -> dict:
        time.sleep(0.3)
        s = self._session(execution_id)
        s["call_state"] = "active"
        return self._ok({"callState": "active", "conference": True})

    def voice_transfer(self, execution_id: str, phone_number: str) -> dict:
        time.sleep(0.3)
        s = self._session(execution_id)
        s["call_state"] = "idle"
        return self._ok({"transferred": True, "target": phone_number})

    def voice_wait_for_state(
        self,
        execution_id: str,
        state: str,
        timeout: int = 30,
        timeout_sec: int = 30,
    ) -> dict:
        """Return current call state immediately — simulation doesn't need to poll."""
        time.sleep(0.5)
        s = self._session(execution_id)
        current = s["call_state"]
        reached = current == state
        return self._ok(
            {
                "targetState": state,
                "currentState": current,
                "reached": reached,
                "message": f"[SIM] State is '{current}'"
                + (" ✓" if reached else f" — expected '{state}'"),
            }
        )

    def voice_get_state(self, execution_id: str) -> dict:
        s = self._session(execution_id)
        return self._ok({"callState": s["call_state"]})

    def voice_get_status(self, execution_id: str) -> dict:
        """Alias for voice_get_state — some tool wrappers use this name."""
        return self.voice_get_state(execution_id)

    # ── 5. Network ──────────────────────────────────────────────────────────

    def network_get_info(self, execution_id: str) -> dict:
        time.sleep(0.2)
        s = self._session(execution_id)
        d = self._device_for_exec(execution_id)
        return self._ok(
            {
                "networkType": s["network_type"],
                "operator": d["operator"],
                "signalStrength": -78,
                "lteRsrp": -85,
                "imsRegistered": not s["airplane_mode"],
                "volteEnabled": True,
                "roaming": False,
            }
        )

    def network_set_airplane_mode(
            self,
            execution_id: str,
            enabled: bool) -> dict:
        time.sleep(0.5)
        s = self._session(execution_id)
        s["airplane_mode"] = enabled
        s["network_type"] = "None" if enabled else "LTE"
        if enabled:
            s["call_state"] = "idle"
        return self._ok({"airplaneMode": enabled})

    def network_set_wifi(self, execution_id: str, enabled: bool) -> dict:
        time.sleep(0.3)
        return self._ok({"wifi": enabled})

    def network_set_type(self, execution_id: str, network_type: str) -> dict:
        """Force network type: LTE, WCDMA, GSM, etc."""
        time.sleep(0.5)
        s = self._session(execution_id)
        s["network_type"] = network_type
        return self._ok({"networkType": network_type})

    # ── 6. Application ──────────────────────────────────────────────────────

    def app_install(self, execution_id: str, app_url: str) -> dict:
        time.sleep(1.0)
        return self._ok({"installed": True, "appUrl": app_url})

    def app_open(self, execution_id: str, app_id: str) -> dict:
        time.sleep(0.5)
        return self._ok({"opened": True, "appId": app_id})

    def app_close(self, execution_id: str, app_id: str) -> dict:
        time.sleep(0.3)
        return self._ok({"closed": True})

    # ── 7. Media ────────────────────────────────────────────────────────────

    def recording_start(self, execution_id: str) -> dict:
        time.sleep(0.2)
        return self._ok({"recording": True})

    def recording_stop(self, execution_id: str) -> dict:
        time.sleep(0.2)
        return self._ok(
            {
                "recording": False,
                "videoUrl": f"https://sim.perfecto.io/recordings/{execution_id}.mp4",
            }
        )

    def recording_download(self, execution_id: str, local_path: str) -> dict:
        return self._ok({"savedTo": local_path})

    # ── 8. Repository ───────────────────────────────────────────────────────

    def repo_upload(self, local_path: str, repo_path: str) -> dict:
        time.sleep(0.3)
        return self._ok({"repoPath": repo_path})

    def repo_download(self, repo_path: str, local_path: str) -> dict:
        time.sleep(0.3)
        return self._ok({"localPath": local_path})

    # ── 9. Reporting ─────────────────────────────────────────────────────────

    def get_execution_report(self, execution_id: str) -> dict:
        time.sleep(0.2)
        return self._ok(
            {
                "executionId": execution_id,
                "reportUrl": f"https://sim.perfecto.io/reports/{execution_id}.html",
            })

    # ── 10. Timer ───────────────────────────────────────────────────────────

    def timer_start(self, execution_id: str, name: str) -> dict:
        return self._ok({"timer": name, "started": True})

    def timer_stop(self, execution_id: str, name: str) -> dict:
        return self._ok({"timer": name, "elapsedMs": 5432})
