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
SAP_HOST = os.environ.get("SAP_HOST", "fbpl08v010.holcimbp.net:8000")
SAP_CLIENT = os.environ.get("SAP_CLIENT", "130")
SAP_USER = os.environ.get("SAP_USER", "DAVILAESTEBA")
SAP_PASSWORD = os.environ.get("SAP_PASSWORD", "")
SAP_SECURE = os.environ.get("SAP_SECURE", "false").lower() == "true"
SAP_SYSTEM_ID = os.environ.get("SAP_SYSTEM_ID", "BZD")

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
    return {"ok": False, "message": "program_name es requerido"} if not p else sap.get_program_source(p)

def _h_get_class_source(args):
    c = args.get("class_name", "").upper()
    return {"ok": False, "message": "class_name es requerido"} if not c else sap.get_class_source(c)

def _h_get_include_source(args):
    i = args.get("include_name", "").upper()
    return {"ok": False, "message": "include_name es requerido"} if not i else sap.get_include_source(i)

def _h_get_interface_source(args):
    i = args.get("interface_name", "").upper()
    return {"ok": False, "message": "interface_name es requerido"} if not i else sap.get_interface_source(i)

def _h_get_function_module_source(args):
    fg = args.get("function_group", "").upper()
    fm = args.get("function_name", "").upper()
    if not fg or not fm:
        return {"ok": False, "message": "function_group y function_name son requeridos"}
    return sap.get_function_module_source(fg, fm)

def _h_get_function_group_source(args):
    fg = args.get("function_group", "").upper()
    return {"ok": False, "message": "function_group es requerido"} if not fg else sap.get_function_group_source(fg)

def _h_get_structure(args):
    s = args.get("structure_name", "").upper()
    return {"ok": False, "message": "structure_name es requerido"} if not s else sap.get_structure_source(s)

def _h_get_cds_view_source(args):
    c = args.get("cds_view_name", "").upper()
    return {"ok": False, "message": "cds_view_name es requerido"} if not c else sap.get_cds_view_source(c)

def _h_get_table_definition(args):
    t = args.get("table_name", "").upper()
    return {"ok": False, "message": "table_name es requerido"} if not t else sap.get_table_definition(t)

def _h_get_package_contents(args):
    p = args.get("package_name", "").upper()
    return {"ok": False, "message": "package_name es requerido"} if not p else sap.get_package_contents(p)

def _h_get_transaction_info(args):
    t = args.get("transaction_name", "").upper()
    return {"ok": False, "message": "transaction_name es requerido"} if not t else sap.get_transaction_info(t)

def _h_search_objects(args):
    q = args.get("query", "")
    return {"ok": False, "message": "query es requerido"} if not q else sap.search_objects(q, args.get("max_results", 20))

def _h_get_usage_references(args):
    ot = args.get("object_type", "")
    on = args.get("object_name", "")
    fg = args.get("function_group", "")
    if not ot or not on:
        return {"ok": False, "message": "object_type y object_name son requeridos"}
    return sap.get_usage_references(ot, on, fg)

def _h_get_enhancements(args):
    o = args.get("object_name", "").upper()
    if not o:
        return {"ok": False, "message": "object_name es requerido"}
    return sap.get_enhancements(o, args.get("program_context", ""))

def _h_get_sql_query(args):
    q = args.get("sql_query", "")
    if not q:
        return {"ok": False, "message": "sql_query es requerido"}
    return sap.get_sql_query(q, args.get("max_rows", 100))

def _h_get_includes_list(args):
    o = args.get("object_name", "").upper()
    if not o:
        return {"ok": False, "message": "object_name es requerido"}
    return sap.get_includes_list(o, args.get("object_type", "program"))

def _h_get_source_by_uri(args):
    u = args.get("uri", "")
    return {"ok": False, "message": "uri es requerido"} if not u else sap.get_source_by_uri(u)

def _h_create_program(args):
    n = args.get("program_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "program_name y source_code son requeridos"}
    return sap.create_program(n, args.get("description", ""), args.get("package", "$TMP").upper(),
                              args.get("transport", ""), src)

def _h_update_program_source(args):
    n = args.get("program_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "program_name y source_code son requeridos"}
    return sap.update_program_source(n, src, args.get("transport", ""))

def _h_update_program_from_file(args):
    n = args.get("program_name", "").upper()
    f = args.get("file_path", "")
    if not n or not f:
        return {"ok": False, "message": "program_name y file_path son requeridos"}
    return sap.update_program_from_file(n, f, args.get("transport", ""))

def _h_create_class(args):
    n = args.get("class_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "class_name y source_code son requeridos"}
    return sap.create_class(n, args.get("description", ""), args.get("package", "$TMP").upper(),
                            args.get("transport", ""), src, args.get("is_final", True))

def _h_update_class_source(args):
    n = args.get("class_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "class_name y source_code son requeridos"}
    return sap.update_class_source(n, src, args.get("transport", ""))

def _h_create_interface(args):
    n = args.get("interface_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "interface_name y source_code son requeridos"}
    return sap.create_interface(n, args.get("description", ""), args.get("package", "$TMP").upper(),
                                args.get("transport", ""), src)

def _h_update_interface_source(args):
    n = args.get("interface_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "interface_name y source_code son requeridos"}
    return sap.update_interface_source(n, src, args.get("transport", ""))

def _h_create_structure(args):
    n = args.get("structure_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "structure_name y source_code son requeridos"}
    return sap.create_structure(n, args.get("description", ""), args.get("package", "$TMP").upper(),
                                args.get("transport", ""), src)

def _h_update_structure_source(args):
    n = args.get("structure_name", "").upper()
    src = args.get("source_code", "")
    if not n or not src:
        return {"ok": False, "message": "structure_name y source_code son requeridos"}
    return sap.update_structure_source(n, src, args.get("transport", ""))

def _h_update_function_module_source(args):
    fg = args.get("function_group", "").upper()
    fm = args.get("function_name", "").upper()
    src = args.get("source_code", "")
    if not fg or not fm or not src:
        return {"ok": False, "message": "function_group, function_name y source_code son requeridos"}
    return sap.update_function_module_source(fg, fm, src, args.get("transport", ""))

def _h_patch_source(args):
    uri = args.get("object_uri", "")
    ops_raw = args.get("operations", "")
    if not uri or not ops_raw:
        return {"ok": False, "message": "object_uri y operations son requeridos"}
    try:
        ops = json.loads(ops_raw) if isinstance(ops_raw, str) else ops_raw
    except json.JSONDecodeError as e:
        return {"ok": False, "message": f"operations JSON inválido: {e}"}
    return sap.patch_source(uri, ops, args.get("transport", ""))

def _h_delete_object(args):
    uri = args.get("object_uri", "")
    return {"ok": False, "message": "object_uri es requerido"} if not uri else sap.delete_object(uri, args.get("transport", ""))

def _h_activate_object(args):
    n = args.get("object_name", "").upper()
    if not n:
        return {"ok": False, "message": "object_name es requerido"}
    return sap.activate_object(n, args.get("object_type", "PROG/P"))

def _h_syntax_check(args):
    u = args.get("object_url", "")
    return {"ok": False, "message": "object_url es requerido"} if not u else sap.syntax_check(u)

def _h_run_abap_unit(args):
    u = args.get("object_url", "")
    return {"ok": False, "message": "object_url es requerido"} if not u else sap.run_abap_unit(u)

def _h_create_transport(args):
    d = args.get("description", "")
    if not d:
        return {"ok": False, "message": "description es requerido"}
    return sap.create_transport(d, args.get("request_type", "K"), args.get("target", ""))

def _h_list_transports(args):
    return sap.list_transports(args.get("user", ""))

def _h_get_transport_details(args):
    t = args.get("transport_number", "").upper()
    return {"ok": False, "message": "transport_number es requerido"} if not t else sap.get_transport_details(t)

def _h_get_transport_xml_raw(args):
    t = args.get("transport_number", "").upper()
    return {"ok": False, "message": "transport_number es requerido"} if not t else sap.get_transport_xml_raw(t)

def _h_release_transport(args):
    t = args.get("transport_number", "").upper()
    return {"ok": False, "message": "transport_number es requerido"} if not t else sap.release_transport(t)

def _h_add_to_transport(args):
    uri = args.get("object_uri", "")
    t = args.get("transport_number", "").upper()
    if not uri or not t:
        return {"ok": False, "message": "object_uri y transport_number son requeridos"}
    return sap.add_to_transport(uri, t)

def _h_create_transport_task(args):
    p = args.get("parent_transport", "").upper()
    d = args.get("description", "")
    if not p or not d:
        return {"ok": False, "message": "parent_transport y description son requeridos"}
    return sap.create_transport_task(p, d, args.get("owner", ""))


# ──────────────────────────────────────────────
# Data-driven tool registry (35 tools)
# ──────────────────────────────────────────────

TOOLS = [
    {
        "name": "sap_ping",
        "description": f"Verifica la conectividad con el sistema {SYS}. Úsalo para confirmar que el servidor MCP puede hablar con SAP.",
        "schema": {"type": "object", "properties": {}, "required": []},
        "handler": _h_ping,
    },
    {
        "name": "sap_get_program_source",
        "description": f"Obtiene el código fuente ABAP de un programa o report (objetos tipo PROG) en {SYS}.",
        "schema": {"type": "object", "properties": {"program_name": {"type": "string", "description": "Nombre del programa ABAP en mayúsculas. Ej: ZREPORTE_VENTAS"}}, "required": ["program_name"]},
        "handler": _h_get_program_source,
    },
    {
        "name": "sap_get_class_source",
        "description": f"Obtiene el código fuente de una clase ABAP OO (ZCL_*, LCL_*, etc.) en {SYS}.",
        "schema": {"type": "object", "properties": {"class_name": {"type": "string", "description": "Nombre de la clase ABAP. Ej: ZCL_SD_HELPER"}}, "required": ["class_name"]},
        "handler": _h_get_class_source,
    },
    {
        "name": "sap_get_include_source",
        "description": f"Obtiene el código fuente de un INCLUDE ABAP en {SYS}.",
        "schema": {"type": "object", "properties": {"include_name": {"type": "string", "description": "Nombre del include ABAP en mayúsculas. Ej: ZSDR_DAILY_INVOICE_REPORT_TOP"}}, "required": ["include_name"]},
        "handler": _h_get_include_source,
    },
    {
        "name": "sap_get_interface_source",
        "description": f"Obtiene el código fuente de una interfaz ABAP OO (ZIF_*, IF_*) en {SYS}.",
        "schema": {"type": "object", "properties": {"interface_name": {"type": "string", "description": "Nombre de la interfaz ABAP. Ej: ZIF_SD_STOCK_DAO"}}, "required": ["interface_name"]},
        "handler": _h_get_interface_source,
    },
    {
        "name": "sap_get_function_module_source",
        "description": f"Obtiene el código fuente de un Function Module ABAP en {SYS}.",
        "schema": {"type": "object", "properties": {"function_group": {"type": "string", "description": "Nombre del grupo de funciones. Ej: ZSD_QUOTATION"}, "function_name": {"type": "string", "description": "Nombre del Function Module. Ej: ZSD_QUOTATION_SALSFRC_CHANGE"}}, "required": ["function_group", "function_name"]},
        "handler": _h_get_function_module_source,
    },
    {
        "name": "sap_get_function_group_source",
        "description": f"Obtiene el código fuente de un Function Group ABAP en {SYS}.",
        "schema": {"type": "object", "properties": {"function_group": {"type": "string", "description": "Nombre del grupo de funciones. Ej: ZSD_QUOTATION"}}, "required": ["function_group"]},
        "handler": _h_get_function_group_source,
    },
    {
        "name": "sap_get_structure",
        "description": f"Obtiene la definición fuente de una estructura DDIC (SE11) en {SYS}.",
        "schema": {"type": "object", "properties": {"structure_name": {"type": "string", "description": "Nombre de la estructura DDIC. Ej: ZSSD_QUOTATION_ITEM"}}, "required": ["structure_name"]},
        "handler": _h_get_structure,
    },
    {
        "name": "sap_get_cds_view_source",
        "description": f"Obtiene el código fuente DDL de una CDS View en {SYS}.",
        "schema": {"type": "object", "properties": {"cds_view_name": {"type": "string", "description": "Nombre de la CDS view (DDL source). Ej: I_CURRENCY, ZI_SD_ORDERS"}}, "required": ["cds_view_name"]},
        "handler": _h_get_cds_view_source,
    },
    {
        "name": "sap_get_table_definition",
        "description": f"Obtiene la definición de una tabla del diccionario ABAP en {SYS} (campos, tipos, longitudes).",
        "schema": {"type": "object", "properties": {"table_name": {"type": "string", "description": "Nombre de la tabla ABAP. Ej: ZZSD_QUOTATION o VBAK"}}, "required": ["table_name"]},
        "handler": _h_get_table_definition,
    },
    {
        "name": "sap_get_package_contents",
        "description": f"Obtiene los objetos contenidos en un paquete de desarrollo ABAP en {SYS}. Lista programas, clases, FMs, etc.",
        "schema": {"type": "object", "properties": {"package_name": {"type": "string", "description": "Nombre del paquete. Ej: ZSD_QUOTATION, ZDEV_SD"}}, "required": ["package_name"]},
        "handler": _h_get_package_contents,
    },
    {
        "name": "sap_get_transaction_info",
        "description": f"Obtiene información de una transacción ABAP en {SYS} (paquete, aplicación asociada).",
        "schema": {"type": "object", "properties": {"transaction_name": {"type": "string", "description": "Nombre de la transacción. Ej: VA01, ZSD_MONITOR"}}, "required": ["transaction_name"]},
        "handler": _h_get_transaction_info,
    },
    {
        "name": "sap_search_objects",
        "description": f"Busca objetos ABAP en el repositorio de {SYS} por nombre o patrón. Útil para encontrar Z* o Y* objetos.",
        "schema": {"type": "object", "properties": {"query": {"type": "string", "description": "Término de búsqueda. Ej: ZSD_QUOT* o ZCL_SD*"}, "max_results": {"type": "integer", "description": "Número máximo de resultados (default 20)"}}, "required": ["query"]},
        "handler": _h_search_objects,
    },
]

TOOLS += [
    {
        "name": "sap_get_usage_references",
        "description": f"Obtiene where-used references (dónde se usa) un objeto ABAP en {SYS}. Soporta clases, programas, includes, FMs, interfaces, tablas y estructuras.",
        "schema": {"type": "object", "properties": {"object_type": {"type": "string", "description": "Tipo de objeto: class, program, include, function_module, interface, table, structure"}, "object_name": {"type": "string", "description": "Nombre del objeto ABAP. Ej: ZCL_SD_HELPER, ZSD_QUOTATION"}, "function_group": {"type": "string", "description": "Grupo de funciones (requerido solo si object_type es function_module)"}}, "required": ["object_type", "object_name"]},
        "handler": _h_get_usage_references,
    },
    {
        "name": "sap_get_enhancements",
        "description": f"Obtiene enhancement implementations (BAdIs, user-exits) de un programa o include ABAP en {SYS}. Detecta automáticamente tipo de objeto.",
        "schema": {"type": "object", "properties": {"object_name": {"type": "string", "description": "Nombre del programa o include ABAP. Ej: SAPMV45A, RM07DOCS_F01"}, "program_context": {"type": "string", "description": "Programa padre (opcional, solo para includes si no se detecta automáticamente)"}}, "required": ["object_name"]},
        "handler": _h_get_enhancements,
    },
    {
        "name": "sap_get_sql_query",
        "description": f"Ejecuta una consulta SQL freestyle en {SYS} via ADT Data Preview. Soporta SELECT con JOINs, WHERE, GROUP BY, etc.",
        "schema": {"type": "object", "properties": {"sql_query": {"type": "string", "description": "Consulta SQL a ejecutar. Ej: SELECT * FROM VBAK WHERE ERDAT >= '20240101'"}, "max_rows": {"type": "integer", "description": "Máximo de filas a retornar (default 100)"}}, "required": ["sql_query"]},
        "handler": _h_get_sql_query,
    },
    {
        "name": "sap_get_includes_list",
        "description": f"Descubre recursivamente todos los INCLUDEs dentro de un programa o include ABAP en {SYS}. Construye la jerarquía completa.",
        "schema": {"type": "object", "properties": {"object_name": {"type": "string", "description": "Nombre del programa o include. Ej: SAPMV45A, ZSDR_DAILY_INVOICE_REPORT"}, "object_type": {"type": "string", "description": "Tipo: program o include (default: program)"}}, "required": ["object_name"]},
        "handler": _h_get_includes_list,
    },
    {
        "name": "sap_get_source_by_uri",
        "description": f"Obtiene código fuente ABAP por URI ADT directa en {SYS}. Útil para métodos específicos o fragmentos vía URI.",
        "schema": {"type": "object", "properties": {"uri": {"type": "string", "description": "URI ADT completa. Ej: /sap/bc/adt/oo/classes/zcl_sd_helper/source/main"}}, "required": ["uri"]},
        "handler": _h_get_source_by_uri,
    },
    {
        "name": "sap_create_program",
        "description": f"Crea un programa ABAP nuevo en {SYS}, escribe el código fuente y lo activa.",
        "schema": {"type": "object", "properties": {"program_name": {"type": "string", "description": "Nombre del programa en mayúsculas. Ej: ZR_SD_QUICK_ORDERS"}, "description": {"type": "string", "description": "Descripción corta del programa"}, "package": {"type": "string", "description": "Paquete de desarrollo. Ej: ZDEV_SD, $TMP"}, "source_code": {"type": "string", "description": "Código fuente ABAP completo del programa"}, "transport": {"type": "string", "description": "Orden de transporte. Dejar vacío para $TMP"}}, "required": ["program_name", "description", "package", "source_code"]},
        "handler": _h_create_program,
    },
    {
        "name": "sap_update_program_source",
        "description": f"Actualiza el código fuente de un programa ABAP existente en {SYS}. Hace lock, escribe y unlock.",
        "schema": {"type": "object", "properties": {"program_name": {"type": "string", "description": "Nombre del programa existente. Ej: ZR_SD_QUICK_ORDERS"}, "source_code": {"type": "string", "description": "Código fuente ABAP completo (reemplaza todo el código)"}, "transport": {"type": "string", "description": "Orden de transporte (opcional)"}}, "required": ["program_name", "source_code"]},
        "handler": _h_update_program_source,
    },
    {
        "name": "sap_update_program_from_file",
        "description": f"Actualiza el código fuente de un programa ABAP leyendo desde un archivo local del workspace en {SYS}.",
        "schema": {"type": "object", "properties": {"program_name": {"type": "string", "description": "Nombre del programa existente en mayúsculas. Ej: ZR_SD_TRANSPORT_CHECKER"}, "file_path": {"type": "string", "description": "Ruta al archivo .abap relativa al workspace. Ej: ZR_SD_TRANSPORT_CHECKER/ZR_SD_TRANSPORT_CHECKER.abap"}, "transport": {"type": "string", "description": "Orden de transporte (opcional)"}}, "required": ["program_name", "file_path"]},
        "handler": _h_update_program_from_file,
    },
]

TOOLS += [
    {
        "name": "sap_create_class",
        "description": f"Crea una clase ABAP OO nueva (CLAS/OC) en {SYS}, escribe el código fuente y la activa.",
        "schema": {"type": "object", "properties": {"class_name": {"type": "string", "description": "Nombre de la clase en mayúsculas. Ej: ZCL_SD_STOCK_QUERY"}, "description": {"type": "string", "description": "Descripción corta de la clase"}, "package": {"type": "string", "description": "Paquete de desarrollo. Ej: ZDEV_SD, $TMP"}, "source_code": {"type": "string", "description": "Código fuente ABAP completo de la clase (CLASS DEFINITION + IMPLEMENTATION)"}, "transport": {"type": "string", "description": "Orden de transporte. Dejar vacío para $TMP"}, "is_final": {"type": "boolean", "description": "Si la clase es FINAL (default: true)"}}, "required": ["class_name", "description", "package", "source_code"]},
        "handler": _h_create_class,
    },
    {
        "name": "sap_update_class_source",
        "description": f"Actualiza el código fuente de una clase ABAP OO existente en {SYS}. Hace lock, escribe y unlock.",
        "schema": {"type": "object", "properties": {"class_name": {"type": "string", "description": "Nombre de la clase existente. Ej: ZCL_SD_STOCK_QUERY"}, "source_code": {"type": "string", "description": "Código fuente ABAP completo (reemplaza todo el código)"}, "transport": {"type": "string", "description": "Orden de transporte (opcional)"}}, "required": ["class_name", "source_code"]},
        "handler": _h_update_class_source,
    },
    {
        "name": "sap_create_interface",
        "description": f"Crea una interfaz ABAP OO nueva (INTF/OI) en {SYS}, escribe el código fuente y la activa.",
        "schema": {"type": "object", "properties": {"interface_name": {"type": "string", "description": "Nombre de la interfaz en mayúsculas. Ej: ZIF_SD_STOCK_DAO"}, "description": {"type": "string", "description": "Descripción corta de la interfaz"}, "package": {"type": "string", "description": "Paquete de desarrollo. Ej: ZDEV_SD, $TMP"}, "source_code": {"type": "string", "description": "Código fuente ABAP completo de la interfaz"}, "transport": {"type": "string", "description": "Orden de transporte. Dejar vacío para $TMP"}}, "required": ["interface_name", "description", "package", "source_code"]},
        "handler": _h_create_interface,
    },
    {
        "name": "sap_update_interface_source",
        "description": f"Actualiza el código fuente de una interfaz ABAP OO existente en {SYS}. Hace lock, escribe y unlock.",
        "schema": {"type": "object", "properties": {"interface_name": {"type": "string", "description": "Nombre de la interfaz existente. Ej: ZIF_SD_STOCK_DAO"}, "source_code": {"type": "string", "description": "Código fuente ABAP completo (reemplaza todo el código)"}, "transport": {"type": "string", "description": "Orden de transporte (opcional)"}}, "required": ["interface_name", "source_code"]},
        "handler": _h_update_interface_source,
    },
    {
        "name": "sap_create_structure",
        "description": f"Crea una estructura o tabla DDIC nueva en {SYS} usando DDL source, y la activa. Soporta tablas transparentes y estructuras.",
        "schema": {"type": "object", "properties": {"structure_name": {"type": "string", "description": "Nombre de la estructura/tabla. Ej: ZZSD_MY_TABLE"}, "description": {"type": "string", "description": "Descripción corta"}, "package": {"type": "string", "description": "Paquete de desarrollo. Ej: ZDEV_SD, $TMP"}, "source_code": {"type": "string", "description": "Código DDL completo. Ej: @EndUserText.label : 'My Table'\\ndefine type zzsd_my_table {\\n  key mandt : mandt not null;\\n  key id : char10 not null;\\n  value : char40;\\n}"}, "transport": {"type": "string", "description": "Orden de transporte. Dejar vacío para $TMP"}}, "required": ["structure_name", "description", "package", "source_code"]},
        "handler": _h_create_structure,
    },
    {
        "name": "sap_update_structure_source",
        "description": f"Actualiza el DDL source de una estructura/tabla DDIC existente en {SYS}. Hace lock, escribe y unlock.",
        "schema": {"type": "object", "properties": {"structure_name": {"type": "string", "description": "Nombre de la estructura/tabla existente. Ej: ZZSD_MY_TABLE"}, "source_code": {"type": "string", "description": "Código DDL completo (reemplaza todo)"}, "transport": {"type": "string", "description": "Orden de transporte (opcional)"}}, "required": ["structure_name", "source_code"]},
        "handler": _h_update_structure_source,
    },
    {
        "name": "sap_update_function_module_source",
        "description": f"Actualiza el código fuente de un Function Module ABAP existente en {SYS}. Hace lock, escribe y unlock.",
        "schema": {"type": "object", "properties": {"function_group": {"type": "string", "description": "Nombre del grupo de funciones. Ej: ZSD_PPD"}, "function_name": {"type": "string", "description": "Nombre del Function Module. Ej: ZSD_PPD_REJ_UPDATE"}, "source_code": {"type": "string", "description": "Código fuente ABAP completo del FM (reemplaza todo el código)"}, "transport": {"type": "string", "description": "Orden de transporte (opcional)"}}, "required": ["function_group", "function_name", "source_code"]},
        "handler": _h_update_function_module_source,
    },
    {
        "name": "sap_patch_source",
        "description": f"Aplica operaciones de patch al código fuente ABAP en {SYS} sin reemplazar todo el archivo. Soporta insert, replace, delete y search_replace por línea o texto.",
        "schema": {"type": "object", "properties": {"object_uri": {"type": "string", "description": "URI ADT del objeto. Ej: /sap/bc/adt/programs/programs/ZREPORT"}, "operations": {"type": "string", "description": "JSON array de operaciones. Tipos: insert({type,after_line,content}), replace({type,from_line,to_line,content}), delete({type,from_line,to_line}), search_replace({type,search,replace,all})"}, "transport": {"type": "string", "description": "Orden de transporte (opcional)"}}, "required": ["object_uri", "operations"]},
        "handler": _h_patch_source,
    },
    {
        "name": "sap_delete_object",
        "description": f"Elimina un objeto ABAP del sistema {SYS}. IRREVERSIBLE. Requiere URI del objeto y opcionalmente transporte.",
        "schema": {"type": "object", "properties": {"object_uri": {"type": "string", "description": "URI ADT del objeto a eliminar. Ej: /sap/bc/adt/programs/programs/ZREPORT_OLD"}, "transport": {"type": "string", "description": "Orden de transporte (requerido para objetos en paquetes no-locales)"}}, "required": ["object_uri"]},
        "handler": _h_delete_object,
    },
]

TOOLS += [
    {
        "name": "sap_activate_object",
        "description": f"Activa un objeto ABAP en {SYS} (programa, clase, interfaz, etc.).",
        "schema": {"type": "object", "properties": {"object_name": {"type": "string", "description": "Nombre del objeto. Ej: ZR_SD_QUICK_ORDERS"}, "object_type": {"type": "string", "description": "Tipo del objeto ADT. Ej: PROG/P, CLAS/OC, INTF/OI, FUGR/F"}}, "required": ["object_name"]},
        "handler": _h_activate_object,
    },
    {
        "name": "sap_syntax_check",
        "description": f"Ejecuta syntax check de un objeto ABAP en {SYS}. Retorna errores y warnings de compilación.",
        "schema": {"type": "object", "properties": {"object_url": {"type": "string", "description": "URI ADT del objeto. Ej: /sap/bc/adt/programs/programs/zr_sd_quick_orders"}}, "required": ["object_url"]},
        "handler": _h_syntax_check,
    },
    {
        "name": "sap_run_abap_unit",
        "description": f"Ejecuta ABAP Unit tests para un objeto ABAP en {SYS}. Retorna los resultados de los tests.",
        "schema": {"type": "object", "properties": {"object_url": {"type": "string", "description": "URI ADT del objeto. Ej: /sap/bc/adt/oo/classes/zcl_sd_quick_orders_test"}}, "required": ["object_url"]},
        "handler": _h_run_abap_unit,
    },
    {
        "name": "sap_create_transport",
        "description": f"Crea una orden de transporte (Workbench o Customizing Request) en {SYS}. Retorna el número de OT y task creados.",
        "schema": {"type": "object", "properties": {"description": {"type": "string", "description": "Descripción de la orden de transporte. Ej: L2C:CHG0436752- EHP8 fix"}, "request_type": {"type": "string", "description": "Tipo de request: K = Workbench (default), W = Customizing"}, "target": {"type": "string", "description": "Sistema destino del transporte (opcional)"}}, "required": ["description"]},
        "handler": _h_create_transport,
    },
    {
        "name": "sap_list_transports",
        "description": f"Lista las órdenes de transporte modificables (abiertas) en {SYS}. Opcionalmente filtra por usuario.",
        "schema": {"type": "object", "properties": {"user": {"type": "string", "description": "Usuario SAP para filtrar (opcional)."}}, "required": []},
        "handler": _h_list_transports,
    },
    {
        "name": "sap_get_transport_details",
        "description": f"Obtiene los detalles y objetos contenidos en una orden de transporte específica en {SYS}.",
        "schema": {"type": "object", "properties": {"transport_number": {"type": "string", "description": "Número de la orden de transporte. Ej: BZDK924618"}}, "required": ["transport_number"]},
        "handler": _h_get_transport_details,
    },
    {
        "name": "sap_get_transport_xml_raw",
        "description": f"Retorna el fragmento XML crudo del CTS para una OT específica en {SYS}. Útil para diagnóstico cuando get_transport_details no muestra objetos.",
        "schema": {"type": "object", "properties": {"transport_number": {"type": "string", "description": "Número de la orden de transporte. Ej: BZDK931030"}}, "required": ["transport_number"]},
        "handler": _h_get_transport_xml_raw,
    },
    {
        "name": "sap_release_transport",
        "description": f"Libera (release) una orden de transporte o task en {SYS}. Una vez liberada no se puede modificar. Verifica que la liberación fue exitosa.",
        "schema": {"type": "object", "properties": {"transport_number": {"type": "string", "description": "Número de la OT o task a liberar. Ej: BZDK924618"}}, "required": ["transport_number"]},
        "handler": _h_release_transport,
    },
    {
        "name": "sap_add_to_transport",
        "description": f"Registra un objeto ABAP en una orden de transporte en {SYS}.",
        "schema": {"type": "object", "properties": {"object_uri": {"type": "string", "description": "URI ADT del objeto. Ej: /sap/bc/adt/programs/programs/ZR_SD_REPORT"}, "transport_number": {"type": "string", "description": "Número del transporte (task). Ej: BZDK924619"}}, "required": ["object_uri", "transport_number"]},
        "handler": _h_add_to_transport,
    },
    {
        "name": "sap_create_transport_task",
        "description": f"Crea una task (Aufgabe) bajo una orden de transporte existente en {SYS}.",
        "schema": {"type": "object", "properties": {"parent_transport": {"type": "string", "description": "Número de la orden padre. Ej: BZDK924618"}, "description": {"type": "string", "description": "Descripción corta de la task"}, "owner": {"type": "string", "description": "Usuario SAP dueño de la task (opcional, default: usuario conectado)"}}, "required": ["parent_transport", "description"]},
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
        data = {"ok": False, "message": f"Herramienta desconocida: {name}"}
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
