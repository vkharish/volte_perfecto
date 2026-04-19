# DTMF Tones

**Description:** Verify DTMF tone generation works correctly during an active VoLTE call (e.g. for IVR navigation, call park codes).

**Tags:** volte, dtmf, tones, ivr

**Devices:**
- MO: Android

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

That RFC 4733 DTMF events are correctly sent during a VoLTE call
(in-band tones or RTP telephone-events depending on IMS config).

## Test Procedure

1. Reserve one Android device (label: MO) from Perfecto.
2. Verify MO is on LTE. Log PASS/FAIL.
3. MO dials a test IVR number or lab DTMF sink (e.g. +12125550199). Wait for active state.
4. Send DTMF digits: 1 (wait 1 sec), 2 (wait 1 sec), # (wait 1 sec).
5. Verify no call drop occurred after DTMF sequence — check call state is still active. Log PASS/FAIL.
6. Send longer digit sequence: 1234567890*# (stress test). Verify still active. Log PASS/FAIL.
7. End the call. Verify idle state. Log PASS/FAIL.
8. Release MO device.

## Pass Criteria

- Call remains active throughout DTMF sequence
- No mid-call drops or re-INVITE triggered by DTMF

## Notes

- Actual DTMF reception verification requires server-side IVR log analysis (out of scope here)
- This test only verifies the sending device stays in a healthy call state
- Increase wait between digits if network is congested
