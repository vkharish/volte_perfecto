# Conference Party Leave

**Description:** Verify non-HOST parties can leave a 3-way conference independently, and the remaining parties continue uninterrupted.

**Tags:** volte, conference, 3way, party-leave, ims, refer

**Devices:**
- HOST: Android
- PARTY_A: Android
- PARTY_B: iOS

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

The base Conference_3Way skill only tests HOST ending the entire conference.
This test covers the more complex case where individual parties exit:
- PARTY_A exits mid-conference — PARTY_B and HOST continue
- PARTY_B exits mid-conference — PARTY_A and HOST continue
- Conference degrades gracefully from 3-way to 2-way to idle
- No unexpected drops when non-HOST parties leave
- SIP BYE from a party does not tear down the entire conference

## Test Procedure

1. Reserve HOST (Android), PARTY_A (Android), PARTY_B (iOS) from Perfecto.
2. Verify all three devices are on LTE. Log PASS/FAIL.
3. Start screen recording on all three devices.

**Phase 1 — Establish 3-way conference:**
4. HOST calls PARTY_A. PARTY_A answers. Verify both active. Log PASS/FAIL.
5. HOST places PARTY_A on hold. Verify held. Log PASS/FAIL.
6. HOST calls PARTY_B. PARTY_B answers. Verify both active. Log PASS/FAIL.
7. HOST merges the calls into conference. Log PASS/FAIL.
8. Wait 5 seconds for conference to stabilize.
9. Verify HOST call state is active/conference. Log PASS/FAIL.

**Phase 2 — PARTY_A leaves the conference:**
10. PARTY_A ends their call (leaves the conference).
11. Verify PARTY_A reaches idle. Log PASS/FAIL.
12. Verify HOST call is still active (conference not torn down). Log PASS/FAIL.
13. Verify PARTY_B call is still active. Log PASS/FAIL.
14. Wait 10 seconds to confirm HOST and PARTY_B have a stable 2-way call.

**Phase 3 — PARTY_B leaves the remaining 2-way call:**
15. PARTY_B ends their call.
16. Verify PARTY_B reaches idle. Log PASS/FAIL.
17. Verify HOST reaches idle (no active calls remaining). Log PASS/FAIL.

**Phase 4 — Reverse: PARTY_B leaves first:**
18. Re-establish a new 3-way conference following steps 4–9.
19. PARTY_B (iOS) ends their call first.
20. Verify PARTY_B reaches idle. Log PASS/FAIL.
21. Verify HOST and PARTY_A still have active 2-way call. Log PASS/FAIL.
22. Wait 10 seconds to confirm stability.
23. HOST ends the remaining call. Verify HOST and PARTY_A reach idle. Log PASS/FAIL.

24. Stop recordings. Fetch execution reports.
25. Release all three devices.

## Pass Criteria

- 3-way conference established successfully in both phases
- PARTY_A leaving does not drop HOST-PARTY_B call
- PARTY_B leaving does not drop HOST-PARTY_A call
- Remaining 2-way call is stable after a party leaves
- All devices reach idle cleanly after full teardown

## Notes

- When a participant leaves a REFER-based conference, the focus server must handle the BYE and notify remaining parties — this is the most common conference implementation bug
- If HOST drops when PARTY_A leaves, the conference anchor is on HOST's device (local mix) not on a server-side focus — this is a device-side implementation issue
- iOS PARTY_B leaving first (Phase 4) is intentional — iOS sends BYE differently than Android when leaving a conference
- Compare with Conference_3Way results — if basic conference passes but party-leave fails, the issue is in BYE handling post-merge
