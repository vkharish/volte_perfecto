# Call Waiting

**Description:** Verify call waiting — a second incoming call arrives while UE is on an active VoLTE call, UE accepts it, and both calls are managed correctly.

**Tags:** volte, call-waiting, hold, swap, ims

**Devices:**
- UE: Android (device under test)
- CALLER_1: iOS (first call)
- CALLER_2: Android (waiting call)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

Call waiting requires the IMS core to deliver a second INVITE to a busy UE.
The UE must:
- Alert the user while keeping the first call active
- Allow the user to accept the waiting call (putting first on hold)
- Allow the user to swap between calls
- Allow the user to end one call and return to the other

## Test Procedure

1. Reserve UE (Android), CALLER_1 (iOS), and CALLER_2 (Android) from Perfecto.
2. Verify all three devices are on LTE. Log PASS/FAIL for each.
3. Start screen recording on UE.

**Phase 1 — Establish first call:**
4. CALLER_1 calls UE. UE answers. Verify both show active. Log PASS/FAIL.
5. Wait 5 seconds to confirm stable call.

**Phase 2 — Second call arrives:**
6. CALLER_2 calls UE while UE is on active call with CALLER_1.
7. Verify UE shows call waiting indication (ringing or waiting state). Log PASS/FAIL.
8. Verify CALLER_1 call remains active (not dropped) during waiting alert. Log PASS/FAIL.

**Phase 3 — Accept waiting call:**
9. UE answers CALLER_2 (this should put CALLER_1 on hold).
10. Verify UE and CALLER_2 show active. Log PASS/FAIL.
11. Verify CALLER_1 shows held state. Log PASS/FAIL.

**Phase 4 — Swap calls:**
12. UE swaps back to CALLER_1 (puts CALLER_2 on hold).
13. Verify UE and CALLER_1 show active. Log PASS/FAIL.
14. Verify CALLER_2 shows held. Log PASS/FAIL.

**Phase 5 — End calls cleanly:**
15. UE ends call with CALLER_1. Verify CALLER_1 reaches idle. Log PASS/FAIL.
16. Verify CALLER_2 is now automatically resumed to active. Log PASS/FAIL.
17. UE ends call with CALLER_2. Verify both UE and CALLER_2 reach idle. Log PASS/FAIL.

18. Stop recording on UE. Fetch execution reports.
19. Release all three devices.

## Pass Criteria

- UE shows call waiting indication while on active call
- First call stays active (not dropped) when second call arrives
- UE can accept waiting call — first call moves to held
- UE can swap between held and active calls
- Ending one call automatically resumes the other
- All devices reach idle cleanly

## Notes

- Call waiting must be provisioned in IMS/HSS for UE's IMSI — verify before running
- Some carriers send a SIP INVITE with `Call-Info: answer-after=0` for waiting calls
- If CALLER_1 drops when CALLER_2 arrives, the IMS core is not delivering the waiting INVITE correctly
- iOS CALLER_1 is intentional — cross-platform hold behavior during call waiting is a known asymmetry
