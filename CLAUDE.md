# VoLTE Lab Certification Agent

Lab engineers describe what they want in plain English.
You (Claude Code) read skill files, execute tests via Perfecto API, and manage the skill library.

## Quick Reference

| Engineer says | You do |
|---|---|
| "What tests can I run?" | Read `skills/*.md`, list them clearly |
| "Run the Hold Resume skill" | `python run_skill.py --skill Hold_Resume` |
| "Run IMS test on Verizon" | `python run_skill.py --skill IMS_Reregistration --operator Verizon` |
| "Run a quick ad-hoc test" | `python run_skill.py --prompt "..."` |
| "Create a skill for SRVCC" | Write `skills/SRVCC_Handover.md`, confirm to engineer |
| "Update Hold Resume to add mute" | Edit `skills/Hold_Resume.md`, bump version |
| "Show me the hold resume skill" | `cat skills/Hold_Resume.md` (Read the file) |
| "Find skills about IMS" | `python run_skill.py --list` or search skills/ |

## Environment Variables (required)

Copy `.env.example` to `.env` and fill in your values:

```bash
ANTHROPIC_API_KEY=sk-ant-...

# Used by run_skill.py and agent.py (skill execution + CI/CD)
PERFECTO_API_URL=https://api.yourcompany.com/perfecto
PERFECTO_TOKEN=your-perfecto-token

# Used by Perfecto MCP Server (ad-hoc interactive use via Claude Code)
PERFECTO_CLOUD_NAME=your-cloud-name
PERFECTO_SECURITY_TOKEN=your-perfecto-security-token
```

## Two Modes of Operation

| Mode | When to use | How |
|---|---|---|
| **Skill execution** | Run a certified test, CI/CD regression | `python run_skill.py --skill <name>` |
| **Ad-hoc interactive** | Explore devices, debug, one-off checks | Just talk to Claude Code — Perfecto MCP handles it |

**Ad-hoc examples (no script needed):**
- "What Android devices are available on AT&T right now?"
- "Show me all executions running in the last hour"
- "Stop execution ID abc-123"
- "List all Scriptless tests for the VoLTE project"

## File Structure

```
volte_perfecto/
├── CLAUDE.md              ← You are here (loaded automatically by Claude Code)
├── run_skill.py           ← Execution engine
├── perfecto/
│   ├── api.py             ← Complete Perfecto REST API (40+ methods)
│   ├── device_pool.py     ← Device reservation by type / carrier / OS
│   ├── tools.py           ← All 36 Claude tool definitions + executor
│   └── skill_manager.py   ← Reads/writes skills/*.md files
├── skills/                ← TEST PROCEDURES — plain Markdown, one file per test
│   ├── MO_MT_Basic_Call.md
│   ├── Hold_Resume.md
│   ├── IMS_Reregistration.md
│   ├── Conference_3Way.md
│   ├── DTMF_Tones.md
│   └── <engineers add new .md files here>
└── reports/               ← HTML + JSON cert reports (auto-generated)
```

## Skills — The Core Concept

A skill is a plain `.md` file in `skills/`. Engineers write them like documentation.
Claude reads the file and executes it as a test procedure using the Perfecto API.

**Skill file format:**
```markdown
# Skill Name

**Description:** What this test validates in one line.

**Tags:** volte, hold, ims, etc.

**Devices:**
- MO: Android (AT&T)     ← label: os (optional carrier)
- MT: iOS

**Version:** 1.0
**Author:** Engineer Name

---

## What This Test Validates
<explain the protocol behavior being checked>

## Test Procedure
1. Reserve devices...
2. Verify LTE...
3. Make call...
<plain English — Claude handles all API calls>

## Pass Criteria
- What must be true for PASS
```

**Key rules for skill files:**
- Title (`# Name`) → becomes the skill name for `--skill` flag (spaces → underscores)
- `**Devices:**` block → tells the device pool what to reserve
- The entire file is the execution prompt — Claude reads it and decides how to use the tools
- No code, no YAML syntax — just describe the test

## How to Create a New Skill

When an engineer describes a new test scenario:

1. Write `skills/New_Skill_Name.md` following the format above
2. The `## Test Procedure` section should be clear, numbered steps
3. Each step should map to an observable state (what device should show after the action)
4. Confirm to the engineer: "Saved as `New_Skill_Name` — run with `python run_skill.py --skill New_Skill_Name`"

## How to Update an Existing Skill

When an engineer says "update X to also do Y":

1. Read the existing `skills/X.md`
2. Edit the `## Test Procedure` section to add the new steps
3. Bump `**Version:**` (e.g. 1.0 → 1.1)
4. Update `**Last Updated:**` date
5. Confirm to engineer what changed

## Perfecto API Capabilities

The agent controls devices through these categories (all in `perfecto/api.py`):

| Category | What it can do |
|---|---|
| **Devices** | List/filter by OS, model, carrier, OS version, phone number |
| **Sessions** | Reserve (open), release (close), status, list active |
| **Device utils** | Screenshot, logcat, reboot, GPS injection |
| **VoLTE/Voice** | call, answer, end, hold, resume, mute, unmute, DTMF, conference merge, transfer, wait_for_state |
| **Network** | LTE/5G/3G info, airplane mode, WiFi toggle, cellular data, force network type |
| **Application** | install, open, close, uninstall, info |
| **Media** | Start/stop screen recording, download recording |
| **Repository** | Upload/download/delete files in Perfecto repo |
| **Reporting** | Execution reports, artifacts, custom fields |

## Execution Flow

When `run_skill.py --skill X` runs:
1. Loads `skills/X.md` → passes full content as prompt to Claude
2. Claude reads the procedure and starts calling Perfecto tools
3. `list_devices` → `reserve_devices` → test steps → `release_devices`
4. Every verification point is logged with `log_step` (expected vs actual)
5. HTML + JSON report saved to `reports/`

## Running Tests

```bash
cd volte_perfecto

# List all skills
python run_skill.py --list

# Run a skill by name
python run_skill.py --skill MO_MT_Basic_Call
python run_skill.py --skill Hold_Resume
python run_skill.py --skill IMS_Reregistration

# Override carrier without editing the skill file
python run_skill.py --skill Hold_Resume --operator "AT&T"
python run_skill.py --skill MO_MT_Basic_Call --os iOS

# Run an ad-hoc test without a skill file
python run_skill.py --prompt "Test VoLTE call from iPhone 15 to Galaxy S24 on T-Mobile"
```
