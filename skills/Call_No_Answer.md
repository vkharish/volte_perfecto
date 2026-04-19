# Call No Answer

**Description:** Verify correct handling when MT does not answer — MO should eventually timeout and return to idle, voicemail or no-answer treatment applied correctly.

**Tags:** volte, no-answer, timeout, voicemail, sip-408, ims, negative

**Devices:**
- MO: Android (originating)
- MT: iOS (not answering)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

No-answer handling involves a timer in the IMS core (typically 30–60 seconds)
after which the network sends a SIP response to MO (408 Request Timeout,
480 Temporarily Unavailable, or redirects to voicemail).
Validates:
- MO stays in calling/ringing state until no-answer timer expires
- MO receives appropriate SIP response after timeout
- MO returns to idle cleanly without hanging
- MT returns to idle (stops ringing) after no-answer timeout
- Voicemail redirect (if configured) is triggered correctly

## Test Procedure

1. Reserve MO (Android) and MT (iOS) from Perfecto.
2. Verify both devices are on LTE. Log PASS/FAIL.

**Phase 1 — No answer scenario:**
3. MO calls MT.
4. Verify MT reaches ringing state within 20 seconds. Log PASS/FAIL.
5. Do NOT answer — monitor both devices.
6. Verify MO stays in calling state (does not drop prematurely). Log PASS/FAIL — check at 15 second mark.
7. Wait for no-answer timer to expire (up to 60 seconds total from step 3).
8. Verify MO returns to idle after timeout. Log PASS/FAIL.
9. Record the actual timeout duration (time from call initiation to MO idle). Log as metric.
10. Verify MT also returns to idle (stops ringing). Log PASS/FAIL.

**Phase 2 — Check for voicemail redirect (if applicable):**
11. If MO was redirected to voicemail (heard voicemail greeting before idle):
    - Log that voicemail redirect is active. Mark as INFO (not FAIL unless unexpected).
12. If MO returned directly to idle (no voicemail):
    - Log that no-answer goes directly to idle. Mark as INFO.

**Phase 3 — MO not reachable (MT airplane mode):**
13. Enable airplane mode on MT.
14. Wait 5 seconds.
15. MO calls MT.
16. Verify MO receives a fast-failure response (SIP 480 or 408) within 10 seconds. Log PASS/FAIL.
17. Verify MO reaches idle within 10 seconds. Log PASS/FAIL.
18. Disable airplane mode on MT. Wait 15 seconds for MT IMS recovery.

**Phase 4 — Verify IMS healthy after no-answer tests:**
19. MO calls MT. MT answers this time.
20. Verify both show active. Log PASS/FAIL.
21. MO ends call. Verify both reach idle. Log PASS/FAIL.

22. Fetch execution reports. Release both devices.

## Pass Criteria

- MO stays in calling state until no-answer timer expires (no premature drop)
- MO returns to idle cleanly after no-answer timeout
- MT returns to idle after no-answer timeout
- When MT is unreachable, MO gets fast failure within 10 seconds
- Normal VoLTE call works after no-answer tests (IMS not degraded)

## Notes

- No-answer timeout is carrier-configured (typically 30–60 seconds) — note actual duration in the report for comparison against carrier SLA
- Voicemail redirect behavior varies by carrier and user account settings — record observed behavior, do not fail for voicemail presence
- Phase 3 (MT in airplane mode) tests SIP 480 Temporarily Unavailable — faster than waiting for no-answer timer
- If MO drops before the expected timeout (e.g., drops at 5 seconds), the IMS core has a misconfigured timer or is returning an error prematurely
