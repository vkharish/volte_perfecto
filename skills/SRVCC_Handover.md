# SRVCC Handover

**Description:** Verify Single Radio Voice Call Continuity — active VoLTE call handed over to WCDMA/GSM mid-call without drop.

**Tags:** srvcc, handover, volte, 3g, gsm, continuity, lte

**Devices:**
- UE: Android (carrier with SRVCC support)
- MT: Android (any carrier)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

When a VoLTE device moves out of LTE coverage during an active call, the IMS session
must hand over to the CS (circuit-switched) domain via SRVCC without dropping the call.
This validates:
- STN-SR (Session Transfer Number for SR-VCC) provisioning is correct
- IMS core sends SIP REFER to transfer the session to CS
- Device completes the handover within the ITU-T threshold (~300ms audio gap)
- Audio codec transitions from AMR-WB (VoLTE) to AMR-NB (CS voice)

## Test Procedure

1. Reserve UE (Android) and MT (Android) from Perfecto.
2. Verify both devices are on LTE. Log PASS/FAIL.
3. Start screen recording on UE for certification evidence.
4. UE calls MT. MT answers. Verify both devices show active state. Log PASS/FAIL.
5. Wait 10 seconds to confirm stable VoLTE call.
6. Force UE from LTE to WCDMA using network_set_type (simulate LTE coverage loss).
7. Wait 5 seconds for SRVCC handover to complete.
8. Verify UE call state is still active (call did not drop). Log PASS/FAIL.
9. Verify UE is now on WCDMA network via network_get_info. Log PASS/FAIL.
10. Wait 15 seconds to confirm call stability on CS domain.
11. Restore UE to LTE using network_set_type.
12. Wait 10 seconds for LTE re-attachment.
13. UE ends the call. Verify both devices return to idle. Log PASS/FAIL.
14. Stop recording on UE. Fetch execution reports.
15. Release both devices.

## Pass Criteria

- Call remains active through LTE → WCDMA transition (no drop)
- UE shows WCDMA network after handover
- Call stable on CS domain for at least 15 seconds post-handover
- Both devices reach idle cleanly after call end

## Notes

- SRVCC requires STN-SR to be provisioned in HSS — if call drops immediately on LTE removal, check provisioning
- Audio gap during handover should be imperceptible (<300ms) — Perfecto cannot measure this, verify via network logs
- Some Android devices require `network_set_type` to force 3G; check device capabilities in list_devices
- If WCDMA is unavailable in the lab, use GSM (2G) as the CS fallback target
- This test is the most critical for carrier certification — a FAIL here blocks the entire certification
