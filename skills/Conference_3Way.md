# Conference 3 Way

**Description:** VoLTE 3-way conference call — HOST establishes calls to PARTY_A and PARTY_B then merges them.

**Tags:** volte, conference, 3way, merge

**Devices:**
- HOST: Android
- PARTY_A: Android
- PARTY_B: iOS

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

The IMS conference service (REFER-based or local mix) works correctly when
a VoLTE device merges two separate active/held calls into a 3-way conference.

## Test Procedure

1. Reserve HOST (Android), PARTY_A (Android), and PARTY_B (iOS) from Perfecto.
2. Verify all three devices are on LTE. Log PASS/FAIL for each.
3. Start screen recording on all three devices.
4. HOST calls PARTY_A. PARTY_A answers. Verify HOST and PARTY_A show active. Log PASS/FAIL.
5. HOST places PARTY_A on hold. Verify PARTY_A shows held. Log PASS/FAIL.
6. HOST calls PARTY_B. PARTY_B answers. Verify HOST and PARTY_B show active. Log PASS/FAIL.
7. HOST merges the calls (conference). Log PASS/FAIL.
8. Wait 5 seconds for conference to stabilize.
9. Verify HOST call state reflects conference (active or conference). Log PASS/FAIL.
10. HOST ends the conference. Verify all three devices return to idle. Log PASS/FAIL.
11. Stop recordings on all three devices.
12. Fetch execution reports for all devices.
13. Release all three devices.

## Pass Criteria

- All three devices confirm LTE before testing
- Both individual calls establish successfully (active state)
- Conference merge succeeds
- All three parties return to idle after HOST ends the conference

## Notes

- Some IMS implementations show 'active' not a distinct 'conference' state — check vendor behavior
- If PARTY_A does not return to idle after conference end, it may indicate a SIP REFER handling issue
