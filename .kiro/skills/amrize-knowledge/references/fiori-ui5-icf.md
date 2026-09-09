# Fiori / SAPUI5 apps on SAP CRM 7.0 EHP4 (non-HANA) — JSON-over-ICF pattern

Validated in production system BZA (CRM 7.0 EHP4, NW 7.50, non-HANA) during the
CRM Claims/Service-Order DOA approval app (`ZCRM_CLAIM_APPR`). This is the reference
for building custom UI5 apps on classic CRM/ECC without Gateway/SEGW/RAP.

---

## 1. Architecture decision — why JSON-over-ICF, not OData/SEGW

On this landscape, **do NOT use SEGW/OData or RAP**:
- SEGW global DPC/MPC generation hits `GEN_DUPLICATE_ENTRY` (SAP Note 2289003) on this release.
- RAP/OData V4 is not available (no ABAP Cloud, non-HANA).

**Chosen pattern (works reliably):** a custom UI5 app that talks to a plain
**ICF handler class** returning/consuming **JSON**.

```
UI5 app (BSP repository)  ──HTTP GET/POST (JSON)──▶  ICF node /sap/bc/z_<app>
                                                        └─ ZCL_..._SRV  (implements IF_HTTP_EXTENSION)
```

- GET  → returns a JSON list (`{ "items": [ ... ] }`).
- POST → receives a JSON decision payload, performs the real business action, returns `{ "success": true/false, ... }`.
- JSON (de)serialization: `/ui2/cl_json=>serialize / deserialize` with
  `pretty_name = /ui2/cl_json=>pretty_mode-camel_case` (ABAP snake_case ⇄ JS camelCase).

---

## 2. Object inventory (what a full app needs)

| Object | Type | Purpose |
|--------|------|---------|
| `ZCL_<APP>_SRV` | CLAS/OC | ICF handler, `IF_HTTP_EXTENSION~HANDLE_REQUEST` |
| SICF node `/sap/bc/z_<app>` | SICF service | REST endpoint (handler class assigned) |
| BSP application `Z<APP>` | BSP (UI5 repo) | UI5 webapp files, loaded via `/UI5/UI5_REPOSITORY_LOAD` |
| Config table(s) `Z...` | TABL | Parametric config (e.g. thresholds) — customizing class C, editable by SM30/SE16 |
| Audit table `Z..._AUDIT` | TABL | Who/what/when/why of each action |

Handler + config/audit tables live in the WRICEF Z-package.

---

## 3. ICF handler skeleton (validated)

```abap
CLASS zcl_app_srv DEFINITION PUBLIC FINAL CREATE PUBLIC.
  PUBLIC SECTION.
    INTERFACES if_http_extension.
  PRIVATE SECTION.
    METHODS handle_list     IMPORTING io_server TYPE REF TO if_http_server.
    METHODS handle_decision IMPORTING io_server TYPE REF TO if_http_server.
    METHODS set_cors        IMPORTING io_server TYPE REF TO if_http_server.
ENDCLASS.

CLASS zcl_app_srv IMPLEMENTATION.
  METHOD if_http_extension~handle_request.
    DATA lv_method TYPE string.
    set_cors( server ).
    lv_method = server->request->get_header_field( '~request_method' ).
    CASE lv_method.
      WHEN 'OPTIONS'. server->response->set_status( code = 200 reason = 'OK' ).  " CORS preflight
      WHEN 'GET'.     handle_list( server ).
      WHEN 'POST'.    handle_decision( server ).
      WHEN OTHERS.    server->response->set_status( code = 405 reason = 'Method Not Allowed' ).
    ENDCASE.
    me->if_http_extension~flow_rc = if_http_extension=>co_flow_ok.
  ENDMETHOD.

  METHOD set_cors.
    io_server->response->set_header_field( name = 'Access-Control-Allow-Origin'  value = '*' ).
    io_server->response->set_header_field( name = 'Access-Control-Allow-Methods' value = 'GET, POST, OPTIONS' ).
    io_server->response->set_header_field( name = 'Access-Control-Allow-Headers' value = 'Content-Type' ).
  ENDMETHOD.
ENDCLASS.
```

Response essentials for every branch:
```abap
io_server->response->set_header_field( name = 'Content-Type' value = 'application/json; charset=utf-8' ).
io_server->response->set_cdata( data = lv_json ).
io_server->response->set_status( code = 200 reason = 'OK' ).
```

- Read POST body: `lv_body = io_server->request->get_cdata( )`.
- In JSON string templates, escape braces: `|\{ "success": true \}|`.

---

## 4. Reading real CRM One Order data (list)

- Pending orders come from `CRMD_ORDERADM_H` joined to `CRM_JEST` (active user status).
- Aggregate amount via LEFT JOIN `CRMD_ORDERADM_I` → `CRMD_PRICING_I` with `SUM(net_value)` + `GROUP BY`.
- Open SQL 7.50 strict: commas between fields, `@` host variables, `@space` for empty CHAR compare.

```abap
SELECT h~object_id AS object_id, h~guid AS guid, h~description AS descr,
       SUM( p~net_value ) AS net_value
  FROM crmd_orderadm_h AS h
  INNER JOIN crm_jest AS j ON j~objnr = h~guid
  LEFT OUTER JOIN crmd_orderadm_i AS i ON i~header = h~guid
  LEFT OUTER JOIN crmd_pricing_i  AS p ON p~guid   = i~guid
  WHERE h~process_type IN ( 'ZSVO', 'ZOTS' )
    AND j~stat  = @gc_st_pending
    AND j~inact = @space
  GROUP BY h~object_id, h~guid, h~description
  INTO CORRESPONDING FIELDS OF TABLE @lt_out.
```

---

## 5. Changing CRM user status the RIGHT way (the hard-won part)

This is where most time was lost. The correct, production-aligned recipe:

### 5.1 Reuse the proven helper, don't hand-roll CRM_ORDER_MAINTAIN
Use the existing production helper **`ZCL_CA_CRM_TOOLS=>SET_USER_STATUS`** (takes GUID +
`TXT04` 4-char status code + activate flag). It internally:
- resolves the **internal status number** from the TXT04 via `CRM_STATUS_TEXT_CONVERSION`,
- sets the mandatory **`logical_key`** on the input field,
- sets the `ACTIVATE` input field,
- calls `CRM_ORDER_MAINTAIN`.

Then **you** save + commit:
```abap
zcl_ca_crm_tools=>set_user_status( EXPORTING iv_guid = iv_guid iv_sttxt = iv_sttxt iv_activ = abap_true
                                   CHANGING ev_stat = lv_stat_num
                                   EXCEPTIONS error = 1 OTHERS = 2 ).
IF sy-subrc <> 0 OR lv_stat_num IS INITIAL. " rollback path ... RETURN. ENDIF.

APPEND iv_guid TO lt_save.
CALL FUNCTION 'CRM_ORDER_SAVE'
  EXPORTING it_objects_to_save   = lt_save
            iv_update_task_local = abap_true          " <-- CRITICAL in ICF/batch context
  IMPORTING et_saved_objects     = lv_saved
            et_exception         = lt_exception
            et_objects_not_saved = lt_not_saved
  EXCEPTIONS document_not_saved = 1 OTHERS = 2.
IF sy-subrc <> 0 OR lt_exception IS NOT INITIAL. " rollback + CRM_ORDER_INITIALIZE ... RETURN. ENDIF.
COMMIT WORK AND WAIT.
CALL FUNCTION 'CRM_ORDER_INITIALIZE' EXPORTING it_guids_to_init = VALUE #( ( iv_guid ) ).
```

### 5.2 The four traps (each caused a distinct failure)
1. **`ITAB_ILLEGAL_SORT_ORDER`** — `crmt_input_field-field_names` is a SORTED table
   (key `FIELDNAME`). Never `APPEND` to it; use `INSERT ... INTO TABLE`.
2. **`CALL_FUNCTION_CONFLICT_TAB_TYP`** on `CRM_ORDER_SAVE` — `ET_SAVED_OBJECTS` is
   `CRMT_RETURN_OBJECTS`, NOT a GUID table. Declare the receiver with the exact type.
3. **"No error but nothing persists"** — two causes:
   - Missing `iv_update_task_local = abap_true` on `CRM_ORDER_SAVE`. In an ICF (non-dialog)
     context the standard update task is not materialized by the handler's commit.
     The standard report `CRM_STATUS_MAINTAIN` uses `iv_update_task_local = true` + `COMMIT WORK AND WAIT`.
   - Measuring success by `et_saved_objects` — WRONG. `SAVE_PREPARE` can leave it empty on
     a valid save. Production code (`ZCL_SE_ERMS_AH_SRQ_STAT_UPD`) measures success only by
     **absence of exceptions** (`sy-subrc` / `et_exception`).
4. **Forbidden status transition (silent)** — the schema's transition rules (table `TJ30`,
   fields `STONR` / `NSONR` / `HSONR`) decide which target statuses are reachable from the
   current one. If the target's `STONR` is outside the current status' `[NSONR..HSONR]`
   range, `CRM_ORDER_MAINTAIN` silently ignores the change (no dump, no exception, empty save).
   **Always validate the real workflow states before mapping approve/reject.**

### 5.3 Concrete DOA example (profile `ZSO_SVO`)
- Pending-for-approver status = **E0016** "Waiting for Warranty Claims Mg" (STONR 50),
  NOT E0001 (New). From E0016 the valid transitions are E0017 (approve, STONR 51) and
  E0018 (reject, STONR 52) — both inside E0016's `[30..52]` range.
- Status codes are stored/activated by their **TXT04**: E0017=`AQBM`, E0018=`RQBM`.
- Verify transitions with:
  `SELECT estat, stonr, nsonr, hsonr FROM tj30 WHERE stsma = '<schema>'`.
- Verify TXT04 ↔ Exxxx mapping with:
  `SELECT estat, txt04, txt30 FROM tj30t WHERE stsma = '<schema>' AND spras = 'E'`.

---

## 6. Parametric configuration (avoid hardcoded keys)

Config tables should be consumed **by their data semantics, not by a magic key**.
Example (DOA thresholds): instead of hardcoding `WHERE doa_level = '00'`, load the real
bands (`active = X AND amount_to > 0`), and derive:
- entry threshold = `MIN(amount_from)` across bands,
- level classification = band where `amount_from <= amount < amount_to` (top band inclusive).

This keeps behavior driven by table content — change the rows, behavior follows, no code change.

---

## 7. UI5 frontend (SplitApp master-detail)

- App type: `sap.m.SplitApp` (master list left, detail right). Works from UI5 1.38+.
- Master: `List` mode `SingleSelectMaster`, a `SearchField` in the sub-header for
  client-side filtering (`sap.ui.model.Filter` on multiple fields, `and: false`).
- Detail: `ObjectHeader` + editable `TextArea` (reason) + footer `Toolbar` with
  Approve/Reject buttons. Navigate with `oSplitApp.toDetail(this.createId("detailPage"))`.
- rootView should be the view that hosts the `SplitApp` directly (set in `manifest.json`).
- Same-origin calls: app and service both under `/sap/bc`, so `jQuery.ajax` to a relative
  URL (`/sap/bc/z_<app>`) needs no auth juggling. CORS headers on the handler cover
  cross-origin dev.
- Bootstrap path on this system: `/sap/public/bc/ui5_ui5/resources/sap-ui-core.js`
  (the SICF node for UI5 resources must be active).

---

## 8. Deployment & lifecycle

- **Deploy UI5**: SE38 report `/UI5/UI5_REPOSITORY_LOAD`, application name = BSP app
  (e.g. `ZCRM_CLAIM_APPR`), point it to the local `webapp` folder; uploads all files.
  Re-run to redeploy after frontend changes. Hard refresh browser (Ctrl+F5) to drop cache.
- **App URL** pattern: `https://<host>:<port>/sap/bc/ui5_ui5/sap/<bsp_app>/index.html`.
- **Global classes**: on this release, ADT-*created* global classes can dump
  `GEN_DUPLICATE_ENTRY`. Historical workaround was manual SE24 creation; note that the
  workspace tooling is now configured so ADT create+activate works — prefer ADT going
  forward, keep the manual fallback in mind if the dump reappears.
- **Runtime load cache (ICF)**: after activating the handler, a dump's "Source Code
  Extract" showing OLD code usually means you're looking at a pre-activation dump; a fresh
  request runs the new load. Re-activate to force regeneration if in doubt.
- **Method lock**: editing the same method concurrently in SE24/SE80 while patching via
  ADT causes a lock (`... is currently editing`) — close the SAPGUI editor first.

---

## 9. Audit pattern

Every decision writes a row to `Z..._AUDIT` (uuid, object_id, doa_level, action, actor
`sy-uname`, reason text, `event_at` timestampl). Store the **real** classified level, not
a constant. Note: the decision reason lives ONLY in the audit table — it is deliberately
NOT written into the Service Order notes/texts (business decision for this app).

---

## 10. Quick failure → cause cheat sheet

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| `ITAB_ILLEGAL_SORT_ORDER` in status build | APPEND to sorted `field_names` | `INSERT ... INTO TABLE` |
| `CALL_FUNCTION_CONFLICT_TAB_TYP` on SAVE | wrong type for `et_saved_objects` | use `CRMT_RETURN_OBJECTS` |
| approve "succeeds" but status unchanged | missing `iv_update_task_local`; or judging by `et_saved_objects`; or forbidden transition | add `iv_update_task_local=abap_true` + `COMMIT WORK AND WAIT`; judge by exceptions; list from the correct pending status (TJ30 reachability) |
| dump shows old code after fix | pre-activation dump / stale ICF load | re-activate; a fresh request uses new load |
| ADT write 403 "is currently editing" | method open in SAPGUI | close SE24/SE80 editor |
