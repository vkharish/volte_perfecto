# Long Duration Call

**Description:** Verify VoLTE call stability over 30 minutes — tests IMS re-REGISTER mid-call, RTP keepalive, and absence of silent drops.

**Tags:** volte, endurance, long-duration, keepalive, re-register, stability

**Devices:**
- MO: Android
- MT: iOS

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

Short call tests miss a class of bugs that only surface over time:
- IMS re-REGISTER while call is active (registration expiry during call)
- RTP inactivity timer on the IMS core triggering a silent BYE
- Media gateway keepalive (RTCP) failures
- Memory/buffer exhaustion on device after sustained RTP stream
- Carrier-side session timer (Session-Expires header) requiring re-INVITE

## Test Procedure

1. Reserve MO (Android) and MT (iOS) from Perfecto.
2. Verify both devices are on LTE. Log PASS/FAIL.
3. Start screen recording on both devices.

**Phase 1 — Establish call:**
4. MO calls MT. MT answers.
5. Verify both show active. Log PASS/FAIL.
6. Record call start timestamp.

**Phase 2 — Stability checkpoints (every 5 minutes for 30 minutes):**
7. At T+5min: Verify both devices still show active. Log PASS/FAIL with timestamp.
8. At T+10min: Verify both devices still show active. Log PASS/FAIL with timestamp.
9. At T+15min: Verify both devices still show active. Log PASS/FAIL with timestamp.
   - Take screenshot on both devices as mid-call evidence.
10. At T+20min: Verify both devices still show active. Log PASS/FAIL with timestamp.
11. At T+25min: Verify both devices still show active. Log PASS/FAIL with timestamp.
12. At T+30min: Verify both devices still show active. Log PASS/FAIL with timestamp.
    - Take screenshot on both devices as 30-minute evidence.

**Phase 3 — Post-endurance functional check:**
13. MO places call on hold. Verify MO shows held. Log PASS/FAIL.
14. MO resumes call. Verify both show active. Log PASS/FAIL.
15. Send DTMF digits 1-2-3 from MO. Verify call stays active. Log PASS/FAIL.

**Phase 4 — Teardown:**
16. MO ends the call. Verify both devices reach idle. Log PASS/FAIL.
17. Record call end timestamp. Log total call duration.
18. Stop recordings. Fetch execution reports from both devices.
19. Release both devices.

## Pass Criteria

- Call active at every 5-minute checkpoint (6 of 6 checkpoints pass)
- No silent drop at any point during 30 minutes
- Hold/resume functional after 30-minute call
- DTMF functional after 30-minute call
- Total call duration ≥ 30 minutes

## Notes

- IMS registration expiry is typically 3600 seconds — this test won't catch re-REGISTER issues; for that, run a 60+ minute call
- Session-Expires header (RFC 4028) may trigger a re-INVITE at the midpoint — if call drops around 15 min, check session timer config
- Silent drops (device shows active but audio is gone) are NOT caught by state polling alone — supplement with server-side RTP monitoring
- If call drops at a consistent interval (e.g., always at 10 min), that interval is likely an IMS timer — note exact drop time for network team
- This test consumes a Perfecto session for 30+ minutes — schedule during off-peak lab hours
