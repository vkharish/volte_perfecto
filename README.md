# VoLTE Perfecto — AI Lab Certification Agent

An AI-powered VoLTE certification agent that lets lab engineers describe tests in plain English.
Claude executes them automatically via the Perfecto device lab API.

---

## How It Works

1. Engineer writes a test procedure in plain Markdown (`skills/Hold_Resume.md`)
2. Claude reads the skill file and executes it step-by-step using Perfecto tools
3. Every verification is logged → HTML + JSON report saved to `reports/`

```
Engineer: "Run the Hold Resume test on AT&T Android devices"
    ↓
Claude: list_devices → reserve_devices → voice_call → voice_hold → voice_resume → log_step → release_devices
    ↓
Report: cert_Hold_Resume_20260418_120000.html  [PASS]
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install anthropic python-dotenv
```

### 2. Configure environment
```bash
cp .env.example .env
```
Edit `.env` and fill in:
```
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-6
PERFECTO_API_URL=https://api.yourcompany.com/perfecto
PERFECTO_TOKEN=your-perfecto-token
```

### 3. Run a test (simulation — no real devices needed)
```bash
python3 run_skill.py --skill Hold_Resume --simulate
```

### 4. Run on real devices
```bash
python3 run_skill.py --skill Hold_Resume --operator "AT&T" --os Android
```

---

## Available Skills

| Skill | Description |
|---|---|
| `MO_MT_Basic_Call` | Basic VoLTE MO/MT call setup and teardown |
| `Hold_Resume` | Call hold and resume verification |
| `Conference_3Way` | 3-way conference call merge and management |
| `Conference_Party_Leave` | Party leaving active conference |
| `DTMF_Tones` | DTMF digit sending and verification |
| `Mute_Unmute` | In-call mute and unmute |
| `Call_Waiting` | Call waiting while active call in progress |
| `Call_Transfer_Blind` | Blind call transfer |
| `Call_Transfer_Attended` | Attended call transfer |
| `Call_No_Answer` | MT device does not answer — verify timeout |
| `MT_Reject_Call` | MT device rejects incoming call |
| `IMS_Reregistration` | IMS re-registration after airplane mode toggle |
| `Long_Duration_Call` | Extended call stability test |
| `SRVCC_Handover` | VoLTE to 3G SRVCC handover |
| `CSFB_Fallback` | CS fallback from LTE to 3G/2G |
| `VoLTE_Plus_Data` | Simultaneous VoLTE call + data session |
| `Inter_Carrier_Call` | Cross-carrier VoLTE call (AT&T ↔ Verizon) |
| `Roaming_VoLTE` | VoLTE call while roaming |
| `Emergency_Call_E911` | E911 emergency call location verification |
| `iOS_MO_Android_MT` | iOS calling Android cross-platform test |

---

## CLI Reference

```bash
# List all available skills
python3 run_skill.py --list

# Run a skill
python3 run_skill.py --skill Hold_Resume

# Run with device overrides
python3 run_skill.py --skill Hold_Resume --operator "AT&T" --os Android

# Simulate (no Perfecto credentials needed)
python3 run_skill.py --skill Hold_Resume --simulate

# Run in background (non-blocking)
python3 run_skill.py --skill Hold_Resume --simulate --background

# Check background job status
python3 run_skill.py --status

# Ad-hoc test without a skill file
python3 run_skill.py --prompt "Test VoLTE call from iPhone to Galaxy on T-Mobile"

# Skip HTML report
python3 run_skill.py --skill Hold_Resume --no-report
```

---

## Adding a New Skill

Create a Markdown file in `skills/`:

```markdown
# My New Test

**Description:** One line description of what this validates.

**Tags:** volte, hold, ims

**Devices:**
- MO: Android (AT&T)
- MT: iOS (Verizon)

**Version:** 1.0

---

## What This Test Validates
Explain the protocol behavior being checked.

## Test Procedure
1. Reserve MO and MT devices
2. Verify both devices are on LTE with IMS registered
3. MO dials MT
4. Verify call is active on both devices
5. ... add your steps ...
6. Release all devices

## Pass Criteria
- Call connects within 10 seconds
- ... your criteria ...
```

Run it immediately:
```bash
python3 run_skill.py --skill My_New_Test --simulate
```

---

## CI/CD Integration

Exit codes are pipeline-friendly:
- `0` → all steps PASS
- `1` → any step FAIL

```groovy
// Jenkins example
stage('VoLTE Certification') {
    steps {
        sh 'python3 run_skill.py --skill Hold_Resume --operator "AT&T"'
    }
    post {
        always {
            publishHTML([reportDir: 'reports', reportFiles: '*.html'])
        }
    }
}
```

Run all skills in one shot:
```python
from agent import init_perfecto, run_all_skills, save_report
init_perfecto()
results = run_all_skills(operator='AT&T')
for skill, log in results.items():
    save_report(log, skill)
```

---

## Token Optimization

This project implements **TOON (Token-Optimized Output Normalization)** — tool results are stripped
to only actionable fields before entering message history, reducing input tokens by ~69%.

Prompt caching is enabled on the system prompt and full tools array.
Use `claude-sonnet-4-6` or `claude-opus-4-6` — Haiku does not support prompt caching.

Typical run stats with Sonnet + caching:
```
[Tokens] in=90,296  out=3,290  cache_read=80,074  cache_write=3,426
[Cache]  ~72,066 tokens saved by prompt caching
```

---

## Project Structure

```
volte_perfecto/
├── agent.py              ← Agentic loop, TOON, prompt caching, token tracking
├── run_skill.py          ← CLI entry point
├── CLAUDE.md             ← Claude Code instructions (NLP-driven execution)
├── MEMORY.md             ← Project context for session continuity
├── .env.example          ← Environment template
├── perfecto/
│   ├── api.py            ← Perfecto REST API client
│   ├── mock_api.py       ← Simulation backend (--simulate)
│   ├── tools.py          ← 36 Claude tool definitions + executor
│   └── device_pool.py    ← Device reservation by OS/carrier
└── skills/               ← Test procedures (plain Markdown)
```

---

## Using with Claude Code

With Claude Code open in this directory, just describe what you want:

```
"Run the Hold Resume test on AT&T Android devices"
"What skills are available?"
"Create a new skill for VoWiFi calling"
"Run all skills in the background"
```

Claude Code reads `CLAUDE.md` and handles everything automatically.
