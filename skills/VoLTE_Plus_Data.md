# VoLTE Plus Data

**Description:** Verify simultaneous VoLTE call and LTE data — voice and data bearers coexist correctly (SVLTE / dual-bearer).

**Tags:** volte, data, svlte, simultaneous, bearer, lte

**Devices:**
- UE: Android (device under test)
- MT: iOS (call partner)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

One of the primary benefits of VoLTE over CSFB is simultaneous voice and data.
When a VoLTE call is active, the device must maintain a separate LTE data bearer.
This validates:
- IMS voice bearer (QCI 1) and default data bearer (QCI 9) coexist
- Data throughput remains functional during active VoLTE call
- LTE stays attached for data throughout the call
- No data stall or bearer teardown when call is answered or ended

## Test Procedure

1. Reserve UE (Android) and MT (iOS) from Perfecto.
2. Verify both devices are on LTE. Log PASS/FAIL.

**Phase 1 — Baseline data check (before call):**
3. Verify LTE data is active on UE via network_get_info. Log PASS/FAIL.

**Phase 2 — Establish VoLTE call:**
4. UE calls MT. MT answers.
5. Verify both show active (VoLTE call). Log PASS/FAIL.

**Phase 3 — Data during active call:**
6. While call is active, verify LTE network type is still LTE on UE (data bearer intact). Log PASS/FAIL.
7. Open a data-dependent app or trigger a network check on UE to confirm data connectivity during call. Log PASS/FAIL.
8. Wait 10 seconds. Re-verify LTE data still active. Log PASS/FAIL.

**Phase 4 — Hold and verify data:**
9. UE places call on hold.
10. Verify LTE data is still active during hold state. Log PASS/FAIL.
11. UE resumes call. Verify active state. Log PASS/FAIL.

**Phase 5 — End call and verify data recovery:**
12. UE ends the call. Verify UE reaches idle. Log PASS/FAIL.
13. Verify LTE data still active after call end (bearer not torn down). Log PASS/FAIL.

14. Fetch execution reports. Release both devices.

## Pass Criteria

- LTE data bearer is active before, during, and after VoLTE call
- Network type remains LTE throughout (no fallback to 3G for data)
- Data connectivity confirmed during active call
- Data connectivity confirmed during hold
- Data bearer remains intact after call ends

## Notes

- CSFB devices CANNOT pass this test — they drop data when a call is active; this test verifies VoLTE advantage
- If UE drops to 3G for data during VoLTE call, SVLTE (simultaneous voice and LTE) is not configured correctly
- Some Android devices require Carrier Aggregation (CA) to maintain full data speeds during VoLTE — data may be present but slower, which is acceptable
- WiFi calling does NOT count as VoLTE for this test — verify UE is on cellular LTE, not WiFi
