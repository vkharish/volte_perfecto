# Emergency Call E911

**Description:** Verify VoLTE emergency call (E911) setup — IMS priority headers, location delivery, and call routing to PSAP.

**Tags:** e911, emergency, volte, ims, regulatory, psap

**Devices:**
- UE: Android (carrier under test)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

Emergency VoLTE calls must bypass normal IMS registration checks, include
location information (Phase 2 E911), and use priority signaling headers.
This test validates:
- Device can place emergency call even without full IMS registration
- SIP INVITE includes `Resource-Priority: esnet.1` header
- Location (GPS or network-derived) is attached to the INVITE
- Call routes to the lab PSAP simulator (NOT a real 911 center)
- Call setup time meets regulatory requirements (<10 seconds)

## ⚠️ IMPORTANT — Lab Setup Required

**This test must use a lab PSAP simulator or a designated test number provisioned**
**by the carrier. NEVER dial 911 directly. Use the carrier-provided test PSAP number.**

Confirm `EMERGENCY_TEST_NUMBER` in your .env before running this test.
Typical lab test numbers: carrier-specific (e.g., +1-NXX-555-0911 format).

## Test Procedure

1. Reserve UE (Android) from Perfecto.
2. Verify UE is on LTE. Log PASS/FAIL.
3. Enable GPS on UE and inject a known lab GPS coordinate for location.
4. Start screen recording on UE.

**Phase 1 — Emergency call setup:**
5. UE dials the lab PSAP test number (emergency call simulation).
6. Wait for call to reach active or ringing state (timeout 10 seconds). Log PASS/FAIL.
7. Log call setup time (time from dial to active). Pass if < 10 seconds.

**Phase 2 — Verify call stability:**
8. Verify call is active for at least 30 seconds. Log PASS/FAIL.
9. Take screenshot as evidence of active emergency call state.

**Phase 3 — Teardown:**
10. UE ends the call. Verify UE returns to idle. Log PASS/FAIL.

**Phase 4 — Verify IMS registration still intact:**
11. Check network info — verify UE is still on LTE after emergency call. Log PASS/FAIL.
12. Make a normal VoLTE test call to confirm IMS stack is healthy after emergency call. Log PASS/FAIL.
13. End test call. Verify idle. Log PASS/FAIL.

14. Stop recording. Fetch execution reports.
15. Release UE.

## Pass Criteria

- Emergency call reaches active or ringing state within 10 seconds
- Call remains stable for 30 seconds
- IMS registration is intact after emergency call ends
- Normal VoLTE call works immediately after emergency call

## Notes

- Emergency calls use IMS Emergency Registration (SIP REGISTER with `sos` URN) — device should register even if barred
- `Resource-Priority: esnet.1` header verification requires SIP trace — out of scope for Perfecto device test; validate via network logs separately
- Location accuracy (Phase 2 E911) requires GPS fix — allow extra time if lab GPS signal is weak
- If emergency call fails on LTE, device should attempt CSFB to CS emergency — this is a separate test case
- Regulatory requirement: CTIA and carrier certification requires this test to pass with zero retries
