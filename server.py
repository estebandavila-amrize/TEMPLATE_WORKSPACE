"""
SAP MCP Server — Clean data-driven rewrite.
Tools defined as a list of dicts. Single list_tools/call_tool dispatch.
Transport: stdio (required by Kiro).
"""

import os
import sys
import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from sap_client import SAPADTClient

# ──────────────────────────────────────────────
# SAP connection config from environment
# ──────────────────────────────────────────────
SAP_HOST = os.environ.get("SAP_HOST", "localhost:8000")
SAP_CLIENT = os.environ.get("SAP_CLIENT", "100")
SAP_USER = os.environ.get("SAP_USER", "")
SAP_PASSWORD = os.environ.get("SAP_PASSWORD", "")
SAP_SECURE = os.environ.get("SAP_SECURE", "false").lower() == "true"
SAP_SYSTEM_ID = os.environ.get("SAP_SYSTEM_ID", "DEV")

sap = SAPADTClient(
    host=SAP_HOST, client=SAP_CLIENT,
    username=SAP_USER, password=SAP_PASSWORD, secure=SAP_SECURE,
)

server = Server(f"sap-{SAP_SYSTEM_ID.lower()}-mcp")
SYS = f"SAP {SAP_SYSTEM_ID} {SAP_CLIENT}"


# ──────────────────────────────────────────────
# Tool handlers
# ──────────────────────────────────────────────

def _h_ping(args):
    return sap.ping()

def _h_get_program_source(args):
    p = args.get("program_name", "").upper()
    return {"ok": False, "message": "program_name is required"} if not p else sap.get_program_source(p)

def _h_get_class_source(args):
    c = args.get("class_name", "").upper()
    return {"ok": False, "message": "class_name is required"} if not c else sap.get_class_source(c)

def _h_get_include_source(args):
    i = args.get("include_name", "").upper()
    return {"ok": False, "message": "include_name is required"} if not i else sap.get_include_source(i)

def _h_get_interface_source(args):
    i = args.get("interface_name", "").upper()
    return {"ok": False, "message": "interface_name is required"} if not i else sap.get_interface_source(i)

def _h_get_function_module_source(args):
    fg = args.get("function_group", "").upper()
    fm = args.get("function_name", "").upper()
    if not fg or not fm:
        return {"ok": False, "message": "function_group and function_name are required"}
    return sap.get_function_module_source(fg, fm)

def _h_get_function_group_source(args):
    fg = args.get("function_group", "").upper()
    return {"ok": False, "message": "function_group is required"} if not fg else sap.get_function_group_source(fg)

def _h_get_structure(args):
    s = args.get("structure_name", "").upper()
    return {"ok": False, "message": "structure_name is required"} if not s else sap.get_structure_source(s)

def _h_get_cds_view_source(args):
    c = args.get("cds_view_name", "").upper()
    return {"ok": False, "message": "cds_view_name is required"} if not c else sap.get_cds_view_source(c)

def _h_get_table_definition(args):
    t = args.get("table_name", "").upper()
    return {"ok": False, "message": "table_name is required"} if not t else sap.get_table_definition(t)

def _h_get_package_contents(args):
    p = args.get("package_name", "").upper()
    return {"ok": False, "message": "package_name is required"} if not p else sap.get_package_contents(p)

def _h_get_transaction_info(args):
    t = args.get("transaction_name", "").upper()
    return {"ok": False, "message": "transaction_name is required"} if not t else sap.get_transaction_info(t)

def _h_search_objects(args):
    q = args.get("query", "")
    return {"ok": False, "message": "query is required"} if not q else sap.search_objects(q, args.get("max_results", 20))

def _h_get_usage_references(args):
    ot = args.get("object_type", "")
    on = args.get("object_name", "")
    fg = args.get("function_group", "")
    if not ot or not on:
        return {"ok": False, "message": "object_type and object_name are required"}
    return sap.get_usage_references(ot, on, fg)

def _h_get_enhancements(args):
    o = args.get("object_name", "").upper()
    if not o:
        return {"ok": False, "message": "object_name is required"}
    return sap.get_enhancements(o, args.get("program_context", ""))

def _h_get_sql_query(args):
    q = args.get("sql_query", "")
    if not q:
        return {"ok": False, "message": "sql_query is required"}
    return sap.get_sql_query(q, args.get("max_rows", 100))

def _h_get_includes_list(args):
    o = args.get("object_name", "").upper()
    if not o:
        return {"ok": False, "message": "object_name is required"}
    return sap.get_includes_list(o, args.get("object_type", "program"))

def _h_get_source_by_uri(args):
    u = args.get("uri", "")
    return {"ok": False, "message": "uri is required"} if not u else sap.get_source_by_uri(u)

def _h_create_program(args):
    n = args.get("program_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "program_name and source_code are required"}
    return sap.create_program(n, args.get("description", ""), args.get("package", "$TMP").upper(),
                              args.get("transport", ""), src)

def _h_update_program_source(args):
    n = args.get("program_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "program_name and source_code are required"}
    return sap.update_program_source(n, src, args.get("transport", ""))

def _h_update_program_from_file(args):
    n = args.get("program_name", "").upper()
    f = args.get("file_path", "")
    if not n or not f:
        return {"ok": False, "message": "program_name and file_path are required"}
    return sap.update_program_from_file(n, f, args.get("transport", ""))

def _h_create_class(args):
    n = args.get("class_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "class_name and source_code are required"}
    return sap.create_class(n, args.get("description", ""), args.get("package", "$TMP").upper(),
                            args.get("transport", ""), src, args.get("is_final", True))

def _h_update_class_source(args):
    n = args.get("class_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "class_name and source_code are required"}
    return sap.update_class_source(n, src, args.get("transport", ""))

def _h_create_interface(args):
    n = args.get("interface_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "interface_name and source_code are required"}
    return sap.create_interface(n, args.get("description", ""), args.get("package", "$TMP").upper(),
                                args.get("transport", ""), src)

def _h_update_interface_source(args):
    n = args.get("interface_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "interface_name and source_code are required"}
    return sap.update_interface_source(n, src, args.get("transport", ""))

def _h_create_structure(args):
    n = args.get("structure_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "structure_name and source_code are required"}
    return sap.create_structure(n, args.get("description", ""), args.get("package", "$TMP").upper(),
                                args.get("transport", ""), src)

def _h_update_structure_source(args):
    n = args.get("structure_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "structure_name and source_code are required"}
    return sap.update_structure_source(n, src, args.get("transport", ""))

def _h_update_function_module_source(args):
    fg = args.get("function_group", "").upper()
    fm = args.get("function_name", "").upper()
    src = args.get("source_code", "")
    if not fg or not fm or not src:
        return {"ok": False, "message": "function_group, function_name, and source_code are required"}
    return sap.update_function_module_source(fg, fm, src, args.get("transport", ""))

def _h_patch_source(args):
    uri = args.get("object_uri", "")
    ops_raw = args.get("operations", "")
    if not uri or not ops_raw:
        return {"ok": False, "message": "object_uri and operations are required"}
    try:
        ops = json.loads(ops_raw) if isinstance(ops_raw, str) else ops_raw
    except json.JSONDecodeError as e:
        return {"ok": False, "message": f"invalid operations JSON: {e}"}
    return sap.patch_source(uri, ops, args.get("transport", ""))

def _h_delete_object(args):
    uri = args.get("object_uri", "")
    return {"ok": False, "message": "object_uri is required"} if not uri else sap.delete_object(uri, args.get("transport", ""))

def _h_activate_object(args):
    n = args.get("object_name", "").upper()
    if not n:
        return {"ok": False, "message": "object_name is required"}
    return sap.activate_object(n, args.get("object_type", "PROG/P"))

def _h_syntax_check(args):
    u = args.get("object_url", "")
    return {"ok": False, "message": "object_url is required"} if not u else sap.syntax_check(u)

def _h_run_abap_unit(args):
    u = args.get("object_url", "")
    return {"ok": False, "message": "object_url is required"} if not u else sap.run_abap_unit(u)

def _h_create_transport(args):
    d = args.get("description", "")
    if not d:
        return {"ok": False, "message": "description is required"}
    return sap.create_transport(d, args.get("request_type", "K"), args.get("target", ""))

def _h_list_transports(args):
    return sap.list_transports(args.get("user", ""))

def _h_get_transport_details(args):
    t = args.get("transport_number", "").upper()
    return {"ok": False, "message": "transport_number is required"} if not t else sap.get_transport_details(t)

def _h_get_transport_xml_raw(args):
    t = args.get("transport_number", "").upper()
    return {"ok": False, "message": "transport_number is required"} if not t else sap.get_transport_xml_raw(t)

def _h_release_transport(args):
    t = args.get("transport_number", "").upper()
    return {"ok": False, "message": "transport_number is required"} if not t else sap.release_transport(t)

def _h_add_to_transport(args):
    uri = args.get("object_uri", "")
    t = args.get("transport_number", "").upper()
    if not uri or not t:
        return {"ok": False, "message": "object_uri and transport_number are required"}
    return sap.add_to_transport(uri, t)

def _h_create_transport_task(args):
    p = args.get("parent_transport", "").upper()
    d = args.get("description", "")
    if not p or not d:
        return {"ok": False, "message": "parent_transport and description are required"}
    return sap.create_transport_task(p, d, args.get("owner", ""))


# ──────────────────────────────────────────────
# Data-driven tool registry (35 tools)
# ──────────────────────────────────────────────

TOOLS = [
    {
        "name": "sap_ping",
        "description": f"Verifies connectivity with the {SYS} system. Use it to confirm the MCP server can communicate with SAP.",
        "schema": {"type": "object", "properties": {}, "required": []},
        "handler": _h_ping,
    },
    {
        "name": "sap_get_program_source",
        "description": f"Gets the ABAP source code of a program or report (PROG type objects) in {SYS}.",
        "schema": {"type": "object", "properties": {"program_name": {"type": "string", "description": "ABAP program name in uppercase. E.g.: ZREPORTE_VENTAS"}}, "required": ["program_name"]},
        "handler": _h_get_program_source,
    },
    {
        "name": "sap_get_class_source",
        "description": f"Gets the source code of an ABAP OO class (ZCL_*, LCL_*, etc.) in {SYS}.",
        "schema": {"type": "object", "properties": {"class_name": {"type": "string", "description": "ABAP class name. E.g.: ZCL_SD_HELPER"}}, "required": ["class_name"]},
        "handler": _h_get_class_source,
    },
    {
        "name": "sap_get_include_source",
        "description": f"Gets the source code of an ABAP INCLUDE in {SYS}.",
        "schema": {"type": "object", "properties": {"include_name": {"type": "string", "description": "ABAP include name in uppercase. E.g.: ZSD_REPORT_F01"}}, "required": ["include_name"]},
        "handler": _h_get_include_source,
    },
    {
        "name": "sap_get_interface_source",
        "description": f"Gets the source code of an ABAP OO interface (ZIF_*, IF_*) in {SYS}.",
        "schema": {"type": "object", "properties": {"interface_name": {"type": "string", "description": "ABAP interface name. E.g.: ZIF_SD_STOCK_DAO"}}, "required": ["interface_name"]},
        "handler": _h_get_interface_source,
    },
    {
        "name": "sap_get_function_module_source",
        "description": f"Gets the source code of an ABAP Function Module in {SYS}.",
        "schema": {"type": "object", "properties": {"function_group": {"type": "string", "description": "Function group name. E.g.: ZSD_QUOTATION"}, "function_name": {"type": "string", "description": "Function Module name. E.g.: ZSD_QUOTATION_SALSFRC_CHANGE"}}, "required": ["function_group", "function_name"]},
        "handler": _h_get_function_module_source,
    },
    {
        "name": "sap_get_function_group_source",
        "description": f"Gets the source code of an ABAP Function Group in {SYS}.",
        "schema": {"type": "object", "properties": {"function_group": {"type": "string", "description": "Function group name. E.g.: ZSD_QUOTATION"}}, "required": ["function_group"]},
        "handler": _h_get_function_group_source,
    },
    {
        "name": "sap_get_structure",
        "description": f"Gets the source definition of a DDIC structure (SE11) in {SYS}.",
        "schema": {"type": "object", "properties": {"structure_name": {"type": "string", "description": "DDIC structure name. E.g.: ZSSD_QUOTATION_ITEM"}}, "required": ["structure_name"]},
        "handler": _h_get_structure,
    },
    # NOTE: sap_get_cds_view_source REMOVED — ECC 7.5 EHP8 does not support CDS views (no HANA).
    {
        "name": "sap_get_table_definition",
        "description": f"Gets the definition of an ABAP dictionary table in {SYS} (fields, types, lengths).",
        "schema": {"type": "object", "properties": {"table_name": {"type": "string", "description": "ABAP table name. E.g.: ZZSD_QUOTATION or VBAK"}}, "required": ["table_name"]},
        "handler": _h_get_table_definition,
    },
    {
        "name": "sap_get_package_contents",
        "description": f"Gets the objects contained in an ABAP development package in {SYS}. Lists programs, classes, FMs, etc.",
        "schema": {"type": "object", "properties": {"package_name": {"type": "string", "description": "Package name. E.g.: ZSD_QUOTATION, ZDEV_SD"}}, "required": ["package_name"]},
        "handler": _h_get_package_contents,
    },
    {
        "name": "sap_get_transaction_info",
        "description": f"Gets information about an ABAP transaction in {SYS} (package, associated application).",
        "schema": {"type": "object", "properties": {"transaction_name": {"type": "string", "description": "Transaction name. E.g.: VA01, ZSD_MONITOR"}}, "required": ["transaction_name"]},
        "handler": _h_get_transaction_info,
    },
    {
        "name": "sap_search_objects",
        "description": f"Searches for ABAP objects in the {SYS} repository by name or pattern. Useful for finding Z* or Y* objects.",
        "schema": {"type": "object", "properties": {"query": {"type": "string", "description": "Search term. E.g.: ZSD_QUOT* or ZCL_SD*"}, "max_results": {"type": "integer", "description": "Maximum number of results (default 20)"}}, "required": ["query"]},
        "handler": _h_search_objects,
    },
]

TOOLS += [
    {
        "name": "sap_get_usage_references",
        "description": f"Gets where-used references for an ABAP object in {SYS}. Supports classes, programs, includes, FMs, interfaces, tables, and structures.",
        "schema": {"type": "object", "properties": {"object_type": {"type": "string", "description": "Object type: class, program, include, function_module, interface, table, structure"}, "object_name": {"type": "string", "description": "ABAP object name. E.g.: ZCL_SD_HELPER, ZSD_QUOTATION"}, "function_group": {"type": "string", "description": "Function group (required only if object_type is function_module)"}}, "required": ["object_type", "object_name"]},
        "handler": _h_get_usage_references,
    },
    {
        "name": "sap_get_enhancements",
        "description": f"Gets enhancement implementations (BAdIs, user-exits) from an ABAP program or include in {SYS}. Automatically detects object type.",
        "schema": {"type": "object", "properties": {"object_name": {"type": "string", "description": "ABAP program or include name. E.g.: SAPMV45A, RM07DOCS_F01"}, "program_context": {"type": "string", "description": "Parent program (optional, only for includes if not automatically detected)"}}, "required": ["object_name"]},
        "handler": _h_get_enhancements,
    },
    {
        "name": "sap_get_sql_query",
        "description": f"Executes a freestyle SQL query in {SYS} via ADT Data Preview. Supports SELECT with JOINs, WHERE, GROUP BY, etc.",
        "schema": {"type": "object", "properties": {"sql_query": {"type": "string", "description": "SQL query to execute. E.g.: SELECT * FROM VBAK WHERE ERDAT >= '20240101'"}, "max_rows": {"type": "integer", "description": "Maximum rows to return (default 100)"}}, "required": ["sql_query"]},
        "handler": _h_get_sql_query,
    },
    {
        "name": "sap_get_includes_list",
        "description": f"Recursively discovers all INCLUDEs within an ABAP program or include in {SYS}. Builds the complete hierarchy.",
        "schema": {"type": "object", "properties": {"object_name": {"type": "string", "description": "Program or include name. E.g.: SAPMV45A, ZSD_MY_REPORT"}, "object_type": {"type": "string", "description": "Type: program or include (default: program)"}}, "required": ["object_name"]},
        "handler": _h_get_includes_list,
    },
    {
        "name": "sap_get_source_by_uri",
        "description": f"Gets ABAP source code by direct ADT URI in {SYS}. Useful for specific methods or fragments via URI.",
        "schema": {"type": "object", "properties": {"uri": {"type": "string", "description": "Full ADT URI. E.g.: /sap/bc/adt/oo/classes/zcl_sd_helper/source/main"}}, "required": ["uri"]},
        "handler": _h_get_source_by_uri,
    },
    {
        "name": "sap_create_program",
        "description": f"Creates a new ABAP program in {SYS}, writes the source code, and activates it.",
        "schema": {"type": "object", "properties": {"program_name": {"type": "string", "description": "Program name in uppercase. E.g.: ZR_SD_QUICK_ORDERS"}, "description": {"type": "string", "description": "Short program description"}, "package": {"type": "string", "description": "Development package. E.g.: ZDEV_SD, $TMP"}, "source_code": {"type": "string", "description": "Complete ABAP source code for the program"}, "transport": {"type": "string", "description": "Transport request. Leave empty for $TMP"}}, "required": ["program_name", "description", "package", "source_code"]},
        "handler": _h_create_program,
    },
    {
        "name": "sap_update_program_source",
        "description": f"Updates the source code of an existing ABAP program in {SYS}. Performs lock, write, and unlock.",
        "schema": {"type": "object", "properties": {"program_name": {"type": "string", "description": "Existing program name. E.g.: ZR_SD_QUICK_ORDERS"}, "source_code": {"type": "string", "description": "Complete ABAP source code (replaces all code)"}, "transport": {"type": "string", "description": "Transport request (optional)"}}, "required": ["program_name", "source_code"]},
        "handler": _h_update_program_source,
    },
    {
        "name": "sap_update_program_from_file",
        "description": f"Updates the source code of an ABAP program by reading from a local workspace file in {SYS}.",
        "schema": {"type": "object", "properties": {"program_name": {"type": "string", "description": "Existing program name in uppercase. E.g.: ZR_SD_TRANSPORT_CHECKER"}, "file_path": {"type": "string", "description": "Path to the .abap file relative to workspace. E.g.: ZR_SD_TRANSPORT_CHECKER/ZR_SD_TRANSPORT_CHECKER.abap"}, "transport": {"type": "string", "description": "Transport request (optional)"}}, "required": ["program_name", "file_path"]},
        "handler": _h_update_program_from_file,
    },
]

TOOLS += [
    {
        "name": "sap_create_class",
        "description": f"Creates a new ABAP OO class (CLAS/OC) in {SYS}, writes the source code, and activates it.",
        "schema": {"type": "object", "properties": {"class_name": {"type": "string", "description": "Class name in uppercase. E.g.: ZCL_SD_STOCK_QUERY"}, "description": {"type": "string", "description": "Short class description"}, "package": {"type": "string", "description": "Development package. E.g.: ZDEV_SD, $TMP"}, "source_code": {"type": "string", "description": "Complete ABAP source code for the class (CLASS DEFINITION + IMPLEMENTATION)"}, "transport": {"type": "string", "description": "Transport request. Leave empty for $TMP"}, "is_final": {"type": "boolean", "description": "Whether the class is FINAL (default: true)"}}, "required": ["class_name", "description", "package", "source_code"]},
        "handler": _h_create_class,
    },
    {
        "name": "sap_update_class_source",
        "description": f"Updates the source code of an existing ABAP OO class in {SYS}. Performs lock, write, and unlock.",
        "schema": {"type": "object", "properties": {"class_name": {"type": "string", "description": "Existing class name. E.g.: ZCL_SD_STOCK_QUERY"}, "source_code": {"type": "string", "description": "Complete ABAP source code (replaces all code)"}, "transport": {"type": "string", "description": "Transport request (optional)"}}, "required": ["class_name", "source_code"]},
        "handler": _h_update_class_source,
    },
    {
        "name": "sap_create_interface",
        "description": f"Creates a new ABAP OO interface (INTF/OI) in {SYS}, writes the source code, and activates it.",
        "schema": {"type": "object", "properties": {"interface_name": {"type": "string", "description": "Interface name in uppercase. E.g.: ZIF_SD_STOCK_DAO"}, "description": {"type": "string", "description": "Short interface description"}, "package": {"type": "string", "description": "Development package. E.g.: ZDEV_SD, $TMP"}, "source_code": {"type": "string", "description": "Complete ABAP source code for the interface"}, "transport": {"type": "string", "description": "Transport request. Leave empty for $TMP"}}, "required": ["interface_name", "description", "package", "source_code"]},
        "handler": _h_create_interface,
    },
    {
        "name": "sap_update_interface_source",
        "description": f"Updates the source code of an existing ABAP OO interface in {SYS}. Performs lock, write, and unlock.",
        "schema": {"type": "object", "properties": {"interface_name": {"type": "string", "description": "Existing interface name. E.g.: ZIF_SD_STOCK_DAO"}, "source_code": {"type": "string", "description": "Complete ABAP source code (replaces all code)"}, "transport": {"type": "string", "description": "Transport request (optional)"}}, "required": ["interface_name", "source_code"]},
        "handler": _h_update_interface_source,
    },
    {
        "name": "sap_create_structure",
        "description": f"Creates a new DDIC structure or table in {SYS} using DDL source, and activates it. Supports transparent tables and structures.",
        "schema": {"type": "object", "properties": {"structure_name": {"type": "string", "description": "Structure/table name. E.g.: ZZSD_MY_TABLE"}, "description": {"type": "string", "description": "Short description"}, "package": {"type": "string", "description": "Development package. E.g.: ZDEV_SD, $TMP"}, "source_code": {"type": "string", "description": "Complete DDL code. E.g.: @EndUserText.label : 'My Table'\\ndefine type zzsd_my_table {\\n  key mandt : mandt not null;\\n  key id : char10 not null;\\n  value : char40;\\n}"}, "transport": {"type": "string", "description": "Transport request. Leave empty for $TMP"}}, "required": ["structure_name", "description", "package", "source_code"]},
        "handler": _h_create_structure,
    },
    {
        "name": "sap_update_structure_source",
        "description": f"Updates the DDL source of an existing DDIC structure/table in {SYS}. Performs lock, write, and unlock.",
        "schema": {"type": "object", "properties": {"structure_name": {"type": "string", "description": "Existing structure/table name. E.g.: ZZSD_MY_TABLE"}, "source_code": {"type": "string", "description": "Complete DDL code (replaces all)"}, "transport": {"type": "string", "description": "Transport request (optional)"}}, "required": ["structure_name", "source_code"]},
        "handler": _h_update_structure_source,
    },
    {
        "name": "sap_update_function_module_source",
        "description": f"Updates the source code of an existing ABAP Function Module in {SYS}. Performs lock, write, and unlock.",
        "schema": {"type": "object", "properties": {"function_group": {"type": "string", "description": "Function group name. E.g.: ZSD_PPD"}, "function_name": {"type": "string", "description": "Function Module name. E.g.: ZSD_PPD_REJ_UPDATE"}, "source_code": {"type": "string", "description": "Complete ABAP source code for the FM (replaces all code)"}, "transport": {"type": "string", "description": "Transport request (optional)"}}, "required": ["function_group", "function_name", "source_code"]},
        "handler": _h_update_function_module_source,
    },
    {
        "name": "sap_patch_source",
        "description": f"Applies patch operations to ABAP source code in {SYS} without replacing the entire file. Supports insert, replace, delete, and search_replace by line or text.",
        "schema": {"type": "object", "properties": {"object_uri": {"type": "string", "description": "ADT object URI. E.g.: /sap/bc/adt/programs/programs/ZREPORT"}, "operations": {"type": "string", "description": "JSON array of operations. Types: insert({type,after_line,content}), replace({type,from_line,to_line,content}), delete({type,from_line,to_line}), search_replace({type,search,replace,all})"}, "transport": {"type": "string", "description": "Transport request (optional)"}}, "required": ["object_uri", "operations"]},
        "handler": _h_patch_source,
    },
    {
        "name": "sap_delete_object",
        "description": f"Deletes an ABAP object from the {SYS} system. IRREVERSIBLE. Requires the object URI and optionally a transport.",
        "schema": {"type": "object", "properties": {"object_uri": {"type": "string", "description": "ADT URI of the object to delete. E.g.: /sap/bc/adt/programs/programs/ZREPORT_OLD"}, "transport": {"type": "string", "description": "Transport request (required for objects in non-local packages)"}}, "required": ["object_uri"]},
        "handler": _h_delete_object,
    },
]

TOOLS += [
    {
        "name": "sap_activate_object",
        "description": f"Activates an ABAP object in {SYS} (program, class, interface, etc.).",
        "schema": {"type": "object", "properties": {"object_name": {"type": "string", "description": "Object name. E.g.: ZR_SD_QUICK_ORDERS"}, "object_type": {"type": "string", "description": "ADT object type. E.g.: PROG/P, CLAS/OC, INTF/OI, FUGR/F"}}, "required": ["object_name"]},
        "handler": _h_activate_object,
    },
    {
        "name": "sap_syntax_check",
        "description": f"Runs syntax check on an ABAP object in {SYS}. Returns compilation errors and warnings.",
        "schema": {"type": "object", "properties": {"object_url": {"type": "string", "description": "ADT object URI. E.g.: /sap/bc/adt/programs/programs/zr_sd_quick_orders"}}, "required": ["object_url"]},
        "handler": _h_syntax_check,
    },
    {
        "name": "sap_run_abap_unit",
        "description": f"Runs ABAP Unit tests for an ABAP object in {SYS}. Returns the test results.",
        "schema": {"type": "object", "properties": {"object_url": {"type": "string", "description": "ADT object URI. E.g.: /sap/bc/adt/oo/classes/zcl_sd_quick_orders_test"}}, "required": ["object_url"]},
        "handler": _h_run_abap_unit,
    },
    {
        "name": "sap_create_transport",
        "description": f"Creates a transport request (Workbench or Customizing Request) in {SYS}. Returns the transport and task numbers created.",
        "schema": {"type": "object", "properties": {"description": {"type": "string", "description": "Transport request description. E.g.: L2C:CHG0436752- EHP8 fix"}, "request_type": {"type": "string", "description": "Request type: K = Workbench (default), W = Customizing"}, "target": {"type": "string", "description": "Transport target system (optional)"}}, "required": ["description"]},
        "handler": _h_create_transport,
    },
    {
        "name": "sap_list_transports",
        "description": f"Lists modifiable (open) transport requests in {SYS}. Optionally filters by user.",
        "schema": {"type": "object", "properties": {"user": {"type": "string", "description": "SAP user to filter by (optional)."}}, "required": []},
        "handler": _h_list_transports,
    },
    {
        "name": "sap_get_transport_details",
        "description": f"Gets the details and objects contained in a specific transport request in {SYS}.",
        "schema": {"type": "object", "properties": {"transport_number": {"type": "string", "description": "Transport request number. E.g.: DEVK900001"}}, "required": ["transport_number"]},
        "handler": _h_get_transport_details,
    },
    {
        "name": "sap_get_transport_xml_raw",
        "description": f"Returns the raw CTS XML fragment for a specific transport request in {SYS}. Useful for diagnostics when get_transport_details does not show objects.",
        "schema": {"type": "object", "properties": {"transport_number": {"type": "string", "description": "Transport request number. E.g.: DEVK900002"}}, "required": ["transport_number"]},
        "handler": _h_get_transport_xml_raw,
    },
    {
        "name": "sap_release_transport",
        "description": f"Releases a transport request or task in {SYS}. Once released it cannot be modified. Verifies the release was successful.",
        "schema": {"type": "object", "properties": {"transport_number": {"type": "string", "description": "Transport request or task number to release. E.g.: DEVK900001"}}, "required": ["transport_number"]},
        "handler": _h_release_transport,
    },
    {
        "name": "sap_add_to_transport",
        "description": f"Registers an ABAP object in a transport request in {SYS}.",
        "schema": {"type": "object", "properties": {"object_uri": {"type": "string", "description": "ADT object URI. E.g.: /sap/bc/adt/programs/programs/ZR_SD_REPORT"}, "transport_number": {"type": "string", "description": "Transport number (task). E.g.: DEVK900003"}}, "required": ["object_uri", "transport_number"]},
        "handler": _h_add_to_transport,
    },
    {
        "name": "sap_create_transport_task",
        "description": f"Creates a task (Aufgabe) under an existing transport request in {SYS}.",
        "schema": {"type": "object", "properties": {"parent_transport": {"type": "string", "description": "Parent transport request number. E.g.: DEVK900001"}, "description": {"type": "string", "description": "Short task description"}, "owner": {"type": "string", "description": "SAP user who owns the task (optional, default: connected user)"}}, "required": ["parent_transport", "description"]},
        "handler": _h_create_transport_task,
    },
]


# ──────────────────────────────────────────────
# Build lookup for call_tool dispatch
# ──────────────────────────────────────────────
_TOOL_MAP = {t["name"]: t["handler"] for t in TOOLS}


# ──────────────────────────────────────────────
# MCP server handlers
# ──────────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name=t["name"], description=t["description"], inputSchema=t["schema"])
        for t in TOOLS
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    handler = _TOOL_MAP.get(name)
    if not handler:
        data = {"ok": False, "message": f"Unknown tool: {name}"}
    else:
        data = handler(arguments)
    return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
