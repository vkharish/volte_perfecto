# Roaming VoLTE

**Description:** Verify VoLTE works when device is roaming on a visited network — S8HR or LBO roaming architecture, IMS registration via home network.

**Tags:** volte, roaming, s8hr, lbo, ims, visited-network, hplmn, vplmn

**Devices:**
- ROAMING_UE: Android (home carrier SIM, roaming on visited network)
- MT: Android (home carrier, on home network)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

VoLTE roaming has two architectures:
- **S8HR (Home Routed)**: All IMS signaling and media goes through home IMS core. More common.
- **LBO (Local Breakout)**: UE registers with visited IMS. Rarer, carrier-specific.

This test validates S8HR by default (LBO noted separately).
Key validations:
- Roaming UE can register with home IMS core via visited network
- VoLTE call from roaming UE to home-network MT establishes correctly
- Home network MT can call the roaming UE (MT roaming)
- Hold/resume works over the S8HR path (longer RTT may affect re-INVITE)

## Test Procedure

1. Reserve ROAMING_UE (Android, home carrier SIM in visited network) and MT (Android, home network) from Perfecto.
2. Verify ROAMING_UE is showing roaming indicator and LTE. Log PASS/FAIL.
3. Verify MT is on LTE on home network. Log PASS/FAIL.

**Phase 1 — IMS registration check on roaming device:**
4. Verify ROAMING_UE network info shows LTE and roaming. Log PASS/FAIL.
5. Wait 15 seconds for IMS registration over roaming path.

**Phase 2 — MO from roaming device:**
6. ROAMING_UE calls MT (home network).
7. Wait for MT to reach ringing state (timeout 45 seconds — roaming path latency). Log PASS/FAIL.
8. MT answers. Verify both show active. Log PASS/FAIL.
9. Wait 15 seconds to confirm stable roaming VoLTE call.

**Phase 3 — Hold/resume over roaming path:**
10. ROAMING_UE places call on hold. Verify held state. Log PASS/FAIL.
11. Wait 5 seconds.
12. ROAMING_UE resumes. Verify both active. Log PASS/FAIL.

**Phase 4 — Teardown:**
13. ROAMING_UE ends the call. Verify both reach idle. Log PASS/FAIL.

**Phase 5 — MT calling roaming device:**
14. MT (home network) calls ROAMING_UE (roaming).
15. Wait for ROAMING_UE to ring (timeout 45 seconds). Log PASS/FAIL.
16. ROAMING_UE answers. Verify both show active. Log PASS/FAIL.
17. Wait 10 seconds.
18. MT ends the call. Verify both reach idle. Log PASS/FAIL.

19. Fetch execution reports. Release both devices.

## Pass Criteria

- Roaming UE shows LTE + roaming indicator
- VoLTE call from roaming UE establishes within 45 seconds
- Hold/resume works over S8HR roaming path
- MT can successfully call the roaming UE (inbound to roaming works)
- All devices reach idle cleanly

## Notes

- Roaming VoLTE requires VPLMN to support PS handover and home IMS routing — confirm lab simulates roaming correctly
- If ROAMING_UE falls back to CSFB when roaming (no VoLTE), the VPLMN does not support VoLTE roaming — this is a network gap, not a device failure
- Hold/resume latency over S8HR is higher than on-net — increase wait times by 2–3 seconds per step
- For LBO testing: UE must detect VPLMN supports VoLTE and register with visited IMS — requires specific network configuration
- Roaming surcharges apply to real SIM cards — confirm lab uses test SIMs with roaming emulation to avoid billing
