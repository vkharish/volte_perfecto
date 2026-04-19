"""
Claude Tool Definitions + Executor
===================================
Every Perfecto capability is exposed as a Claude tool.
The agentic loop calls execute_tool() with name + args from Claude's tool_use blocks.

Tool categories:
  1. Device Discovery & Reservation
  2. Device Utilities
  3. VoLTE / Voice
  4. Network
  5. Application
  6. Media (recording, screenshot)
  7. Repository
  8. Reporting
  9. Timing & Coordination
  10. Certification Logging
  11. Skill Management (list / load / save / update / delete skills)
"""

from __future__ import annotations

import time
from typing import Any

from .api import PerfectoAPI, PerfectoAPIError
from .device_pool import DevicePool, DeviceRequirement

# ─────────────────────────────────────────────────────────────────────────────
# Runtime state — injected by the agent before the loop starts
# ─────────────────────────────────────────────────────────────────────────────

_api: PerfectoAPI | None = None
_pool: DevicePool | None = None
_cert_log: list[dict] = []


def init(api: PerfectoAPI) -> None:
    global _api, _pool, _cert_log
    _api = api
    _pool = DevicePool(api)
    _cert_log = []


def get_cert_log() -> list[dict]:
    return list(_cert_log)


def init_cert_log() -> None:
    """Reset the cert log. Call at the start of each skill run to prevent bleed."""
    global _cert_log
    _cert_log = []


def release_all_devices() -> None:
    """Release all reserved devices. Safe to call multiple times (idempotent)."""
    if _pool is not None:
        try:
            _pool.release_all()
        except Exception:
            pass  # best-effort on crash/atexit


def _a() -> PerfectoAPI:
    if _api is None:
        raise RuntimeError("Call init() before using tools.")
    return _api


def _p() -> DevicePool:
    if _pool is None:
        raise RuntimeError("Call init() before using tools.")
    return _pool


# ─────────────────────────────────────────────────────────────────────────────
# TOOL DEFINITIONS  (passed verbatim to Claude's `tools` parameter)
# ─────────────────────────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    # ── 1. Device Discovery & Reservation ────────────────────────────────
    {
        "name": "list_devices",
        "description": "Query device inventory. Filter by os, model, operator, os_version, phone_number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "os": {"type": "string", "enum": ["Android", "iOS"]},
                "model": {"type": "string", "description": "e.g. 'iPhone 15 Pro'"},
                "operator": {"type": "string", "description": "e.g. 'AT&T'"},
                "os_version": {"type": "string", "description": "e.g. '17.4'"},
                "phone_number": {"type": "string", "description": "E.164 format"},
            },
            "required": [],
        },
    },
    {
        "name": "reserve_devices",
        "description": "Reserve devices by role label (MO/MT/CONFEREE). Pool assigns unique physical devices per role.",
        "input_schema": {
            "type": "object",
            "properties": {
                "requirements": {
                    "type": "array",
                    "description": "List of device requirements, one per role.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {
                                "type": "string",
                                "description": "Role name, e.g. 'MO', 'MT', 'CONFEREE'",
                            },
                            "os": {"type": "string", "enum": ["Android", "iOS"]},
                            "model": {"type": "string"},
                            "operator": {"type": "string"},
                            "os_version": {"type": "string"},
                            "phone_number": {"type": "string"},
                        },
                        "required": ["label"],
                    },
                }
            },
            "required": ["requirements"],
        },
    },
    {
        "name": "list_reserved_devices",
        "description": "List currently reserved devices: labels, IDs, model, carrier, phone numbers.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "release_devices",
        "description": "Release devices back to pool. Omit labels to release all.",
        "input_schema": {
            "type": "object",
            "properties": {
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Labels to release. Omit to release all.",
                }
            },
            "required": [],
        },
    },
    # ── 2. Device Utilities ───────────────────────────────────────────────
    {
        "name": "get_device_properties",
        "description": "Get hardware/software properties of a reserved device (IMEI, model, OS build, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Device slot label (e.g. 'MO')",
                }
            },
            "required": ["label"],
        },
    },
    {
        "name": "take_screenshot",
        "description": "Capture a screenshot of the device screen. Returns a repository key for the image.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "key": {
                    "type": "string",
                    "description": "Optional filename/key in Perfecto repo",
                },
            },
            "required": ["label"],
        },
    },
    {
        "name": "get_device_log",
        "description": (
            "Download device logs. "
            "log_type: 'device' (logcat/syslog), 'vitals', or 'network'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "log_type": {"type": "string", "enum": ["device", "vitals", "network"]},
            },
            "required": ["label"],
        },
    },
    {
        "name": "reboot_device",
        "description": "Reboot a reserved device. Takes ~60 seconds. Use only if needed for test setup.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    # ── 3. VoLTE / Voice ─────────────────────────────────────────────────
    {
        "name": "voice_call",
        "description": "Initiate a VoLTE call from a device to a phone number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Calling device label (MO side)",
                },
                "phone_number": {
                    "type": "string",
                    "description": "E.164 number to call (e.g. '+12125551234')",
                },
            },
            "required": ["label", "phone_number"],
        },
    },
    {
        "name": "voice_answer",
        "description": "Answer an incoming call on a device (MT side).",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "voice_end",
        "description": "End / hang up the active call on a device.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "voice_hold",
        "description": "Place the active call on hold.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "voice_resume",
        "description": "Resume a held call.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "voice_mute",
        "description": "Mute the microphone on the active call.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "voice_unmute",
        "description": "Unmute the microphone on the active call.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "voice_send_dtmf",
        "description": "Send DTMF tones during an active call (e.g. for IVR navigation or call-park codes).",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "digits": {
                    "type": "string",
                    "description": "Digit string to send (e.g. '1#23*')",
                },
            },
            "required": ["label", "digits"],
        },
    },
    {
        "name": "voice_get_status",
        "description": "Get current call state: idle/ringing/active/held/failed.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "voice_wait_for_state",
        "description": "Wait for call to reach target state. Returns {reached, final_state}.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "target_state": {
                    "type": "string",
                    "enum": ["idle", "ringing", "active", "held", "failed"],
                },
                "timeout_sec": {"type": "integer", "minimum": 5, "maximum": 120},
            },
            "required": ["label", "target_state"],
        },
    },
    {
        "name": "voice_conference",
        "description": "Merge held+active calls into 3-way conference.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "voice_transfer",
        "description": "Blind transfer the active call to a different phone number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "phone_number": {
                    "type": "string",
                    "description": "Target E.164 number for transfer",
                },
            },
            "required": ["label", "phone_number"],
        },
    },
    # ── 4. Network ────────────────────────────────────────────────────────
    {
        "name": "network_get_info",
        "description": "Get network info: type, signal, carrier, roaming, IMS/VoLTE status.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "network_set_airplane_mode",
        "description": "Enable/disable airplane mode (forces IMS re-registration).",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "enable": {
                    "type": "boolean",
                    "description": "true to enable airplane mode, false to disable",
                },
            },
            "required": ["label", "enable"],
        },
    },
    {
        "name": "network_set_wifi",
        "description": "Enable or disable WiFi on a device.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "enable": {"type": "boolean"},
            },
            "required": ["label", "enable"],
        },
    },
    {
        "name": "network_set_data",
        "description": "Enable or disable cellular data on a device.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "enable": {"type": "boolean"},
            },
            "required": ["label", "enable"],
        },
    },
    {
        "name": "network_set_type",
        "description": "Force a specific network type: '5G', 'LTE', '3G', '2G', or 'Auto'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "network_type": {
                    "type": "string",
                    "enum": ["5G", "LTE", "3G", "2G", "Auto"],
                },
            },
            "required": ["label", "network_type"],
        },
    },
    # ── 5. Application ────────────────────────────────────────────────────
    {
        "name": "app_install",
        "description": "Install an app from the Perfecto repository onto a reserved device.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "repository_key": {
                    "type": "string",
                    "description": "Perfecto repo path, e.g. 'PUBLIC:apps/myapp.apk'",
                },
            },
            "required": ["label", "repository_key"],
        },
    },
    {
        "name": "app_open",
        "description": "Launch an installed app by package name (Android) or bundle ID (iOS).",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "app_identifier": {
                    "type": "string",
                    "description": "Package name or bundle ID",
                },
            },
            "required": ["label", "app_identifier"],
        },
    },
    {
        "name": "app_close",
        "description": "Close/force-stop an application.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "app_identifier": {"type": "string"},
            },
            "required": ["label", "app_identifier"],
        },
    },
    {
        "name": "app_uninstall",
        "description": "Uninstall an application from a device.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "app_identifier": {"type": "string"},
            },
            "required": ["label", "app_identifier"],
        },
    },
    # ── 6. Media ──────────────────────────────────────────────────────────
    {
        "name": "recording_start",
        "description": "Start screen recording for certification evidence.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    {
        "name": "recording_stop",
        "description": "Stop screen recording. Returns a repository key for the saved video artifact.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    # ── 7. Repository ─────────────────────────────────────────────────────
    {
        "name": "repo_list",
        "description": "List files stored in the Perfecto repository (apps, test data, recordings).",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder": {
                    "type": "string",
                    "description": "Repository folder (default: 'PUBLIC')",
                },
            },
            "required": [],
        },
    },
    # ── 8. Reporting ──────────────────────────────────────────────────────
    {
        "name": "get_execution_report",
        "description": "Fetch the full Perfecto execution report for a reserved device (steps, artifacts, pass/fail summary).",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string"}},
            "required": ["label"],
        },
    },
    # ── 9. Timing ─────────────────────────────────────────────────────────
    {
        "name": "wait_seconds",
        "description": "Wait N seconds between steps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {
                    "type": "integer",
                    "description": "Seconds to wait",
                    "minimum": 1,
                    "maximum": 120,
                },
            },
            "required": ["seconds"],
        },
    },
    # ── 10. Certification Logging ─────────────────────────────────────────
    {
        "name": "log_step",
        "description": "Record a test step result (PASS/FAIL/SKIP) in the certification log.",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_case": {
                    "type": "string",
                    "description": "Test case name, e.g. 'TC-001 MO Basic Call'",
                },
                "step": {
                    "type": "string",
                    "description": "Step description, e.g. 'Verify MT device shows ringing'",
                },
                "result": {"type": "string", "enum": ["PASS", "FAIL", "SKIP"]},
                "expected": {"type": "string"},
                "actual": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["test_case", "step", "result"],
        },
        # Cache all tools up to this point — saves ~2,400 tokens per turn after
        # turn 1
        "cache_control": {"type": "ephemeral"},
    },
]

# Skills are plain .md files in skills/.
# Claude Code manages them directly using its native Read / Write / Edit / Glob / Grep tools.
# The execution agent (run_skill.py) just reads the .md content and uses
# it as a prompt.


# ─────────────────────────────────────────────────────────────────────────────
# TOOL EXECUTOR  — dispatch table called by the agentic loop
# ─────────────────────────────────────────────────────────────────────────────


def execute_tool(name: str, args: dict) -> Any:
    """
    Dispatch a tool call from Claude to the appropriate Perfecto API method.

    Returns a JSON-serializable dict with the result or an error key.
    """
    try:
        return _dispatch(name, args)
    except PerfectoAPIError as exc:
        return {
            "error": f"Perfecto API error: {exc}",
            "status_code": exc.status_code}
    except KeyError as exc:
        return {"error": f"Device not found: {exc}"}
    except Exception as exc:
        return {"error": f"Unexpected error in {name}: {exc}"}


def _dispatch(name: str, args: dict) -> Any:  # noqa: PLR0912
    # ── Device Discovery & Reservation ─────────────────────────────────
    if name == "list_devices":
        devices = _a().list_devices(
            os=args.get("os"),
            model=args.get("model"),
            operator=args.get("operator"),
            os_version=args.get("os_version"),
            phone_number=args.get("phone_number"),
        )
        return {"count": len(devices), "devices": devices[:20]}

    elif name == "reserve_devices":
        reqs = [
            DeviceRequirement(
                label=r["label"],
                os=r.get("os"),
                model=r.get("model"),
                operator=r.get("operator"),
                os_version=r.get("os_version"),
                phone_number=r.get("phone_number"),
            )
            for r in args["requirements"]
        ]
        slots = _p().reserve_devices(reqs)
        return {
            "reserved": [
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
                for s in slots
            ]
        }

    elif name == "list_reserved_devices":
        return {"reserved_devices": _p().summary()}

    elif name == "release_devices":
        labels = args.get("labels")
        if labels:
            results = [_p().release(lbl) for lbl in labels]
        else:
            results = _p().release_all()
        return {"released": results}

    # ── Device Utilities ────────────────────────────────────────────────
    elif name == "get_device_properties":
        return _a().get_device_properties(_p().exec_id(args["label"]))

    elif name == "take_screenshot":
        return _a().take_screenshot(
            _p().exec_id(
                args["label"]),
            args.get("key"))

    elif name == "get_device_log":
        return _a().get_device_log(
            _p().exec_id(args["label"]), args.get("log_type", "device")
        )

    elif name == "reboot_device":
        return _a().reboot_device(_p().exec_id(args["label"]))

    # ── VoLTE / Voice ────────────────────────────────────────────────────
    elif name == "voice_call":
        return _a().voice_call(
            _p().exec_id(
                args["label"]),
            args["phone_number"])

    elif name == "voice_answer":
        return _a().voice_answer(_p().exec_id(args["label"]))

    elif name == "voice_end":
        return _a().voice_end(_p().exec_id(args["label"]))

    elif name == "voice_hold":
        return _a().voice_hold(_p().exec_id(args["label"]))

    elif name == "voice_resume":
        return _a().voice_resume(_p().exec_id(args["label"]))

    elif name == "voice_mute":
        return _a().voice_mute(_p().exec_id(args["label"]))

    elif name == "voice_unmute":
        return _a().voice_unmute(_p().exec_id(args["label"]))

    elif name == "voice_send_dtmf":
        return _a().voice_send_dtmf(
            _p().exec_id(
                args["label"]),
            args["digits"])

    elif name == "voice_get_status":
        state = _a().voice_get_status(_p().exec_id(args["label"]))
        return {"label": args["label"], "call_state": state}

    elif name == "voice_wait_for_state":
        reached = _a().voice_wait_for_state(
            _p().exec_id(args["label"]),
            args["target_state"],
            timeout_sec=args.get("timeout_sec", 30),
        )
        final = _a().voice_get_status(_p().exec_id(args["label"]))
        return {
            "label": args["label"],
            "target_state": args["target_state"],
            "reached": reached,
            "final_state": final,
        }

    elif name == "voice_conference":
        return _a().voice_conference_add(_p().exec_id(args["label"]))

    elif name == "voice_transfer":
        return _a().voice_transfer(
            _p().exec_id(
                args["label"]),
            args["phone_number"])

    # ── Network ──────────────────────────────────────────────────────────
    elif name == "network_get_info":
        return _a().network_get_info(_p().exec_id(args["label"]))

    elif name == "network_set_airplane_mode":
        return _a().network_set_airplane_mode(
            _p().exec_id(args["label"]), args["enable"]
        )

    elif name == "network_set_wifi":
        return _a().network_set_wifi(
            _p().exec_id(
                args["label"]),
            args["enable"])

    elif name == "network_set_data":
        return _a().network_set_data(
            _p().exec_id(
                args["label"]),
            args["enable"])

    elif name == "network_set_type":
        return _a().network_set_type(
            _p().exec_id(
                args["label"]),
            args["network_type"])

    # ── Application ──────────────────────────────────────────────────────
    elif name == "app_install":
        return _a().app_install(
            _p().exec_id(
                args["label"]),
            args["repository_key"])

    elif name == "app_open":
        return _a().app_open(
            _p().exec_id(
                args["label"]),
            args["app_identifier"])

    elif name == "app_close":
        return _a().app_close(
            _p().exec_id(
                args["label"]),
            args["app_identifier"])

    elif name == "app_uninstall":
        return _a().app_uninstall(
            _p().exec_id(
                args["label"]),
            args["app_identifier"])

    # ── Media ────────────────────────────────────────────────────────────
    elif name == "recording_start":
        return _a().recording_start(_p().exec_id(args["label"]))

    elif name == "recording_stop":
        return _a().recording_stop(_p().exec_id(args["label"]))

    # ── Repository ───────────────────────────────────────────────────────
    elif name == "repo_list":
        return _a().repo_list(folder=args.get("folder", "PUBLIC"))

    # ── Reporting ────────────────────────────────────────────────────────
    elif name == "get_execution_report":
        return _a().report_get_execution(_p().exec_id(args["label"]))

    # ── Timing ───────────────────────────────────────────────────────────
    elif name == "wait_seconds":
        time.sleep(args["seconds"])
        return {"waited_seconds": args["seconds"]}

    # ── Certification Logging ─────────────────────────────────────────────
    elif name == "log_step":
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "test_case": args["test_case"],
            "step": args["step"],
            "result": args["result"],
            "expected": args.get("expected", ""),
            "actual": args.get("actual", ""),
            "notes": args.get("notes", ""),
        }
        _cert_log.append(entry)
        return {"logged": entry, "total_steps": len(_cert_log)}

    else:
        return {"error": f"Unknown tool '{name}'"}
