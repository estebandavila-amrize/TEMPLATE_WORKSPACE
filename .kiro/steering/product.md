# Global Product Context

- Objective: Python-based Model Context Protocol (MCP) server interfacing with SAP ECC 6.0 EHP8 (NetWeaver 7.50).
- Business Domain: SAP ECC classic modules (SD, MM, FI, CO, PP, etc.) — no S/4HANA, no Fiori/RAP, no HANA-native features.
- Development Standard: All modifications are tracked via Change Requests (CHGxxxxxx) and WRICEF IDs. Objects must be grouped into designated Z-packages corresponding to their WRICEF ID.
- Available with Limitations: Classic ABAP CDS view entities (non-HANA-specific) — usable without a HANA database.
- Unavailable Technologies: AMDP, RAP/EML, ABAP Cloud, Fiori Elements (annotation-driven), OData V4 via RAP, XCO library, ABAP Environment on BTP, Generative AI SDK, and any CDS feature requiring HANA (OLAP/analytics annotations, HANA-specific SQL functions, code pushdown).
