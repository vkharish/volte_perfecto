"""
Device Pool Manager
===================
Handles smart device reservation for VoLTE testing scenarios.

Key concepts:
- A "slot" is a named role in a test (e.g. "MO", "MT", "CONFEREE")
- You declare what type of device you need; the pool finds and reserves it
- All active sessions are tracked so they can be bulk-released on failure
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

from .api import PerfectoAPI, PerfectoAPIError

log = logging.getLogger(__name__)


@dataclass
class DeviceSlot:
    """Represents one reserved device in a test scenario."""

    label: str  # Human name: "MO_device", "MT_device", "CONFEREE"
    device_id: str  # Perfecto device ID
    execution_id: str  # Active session ID
    os: str  # "Android" or "iOS"
    model: str
    operator: str
    phone_number: str  # E.164 if Perfecto knows it
    os_version: str
    meta: dict = field(default_factory=dict)  # Extra device properties

    def __str__(self) -> str:
        return (
            f"[{self.label}] {self.os} {self.model} "
            f"({self.operator}, {self.phone_number}) "
            f"exec={self.execution_id}"
        )


@dataclass
class DeviceRequirement:
    """Specification for a device slot — passed to reserve_devices()."""

    label: str  # Role name in the test
    os: Optional[str] = None  # "Android" or "iOS"
    model: Optional[str] = None  # e.g. "iPhone 15 Pro", "Galaxy S24"
    operator: Optional[str] = None  # e.g. "AT&T", "Verizon", "T-Mobile"
    os_version: Optional[str] = None  # e.g. "17.2", "14"
    # Reserve specific number for dial-in tests
    phone_number: Optional[str] = None
    exclude_device_ids: list[str] = field(
        default_factory=list
    )  # avoid already-reserved

    def to_filter_args(self) -> dict:
        return {
            k: v
            for k, v in {
                "os": self.os,
                "model": self.model,
                "operator": self.operator,
                "os_version": self.os_version,
                "phone_number": self.phone_number,
            }.items()
            if v is not None
        }


class DevicePool:
    """
    Thread-safe device reservation manager.

    Typical usage:
        pool = DevicePool(api)

        slots = pool.reserve_devices([
            DeviceRequirement(label="MO", os="Android", operator="AT&T"),
            DeviceRequirement(label="MT", os="iOS",     operator="T-Mobile"),
        ])

        mo = pool.get("MO")
        api.voice_call(mo.execution_id, mt.phone_number)

        pool.release_all()
    """

    def __init__(self, api: PerfectoAPI):
        self._api = api
        self._slots: dict[str, DeviceSlot] = {}  # label → DeviceSlot
        self._lock = threading.Lock()

    # ── Reservation ───────────────────────────────────────────────────────

    def reserve_devices(
        self, requirements: list[DeviceRequirement]
    ) -> list[DeviceSlot]:
        """
        Reserve one device per requirement, respecting exclusion lists so no
        two roles get the same physical device.

        Returns:
            List of DeviceSlot (same order as requirements).

        Raises:
            PerfectoAPIError: if any requirement cannot be satisfied.
            ValueError: if a label is already reserved in this pool.
        """
        reserved_ids: set[str] = set(s.device_id for s in self._slots.values())
        new_slots: list[DeviceSlot] = []

        for req in requirements:
            if req.label in self._slots:
                raise ValueError(
                    f"Label '{
                        req.label}' is already reserved. Release it first.")

            req.exclude_device_ids = list(
                reserved_ids | set(
                    req.exclude_device_ids))
            slot = self._reserve_one(req)
            reserved_ids.add(slot.device_id)
            new_slots.append(slot)

        with self._lock:
            for slot in new_slots:
                self._slots[slot.label] = slot

        for slot in new_slots:
            log.info("Reserved: %s", slot)

        return new_slots

    def reserve_one(self, req: DeviceRequirement) -> DeviceSlot:
        """Convenience wrapper to reserve a single device."""
        return self.reserve_devices([req])[0]

    def _reserve_one(self, req: DeviceRequirement) -> DeviceSlot:
        """Find a matching available device and open a session."""
        filter_args = req.to_filter_args()
        candidates = self._api.list_devices(**filter_args)

        # Filter out already-reserved devices
        candidates = [d for d in candidates if d["device_id"]
                      not in req.exclude_device_ids]

        if not candidates:
            desc = ", ".join(
                f"{k}={v}" for k,
                v in filter_args.items()) or "any"
            raise PerfectoAPIError(
                f"No available device found for [{
                    req.label}] " f"with filters: {desc}")

        # Pick first matching candidate
        device = candidates[0]
        execution_id = self._api.open_session(device["device_id"])

        return DeviceSlot(
            label=req.label,
            device_id=device["device_id"],
            execution_id=execution_id,
            os=device["os"],
            model=device["model"],
            operator=device["operator"],
            phone_number=device["phone_number"],
            os_version=device["os_version"],
            meta=device,
        )

    # ── Access ────────────────────────────────────────────────────────────

    def get(self, label: str) -> DeviceSlot:
        """
        Retrieve a reserved slot by label.

        Raises:
            KeyError: if label not found.
        """
        with self._lock:
            if label not in self._slots:
                available = list(self._slots.keys())
                raise KeyError(
                    f"No reserved slot '{label}'. " f"Available: {available}"
                )
            return self._slots[label]

    def exec_id(self, label: str) -> str:
        """Shortcut: get execution_id for a label."""
        return self.get(label).execution_id

    def phone_number(self, label: str) -> str:
        """Shortcut: get phone number for a label."""
        return self.get(label).phone_number

    def all_slots(self) -> list[DeviceSlot]:
        """Return all currently reserved slots."""
        with self._lock:
            return list(self._slots.values())

    def labels(self) -> list[str]:
        with self._lock:
            return list(self._slots.keys())

    def is_reserved(self, label: str) -> bool:
        with self._lock:
            return label in self._slots

    def summary(self) -> list[dict]:
        """Return a JSON-serializable summary of all active slots."""
        return [
            {
                "label": s.label,
                "device_id": s.device_id,
                "execution_id": s.execution_id,
                "os": s.os,
                "model": s.model,
                "operator": s.operator,
                "phone_number": s.phone_number,
                "os_version": s.os_version,
            }
            for s in self.all_slots()
        ]

    # ── Release ───────────────────────────────────────────────────────────

    def release(self, label: str) -> dict:
        """Release a single reserved device by label."""
        with self._lock:
            slot = self._slots.pop(label, None)
        if slot is None:
            log.warning("release(%s): label not found, nothing to do.", label)
            return {"status": "not_found", "label": label}
        try:
            result = self._api.close_session(slot.execution_id)
            log.info("Released %s (exec=%s)", label, slot.execution_id)
            return {"status": "released", "label": label, "result": result}
        except PerfectoAPIError as exc:
            log.error("Error releasing %s: %s", label, exc)
            return {"status": "error", "label": label, "error": str(exc)}

    def release_all(self) -> list[dict]:
        """
        Release every reserved device in the pool.
        Always call this in a finally block to prevent device leaks.
        """
        results = []
        labels = self.labels()
        for label in labels:
            results.append(self.release(label))
        return results
