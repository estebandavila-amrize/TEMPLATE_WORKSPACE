# Global Technical Constraints

- Target Environment: SAP ECC 6.0 EHP8, NetWeaver 7.50, ABAP 7.50. Database: NOT SAP HANA (traditional DB — MaxDB, Oracle, SQL Server, or DB2).
- ABAP Rules: Strict classic ABAP syntax (release 7.50). Inline declarations (DATA(x), FIELD-SYMBOL(<fs>)) are permitted. Constructor expressions (VALUE, NEW, COND, SWITCH, CORRESPONDING, CONV, REF, REDUCE, FILTER) are permitted. String templates |...| are permitted. NO ABAP Cloud / RAP / Steampunk / EML syntax. NO CDS views (not available without HANA). NO AMDP (ABAP-Managed Database Procedures require HANA). NO XCO library. NO FINAL(x) immutable inline declarations (requires ABAP 7.57+).
- SQL Rules: Use Open SQL (not ABAP SQL new syntax). No WITH (CTE) — requires HANA. No HIERARCHY expressions. Use FOR ALL ENTRIES or JOINs for multi-table reads. Aggregate functions (COUNT, SUM, AVG, MIN, MAX) are available.
- DDIC Rules: Use classical Dictionary objects (SE11) — tables, structures, data elements, domains, search helps, lock objects, table types. No DDL-based CDS artifacts.
- Enhancement Rules: Use classic BAdIs, user-exits, enhancement spots, and implicit/explicit enhancement points. No new-style RAP-based extensibility.
- Python MCP Rules: Flat input schemas for tools (no top-level Union, oneOf, or anyOf).
