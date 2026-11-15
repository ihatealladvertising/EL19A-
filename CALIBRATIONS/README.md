# Calibration Register Guide

The current engineering source is the V53 workbook, not the early seed CSVs in this repository.

Primary V53 sheets:
- `Theory Handoff 2026-11-15` — provisional family hypotheses and discriminators.
- `Project2 1D Crosswalk`
- `EL19A 1D Lookup Candidates`
- `P2 Candidate Register`
- `P2 Handoff Log`
- `Candidate Evidence Ledger`

The initial `candidate_register.csv` and `EVIDENCE/open_leads.csv` are compact historical seed subsets assembled from earlier project context. They are not a complete inventory and are superseded by the V53 registers. Do not promote their names/scales to confirmed XML semantics.

Current inventory accounting recorded in V53:
- 122 unique V7 `storageaddress` placements.
- 121 rows in the supplied pasted table; the omitted placement was identified as `AD22`.
- 71 unique pointers from 84 `sub_22E10` callsites; all 71 addresses occur in V7.
- Broader screenshot-scope inventory remains 175 = 122 + 53; the 53 expansion entries were not freshly audited in the V53 reconciliation.
- E8C0/E94C remain out-of-V7 review candidates; E880 remains conditional/disputed.
