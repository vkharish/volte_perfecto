# MO MT Basic Call

**Description:** End-to-end VoLTE call between a Mobile Originating (Android) and Mobile Terminating (iOS) device, including hold and resume.

**Tags:** volte, mo, mt, basic, call, hold, resume

**Devices:**
- MO: Android (any carrier)
- MT: iOS (any carrier)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

A complete VoLTE call lifecycle between two devices on different platforms:
- IMS registration and LTE attachment on both devices
- Successful call origination (MO) and termination (MT)
- Call state transitions: idle → ringing → active → held → active → idle
- Proper signaling for hold and resume (re-INVITE flows)

## Test Procedure

1. Reserve one Android device (label: MO) and one iOS device (label: MT) from Perfecto.
2. Check network info on both devices — verify LTE network type (not WiFi, not 3G). Log PASS/FAIL for each.
3. Start screen recording on both devices for certification evidence.
4. MO device dials the MT device's assigned phone number.
5. Wait for MT device to reach ringing state (timeout 30 seconds). Log PASS/FAIL.
6. MT device answers the call.
7. Wait for both devices to show active state (timeout 30 seconds). Log PASS/FAIL.
8. MO device places the call on hold.
9. Verify MO shows held state. Log PASS/FAIL.
10. MO device resumes the call.
11. Verify both devices return to active state. Log PASS/FAIL.
12. MO device ends the call.
13. Verify both devices return to idle state. Log PASS/FAIL.
14. Stop screen recordings on both devices.
15. Fetch execution reports for both devices.
16. Release both devices.

## Pass Criteria

- Both devices confirm LTE before the call
- MT rings within 30 seconds of MO dialing
- Both devices reach active state within 30 seconds of answer
- MO transitions to held after hold command
- Both devices return to active after resume
- Both devices return to idle after call end

## Notes

- If MT does not ring within 30 seconds, check IMS registration status before retrying
- Hold/resume failures often indicate re-INVITE signaling issues at the IMS core
