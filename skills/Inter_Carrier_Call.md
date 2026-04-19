# Inter Carrier Call

**Description:** Verify VoLTE call between devices on different carriers — validates IMS peering, codec negotiation, and signaling across carrier boundaries.

**Tags:** volte, inter-carrier, peering, ims, att, verizon, tmobile

**Devices:**
- MO: Android (Carrier A — e.g. AT&T)
- MT: Android (Carrier B — e.g. Verizon)

**Version:** 1.0
**Author:** Lab Team

---

## What This Test Validates

Inter-carrier VoLTE calls traverse IMS peering points (IBCFs/TrGWs).
This introduces additional failure points not present in on-net calls:
- IBCF codec transcoding (AMR-WB → AMR-NB if peering is narrowband)
- SIP header manipulation at the peering point
- Different ring tones and call progress treatment across carriers
- Hold/resume across peering (re-INVITE must traverse IBCF)
- Post-dial delay at inter-carrier peering point

## Test Procedure

1. Reserve MO (Android, Carrier A) and MT (Android, Carrier B) from Perfecto.
   Use operator filter to select specific carriers.
2. Verify MO is on LTE on Carrier A. Log PASS/FAIL.
3. Verify MT is on LTE on Carrier B. Log PASS/FAIL.

**Phase 1 — Basic inter-carrier call:**
4. MO calls MT (cross-carrier).
5. Wait for MT to reach ringing state (timeout 45 seconds — inter-carrier PDD is longer). Log PASS/FAIL.
6. MT answers. Verify both show active. Log PASS/FAIL.
7. Wait 15 seconds to confirm stable inter-carrier call.

**Phase 2 — Hold/resume across peering:**
8. MO places call on hold. Verify MO shows held. Log PASS/FAIL.
9. Wait 5 seconds.
10. MO resumes call. Verify both show active. Log PASS/FAIL.

**Phase 3 — MT-side hold:**
11. MT places call on hold. Verify MT shows held. Log PASS/FAIL.
12. MT resumes. Verify both show active. Log PASS/FAIL.

**Phase 4 — DTMF across peering:**
13. MO sends DTMF digits: 1, 2, 3. Verify call stays active. Log PASS/FAIL.

**Phase 5 — Teardown:**
14. MO ends the call. Verify both reach idle. Log PASS/FAIL.

**Phase 6 — Reverse direction (Carrier B → Carrier A):**
15. MT (Carrier B) calls MO (Carrier A).
16. Wait for MO to reach ringing state (timeout 45 seconds). Log PASS/FAIL.
17. MO answers. Verify both show active. Log PASS/FAIL.
18. Wait 10 seconds.
19. MT ends the call. Verify both reach idle. Log PASS/FAIL.

20. Fetch execution reports. Release both devices.

## Pass Criteria

- Inter-carrier call establishes in both directions
- Ringing state reached within 45 seconds (inter-carrier PDD allowance)
- Hold/resume works correctly across carrier peering
- DTMF does not drop the inter-carrier call
- Reverse direction (B→A) also establishes correctly

## Notes

- Use --operator flag to select specific carriers: `python run_skill.py --skill Inter_Carrier_Call --operator "AT&T"` selects MO carrier
- If inter-carrier call fails but on-net calls pass, the issue is at the IBCF peering point — escalate to network peering team
- Codec transcoding at the IBCF may degrade from AMR-WB (HD voice) to AMR-NB — this is acceptable if call connects, but note it in the report
- Some carrier pairs have E.164 number format requirements at the peering point — ensure phone numbers are in +1NPANXXXXXX format
- PDD (post-dial delay) for inter-carrier calls is typically 2–5 seconds longer than on-net — adjust timeout accordingly
