# MT Reject Call

**Description:** Verify correct SIP signaling when MT device rejects an incoming VoLTE call — MO receives 486 Busy Here and returns to idle cleanly.

**Tags:** volte, reject, busy, sip-486, negative, ims

**Devices:**
- MO: Android (originating)
- MT: iOS (rejecting)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

Call rejection is a negative test — verifies the error path is handled correctly.
When MT rejects an incoming VoLTE call:
- IMS core must deliver SIP 486 Busy Here (or 603 Decline) to MO
- MO must return to idle cleanly without hanging in ringing state
- No spurious re-INVITE or retry loop on MO
- MT must return to idle immediately after rejection

## Test Procedure

1. Reserve MO (Android) and MT (iOS) from Perfecto.
2. Verify both devices are on LTE. Log PASS/FAIL.

**Phase 1 — Standard rejection:**
3. MO calls MT.
4. Wait for MT to reach ringing state (timeout 15 seconds). Log PASS/FAIL.
5. MT rejects/declines the incoming call.
6. Verify MT reaches idle state immediately. Log PASS/FAIL.
7. Verify MO reaches idle state within 5 seconds of rejection. Log PASS/FAIL.
8. Verify MO does NOT retry the call automatically. Wait 10 seconds and confirm MO stays idle. Log PASS/FAIL.

**Phase 2 — Rejection while ringing (no answer timeout):**
9. MO calls MT again.
10. Wait for MT to reach ringing state. Log PASS/FAIL.
11. Do NOT answer — let the call ring for 30 seconds.
12. Verify MO is still in ringing/calling state after 30 seconds. Log PASS/FAIL.
13. MT rejects after 30 seconds.
14. Verify both MO and MT reach idle. Log PASS/FAIL.

**Phase 3 — Verify IMS stack healthy after rejections:**
15. MO calls MT. MT answers this time.
16. Verify both show active. Log PASS/FAIL.
17. MO ends the call. Verify both reach idle. Log PASS/FAIL.

18. Fetch execution reports. Release both devices.

## Pass Criteria

- MT reaches idle immediately after rejection
- MO reaches idle within 5 seconds of receiving rejection
- MO does not retry the call after rejection
- MO handles 30-second no-answer correctly (stays in calling state, not dropped)
- Normal VoLTE call succeeds after prior rejections (IMS stack not degraded)

## Notes

- SIP response code matters: 486 = Busy Here, 603 = Decline — both are valid but semantically different; check carrier behavior
- If MO hangs in ringing state after MT rejects, the SIP 486 is not propagating from IMS core to MO — network-side issue
- iOS 'Decline' button sends SIP 603 Decline; Android 'Reject' may send 486 — verify carrier normalizes correctly
- Rejection should NOT trigger voicemail unless the carrier has configured immediate voicemail on reject — note any voicemail redirect in test evidence
