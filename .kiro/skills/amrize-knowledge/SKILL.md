---
name: amrize-knowledge
description: |
  Amrize BP knowledge base for SAP ECC development decisions.
  Use when planning, designing, implementing, or reviewing ABAP developments,
  change requests (CHG), WRICEF objects, Mulesoft/Salesforce integrations,
  enhancement spots, FM facades, OO architecture, or deploy workflows.
  Provides naming conventions, coding standards, SOLID patterns, S/4HANA readiness
  rules, deploy workflow, and system table references — all validated in production.
license: GPL-3.0
metadata:
  version: 1.0.0
  last_updated: "2026-08-05"
  target_system: "SAP ECC 6.0 EHP8 / BZD 130"
  company: "Amrize BP (Building Envelope division)"
---
# Amrize BP — Knowledge Base for SAP Development

## When to Consult This Knowledge

Use this reference BEFORE writing any ABAP code for Amrize. It contains:
- Architecture decisions (mandatory OO patterns)
- Naming conventions (prefixes, variables, packages)
- Coding standards (what's required, what's prohibited)
- Deploy workflow (OT rules, verification steps)
- S/4HANA readiness (tables to avoid, syntax to use)
- System tables (verified field lists for CTS, workbench, FMs)
- Integration patterns (Mulesoft RFC, SPROXY, IDocs)

---

## 1. System Context

- **Company**: Amrize BP (formerly Holcim BP) — construction materials
- **System**: BZD — SAP ECC 6.0 EHP8 (client 130), ABAP 7.50 SP19
- **Database**: Non-HANA (traditional DB)
- **NOT available**: S/4HANA, ABAP Cloud, AMDP, RAP, and any CDS feature requiring HANA (OLAP/analytics annotations, HANA-specific SQL functions, code pushdown)
- **Available with limitations**: Classic ABAP CDS view entities (DEFINE VIEW ENTITY) — usable without HANA for standard read views/associations
- **CTS**: Project Management active — OTs must be created manually in SE09
- **Sandbox**: BZN (client 100) — available via MCP
- **Modules**: SD, MM, FI, PP, WM + CRM ↔ ECC + Salesforce via Mulesoft

### EHP8 Known Impacts
- SAPconnect assigns SCOMNO immediately on transmit (was deferred)
- Stricter authority checks in standard FMs (MD_STOCK_REQUIREMENTS_LIST_API)
- VBUK/VBUP behavior changes (S/4 preparation)
- **Validated pattern**: Use TVARVC as date switch to protect legacy behavior

---

## 2. Architecture Decision (Non-Negotiable)

> All NEW code is written in ABAP OO classes.
> Legacy code (FORMs, procedural includes) is NOT refactored — only extended by calling the new class.
> All new logic must be testable with ABAP Unit from day one.

### Mandatory Layer Architecture
```
Entry Point (FORM / Enhancement / FM / BAdI / SPROXY handler)
  └─ ZCL_<MOD>_<PROCESS>           ← orchestrator (pure business logic)
       ├─ ZIF_<MOD>_<PROCESS>_DAO
       │    └─ ZCL_<MOD>_<PROCESS>_DAO   (DB access — only SELECTs here)
       └─ ZIF_<MOD>_<PROCESS>_CHK
            └─ ZCL_<MOD>_<PROCESS>_CHK   (business rules / validations)

Tests (ZCL_<MOD>_<PROCESS>_TEST):
  ├─ LCL_DAO_DOUBLE    (simulates DB — no real table access)
  └─ LCL_CHK_DOUBLE    (simulates business rules)
```

**Golden rule**: The orchestrator NEVER does direct SELECT — always delegates to DAO via interface.

### Dependency Injection (Mandatory)
```abap
CLASS zcl_sd_pricing DEFINITION FINAL.
  PUBLIC SECTION.
    METHODS constructor
      IMPORTING
        io_dao TYPE REF TO zif_sd_pricing_dao OPTIONAL
        io_chk TYPE REF TO zif_sd_pricing_chk OPTIONAL.
  PRIVATE SECTION.
    DATA mo_dao TYPE REF TO zif_sd_pricing_dao.
    DATA mo_chk TYPE REF TO zif_sd_pricing_chk.
ENDCLASS.

CLASS zcl_sd_pricing IMPLEMENTATION.
  METHOD constructor.
    mo_dao = COND #( WHEN io_dao IS BOUND THEN io_dao ELSE NEW zcl_sd_pricing_dao( ) ).
    mo_chk = COND #( WHEN io_chk IS BOUND THEN io_chk ELSE NEW zcl_sd_pricing_chk( ) ).
  ENDMETHOD.
ENDCLASS.
```

---

## 3. Naming Conventions

### Object Prefixes
| Object | Pattern | Example |
|--------|---------|---------|
| Orchestrator class | `ZCL_<MOD>_<PROCESS>` | `ZCL_SD_PRICING` |
| DAO class | `ZCL_<MOD>_<PROCESS>_DAO` | `ZCL_SD_PRICING_DAO` |
| Checker class | `ZCL_<MOD>_<PROCESS>_CHK` | `ZCL_SD_PRICING_CHK` |
| DAO interface | `ZIF_<MOD>_<PROCESS>_DAO` | `ZIF_SD_PRICING_DAO` |
| Checker interface | `ZIF_<MOD>_<PROCESS>_CHK` | `ZIF_SD_PRICING_CHK` |
| Test class | `ZCL_<MOD>_<PROCESS>_TEST` | `ZCL_SD_PRICING_TEST` |
| Test double (local) | `LCL_<OBJ>_DOUBLE` | `LCL_DAO_DOUBLE` |
| FM facade (RFC) | `ZFM_<MOD>_<PROCESS>_<ACTION>` | `ZFM_SD_PRICING_GET` |
| Program/Report | `Z` or `ZR_` | `ZR_SD_QUICK_ORDERS` |
| Function Group | `ZFG_` | `ZFG_SD_STOCK_QUERY` |
| Table Z | `ZTAB_` | `ZTAB_SD_PRICING_EXT` |
| Structure DDIC | `ZST_` | `ZST_SD_PLANT_STOCK` |
| Table Type DDIC | `ZTY_` | `ZTY_SD_PLANT_STOCK_T` |

### Module Prefix (mandatory to avoid BZD collisions)
- `ZSD_` — Sales & Distribution
- `ZMM_` — Materials Management
- `ZFI_` — Finance
- `ZPP_` — Production Planning
- `ZWM_` — Warehouse Management

### Variable Prefixes
| Scope | Object | Value | Table | Structure |
|-------|--------|-------|-------|-----------|
| Instance | `mo_` | `mv_` | `mt_` | `ms_` |
| Local | `lo_` | `lv_` | `lt_` | `ls_` |
| Parameter | `io_`/`eo_` | `iv_`/`ev_` | `it_`/`et_` | — |
| Changing | — | — | `ct_` | `cs_` |
| Class constant | — | `gc_` | — | — |

### Development Packages
- `ZSD_SF` — SD integrations with Salesforce/Mulesoft
- `ZDEV_SD` — general SD developments
- `$TMP` — POCs only (never production)

---

## 4. Coding Standards

### REQUIRED
- Every business class → `_TEST` class with ABAP Unit
- Public methods → ABAP Doc (`"! description`)
- All comments in code → ENGLISH
- Modern ABAP 7.5 syntax: VALUE, FILTER, REDUCE, inline DATA()
- Explicit exception handling (never `EXCEPTIONS others = 0` unhandled)
- Tables declared with `TYPE TABLE OF [FULL_TYPE]`
- ENQUEUE/DEQUEUE before change BAPIs
- RFC FMs use LIKE in Tables tab (not TYPE with table type)
- Change markers: `" +CHGxxxxxxx — BEGIN` / `" +CHGxxxxxxx — END`

### PROHIBITED
- Untyped FIELD-SYMBOLS
- `SELECT *` — always list fields
- Direct standard table modification (use Enhancement/BAdI)
- Hard-coded client (use SY-MANDT)
- `COMMIT WORK` in business logic (only at process controller level)
- `DO...ENDDO + EXIT` — use WHILE with explicit condition
- New FORMs (PERFORM/FORM) — use class methods
- SELECT inside LOOPs — use FOR ALL ENTRIES or JOIN

### Validated Production Patterns
- **TVARVC date switch** for legacy protection after EHP8 upgrades
- **Enqueue with retries** (WHILE + WAIT UP TO 5 SECONDS) before BAPIs
- **MESSAGE TYPE 'E'** for Workflow integration (puts work item in ERROR state)
- **Authority check replication** before FMs with internal auth checks

### Lessons Learned
- FOR ALL ENTRIES requires identical types (`TYPE dbtab-field`, not loose data elements)
- ADT activation ≠ syntax check (always run `sap_syntax_check` after activate)
- `VALUE #()` with `LET` + table expression `OPTIONAL` is unstable — use classic LOOP fallback
- EISBE is in MARC, not MARD

---

## 5. Integration Patterns

### Pattern 1 — From FORM/Include (most common)
Add testable logic without touching existing FORM:
```abap
FORM calcular_precio USING iv_matnr TYPE matnr.
  " ... existing legacy — do not modify ...
  " +CHG04XXXXX — BEGIN
  DATA(lo_pricing) = NEW zcl_sd_pricing( ).
  DATA(lv_discount) = lo_pricing->get_discount( iv_matnr ).
  " +CHG04XXXXX — END
ENDFORM.
```

### Pattern 2 — Enhancement Spot Include (facade)
Include maps globals → own types → calls orchestrator → writes back:
```abap
" 1. Map globals to own types
DATA(ls_input) = VALUE zcl_sd_proceso=>ty_input( matnr = vbap-matnr werks = vbap-werks ).
" 2. Execute OO logic
DATA(lo_handler) = NEW zcl_sd_proceso( ).
DATA(ls_result) = lo_handler->execute( ls_input ).
" 3. Write result back to globals
IF ls_result-success = abap_true.
  vbap-werks = ls_result-werks.
ENDIF.
```
> The orchestrator NEVER touches program global variables.

### Pattern 3 — FM RFC Facade (for Mulesoft)
FM only instantiates and delegates. All logic in testable OO class:
```abap
FUNCTION zfm_sd_pricing_get.
  TRY.
      DATA(lo_query) = NEW zcl_sd_pricing( ).
      et_result[] = lo_query->get_pricing( iv_matnr = iv_matnr iv_vkorg = iv_vkorg ).
    CATCH cx_root INTO DATA(lx_error).
      APPEND VALUE bapiret2( type = 'E' message = lx_error->get_text( ) ) TO et_messages[].
  ENDTRY.
ENDFUNCTION.
```
- Always return `et_messages TYPE bapiret2_t` for Mulesoft error reading

### Pattern 4 — SPROXY / IDoc Handler → OO
Proxy method or IDoc FM instantiates handler class and delegates.
- Retry errors: `CX_AI_SYSTEM_FAULT`
- Business errors (no retry): `CX_AI_APPLICATION_FAULT`

---

## 6. Deploy Workflow

### Controlled Flow
```
1. Developer creates OT in SE09 (correct CTS project)
2. Developer provides OT number to Kiro
3. Kiro reads current code from SAP (baseline for diff)
4. Kiro generates new code locally
5. Developer reviews diff
6. Kiro uploads code to SAP with provided OT
7. Kiro activates the object
8. Kiro runs syntax check (sap_syntax_check) — activation ≠ compilation
9. Kiro reads code back to verify
```

### Deploy Order for New Developments
```
1. ZIF_<MOD>_<PROCESS>_DAO    — DAO interface (no dependencies)
2. ZIF_<MOD>_<PROCESS>_CHK    — checker interface (if applicable)
3. ZIF_<MOD>_<PROCESS>        — orchestrator interface (if applicable)
4. ZCL_<MOD>_<PROCESS>_DAO    — DAO implementation
5. ZCL_<MOD>_<PROCESS>_CHK    — checker implementation
6. ZCL_<MOD>_<PROCESS>        — orchestrator
7. ZCL_<MOD>_<PROCESS>_TEST   — test class → run ABAP Unit → must pass
8. Entry point (FM / include / BAdI / SPROXY) — LAST, when tests pass
```

### OT Rules
- Always provide OT explicitly (ADT API doesn't support CTS project assignment)
- Create OT BEFORE asking Kiro to upload
- `$TMP` only for POCs
- Review ALL tasks within an OT (objects are in tasks, not in request header)
- One object at a time — upload, verify, next

### Technical Notes
- FM source endpoint rejects local interface comment blocks (`*"------`)
- ABAP Unit via ADT doesn't detect local test classes in reports — only global classes (ZCL_*)
- Activation types: PROG/P, PROG/I, FUGR/FF, CLAS/OC, INTF/OI

---

## 7. S/4HANA Readiness

### Tables NOT to Use in New Code
| Don't Use | Use Instead | Reason |
|-----------|-------------|--------|
| VBUK | Status fields in VBAK | Eliminated in S/4 |
| VBUP | Status fields in VBAP | Eliminated in S/4 |
| KONV | PRCD_ELEMENTS | Replaced |
| BSEG (as real table) | ACDOCA | Universal Journal |
| MSEG, MKPF | MATDOC | New material document |
| FAGLFLEXA, FAGLFLEXT | ACDOCA | Eliminated |

### Field Traps
- EISBE (safety stock) is in MARC, NOT MARD
- MATNR will be 40 chars in S/4 (currently 18) — don't assume fixed length
- KUNNR/LIFNR replaced by Business Partner (BUPA) in S/4

### Mandatory Modern Syntax (all new code)
- `DATA()` / `FIELD-SYMBOL()` inline declarations
- `VALUE #()` for table/structure construction
- `NEW #()` instead of CREATE OBJECT
- Functional method calls `obj->method()` instead of CALL METHOD
- `@` host variables in Open SQL
- `COND` / `SWITCH` for simple assignments
- `FILTER #()` instead of LOOP+APPEND for filtering
- `REDUCE` for aggregations
- `xsdbool()` for boolean expressions

---

## 8. System Tables — Verified Fields (BZD 130)

These tables are pool/cluster tables NOT accessible via ADT DDIC endpoint.
Fields verified against real system.

### E070 — Transport Request Header
```
TRKORR, TRFUNCTION, TRSTATUS, TARSYSTEM, AS4USER, AS4DATE, AS4TIME, STRKORR
```
**NOTE: E070 does NOT have AS4TEXT.** Description is in E07T.

### E07T — Transport Request Texts
```
TRKORR, LANGU, AS4TEXT
```

### E071 — Objects in Transport Requests
```
TRKORR, AS4POS, PGMID, OBJECT, OBJ_NAME
```

### TRDIR — Program Directory
```
NAME, SUBC, UDAT, UNAM
```

### TADIR — Repository Object Catalog
```
PGMID, OBJECT, OBJ_NAME, DEVCLASS, AUTHOR
```

### TFDIR — Function Module Directory
```
FUNCNAME, PNAME, INCLUDE, STEXT
```

### DWINACTIV — Inactive Workbench Objects
```
OBJECT, OBJ_NAME, UNAME, UDATE
```
**NOTE: DWINACTIV does NOT have PGMID or OBJ_TYPE.**

### Open SQL Rules for These Tables
1. Use classic syntax (no `@`) for pool/cluster tables — new syntax can fail in ABAP 7.50
2. Don't use string templates in WHERE — use CONCATENATE prior
3. Prefer standard FMs (RS_GET_ALL_INCLUDES, TR_READ_REQUEST) over direct SELECTs
4. Never assume fields — if not listed here, verify in SE11 first

---

## 9. Testability Rules (Non-Negotiable)

1. Every public method has at least one test in `ZCL_<MOD>_<PROCESS>_TEST`
2. Tests do NOT access real DB — use doubles to simulate data
3. Test doubles are local classes (`LCL_*_DOUBLE`) inside the test class — not deployed to production
4. Tests run BEFORE modifying the legacy entry point
5. A passing test = OO logic is correct = safe to plug into legacy

---

## 10. Reference Architectures

### FM Facade (ConsultaStockMaterial)
```
ZFM_SD_GET_MATERIAL_STOCK (FM RFC — facade)
  └─ ZCL_SD_STOCK_QUERY (orchestrator)
       ├─ ZIF_SD_STOCK_DAO → ZCL_SD_STOCK_DAO (data access)
       └─ ZIF_SD_EXCLUSION_CHECKER → ZCL_SD_EXCLUSION_CHECKER (rules)
Tests: ZCL_SD_STOCK_QUERY_TEST + LCL_DAO_DOUBLE + LCL_EXCLUSION_DOUBLE
```

### Enhancement Include (SD_E_112 Plant Determination)
```
ZI_SD_E_112_PLANT_DETERMINE (include — facade, maps globals ↔ own types)
  └─ ZCL_SD_PLANT_DETERMINATOR (orchestrator — receives/returns own types)
       ├─ ZIF_SD_PLANT_DET_DAO → ZCL_SD_PLANT_DET_DAO
       └─ ZIF_SD_ENH_STATUS_CHECKER → ZCL_SD_ENH_STATUS_CHECKER
Tests: ZCL_SD_PLANT_DETERMINATOR_TEST + LCL_DAO_DOUBLE + LCL_ENH_DOUBLE
```

Key difference vs FM facade: include must **read globals at start** and **write results back at end**. Orchestrator never touches program globals.
