# Call Transfer Blind

**Description:** Verify blind (unattended) call transfer — Party A transfers an active call to Party C without consulting Party C first.

**Tags:** volte, transfer, blind, refer, ims

**Devices:**
- PARTY_A: Android (transferring party)
- PARTY_B: iOS (transferred party)
- PARTY_C: Android (transfer target)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

Blind transfer uses SIP REFER with a Refer-To header pointing to Party C.
Party A sends REFER to Party B, then A drops out. Party B's IMS stack must
initiate a new INVITE to Party C autonomously.
Validates:
- SIP REFER handling on both transferring and transferred devices
- Party B can originate a new call based on REFER without user interaction
- Party A exits cleanly without a drop indication
- Party C receives and can answer the transferred call

## Test Procedure

1. Reserve PARTY_A (Android), PARTY_B (iOS), PARTY_C (Android) from Perfecto.
2. Verify all three devices are on LTE. Log PASS/FAIL for each.
3. Start screen recording on all three devices.

**Phase 1 — Establish A-B call:**
4. PARTY_A calls PARTY_B. PARTY_B answers.
5. Verify both show active. Log PASS/FAIL.
6. Wait 5 seconds to confirm stable call.

**Phase 2 — Blind transfer to C:**
7. PARTY_A initiates blind transfer to PARTY_C's phone number.
8. Verify PARTY_A call ends (reaches idle). Log PASS/FAIL.
9. Verify PARTY_C receives an incoming call (ringing state). Log PASS/FAIL — timeout 20 seconds.

**Phase 3 — Complete the transfer:**
10. PARTY_C answers the transferred call.
11. Verify PARTY_B and PARTY_C show active. Log PASS/FAIL.
12. Wait 10 seconds to confirm stable transferred call.

**Phase 4 — Teardown:**
13. PARTY_C ends the call. Verify both PARTY_B and PARTY_C reach idle. Log PASS/FAIL.

14. Stop recordings. Fetch execution reports.
15. Release all three devices.

## Pass Criteria

- A-B call establishes successfully
- PARTY_A exits cleanly after initiating blind transfer
- PARTY_C receives incoming call within 20 seconds
- PARTY_B and PARTY_C establish active call after transfer completes
- All devices reach idle cleanly

## Notes

- Blind transfer requires PARTY_B's SIP stack to handle REFER and autonomously send INVITE to PARTY_C
- If PARTY_C never rings, check if PARTY_B's carrier permits REFER handling (some carriers strip REFER)
- iOS (PARTY_B) REFER handling varies by iOS version — note iOS version in test evidence
- PARTY_A should see a SIP 202 Accepted response to the REFER before hanging up
