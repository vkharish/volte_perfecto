# VoLTE Perfecto — Project Memory
_Last updated: 2026-04-18_

## What This Project Is
AI-powered VoLTE lab certification agent. Lab engineers describe tests in plain English (skills/*.md),
and Claude executes them via Perfecto API. Supports real devices and simulation mode.

---

## Current State — Everything Working

### Model Configuration
- **Agent model** (run_skill.py): `CLAUDE_MODEL=claude-sonnet-4-6` in `.env`
  - Sonnet is cheaper than Haiku overall because it supports **prompt caching**
  - Haiku does NOT support prompt caching — always cache_read=0
- **Claude Code terminal**: `claude-sonnet-4-6` set in `.claude/settings.json`
- Caching verified working: `cache_read=80,074` tokens saved in last run

### Last Simulation Run Result
```
[Tokens] in=90,296  out=3,290  cache_read=80,074  cache_write=3,426
[Cache]  ~72,066 tokens saved by prompt caching
```

### Key Files and Their Purpose
```
volte_perfecto/
├── agent.py              ← Agentic loop, TOON, prompt caching, token tracking
├── run_skill.py          ← CLI: --skill, --prompt, --simulate, --background, --status, --list
├── CLAUDE.md             ← Claude Code instructions (auto-loaded)
├── MEMORY.md             ← This file
├── .env                  ← ANTHROPIC_API_KEY, CLAUDE_MODEL, Perfecto creds
├── .gitignore            ← Excludes .env, reports/, logs/, __pycache__/
├── perfecto/
│   ├── api.py            ← Real Perfecto REST API client
│   ├── mock_api.py       ← Simulation (--simulate flag, no real creds needed)
│   ├── tools.py          ← 36 Claude tool definitions + executor + TOOLS array
│   └── skill_manager.py  ← Reads/writes skills/*.md
└── skills/
    ├── Hold_Resume.md
    ├── MO_MT_Basic_Call.md
    ├── IMS_Reregistration.md
    ├── Conference_3Way.md
    └── DTMF_Tones.md
```

---

## Key Technical Decisions Made

### TOON (Token-Optimized Output Normalization)
- Implemented in `agent.py` — strips verbose fields from tool results before they enter message history
- `_TOON_KEEP` dict defines which fields to keep per tool
- Reduced tool result size by ~69% (e.g. network_get_info: 280→87 chars)
- Special case: `voice_wait_for_state` flattens nested dict → `{reached: bool, target_state: str}`

### Prompt Caching
- System prompt has `cache_control: {type: ephemeral}`
- Last tool in TOOLS array (`log_step`) has `cache_control: {type: ephemeral}` — caches entire TOOLS array
- Uses `client.beta.messages.stream()` with `betas=["prompt-caching-2024-07-31"]`
- Only works on Sonnet and Opus — NOT Haiku

### Background Execution (so Claude Code doesn't block)
```bash
python3 run_skill.py --skill Hold_Resume --simulate --background
python3 run_skill.py --status       # check running jobs
tail -f logs/<filename>.log         # follow live output
```
Uses `subprocess.Popen` with `start_new_session=True` + `PYTHONUNBUFFERED=1`

### CI/CD / Scheduler Integration
- Exit code: `0` = all PASS, `1` = any FAIL (Jenkins-friendly)
- Reports saved to `reports/cert_<skill>_<timestamp>.html` and `.json`
- Override carrier/OS without editing skill files: `--operator "AT&T" --os Android`

### Wall-clock timeout
- `_WALL_CLOCK_TIMEOUT = 30 * 60` (30 minutes) — aborts if test hangs
- `_MAX_TURNS = 25` — max agentic turns per run

---

## MockPerfectoAPI Fixes Applied
All these bugs were found and fixed during development:
1. `take_screenshot` — added optional `key` parameter
2. `voice_wait_for_state` — added `timeout_sec` kwarg (tools.py passes this name)
3. `voice_get_status` — added as alias for `voice_get_state`
4. `open_session()` returns plain string exec_id (not dict)
5. All field names are snake_case in mock

---

## How to Run

```bash
cd /path/to/volte_perfecto

# Simulation (no Perfecto creds needed)
python3 run_skill.py --skill Hold_Resume --simulate

# Real devices
python3 run_skill.py --skill Hold_Resume --operator "AT&T" --os Android

# Background (non-blocking)
python3 run_skill.py --skill Hold_Resume --simulate --background

# Check background job status
python3 run_skill.py --status

# List all available skills
python3 run_skill.py --list

# NLP ad-hoc (from Claude Code terminal — goes through CLAUDE.md)
# Just say: "Run the Hold Resume test on AT&T Android devices"
```

---

## .env Template
```
ANTHROPIC_API_KEY=sk-ant-...

CLAUDE_MODEL=claude-sonnet-4-6          # use sonnet for caching; haiku has no caching

PERFECTO_API_URL=https://api.yourcompany.com/perfecto
PERFECTO_TOKEN=your-perfecto-token

PERFECTO_CLOUD_NAME=your-cloud-name
PERFECTO_SECURITY_TOKEN=your-perfecto-security-token
```

---

## Dependencies
```bash
pip install anthropic python-dotenv
```

---

## Pending / Future Ideas
- [ ] Multi-skill suite runner with summary report (run_all_skills already in agent.py)
- [ ] Slack/email notification on FAIL
- [ ] Schedule config file (yaml-based) for teams without Jenkins
- [ ] Device pool retry logic (if no devices available, wait and retry)
- [ ] Parallel skill execution (run MO_MT and Hold_Resume simultaneously)
