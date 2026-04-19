# CSFB Fallback

**Description:** Verify Circuit Switched Fallback — when IMS/VoLTE is unavailable, device falls back to CS voice call on 3G/2G correctly.

**Tags:** csfb, fallback, 3g, gsm, volte, degradation, ims

**Devices:**
- UE: Android (device under test)
- MT: Android (any carrier)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

CSFB is the fallback mechanism when VoLTE is unavailable.
The device must detect IMS unavailability and automatically route the call
through the CS domain. This validates:
- Device correctly identifies IMS unavailability
- Call is placed via CSFB (device moves from LTE to 3G/2G for CS call)
- Call audio works on CS domain (AMR-NB codec)
- Device returns to LTE for data after call ends
- No permanent degradation of IMS after CSFB call

## Test Procedure

1. Reserve UE (Android) and MT (Android) from Perfecto.
2. Verify both devices are on LTE. Log PASS/FAIL.

**Phase 1 — Simulate IMS unavailability:**
3. Force UE to use 3G/WCDMA only (disable LTE) using network_set_type.
4. Wait 10 seconds for network transition.
5. Verify UE is now on WCDMA. Log PASS/FAIL.

**Phase 2 — CS fallback call:**
6. UE calls MT.
7. Wait for MT to show ringing state (timeout 20 seconds). Log PASS/FAIL.
8. MT answers.
9. Verify UE and MT show active. Log PASS/FAIL.
10. Verify UE is on WCDMA/GSM (CS domain, not LTE). Log PASS/FAIL.
11. Wait 15 seconds to confirm stable CS call.

**Phase 3 — Teardown and LTE recovery:**
12. UE ends the call. Verify both reach idle. Log PASS/FAIL.
13. Restore UE to LTE using network_set_type.
14. Wait 15 seconds for LTE re-attachment and IMS re-registration.
15. Verify UE is back on LTE. Log PASS/FAIL.

**Phase 4 — VoLTE functional after CSFB:**
16. UE calls MT again on LTE.
17. MT answers. Verify both show active (VoLTE call restored). Log PASS/FAIL.
18. UE ends the call. Verify both reach idle. Log PASS/FAIL.

19. Fetch execution reports. Release both devices.

## Pass Criteria

- UE transitions to 3G/WCDMA correctly
- Call establishes on CS domain (no VoLTE)
- UE returns to LTE after CSFB call ends
- VoLTE call works correctly after CSFB event (IMS not degraded)

## Notes

- This test simulates CSFB by forcing network type — in the field, CSFB is triggered by IMS registration failure or network signaling
- True CSFB behavior (network-initiated fallback via SIP 380 Alternative Service) requires network cooperation — this test validates device-side behavior
- If UE does not return to LTE after the CSFB call, network_set_type should force it back — note if automatic LTE recovery failed
- CSFB + E911 is a separate but critical test: emergency call must succeed even when VoLTE fails
