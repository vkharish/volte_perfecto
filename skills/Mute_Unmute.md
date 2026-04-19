# Mute Unmute

**Description:** Verify mute and unmute during an active VoLTE call — audio path is correctly suppressed and restored, no one-way audio after unmute.

**Tags:** volte, mute, unmute, audio, rtp, one-way-audio

**Devices:**
- MO: Android
- MT: iOS

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

Mute suppresses the local microphone input (or sends silence frames per RFC 3550).
One-way audio after unmute is a common IMS bug where the RTP stream does not
resume correctly after mute is released.
Validates:
- Mute can be applied on either side during active call
- Call state remains active during mute (no drop, no re-INVITE triggered by silence)
- Unmute restores the audio path (no one-way audio)
- Mute during hold does not corrupt state

## Test Procedure

1. Reserve MO (Android) and MT (iOS) from Perfecto.
2. Verify both devices are on LTE. Log PASS/FAIL.

**Phase 1 — MO-side mute:**
3. MO calls MT. MT answers. Verify both show active. Log PASS/FAIL.
4. MO mutes the call.
5. Wait 10 seconds (sustained mute period).
6. Verify call is still active on both devices during mute. Log PASS/FAIL.
7. MO unmutes the call.
8. Verify call is still active after unmute. Log PASS/FAIL.
9. Wait 5 seconds to confirm no delayed drop after unmute. Log PASS/FAIL.

**Phase 2 — MT-side mute:**
10. MT mutes the call.
11. Wait 10 seconds.
12. Verify call is still active on both devices. Log PASS/FAIL.
13. MT unmutes the call.
14. Verify call is still active after unmute. Log PASS/FAIL.

**Phase 3 — Mute + hold interaction:**
15. MO mutes the call.
16. MO places the call on hold.
17. Verify MO shows held. Log PASS/FAIL.
18. MO resumes the call.
19. Verify both devices show active. Log PASS/FAIL.
20. MO unmutes. Verify still active. Log PASS/FAIL.

**Phase 4 — Teardown:**
21. MO ends the call. Verify both reach idle. Log PASS/FAIL.
22. Fetch execution reports. Release both devices.

## Pass Criteria

- Call remains active throughout all mute periods
- No call drop triggered by silence frames during mute
- Call active immediately after unmute on both sides
- Mute + hold combination does not corrupt call state
- No one-way audio condition after any unmute (state remains active with no re-INVITE timeout)

## Notes

- Perfecto cannot verify actual audio content — state checks confirm the signaling plane only; one-way audio must be verified separately via audio analysis or network capture
- If call drops exactly at 20 seconds of mute, the IMS core has a RTP inactivity timer set to 20s — report to network team
- Android mute behavior: typically sends CNG (comfort noise) or silence RTP frames
- iOS mute behavior: may send DTX (discontinuous transmission) — either is acceptable per RFC 3550
- This test pairs with DTMF_Tones — DTMF during mute is a separate edge case worth testing
