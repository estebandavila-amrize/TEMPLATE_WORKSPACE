"""
SAP MCP Server (Multi-System)
MCP Server en Python para conectar Kiro con sistemas SAP via ADT REST API.
Soporta múltiples instancias (DEV, SBX, etc.) usando SAP_SYSTEM_ID.
Transport: stdio (requerido por Kiro)
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
# Configuración de conexión SAP
# Sin defaults reales: todo viene de env vars, configuradas por install.bat
# a partir de config-systems.json (nunca hardcodear host/usuario/cliente aquí).
# ──────────────────────────────────────────────
SAP_HOST     = os.environ.get("SAP_HOST",     "")
SAP_CLIENT   = os.environ.get("SAP_CLIENT",   "")
SAP_USER     = os.environ.get("SAP_USER",     "")
SAP_PASSWORD = os.environ.get("SAP_PASSWORD", "")
SAP_SECURE   = os.environ.get("SAP_SECURE",   "false").lower() == "true"
SAP_SYSTEM_ID = os.environ.get("SAP_SYSTEM_ID", "")
# Opcionales — solo algunos sistemas SAP requieren gestión de proyecto CTS
SAP_CTS_PROJECT = os.environ.get("SAP_CTS_PROJECT", "")
SAP_TRANSPORT_LAYER = os.environ.get("SAP_TRANSPORT_LAYER", "")

# Instancia global del cliente ADT
sap = SAPADTClient(
    host=SAP_HOST,
    client=SAP_CLIENT,
    username=SAP_USER,
    password=SAP_PASSWORD,
    secure=SAP_SECURE,
    cts_project=SAP_CTS_PROJECT,
    transport_layer=SAP_TRANSPORT_LAYER,
)

# ──────────────────────────────────────────────
# Crear el servidor MCP con nombre dinámico
# ──────────────────────────────────────────────
server = Server(f"sap-{SAP_SYSTEM_ID.lower()}-mcp")

SYS_LABEL = f"SAP {SAP_SYSTEM_ID} {SAP_CLIENT}"


# ──────────────────────────────────────────────
# Lista de herramientas disponibles
# ──────────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="sap_ping",
            description=f"Verifica la conectividad con el sistema {SYS_LABEL}. Úsalo para confirmar que el servidor MCP puede hablar con SAP.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="sap_get_program_source",
            description=f"Obtiene el código fuente ABAP de un programa o report (objetos tipo PROG) en {SYS_LABEL}. Ejemplo: ZREPORTE_VENTAS.",
            inputSchema={
                "type": "object",
                "properties": {
                    "program_name": {
                        "type": "string",
                        "description": "Nombre del programa ABAP en mayúsculas. Ej: ZREPORTE_VENTAS"
                    }
                },
                "required": ["program_name"]
            }
        ),
        types.Tool(
            name="sap_get_class_source",
            description=f"Obtiene el código fuente de una clase ABAP OO (ZCL_*, LCL_*, etc.) en {SYS_LABEL}.",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "Nombre de la clase ABAP. Ej: ZCL_SD_HELPER"
                    }
                },
                "required": ["class_name"]
            }
        ),
        types.Tool(
            name="sap_get_function_module_source",
            description=f"Obtiene el código fuente de un Function Module ABAP en {SYS_LABEL}. Necesitas el nombre del grupo de funciones y el nombre del FM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "function_group": {
                        "type": "string",
                        "description": "Nombre del grupo de funciones. Ej: ZSD_QUOTATION"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Nombre del Function Module. Ej: ZSD_QUOTATION_SALSFRC_CHANGE"
                    }
                },
                "required": ["function_group", "function_name"]
            }
        ),
        types.Tool(
            name="sap_get_include_source",
            description=f"Obtiene el código fuente de un INCLUDE ABAP en {SYS_LABEL}.",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_name": {
                        "type": "string",
                        "description": "Nombre del include ABAP en mayúsculas. Ej: ZSDR_DAILY_INVOICE_REPORT_TOP"
                    }
                },
                "required": ["include_name"]
            }
        ),
        types.Tool(
            name="sap_search_objects",
            description=f"Busca objetos ABAP en el repositorio de {SYS_LABEL} por nombre o patrón. Útil para encontrar Z* o Y* objetos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda. Ej: ZSD_QUOT* o ZCL_SD*"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Número máximo de resultados (default 20)",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="sap_get_table_definition",
            description=f"Obtiene la definición de una tabla del diccionario ABAP en {SYS_LABEL} (campos, tipos, longitudes).",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Nombre de la tabla ABAP. Ej: ZZSD_QUOTATION o VBAK"
                    }
                },
                "required": ["table_name"]
            }
        ),
        types.Tool(
            name="sap_check_adt_capabilities",
            description=f"Lista todos los servicios ADT disponibles en {SYS_LABEL}. Útil para verificar qué operaciones soporta el sistema (lectura, escritura, activación, etc.).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="sap_test_endpoint",
            description=f"Prueba un endpoint ADT específico en {SYS_LABEL} para verificar si está disponible y responde. Útil para diagnóstico.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path del endpoint ADT. Ej: /sap/bc/adt/programs/programs"
                    },
                    "method": {
                        "type": "string",
                        "description": "Método HTTP: GET, HEAD, OPTIONS. Default: GET",
                        "default": "GET"
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="sap_create_interface",
            description=f"Crea una interfaz ABAP OO nueva (INTF/OI) en {SYS_LABEL}, escribe el código fuente y la activa.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface_name": {
                        "type": "string",
                        "description": "Nombre de la interfaz en mayúsculas. Ej: ZIF_SD_STOCK_DAO"
                    },
                    "description": {
                        "type": "string",
                        "description": "Descripción corta de la interfaz"
                    },
                    "package": {
                        "type": "string",
                        "description": "Paquete de desarrollo. Ej: ZDEV_SD, $TMP"
                    },
                    "transport": {
                        "type": "string",
                        "description": "Orden de transporte. Dejar vacío para $TMP"
                    },
                    "source_code": {
                        "type": "string",
                        "description": "Código fuente ABAP completo de la interfaz"
                    }
                },
                "required": ["interface_name", "description", "package", "source_code"]
            }
        ),
        types.Tool(
            name="sap_create_class",
            description=f"Crea una clase ABAP OO nueva (CLAS/OC) en {SYS_LABEL}, escribe el código fuente y la activa.",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "Nombre de la clase en mayúsculas. Ej: ZCL_SD_STOCK_QUERY"
                    },
                    "description": {
                        "type": "string",
                        "description": "Descripción corta de la clase"
                    },
                    "package": {
                        "type": "string",
                        "description": "Paquete de desarrollo. Ej: ZDEV_SD, $TMP"
                    },
                    "transport": {
                        "type": "string",
                        "description": "Orden de transporte. Dejar vacío para $TMP"
                    },
                    "source_code": {
                        "type": "string",
                        "description": "Código fuente ABAP completo de la clase (CLASS DEFINITION + IMPLEMENTATION)"
                    },
                    "is_final": {
                        "type": "boolean",
                        "description": "Si la clase es FINAL (default: true)",
                        "default": True
                    }
                },
                "required": ["class_name", "description", "package", "source_code"]
            }
        ),
        types.Tool(
            name="sap_update_class_source",
            description=f"Actualiza el código fuente de una clase ABAP OO existente en {SYS_LABEL}. Hace lock, escribe y unlock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "Nombre de la clase existente. Ej: ZCL_SD_STOCK_QUERY"
                    },
                    "source_code": {
                        "type": "string",
                        "description": "Código fuente ABAP completo (reemplaza todo el código)"
                    },
                    "transport": {
                        "type": "string",
                        "description": "Orden de transporte (opcional)"
                    }
                },
                "required": ["class_name", "source_code"]
            }
        ),
        types.Tool(
            name="sap_update_interface_source",
            description=f"Actualiza el código fuente de una interfaz ABAP OO existente en {SYS_LABEL}. Hace lock, escribe y unlock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface_name": {
                        "type": "string",
                        "description": "Nombre de la interfaz existente. Ej: ZIF_SD_STOCK_DAO"
                    },
                    "source_code": {
                        "type": "string",
                        "description": "Código fuente ABAP completo (reemplaza todo el código)"
                    },
                    "transport": {
                        "type": "string",
                        "description": "Orden de transporte (opcional)"
                    }
                },
                "required": ["interface_name", "source_code"]
            }
        ),
        types.Tool(
            name="sap_create_program",
            description=f"Crea un programa ABAP nuevo en {SYS_LABEL}, escribe el código fuente y lo activa. Requiere nombre, descripción, paquete, orden de transporte y código fuente.",
            inputSchema={
                "type": "object",
                "properties": {
                    "program_name": {
                        "type": "string",
                        "description": "Nombre del programa en mayúsculas. Ej: ZR_SD_QUICK_ORDERS"
                    },
                    "description": {
                        "type": "string",
                        "description": "Descripción corta del programa"
                    },
                    "package": {
                        "type": "string",
                        "description": "Paquete de desarrollo. Ej: ZDEV_SD, $TMP"
                    },
                    "transport": {
                        "type": "string",
                        "description": "Orden de transporte. Ej: DEVK900123. Dejar vacío para $TMP"
                    },
                    "source_code": {
                        "type": "string",
                        "description": "Código fuente ABAP completo del programa"
                    }
                },
                "required": ["program_name", "description", "package", "source_code"]
            }
        ),
        types.Tool(
            name="sap_update_program_source",
            description=f"Actualiza el código fuente de un programa ABAP existente en {SYS_LABEL}. Hace lock, escribe y unlock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "program_name": {
                        "type": "string",
                        "description": "Nombre del programa existente. Ej: ZR_SD_QUICK_ORDERS"
                    },
                    "source_code": {
                        "type": "string",
                        "description": "Código fuente ABAP completo (reemplaza todo el código)"
                    },
                    "transport": {
                        "type": "string",
                        "description": "Orden de transporte (opcional)"
                    }
                },
                "required": ["program_name", "source_code"]
            }
        ),
        types.Tool(
            name="sap_update_program_from_file",
            description=f"Actualiza el código fuente de un programa ABAP leyendo desde un archivo local del workspace en {SYS_LABEL}.",
            inputSchema={
                "type": "object",
                "properties": {
                    "program_name": {
                        "type": "string",
                        "description": "Nombre del programa existente en mayúsculas. Ej: ZR_SD_TRANSPORT_CHECKER"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Ruta al archivo .abap relativa al workspace. Ej: ZR_SD_TRANSPORT_CHECKER/ZR_SD_TRANSPORT_CHECKER.abap"
                    },
                    "transport": {
                        "type": "string",
                        "description": "Orden de transporte (opcional)"
                    }
                },
                "required": ["program_name", "file_path"]
            }
        ),
        types.Tool(
            name="sap_update_function_module_source",
            description=f"Actualiza el código fuente de un Function Module ABAP existente en {SYS_LABEL}. Hace lock, escribe y unlock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "function_group": {
                        "type": "string",
                        "description": "Nombre del grupo de funciones. Ej: ZSD_PPD"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Nombre del Function Module. Ej: ZSD_PPD_REJ_UPDATE"
                    },
                    "source_code": {
                        "type": "string",
                        "description": "Código fuente ABAP completo del FM (reemplaza todo el código)"
                    },
                    "transport": {
                        "type": "string",
                        "description": "Orden de transporte (opcional)"
                    }
                },
                "required": ["function_group", "function_name", "source_code"]
            }
        ),
        types.Tool(
            name="sap_create_transport",
            description=f"Crea una orden de transporte (Workbench o Customizing Request) en {SYS_LABEL}. Retorna el número de OT y task creados.",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Descripción de la orden de transporte. Ej: L2C:CHG0436752- EHP8 fix"
                    },
                    "request_type": {
                        "type": "string",
                        "description": "Tipo de request: K = Workbench (default), W = Customizing",
                        "default": "K"
                    },
                    "target": {
                        "type": "string",
                        "description": "Sistema destino del transporte (opcional, se usa el default del sistema si se omite)",
                        "default": ""
                    },
                    "reference_object_uri": {
                        "type": "string",
                        "description": "URI ADT del objeto real que origina el transporte, usado para detectar su DEVCLASS. Ej: /sap/bc/adt/programs/includes/zcl_my_object"
                    }
                },
                "required": ["description", "reference_object_uri"]
            }
        ),
        types.Tool(
            name="sap_activate_object",
            description=f"Activa un objeto ABAP en {SYS_LABEL} (programa, clase, interfaz, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_name": {
                        "type": "string",
                        "description": "Nombre del objeto. Ej: ZR_SD_QUICK_ORDERS"
                    },
                    "object_type": {
                        "type": "string",
                        "description": "Tipo del objeto ADT. Ej: PROG/P, CLAS/OC, INTF/OI, FUGR/F",
                        "default": "PROG/P"
                    }
                },
                "required": ["object_name"]
            }
        ),
        types.Tool(
            name="sap_run_abap_unit",
            description=f"Ejecuta ABAP Unit tests para un objeto ABAP en {SYS_LABEL}. Retorna los resultados de los tests.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_url": {
                        "type": "string",
                        "description": "URI ADT del objeto. Ej: /sap/bc/adt/oo/classes/zcl_sd_quick_orders_test"
                    }
                },
                "required": ["object_url"]
            }
        ),
        types.Tool(
            name="sap_syntax_check",
            description=f"Ejecuta syntax check de un objeto ABAP en {SYS_LABEL}. Retorna errores y warnings de compilación.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_url": {
                        "type": "string",
                        "description": "URI ADT del objeto. Ej: /sap/bc/adt/programs/programs/zr_sd_quick_orders"
                    }
                },
                "required": ["object_url"]
            }
        ),
        types.Tool(
            name="sap_list_transports",
            description=f"Lista las órdenes de transporte modificables (abiertas) en {SYS_LABEL}. Opcionalmente filtra por usuario.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user": {
                        "type": "string",
                        "description": "Usuario SAP para filtrar (opcional). Si se omite, muestra todas las visibles para el usuario conectado."
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="sap_get_transport_details",
            description=f"Obtiene los detalles y objetos contenidos en una orden de transporte específica en {SYS_LABEL}.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transport_number": {
                        "type": "string",
                        "description": "Número de la orden de transporte. Ej: DEVK900124"
                    }
                },
                "required": ["transport_number"]
            }
        ),
        types.Tool(
            name="sap_get_transport_xml_raw",
            description=f"Retorna el fragmento XML crudo del CTS para una OT específica en {SYS_LABEL}. Útil para diagnóstico cuando get_transport_details no muestra objetos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transport_number": {
                        "type": "string",
                        "description": "Número de la orden de transporte. Ej: DEVK900125"
                    }
                },
                "required": ["transport_number"]
            }
        ),
    ]


# ──────────────────────────────────────────────
# Ejecutar herramientas
# ──────────────────────────────────────────────
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    def respond(data: dict) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    if name == "sap_ping":
        result = sap.ping()
        return respond(result)

    elif name == "sap_get_program_source":
        program = arguments.get("program_name", "").upper()
        if not program:
            return respond({"ok": False, "message": "program_name es requerido"})
        result = sap.get_program_source(program)
        return respond(result)

    elif name == "sap_get_class_source":
        cls = arguments.get("class_name", "").upper()
        if not cls:
            return respond({"ok": False, "message": "class_name es requerido"})
        result = sap.get_class_source(cls)
        return respond(result)

    elif name == "sap_get_function_module_source":
        fg = arguments.get("function_group", "").upper()
        fm = arguments.get("function_name", "").upper()
        if not fg or not fm:
            return respond({"ok": False, "message": "function_group y function_name son requeridos"})
        result = sap.get_function_module_source(fg, fm)
        return respond(result)

    elif name == "sap_get_include_source":
        include = arguments.get("include_name", "").upper()
        if not include:
            return respond({"ok": False, "message": "include_name es requerido"})
        result = sap.get_include_source(include)
        return respond(result)

    elif name == "sap_search_objects":
        query = arguments.get("query", "")
        max_r = arguments.get("max_results", 20)
        if not query:
            return respond({"ok": False, "message": "query es requerido"})
        result = sap.search_objects(query, max_r)
        return respond(result)

    elif name == "sap_get_table_definition":
        table = arguments.get("table_name", "").upper()
        if not table:
            return respond({"ok": False, "message": "table_name es requerido"})
        result = sap.get_table_definition(table)
        return respond(result)

    elif name == "sap_check_adt_capabilities":
        result = sap.check_adt_capabilities()
        return respond(result)

    elif name == "sap_test_endpoint":
        path = arguments.get("path", "")
        method = arguments.get("method", "GET")
        if not path:
            return respond({"ok": False, "message": "path es requerido"})
        result = sap.test_endpoint(path, method)
        return respond(result)

    elif name == "sap_create_interface":
        intf = arguments.get("interface_name", "").upper()
        desc = arguments.get("description", "")
        pkg = arguments.get("package", "$TMP").upper()
        tr = arguments.get("transport", "")
        src = arguments.get("source_code", "")
        if not intf or not src:
            return respond({"ok": False, "message": "interface_name y source_code son requeridos"})
        result = sap.create_interface(intf, desc, pkg, tr, src)
        return respond(result)

    elif name == "sap_create_class":
        cls = arguments.get("class_name", "").upper()
        desc = arguments.get("description", "")
        pkg = arguments.get("package", "$TMP").upper()
        tr = arguments.get("transport", "")
        src = arguments.get("source_code", "")
        is_final = arguments.get("is_final", True)
        if not cls or not src:
            return respond({"ok": False, "message": "class_name y source_code son requeridos"})
        result = sap.create_class(cls, desc, pkg, tr, src, is_final)
        return respond(result)

    elif name == "sap_update_class_source":
        cls = arguments.get("class_name", "").upper()
        src = arguments.get("source_code", "")
        tr = arguments.get("transport", "")
        if not cls or not src:
            return respond({"ok": False, "message": "class_name y source_code son requeridos"})
        result = sap.update_class_source(cls, src, tr)
        return respond(result)

    elif name == "sap_update_interface_source":
        intf = arguments.get("interface_name", "").upper()
        src = arguments.get("source_code", "")
        tr = arguments.get("transport", "")
        if not intf or not src:
            return respond({"ok": False, "message": "interface_name y source_code son requeridos"})
        result = sap.update_interface_source(intf, src, tr)
        return respond(result)

    elif name == "sap_create_program":
        prog = arguments.get("program_name", "").upper()
        desc = arguments.get("description", "")
        pkg = arguments.get("package", "$TMP").upper()
        tr = arguments.get("transport", "")
        src = arguments.get("source_code", "")
        if not prog or not src:
            return respond({"ok": False, "message": "program_name y source_code son requeridos"})
        result = sap.create_program(prog, desc, pkg, tr, src)
        return respond(result)

    elif name == "sap_update_program_source":
        prog = arguments.get("program_name", "").upper()
        src = arguments.get("source_code", "")
        tr = arguments.get("transport", "")
        if not prog or not src:
            return respond({"ok": False, "message": "program_name y source_code son requeridos"})
        result = sap.update_program_source(prog, src, tr)
        return respond(result)

    elif name == "sap_update_program_from_file":
        prog = arguments.get("program_name", "").upper()
        fpath = arguments.get("file_path", "")
        tr = arguments.get("transport", "")
        if not prog or not fpath:
            return respond({"ok": False, "message": "program_name y file_path son requeridos"})
        result = sap.update_program_from_file(prog, fpath, tr)
        return respond(result)

    elif name == "sap_update_function_module_source":
        fg = arguments.get("function_group", "").upper()
        fm = arguments.get("function_name", "").upper()
        src = arguments.get("source_code", "")
        tr = arguments.get("transport", "")
        if not fg or not fm or not src:
            return respond({"ok": False, "message": "function_group, function_name y source_code son requeridos"})
        result = sap.update_function_module_source(fg, fm, src, tr)
        return respond(result)

    elif name == "sap_create_transport":
        desc = arguments.get("description", "")
        req_type = arguments.get("request_type", "K").upper()
        target = arguments.get("target", "")
        ref_uri = arguments.get("reference_object_uri", "")
        if not desc or not ref_uri:
            return respond({"ok": False, "message": "description y reference_object_uri son requeridos"})
        result = sap.create_transport_request(desc, req_type, target, ref_uri)
        return respond(result)

    elif name == "sap_activate_object":
        obj = arguments.get("object_name", "").upper()
        obj_type = arguments.get("object_type", "PROG/P")
        if not obj:
            return respond({"ok": False, "message": "object_name es requerido"})
        result = sap.activate_object(obj, obj_type)
        return respond(result)

    elif name == "sap_run_abap_unit":
        obj_url = arguments.get("object_url", "")
        if not obj_url:
            return respond({"ok": False, "message": "object_url es requerido"})
        result = sap.run_abap_unit(obj_url)
        return respond(result)

    elif name == "sap_syntax_check":
        obj_url = arguments.get("object_url", "")
        if not obj_url:
            return respond({"ok": False, "message": "object_url es requerido"})
        result = sap.syntax_check(obj_url)
        return respond(result)

    elif name == "sap_list_transports":
        user = arguments.get("user", "")
        result = sap.list_transports(user)
        return respond(result)

    elif name == "sap_get_transport_details":
        tr = arguments.get("transport_number", "").upper()
        if not tr:
            return respond({"ok": False, "message": "transport_number es requerido"})
        result = sap.get_transport_details(tr)
        return respond(result)

    elif name == "sap_get_transport_xml_raw":
        tr = arguments.get("transport_number", "").upper()
        if not tr:
            return respond({"ok": False, "message": "transport_number es requerido"})
        result = sap.get_transport_xml_raw(tr)
        return respond(result)

    else:
        return respond({"ok": False, "message": f"Herramienta desconocida: {name}"})


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
async def main():
    missing = [
        name for name, value in (
            ("SAP_HOST", SAP_HOST),
            ("SAP_CLIENT", SAP_CLIENT),
            ("SAP_USER", SAP_USER),
            ("SAP_PASSWORD", SAP_PASSWORD),
            ("SAP_SYSTEM_ID", SAP_SYSTEM_ID),
        ) if not value
    ]
    if missing:
        print(
            f"ERROR: Variables de entorno faltantes: {', '.join(missing)}.\n"
            "Estas se configuran en ~/.kiro/settings/mcp.json por install.bat — "
            "vuelve a ejecutar install.bat o revisa ese archivo manualmente.",
            file=sys.stderr
        )
        sys.exit(1)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
