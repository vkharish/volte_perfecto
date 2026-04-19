# Hold Resume

**Description:** Bidirectional hold and resume call flow — MO side holds then MT side holds, verifying correct state transitions each way.

**Tags:** volte, hold, resume, bidirectional

**Devices:**
- MO: Android
- MT: iOS

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

That hold and resume signaling (re-INVITE with sendonly/recvonly) works correctly
when initiated from either side of a VoLTE call.

## Test Procedure

1. Reserve Android device (label: MO) and iOS device (label: MT) from Perfecto.
2. Verify both are on LTE. Log PASS/FAIL.
3. MO calls MT. MT answers. Verify both show active. Log PASS/FAIL.
4. MO places call on hold. Verify MO shows held. Log PASS/FAIL.
5. MO resumes call. Verify both show active. Log PASS/FAIL.
6. MT places call on hold. Verify MT shows held. Log PASS/FAIL.
7. MT resumes call. Verify both show active. Log PASS/FAIL.
8. MO ends the call. Verify both show idle. Log PASS/FAIL.
9. Release both devices.

## Pass Criteria

- Each hold transitions correctly to held state on the initiating device
- Each resume returns both devices to active state
- No call drops during any hold/resume cycle

## Notes

- Test both directions (step 4 and step 6) to catch asymmetric IMS issues
- A FAIL on MT-initiated hold often points to different SIP stack behavior on iOS
