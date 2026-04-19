# iOS MO Android MT

**Description:** Verify VoLTE call parity with iOS as the originating party and Android as the terminating party — reverse direction of MO_MT_Basic_Call.

**Tags:** volte, ios, android, mo, mt, parity, cross-platform

**Devices:**
- MO: iOS (originating)
- MT: Android (terminating)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

IMS bugs are often asymmetric between platforms. iOS uses Apple's proprietary
SIP/IMS stack; Android uses the OEM-customized IMS stack. Running the call in
reverse direction catches:
- iOS MO post-dial delay (PDD) differences vs Android MO
- iOS hold signaling (re-INVITE) behavior when iOS initiates
- Android MT behavior when receiving a call from iOS (different SDP offer format)
- iOS-to-Android codec negotiation (AMR-WB preference order)

## Test Procedure

1. Reserve MO (iOS) and MT (Android) from Perfecto.
2. Verify both devices are on LTE. Log PASS/FAIL.
3. Start screen recording on both devices.

**Phase 1 — Basic call (iOS → Android):**
4. MO (iOS) calls MT (Android) phone number.
5. Wait for MT to show ringing state (timeout 30 seconds). Log PASS/FAIL.
6. MT (Android) answers.
7. Verify both show active. Log PASS/FAIL.
8. Wait 10 seconds to confirm stable call.

**Phase 2 — Hold from iOS side:**
9. MO (iOS) places call on hold.
10. Verify MO shows held. Log PASS/FAIL.
11. Verify MT shows held/remote-hold. Log PASS/FAIL.
12. Wait 5 seconds.
13. MO (iOS) resumes call.
14. Verify both show active. Log PASS/FAIL.

**Phase 3 — Hold from Android side:**
15. MT (Android) places call on hold.
16. Verify MT shows held. Log PASS/FAIL.
17. MT (Android) resumes call.
18. Verify both show active. Log PASS/FAIL.

**Phase 4 — DTMF from iOS:**
19. MO (iOS) sends DTMF digits: 1, 2, 3.
20. Verify call stays active. Log PASS/FAIL.

**Phase 5 — Teardown:**
21. MT (Android) ends the call. Verify both reach idle. Log PASS/FAIL.
22. Stop recordings. Fetch execution reports.
23. Release both devices.

## Pass Criteria

- iOS MO call reaches Android MT ringing state within 30 seconds
- Both devices reach active state within 30 seconds of answer
- iOS-initiated hold transitions correctly on both devices
- Android-initiated hold transitions correctly on both devices
- DTMF from iOS does not drop the call
- Both devices reach idle cleanly

## Notes

- Compare results with MO_MT_Basic_Call (Android → iOS) — any asymmetry indicates platform-specific IMS behavior
- iOS PDD (post-dial delay) is often longer than Android — if ringing timeout fails, increase from 30 to 45 seconds for iOS
- iOS sends SDP with different codec preference order — Android MT must negotiate correctly (AMR-WB preferred)
- MT-ends-call (step 21) is intentional — this tests Android MT teardown initiated from Android side
