# SAP ABAP Development Skill — ECC 6.0 EHP8

ABAP development skill tuned for **SAP ECC 6.0 EHP8** (NetWeaver 7.50, ABAP 7.50, non-HANA database).

## System Scope

| Available | NOT Available |
|-----------|---------------|
| ABAP 7.50 (inline DATA, constructor expressions) | AMDP |
| Open SQL (SELECT, JOIN, FOR ALL ENTRIES) | RAP / EML |
| Classic OO (classes, interfaces, inheritance) | ABAP Cloud / Steampunk |
| ABAP Unit testing | XCO Library |
| RTTI / RTTC / dynamic programming | WITH (CTE) in SQL |
| SE11 DDIC (tables, structures, domains) | HIERARCHY expressions |
| Classic BAdIs, user-exits, enhancements | Generative AI SDK |
| Function Modules / Function Groups | FINAL(x) declarations |
| SAPscript, Smartforms, Adobe Forms | CDS views with HANA-specific functions/annotations |
| CDS View Entities (classic, non-HANA-specific) | |

## Auto-Trigger Keywords

This skill activates when discussing:

### ABAP Language
- ABAP, ABAP code, ABAP program, ABAP class, ABAP method
- DATA, TYPES, CONSTANTS, FIELD-SYMBOLS
- IF, CASE, LOOP, DO, WHILE, ENDLOOP, ENDIF
- SELECT, INSERT, UPDATE, DELETE, MODIFY
- TRY, CATCH, RAISE EXCEPTION, CLEANUP
- CLASS, INTERFACE, METHOD, ENDCLASS

### Internal Tables
- internal table, itab, TABLE OF, STANDARD TABLE, SORTED TABLE, HASHED TABLE
- APPEND, INSERT, READ TABLE, MODIFY TABLE, DELETE
- LOOP AT, FIELD-SYMBOL, ASSIGNING, INTO
- table key, secondary key, WITH KEY
- FOR, REDUCE, FILTER
- GROUP BY, GROUP SIZE, WITHOUT MEMBERS

### Constructor Expressions
- VALUE, NEW, CONV, CORRESPONDING, CAST, REF
- COND, SWITCH
- REDUCE, FILTER, FOR
- constructor expression, inline declaration
- OPTIONAL, DEFAULT, BASE

### Object Orientation
- ABAP OO, class definition, class implementation
- inheritance, INHERITING FROM, REDEFINITION
- interface, INTERFACES, ALIASES
- CREATE OBJECT, instantiation, factory method
- PUBLIC SECTION, PRIVATE SECTION, PROTECTED SECTION
- event, RAISE EVENT, SET HANDLER
- factory pattern, singleton, strategy pattern

### Open SQL
- Open SQL, SELECT, FROM, WHERE, INTO TABLE
- INNER JOIN, LEFT OUTER JOIN, RIGHT OUTER JOIN
- GROUP BY, HAVING, ORDER BY
- aggregate function, COUNT, SUM, AVG, MIN, MAX
- FOR ALL ENTRIES, subquery
- UP TO n ROWS, PACKAGE SIZE

### Dynamic Programming
- field symbol, ASSIGN, UNASSIGN, IS ASSIGNED
- data reference, REF TO, CREATE DATA, dereference
- RTTI, RTTC, cl_abap_typedescr, cl_abap_structdescr
- dynamic SQL, dynamic method call
- CASTING

### String Processing
- string, string template, string function
- FIND, REPLACE, CONCATENATE, SPLIT
- to_upper, to_lower, strlen, substring
- PCRE, regular expression, regex, pattern matching

### Testing
- ABAP Unit, test class, FOR TESTING
- cl_abap_unit_assert, assert_equals
- test double, mock, stub, injection
- RISK LEVEL, DURATION

### Exception Handling
- exception, TRY, CATCH, ENDTRY
- RAISE EXCEPTION, THROW
- cx_root, cx_static_check, cx_dynamic_check
- exception class, get_text

### Authorization
- AUTHORITY-CHECK, authorization object
- ACTVT, activity code
- pfcg_auth

### ABAP Dictionary
- data element, domain, structure
- table type, database table
- DDIC, dictionary type, SE11

### Enhancements
- BAdI, user-exit, enhancement point
- enhancement spot, enhancement implementation
- SMOD, CMOD, SE18, SE19, SE80

### Errors and Debugging
- sy-subrc, sy-tabix, sy-index
- runtime error, dump, exception
- CX_SY_ZERODIVIDE, CX_SY_ITAB_LINE_NOT_FOUND
- debugging, breakpoint

## Directory Structure

```
ABAP/
├── SKILL.md                        # Main skill file with quick reference
├── README.md                       # This file
└── references/                     # Detailed reference files
    ├── abap-dictionary.md          # DDIC objects, types
    ├── abap-sql.md                 # Open SQL guide (ignore CTE sections)
    ├── authorization.md            # Authorization checks
    ├── bits-bytes.md               # Binary operations
    ├── builtin-functions.md        # String, numeric, table functions
    ├── constructor-expressions.md  # Constructor operators
    ├── date-time.md                # Classic date/time patterns
    ├── design-patterns.md          # Factory, Singleton, Strategy
    ├── dynamic-programming.md      # RTTI, RTTC, field symbols
    ├── exceptions.md               # Exception handling
    ├── internal-tables.md          # Complete table operations
    ├── numeric-operations.md       # Math functions
    ├── object-orientation.md       # OO programming patterns
    ├── performance.md              # DB and itab optimization
    ├── program-flow.md             # IF, CASE, LOOP, DO, WHILE
    ├── sap-luw.md                  # Logical Unit of Work
    ├── string-processing.md        # String functions and regex
    ├── table-grouping.md           # GROUP BY loops
    ├── unit-testing.md             # ABAP Unit framework
    ├── where-conditions.md         # WHERE clause patterns
    └── xml-json.md                 # XML/JSON processing
```

**Files NOT applicable to this system** (kept for reference only):
- `references/amdp.md` — Requires HANA
- `references/cloud-development.md` — Requires BTP
- `references/rap-eml.md` — Requires S/4HANA
- `references/released-classes.md` — Cloud-only APIs
- `references/generative-ai.md` — Requires BTP
- `references/sql-hierarchies.md` — Requires HANA

`references/cds-views.md` IS applicable — classic CDS view entities work without HANA. Skip only the HANA-specific SQL functions and OLAP/analytics annotations within that file.

## Version

- **Skill Version**: 2.1.0
- **Last Updated**: 2026-08-06
- **Target ABAP Release**: 7.50 (ECC 6.0 EHP8)
- **Database**: Non-HANA (traditional DB)
- **Applicable Reference Files**: 22 of 28

---

## License

GPL-3.0 License
