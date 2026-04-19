"""
VoLTE Certification Agent
=========================
Reusable core — importable by CI/CD pipelines, schedulers, or any script.

Usage (programmatic):
    from agent import run_skill, run_all_skills, save_report

Usage (from CI/CD):
    results = run_skill("Hold_Resume")
    results = run_skill("Hold_Resume", operator="AT&T", os_filter="Android")
    results = run_all_skills()          # run every skill in skills/
"""

from __future__ import annotations

import atexit
import json
import logging
import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

import perfecto.tools as tools_module
from perfecto.api import PerfectoAPI
from perfecto.tools import TOOLS, execute_tool, get_cert_log, release_all_devices

load_dotenv()

log = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent / "skills"

SYSTEM_PROMPT = """VoLTE lab certification agent. Execute test procedures via Perfecto tools.
Rules: list_devices→reserve_devices→network_get_info(LTE check)→test steps→release_devices.
Use voice_wait_for_state (not polling). log_step every verification. Retry FAIL once.
End with: PASS/FAIL counts + Verdict."""


# ─────────────────────────────────────────────────────────────────────────────
# Initialisation
# ─────────────────────────────────────────────────────────────────────────────


def init_perfecto(simulate: bool = False) -> None:
    """
    Initialise the Perfecto API client.

    Args:
        simulate: If True, use MockPerfectoAPI — no real credentials needed.
    """
    if simulate:
        from perfecto.mock_api import MockPerfectoAPI

        print("[SIMULATE] Using MockPerfectoAPI — no real Perfecto credentials needed.")
        tools_module.init(MockPerfectoAPI())
    else:
        base_url = os.environ.get("PERFECTO_API_URL")
        token = os.environ.get("PERFECTO_TOKEN")
        if not base_url or not token:
            raise EnvironmentError(
                "PERFECTO_API_URL and PERFECTO_TOKEN must be set in .env"
            )
        tools_module.init(PerfectoAPI(base_url, token))
    # Guarantee device release even if the process is killed or crashes
    atexit.register(release_all_devices)


# ─────────────────────────────────────────────────────────────────────────────
# Skill helpers
# ─────────────────────────────────────────────────────────────────────────────


def find_skill(name: str) -> Path:
    """Locate a skill .md file by name (case-insensitive, spaces=underscores)."""
    target = name.lower().replace(" ", "_").replace("-", "_")
    for f in SKILLS_DIR.glob("*.md"):
        if f.stem.lower().replace(" ", "_").replace("-", "_") == target:
            return f
    available = [f.stem for f in SKILLS_DIR.glob("*.md")]
    raise FileNotFoundError(
        f"Skill '{name}' not found. Available: {available}")


def list_skills() -> list[dict]:
    """Return a list of {name, description} dicts for all skills."""
    skills = []
    for f in sorted(SKILLS_DIR.glob("*.md")):
        desc = ""
        for line in f.read_text().splitlines():
            if line.startswith("**Description:**"):
                desc = line.replace("**Description:**", "").strip()
                break
        skills.append({"name": f.stem, "description": desc, "path": str(f)})
    return skills


# ─────────────────────────────────────────────────────────────────────────────
# Agentic loop
# ─────────────────────────────────────────────────────────────────────────────


_MAX_TURNS = 25
_WALL_CLOCK_TIMEOUT = 30 * 60  # 30 minutes — enough for any VoLTE test
_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

# ── TOON: Token-Optimized Output Normalization ──────────────────────────
# Strips verbose fields from tool results before they enter message history.
# The agent only needs the actionable signal — not full nested JSON.
_TOON_KEEP = {
    # what matters from each tool result
    "list_devices": ["count", "devices"],
    "reserve_devices": ["reserved"],
    "release_devices": ["released"],
    "network_get_info": ["networkType", "imsRegistered", "volteEnabled", "operator"],
    "voice_call": ["callState", "dialedNumber"],
    "voice_answer": ["callState"],
    "voice_end": ["callState"],
    "voice_hold": ["callState"],
    "voice_resume": ["callState"],
    "voice_wait_for_state": ["reached", "final_state", "target_state"],
    "voice_get_status": ["callState"],
    "voice_mute": ["muted"],
    "voice_unmute": ["muted"],
    "voice_send_dtmf": ["digitsSent"],
    "voice_conference": ["callState", "conference"],
    "voice_transfer": ["transferred", "target"],
    "take_screenshot": ["screenshotUrl", "key"],
    "recording_start": ["recording"],
    "recording_stop": ["recording", "videoUrl"],
    "log_step": ["logged"],
    "wait_seconds": ["waited_seconds"],
    "get_execution_report": ["executionId", "reportUrl"],
}


def _toon(tool_name: str, result: dict) -> dict:
    """Return a slim version of a tool result — only keys the agent needs."""
    if "error" in result:
        return result  # pass errors through unchanged

    # Special case: voice_wait_for_state returns nested dicts — flatten to
    # booleans
    if tool_name == "voice_wait_for_state":
        reached = result.get("reached")
        # reached may itself be a dict with a "reached" key
        if isinstance(reached, dict):
            reached = reached.get("reached", False)
        state = result.get("target_state", "")
        return {"reached": reached, "target_state": state}

    keep = _TOON_KEEP.get(tool_name)
    if not keep:
        return result
    return {k: result[k] for k in keep if k in result}


def _run_prompt(prompt: str) -> list[dict]:
    """
    Run the agentic loop against a prompt and return the cert log.

    Guarantees:
    - Resets cert log before each run (no bleed between back-to-back skills)
    - Aborts after 30 minutes wall-clock regardless of turn count
    - Devices are released via atexit even if this function raises
    """
    # Fix: reset cert log so back-to-back runs don't bleed into each other
    tools_module.init_cert_log()

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]
    deadline = time.monotonic() + _WALL_CLOCK_TIMEOUT
    total_in = total_out = cache_read = cache_write = 0

    for turn in range(_MAX_TURNS):
        # Fix: wall-clock timeout — abort if test is taking too long
        if time.monotonic() > deadline:
            log.error(
                "Agent hit %d-minute wall-clock timeout after %d turns",
                _WALL_CLOCK_TIMEOUT // 60,
                turn,
            )
            print(
                f"\n[TIMEOUT] Test exceeded {
                    _WALL_CLOCK_TIMEOUT //
                    60} minutes — aborting."
            )
            break

        with client.beta.messages.stream(
            model=_MODEL,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            betas=["prompt-caching-2024-07-31"],
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        # Track token usage per turn
        u = response.usage
        total_in += u.input_tokens
        total_out += u.output_tokens
        cache_read += getattr(u, "cache_read_input_tokens", 0) or 0
        cache_write += getattr(u, "cache_creation_input_tokens", 0) or 0

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\n{block.text}")

        if response.stop_reason == "end_turn":
            messages.append({"role": "assistant", "content": response.content})
            break

        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_blocks:
            break

        messages.append({"role": "assistant", "content": response.content})

        results = []
        for tb in tool_blocks:
            print(
                f"  ▶ {tb.name}({json.dumps(tb.input, separators=(',', ':'))})")
            result = execute_tool(tb.name, tb.input)
            slim = _toon(tb.name, result)  # TOON: strip verbose fields
            rs = json.dumps(slim)
            print(f"  ◀ {rs[:300]}{'...' if len(rs) > 300 else ''}")
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tb.id,
                    "content": rs,  # history gets slim result only
                }
            )

        messages.append({"role": "user", "content": results})

    # Print token usage summary for this run
    print(
        f"\n[Tokens] in={total_in:,}  out={total_out:,}  "
        f"cache_read={cache_read:,}  cache_write={cache_write:,}"
    )
    if cache_read:
        saved = int(cache_read * 0.9)
        print(f"[Cache]  ~{saved:,} tokens saved by prompt caching")

    return get_cert_log()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def run_skill(
    name: str,
    os_filter: str = "",
    operator: str = "",
) -> list[dict]:
    """
    Load and execute a named skill.

    Args:
        name:       Skill name (fuzzy match against skills/*.md)
        os_filter:  Override device OS, e.g. 'Android' or 'iOS'
        operator:   Override carrier, e.g. 'AT&T', 'Verizon'

    Returns:
        Certification log — list of step dicts with result PASS/FAIL/SKIP
    """
    skill_path = find_skill(name)
    prompt = skill_path.read_text()

    if os_filter or operator:
        overrides = []
        if os_filter:
            overrides.append(f"os={os_filter}")
        if operator:
            overrides.append(f"operator={operator}")
        prompt = f"Override device filters: {', '.join(overrides)}\n\n{prompt}"

    print(f"\n{'=' * 60}")
    print(f"  Running skill: {skill_path.stem}")
    print(f"{'=' * 60}\n")

    return _run_prompt(prompt)


def run_all_skills(
    os_filter: str = "",
    operator: str = "",
    stop_on_fail: bool = False,
) -> dict[str, list[dict]]:
    """
    Run every skill in skills/ and return a dict of {skill_name: cert_log}.

    Args:
        os_filter:    Apply OS override to all skills
        operator:     Apply carrier override to all skills
        stop_on_fail: Stop suite immediately if any skill fails
    """
    results = {}
    for skill in list_skills():
        cert_log = run_skill(
            skill["name"],
            os_filter=os_filter,
            operator=operator)
        results[skill["name"]] = cert_log
        if stop_on_fail and any(e["result"] == "FAIL" for e in cert_log):
            log.warning("Stopping suite — %s failed", skill["name"])
            break
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────────────────


def save_report(cert_log: list[dict], name: str) -> str:
    """Write HTML + JSON certification report to reports/. Returns HTML path."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = Path(__file__).parent / "reports"
    out.mkdir(exist_ok=True)

    passed = sum(1 for e in cert_log if e["result"] == "PASS")
    failed = sum(1 for e in cert_log if e["result"] == "FAIL")
    color = "green" if failed == 0 else "red"
    verdict = "PASS" if failed == 0 else "FAIL"

    rows = "\n".join(
        f"<tr class='{e['result'].lower()}'>"
        f"<td>{e['timestamp']}</td><td>{e['test_case']}</td>"
        f"<td>{e['step']}</td><td><b>{e['result']}</b></td>"
        f"<td>{e.get('expected', '')}</td><td>{e.get('actual', '')}</td>"
        f"<td>{e.get('notes', '')}</td></tr>"
        for e in cert_log
    )
    html = f"""<!DOCTYPE html><html><head><title>VoLTE — {name}</title>
<style>body{{font-family:Arial;margin:20px}}
table{{border-collapse:collapse;width:100%}}
th{{background:#1a4080;color:white;padding:8px}}td{{border:1px solid #ccc;padding:6px}}
tr.pass{{background:#f0fff0}}tr.fail{{background:#fff0f0}}tr.skip{{background:#fffff0}}
</style></head><body>
<h2>VoLTE Lab Certification — {name}</h2>
<p>Date: {time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())} &nbsp;
Steps: {len(cert_log)} &nbsp; Passed: {passed} &nbsp; Failed: {failed} &nbsp;
Verdict: <b style="color:{color}">{verdict}</b></p>
<table><tr><th>Time</th><th>Test Case</th><th>Step</th><th>Result</th>
<th>Expected</th><th>Actual</th><th>Notes</th></tr>{rows}</table>
</body></html>"""

    p = out / f"cert_{name}_{ts}.html"
    p.write_text(html)
    (out / f"cert_{name}_{ts}.json").write_text(json.dumps(cert_log, indent=2))
    return str(p)
