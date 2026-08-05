---
name: sap-abap
description: |
  ABAP development skill for SAP ECC 6.0 EHP8 (NetWeaver 7.50, ABAP 7.50).
  Use when writing ABAP code, working with internal tables, structures, Open SQL,
  object-oriented programming, string processing, dynamic programming, RTTI/RTTC,
  field symbols, data references, exception handling, or ABAP unit testing.
  This system does NOT have HANA, CDS views, RAP, EML, AMDP, or ABAP Cloud.
  Only classic ABAP patterns are valid.
license: GPL-3.0
metadata:
  version: 2.0.0
  last_updated: "2026-07-28"
  target_system: "SAP ECC 6.0 EHP8 / NetWeaver 7.50 / ABAP 7.50"
  database: "Non-HANA (traditional DB)"
  unavailable_features:
    - CDS views
    - AMDP (ABAP Managed Database Procedures)
    - RAP (RESTful Application Programming Model)
    - EML (Entity Manipulation Language)
    - ABAP Cloud / Steampunk
    - XCO library
    - Generative AI SDK
    - WITH (CTE) in Open SQL
    - HIERARCHY in Open SQL
    - FINAL(x) immutable inline declarations
---
# SAP ABAP Development Skill — ECC 7.5 EHP8

## System Constraints (CRITICAL)

This system is SAP ECC 6.0 EHP8 running on NetWeaver 7.50 with ABAP release 7.50.
The database is **NOT SAP HANA**. The following features are **NOT AVAILABLE**:

| Feature | Why Not |
|---------|---------|
| CDS Views | Requires HANA or S/4 |
| AMDP | Requires HANA |
| RAP / EML | Requires S/4HANA / BTP |
| ABAP Cloud (Steampunk) | Requires BTP ABAP Environment |
| XCO Library | Cloud-only released API |
| WITH (CTE) in SQL | Requires HANA 7.51+ |
| HIERARCHY expressions | Requires HANA |
| FINAL(x) declarations | Requires ABAP 7.57+ |
| Generative AI SDK | Requires BTP |

## Table of Contents
- [Quick Reference](#quick-reference)
- [Available ABAP 7.50 Features](#available-abap-750-features)
- [Common Patterns](#common-patterns)
- [Error Catalog](#error-catalog)
- [Performance Tips](#performance-tips)

## Quick Reference

### Data Types and Declarations

```abap
" Elementary types
DATA num TYPE i VALUE 123.
DATA txt TYPE string VALUE `Hello`.
DATA flag TYPE abap_bool VALUE abap_true.

" Inline declarations (available in 7.40+)
DATA(result) = some_method( ).

" Structures
DATA: BEGIN OF struc,
        id   TYPE i,
        name TYPE string,
      END OF struc.

" Internal tables
DATA itab TYPE TABLE OF string WITH EMPTY KEY.
DATA sorted_tab TYPE SORTED TABLE OF struct WITH UNIQUE KEY id.
DATA hashed_tab TYPE HASHED TABLE OF struct WITH UNIQUE KEY id.
```

### Available ABAP 7.50 Features

These constructor expressions and inline features ARE available on your system:

```abap
" VALUE — structures and tables
DATA(struc) = VALUE struct_type( comp1 = 1 comp2 = `text` ).
DATA(itab) = VALUE itab_type( ( a = 1 ) ( a = 2 ) ( a = 3 ) ).

" NEW — create instances
DATA(dref) = NEW i( 123 ).
DATA(oref) = NEW zcl_my_class( param = value ).

" CORRESPONDING — structure/table mapping
target = CORRESPONDING #( source ).
target = CORRESPONDING #( source MAPPING target_field = source_field ).

" COND/SWITCH — conditional values
DATA(text) = COND string( WHEN flag = abap_true THEN `Yes` ELSE `No` ).
DATA(result) = SWITCH #( code WHEN 1 THEN `A` WHEN 2 THEN `B` ELSE `X` ).

" CONV — type conversion
DATA(dec) = CONV decfloat34( 1 / 3 ).

" FILTER — table filtering (requires sorted/hashed table with appropriate key)
DATA(filtered) = FILTER #( itab WHERE status = 'A' ).

" REDUCE — aggregation
DATA(sum) = REDUCE i( INIT s = 0 FOR wa IN itab NEXT s = s + wa-amount ).

" REF — reference operator
DATA(dref) = REF #( variable ).

" String templates
DATA(msg) = |Name: { name }, Date: { sy-datum DATE = ISO }|.
```

### Internal Tables - Essential Operations

```abap
" Create with VALUE
itab = VALUE #( ( col1 = 1 col2 = `a` )
                ( col1 = 2 col2 = `b` ) ).

" Read operations
DATA(line) = itab[ 1 ].                    " By index
DATA(line2) = itab[ col1 = 1 ].            " By key
READ TABLE itab INTO wa INDEX 1.
READ TABLE itab ASSIGNING FIELD-SYMBOL(<fs>) WITH KEY col1 = 1.

" Modify operations
MODIFY TABLE itab FROM VALUE #( col1 = 1 col2 = `updated` ).
itab[ 1 ]-col2 = `changed`.

" Loop processing
LOOP AT itab ASSIGNING FIELD-SYMBOL(<line>).
  <line>-col2 = to_upper( <line>-col2 ).
ENDLOOP.

" Delete
DELETE itab WHERE col1 > 5.
DELETE TABLE itab FROM VALUE #( col1 = 1 ).
```

### Open SQL (NOT ABAP SQL — no CTE/WITH, no HIERARCHY)

```abap
" SELECT into table
SELECT * FROM dbtab INTO TABLE @DATA(result_tab).

" SELECT with conditions
SELECT carrid, connid, fldate
  FROM sflight
  WHERE carrid = 'LH'
  INTO TABLE @DATA(flights).

" Aggregate functions
SELECT carrid, COUNT(*) AS cnt, AVG( price ) AS avg_price
  FROM sflight
  GROUP BY carrid
  INTO TABLE @DATA(stats).

" JOIN operations
SELECT a~carrid, a~connid, b~carrname
  FROM sflight AS a
  INNER JOIN scarr AS b ON a~carrid = b~carrid
  INTO TABLE @DATA(joined).

" FOR ALL ENTRIES (classic alternative to subqueries)
IF itab_keys IS NOT INITIAL.
  SELECT * FROM vbap
    FOR ALL ENTRIES IN @itab_keys
    WHERE vbeln = @itab_keys-vbeln
    INTO TABLE @DATA(lt_items).
ENDIF.

" Modification statements
INSERT dbtab FROM @struc.
UPDATE dbtab FROM @struc.
MODIFY dbtab FROM TABLE @itab.
DELETE FROM dbtab WHERE condition.
```

### Object-Oriented ABAP

```abap
" Class definition
CLASS zcl_example DEFINITION PUBLIC FINAL CREATE PUBLIC.
  PUBLIC SECTION.
    METHODS constructor IMPORTING iv_name TYPE string.
    METHODS get_name RETURNING VALUE(rv_name) TYPE string.
    CLASS-METHODS factory RETURNING VALUE(ro_instance) TYPE REF TO zcl_example.
  PRIVATE SECTION.
    DATA mv_name TYPE string.
ENDCLASS.

CLASS zcl_example IMPLEMENTATION.
  METHOD constructor.
    mv_name = iv_name.
  ENDMETHOD.
  METHOD get_name.
    rv_name = mv_name.
  ENDMETHOD.
  METHOD factory.
    ro_instance = NEW #( `Default` ).
  ENDMETHOD.
ENDCLASS.

" Interface implementation
CLASS zcl_impl DEFINITION PUBLIC.
  PUBLIC SECTION.
    INTERFACES zif_my_interface.
ENDCLASS.
```

### Exception Handling

```abap
TRY.
    DATA(result) = risky_operation( ).
  CATCH cx_sy_zerodivide INTO DATA(exc).
    DATA(msg) = exc->get_text( ).
  CATCH cx_root INTO DATA(any_exc).
    " Handle any exception
  CLEANUP.
    " Cleanup code
ENDTRY.

" Raising exceptions
RAISE EXCEPTION TYPE zcx_my_exception
  EXPORTING textid = zcx_my_exception=>error_occurred.

" With COND/SWITCH
DATA(val) = COND #( WHEN valid THEN result
                    ELSE THROW zcx_my_exception( ) ).
```

### String Processing

```abap
" Concatenation
DATA(full) = first && ` ` && last.
txt &&= ` appended`.

" String templates
DATA(msg) = |Name: { name }, Date: { date DATE = ISO }|.

" Functions (available in 7.50)
DATA(upper) = to_upper( text ).
DATA(len) = strlen( text ).
DATA(found) = find( val = text sub = `search` ).
DATA(replaced) = replace( val = text sub = `old` with = `new` occ = 0 ).
DATA(parts) = segment( val = text index = 2 sep = `,` ).

" FIND/REPLACE statements
FIND ALL OCCURRENCES OF pattern IN text RESULTS DATA(matches).
REPLACE ALL OCCURRENCES OF old IN text WITH new.
```

### Dynamic Programming

```abap
" Field symbols
FIELD-SYMBOLS <fs> TYPE any.
ASSIGN struct-component TO <fs>.
ASSIGN struct-(comp_name) TO <fs>.  " Dynamic component

" Data references
DATA dref TYPE REF TO data.
dref = REF #( variable ).
CREATE DATA dref TYPE (type_name).
dref->* = value.

" RTTI - Get type information
DATA(tdo) = cl_abap_typedescr=>describe_by_data( dobj ).
DATA(components) = CAST cl_abap_structdescr( tdo )->components.

" RTTC - Create types dynamically
DATA(elem_type) = cl_abap_elemdescr=>get_string( ).
CREATE DATA dref TYPE HANDLE elem_type.
```

---

## Common Patterns

### Safe Table Access (Avoid Exceptions)

```abap
" Using VALUE with OPTIONAL
DATA(line) = VALUE #( itab[ key = value ] OPTIONAL ).

" Using VALUE with DEFAULT
DATA(line) = VALUE #( itab[ 1 ] DEFAULT VALUE #( ) ).

" Check before access
IF line_exists( itab[ key = value ] ).
  DATA(line) = itab[ key = value ].
ENDIF.
```

### Functional Method Chaining

```abap
DATA(result) = NEW zcl_builder( )
  ->set_name( `Test` )
  ->set_value( 123 )
  ->build( ).
```

### FOR Iteration Expressions

```abap
" Transform table
DATA(transformed) = VALUE itab_type(
  FOR wa IN source_itab
  ( id = wa-id name = to_upper( wa-name ) ) ).

" With WHERE
DATA(filtered) = VALUE itab_type(
  FOR wa IN source WHERE ( status = 'A' )
  ( wa ) ).

" With INDEX INTO
DATA(numbered) = VALUE itab_type(
  FOR wa IN source INDEX INTO idx
  ( line_no = idx data = wa ) ).
```

### Classic BAdI / Enhancement Implementation

```abap
" Get BAdI handle (new BAdI framework — available since 7.0 EHP2)
DATA: lo_badi TYPE REF TO badi_interface.
GET BADI lo_badi.
CALL BADI lo_badi->method_name
  EXPORTING iv_param = lv_value
  CHANGING  ct_data  = lt_data.

" Classic user-exit / enhancement point
ENHANCEMENT-POINT enh_name SPOTS spot_name.
```

---

## Error Catalog

### CX_SY_ITAB_LINE_NOT_FOUND
**Cause**: Table expression access to non-existent line
**Solution**: Use OPTIONAL, DEFAULT, or check with `line_exists( )`

### CX_SY_ZERODIVIDE
**Cause**: Division by zero
**Solution**: Check divisor before operation

### CX_SY_RANGE_OUT_OF_BOUNDS
**Cause**: Invalid substring access or array bounds
**Solution**: Validate offset and length before access

### CX_SY_CONVERSION_NO_NUMBER
**Cause**: String cannot be converted to number
**Solution**: Validate input format before conversion

### CX_SY_REF_IS_INITIAL
**Cause**: Dereferencing unbound reference
**Solution**: Check `IS BOUND` before dereferencing

---

## Performance Tips

1. **Use SORTED/HASHED tables** for frequent key access
2. **Prefer field symbols** over work areas in loops for modification
3. **Use PACKAGE SIZE** for large SELECT results
4. **Avoid SELECT in loops** — use FOR ALL ENTRIES or JOINs
5. **Use secondary keys** for different access patterns
6. **Check sy-subrc after every DB operation** — never assume success
7. **Buffer-friendly design** — single-record buffering, generic buffering for config tables

---

## Bundled References (ECC 7.5 applicable only)

The following reference files are relevant to your system:
- `references/internal-tables.md` — Complete table operations
- `references/abap-sql.md` — Open SQL reference (ignore CTE/WITH sections)
- `references/object-orientation.md` — Classes and interfaces
- `references/constructor-expressions.md` — VALUE, NEW, COND, REDUCE
- `references/string-processing.md` — String functions and regex
- `references/unit-testing.md` — ABAP Unit framework
- `references/performance.md` — Optimization techniques
- `references/dynamic-programming.md` — RTTI, RTTC, field symbols
- `references/exceptions.md` — Exception handling
- `references/design-patterns.md` — Factory, Singleton, Strategy
- `references/authorization.md` — AUTHORITY-CHECK (classic)
- `references/abap-dictionary.md` — DDIC objects, SE11
- `references/program-flow.md` — IF, CASE, LOOP, DO, WHILE
- `references/builtin-functions.md` — String, numeric, table functions
- `references/sap-luw.md` — Logical Unit of Work, COMMIT/ROLLBACK
- `references/xml-json.md` — XML/JSON processing
- `references/date-time.md` — Date/time (classic sy-datum, sy-uzeit patterns)
- `references/numeric-operations.md` — Math functions
- `references/bits-bytes.md` — Binary operations
- `references/where-conditions.md` — WHERE clause patterns
- `references/table-grouping.md` — GROUP BY loops

**NOT applicable** (do not reference these on this system):
- ~~references/amdp.md~~ — Requires HANA
- ~~references/cds-views.md~~ — Requires HANA/S4
- ~~references/cloud-development.md~~ — Requires BTP
- ~~references/rap-eml.md~~ — Requires S/4HANA
- ~~references/released-classes.md~~ — Cloud-only APIs
- ~~references/generative-ai.md~~ — Requires BTP
- ~~references/sql-hierarchies.md~~ — Requires HANA

---

## Source Documentation

All content based on SAP official documentation:
- SAP Help: [https://help.sap.com/doc/abapdocu_750_index_htm/7.50/en-US/index.htm](https://help.sap.com/doc/abapdocu_750_index_htm/7.50/en-US/index.htm)
- SAP Cheat Sheets: [https://github.com/SAP-samples/abap-cheat-sheets](https://github.com/SAP-samples/abap-cheat-sheets) (filter for 7.50 compatibility)
