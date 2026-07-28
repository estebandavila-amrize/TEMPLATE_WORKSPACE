# Global Technical Constraints

- Target Environment: SAP NetWeaver [target version] — install.bat asks for this and rewrites this line.
- ABAP Rules: Strict classic ABAP syntax. Inline declarations (DATA, FIELD-SYMBOLS) are permitted. NO ABAP Cloud, RAP, or Steampunk syntax.
- DDIC Rules: Use classical Dictionary objects (SE11).
- Python MCP Rules: Flat input schemas for tools (no top-level Union, oneOf, or anyOf).
