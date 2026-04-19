# IMS Reregistration

**Description:** Verify that a device re-registers with IMS and restores VoLTE capability after an airplane mode cycle.

**Tags:** ims, reregistration, airplane, recovery, volte

**Devices:**
- UE: Android (any carrier)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

That the IMS stack correctly de-registers when connectivity is lost (airplane mode on)
and fully re-registers when connectivity is restored (airplane mode off),
resulting in a working VoLTE call immediately after recovery.

## Test Procedure

1. Reserve one Android device (label: UE) from Perfecto.
2. Check network info — verify LTE (not WiFi calling). Log PASS/FAIL.
3. Enable airplane mode on UE.
4. Wait 5 seconds for de-registration to complete.
5. Disable airplane mode on UE.
6. Wait 15 seconds for IMS stack to re-register on LTE.
7. Check network info again — verify LTE is restored. Log PASS/FAIL.
8. Make a VoLTE test call from UE to confirm IMS is functional. Dial +12125550100 (or the lab test number).
9. Wait for ringing or active state (timeout 20 seconds). Log PASS/FAIL.
10. End the call. Verify UE returns to idle. Log PASS/FAIL.
11. Release UE device.

## Pass Criteria

- Device shows LTE before and after airplane mode cycle
- VoLTE call succeeds within 20 seconds after re-enabling connectivity
- Device returns to idle cleanly after call end

## Notes

- 15 second re-registration wait is typical; some networks may need up to 30 seconds
- If the call fails after re-registration, check IMS registration via device log (get_device_log)
- This test is a prerequisite check before any SRVCC or handover test
