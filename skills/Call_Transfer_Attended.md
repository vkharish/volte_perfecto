# Call Transfer Attended

**Description:** Verify attended (consultative) call transfer — Party A consults Party C before transferring Party B to Party C.

**Tags:** volte, transfer, attended, consultative, refer, ims

**Devices:**
- PARTY_A: Android (transferring party)
- PARTY_B: iOS (original caller, gets transferred)
- PARTY_C: Android (transfer target, consulted first)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

Attended transfer: A holds B, calls C to consult, then transfers B to C.
More complex than blind transfer — involves two simultaneous calls on PARTY_A,
a SIP REFER with a Replaces header, and clean teardown of A's leg.
Validates:
- Hold + second call setup (same as conference leg 1)
- SIP REFER with Replaces (replaces A-C call with B-C call)
- Party A exits cleanly from both legs
- Party B and Party C establish direct call after transfer

## Test Procedure

1. Reserve PARTY_A (Android), PARTY_B (iOS), PARTY_C (Android) from Perfecto.
2. Verify all three devices are on LTE. Log PASS/FAIL.
3. Start screen recording on all three devices.

**Phase 1 — Establish A-B call:**
4. PARTY_A calls PARTY_B. PARTY_B answers.
5. Verify both show active. Log PASS/FAIL.
6. Wait 5 seconds.

**Phase 2 — Consult Party C:**
7. PARTY_A places PARTY_B on hold.
8. Verify PARTY_B shows held. Log PASS/FAIL.
9. PARTY_A calls PARTY_C. PARTY_C answers.
10. Verify PARTY_A and PARTY_C show active. Log PASS/FAIL.
11. Wait 5 seconds (consultation period — PARTY_A informs PARTY_C of the transfer).

**Phase 3 — Execute attended transfer:**
12. PARTY_A initiates attended transfer (REFER with Replaces pointing to A-B call).
13. Verify PARTY_A exits both calls (reaches idle). Log PASS/FAIL.
14. Verify PARTY_B and PARTY_C show active (direct call established). Log PASS/FAIL — timeout 20 seconds.

**Phase 4 — Confirm stable transferred call:**
15. Wait 10 seconds to confirm B-C call is stable without PARTY_A.

**Phase 5 — Teardown:**
16. PARTY_B ends the call. Verify both PARTY_B and PARTY_C reach idle. Log PASS/FAIL.

17. Stop recordings. Fetch execution reports.
18. Release all three devices.

## Pass Criteria

- A-B and A-C calls establish successfully
- PARTY_B held correctly while PARTY_A consults PARTY_C
- PARTY_A exits cleanly after transfer
- PARTY_B and PARTY_C establish direct active call
- All devices idle cleanly

## Notes

- Attended transfer (REFER with Replaces) is more complex than blind — requires both call legs to be tracked by IMS
- If PARTY_A's carrier doesn't support REFER with Replaces, the transfer will fail at step 12 — this is a carrier feature gap, not a device bug
- PARTY_B (iOS) being on hold during consultation tests cross-platform hold interoperability
- Compare with blind transfer results — if blind passes but attended fails, the Replaces header is the issue
