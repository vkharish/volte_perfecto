"""
VoLTE Skill Runner — CLI entry point
=====================================
Thin wrapper around agent.py for interactive use and Claude Code.

Usage:
    python run_skill.py --list
    python run_skill.py --skill Hold_Resume
    python run_skill.py --skill Hold_Resume --os Android --operator AT&T
    python run_skill.py --skill Hold_Resume --background        ← non-blocking
    python run_skill.py --status                                ← check running jobs
    python run_skill.py --prompt "Test VoLTE call from iPhone to Galaxy on T-Mobile"
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from agent import init_perfecto, list_skills, save_report

LOGS_DIR = Path(__file__).parent / "logs"


def _launch_background(args: argparse.Namespace) -> None:
    """Re-launch this script as a detached background process, logging to logs/."""
    LOGS_DIR.mkdir(exist_ok=True)

    # Build the foreground command (same args minus --background)
    cmd = [sys.executable, __file__]
    if args.skill:
        cmd += ["--skill", args.skill]
    elif args.prompt:
        cmd += ["--prompt", args.prompt]
    if args.os:
        cmd += ["--os", args.os]
    if args.operator:
        cmd += ["--operator", args.operator]
    if args.simulate:
        cmd += ["--simulate"]
    if args.no_report:
        cmd += ["--no-report"]

    skill_name = args.skill or "adhoc"

    ts = time.strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"{skill_name}_{ts}.log"

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"  # flush output immediately to log file

    with open(log_path, "w") as log_file:
        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,  # detach from parent session
            env=env,
        )

    print(f"[Background] PID {proc.pid} — skill: {skill_name}")
    print(f"[Log]        {log_path}")
    print(f"[Tail]       tail -f {log_path}")


def _show_status() -> None:
    """Show running and recently completed background jobs."""
    if not LOGS_DIR.exists():
        print("No background jobs found.")
        return

    logs = sorted(
        LOGS_DIR.glob("*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True)
    if not logs:
        print("No background jobs found.")
        return

    print(f"\n{'LOG FILE':<50} {'LAST LINE'}")
    print("-" * 100)
    for log in logs[:10]:
        try:
            lines = log.read_text().splitlines()
            last = lines[-1][:48] if lines else "(empty)"
        except Exception:
            last = "(unreadable)"
        print(f"{log.name:<50} {last}")
    print("\nTo follow a job: tail -f logs/<filename>")


def main() -> None:
    parser = argparse.ArgumentParser(description="VoLTE Skill Runner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--skill", help="Skill name to run (fuzzy match)")
    group.add_argument("--prompt", help="Free-text ad-hoc test description")
    group.add_argument(
        "--list",
        action="store_true",
        help="List available skills")
    group.add_argument(
        "--status", action="store_true", help="Show background job status"
    )

    parser.add_argument("--os", help="Override device OS (Android/iOS)")
    parser.add_argument("--operator", help="Override carrier (e.g. AT&T)")
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip HTML report")
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run against MockPerfectoAPI — no real credentials needed",
    )
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run in background — returns immediately, logs to logs/",
    )
    args = parser.parse_args()

    # ── Status ──────────────────────────────────────────────────────────────
    if args.status:
        _show_status()
        return

    # ── Background launch — return immediately so Claude Code stays free ────
    if args.background:
        _launch_background(args)
        return

    from agent import _MODEL

    init_perfecto(simulate=args.simulate)
    print(f"[Model] {_MODEL}")

    # ── List ────────────────────────────────────────────────────────────────
    if args.list:
        skills = list_skills()
        if not skills:
            print("No skills found. Add .md files to skills/")
            return
        print(f"\n{'NAME':<35} DESCRIPTION")
        print("-" * 80)
        for s in skills:
            print(f"{s['name']:<35} {s['description'][:44]}")
        print(f"\n{len(skills)} skill(s) available.")
        return

    # ── Run ─────────────────────────────────────────────────────────────────
    if args.skill:
        from agent import _run_prompt, find_skill

        skill_path = find_skill(args.skill)
        skill_name = skill_path.stem
        prompt = skill_path.read_text()
        if args.os or args.operator:
            overrides = []
            if args.os:
                overrides.append(f"os={args.os}")
            if args.operator:
                overrides.append(f"operator={args.operator}")
            prompt = f"Override device filters: {
                ', '.join(overrides)}\n\n{prompt}"
        print(f"\n{'=' * 60}\n  Running skill: {skill_name}\n{'=' * 60}\n")
        cert_log = _run_prompt(prompt)
    else:
        from agent import _run_prompt

        skill_name = "adhoc"
        print(f"\n{'=' * 60}\n  Running ad-hoc prompt\n{'=' * 60}\n")
        cert_log = _run_prompt(args.prompt)

    # ── Report ──────────────────────────────────────────────────────────────
    if cert_log and not args.no_report:
        path = save_report(cert_log, skill_name)
        print(f"\n[Report] {path}")

    passed = sum(1 for e in cert_log if e["result"] == "PASS")
    failed = sum(1 for e in cert_log if e["result"] == "FAIL")
    print(f"\n{'=' * 40}")
    print(f"  {passed} PASSED   {failed} FAILED")
    print(f"  Verdict: {'PASS' if failed == 0 else 'FAIL'}")
    print(f"{'=' * 40}\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
