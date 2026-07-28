"""
SAP ADT Client - Wrapper para llamadas HTTP a la ADT API de SAP
Usa autenticación básica HTTP, sin RFC ni NW RFC SDK.
"""

import requests
import base64
from requests.auth import HTTPBasicAuth
from typing import Optional
import xml.etree.ElementTree as ET


class SAPADTClient:
    """Cliente HTTP para SAP ABAP Development Tools (ADT) REST API."""

    def __init__(self, host: str, client: str, username: str, password: str, secure: bool = False,
                 cts_project: str = "", transport_layer: str = ""):
        self.base_url = f"{'https' if secure else 'http'}://{host}"
        self.client = client
        self.username = username
        self.password = password
        # Optional — only some SAP systems require CTS project management.
        # Set via SAP_CTS_PROJECT / SAP_TRANSPORT_LAYER env vars; never hardcode a value here.
        self.cts_project = cts_project
        self.transport_layer = transport_layer
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            "sap-client": client,
            "Accept": "application/xml",
            "Content-Type": "application/xml",
        })

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def ping(self) -> dict:
        """Verifica conectividad llamando al endpoint discovery de ADT."""
        try:
            resp = self.session.get(
                self._url("/sap/bc/adt/discovery"),
                timeout=15
            )
            return {
                "ok": resp.status_code == 200,
                "status": resp.status_code,
                "message": "Conexión exitosa a SAP ADT" if resp.status_code == 200 else resp.text[:200]
            }
        except Exception as e:
            return {"ok": False, "status": 0, "message": str(e)}

    def get_object_source(self, object_type: str, object_name: str) -> dict:
        """
        Obtiene el código fuente de un objeto ABAP.
        object_type: 'programs/programs', 'functions/groups', 'oo/classes', etc.
        object_name: nombre del objeto en mayúsculas
        """
        try:
            url = self._url(f"/sap/bc/adt/{object_type}/{object_name}/source/main")
            resp = self.session.get(url, headers={"Accept": "text/plain"}, timeout=30)
            if resp.status_code == 200:
                return {"ok": True, "source": resp.text, "object": object_name}
            else:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_function_module_source(self, function_group: str, function_name: str) -> dict:
        """Obtiene el código fuente de un Function Module."""
        try:
            url = self._url(
                f"/sap/bc/adt/functions/groups/{function_group.upper()}"
                f"/fmodules/{function_name.upper()}/source/main"
            )
            resp = self.session.get(url, headers={"Accept": "text/plain"}, timeout=30)
            if resp.status_code == 200:
                return {"ok": True, "source": resp.text, "function": function_name}
            else:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_class_source(self, class_name: str) -> dict:
        """Obtiene el código fuente de una clase ABAP OO."""
        try:
            url = self._url(f"/sap/bc/adt/oo/classes/{class_name.upper()}/source/main")
            resp = self.session.get(url, headers={"Accept": "text/plain"}, timeout=30)
            if resp.status_code == 200:
                return {"ok": True, "source": resp.text, "class": class_name}
            else:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def search_objects(self, query: str, max_results: int = 20) -> dict:
        """Busca objetos ABAP por nombre (quick search ADT)."""
        try:
            url = self._url("/sap/bc/adt/repository/informationsystem/search")
            params = {
                "operation": "quickSearch",
                "query": query,
                "maxResults": max_results,
            }
            resp = self.session.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                # Parsear XML de respuesta
                objects = []
                try:
                    root = ET.fromstring(resp.text)
                    ns = {"adtcore": "http://www.sap.com/adt/core"}
                    for obj in root.iter():
                        name = obj.get("{http://www.sap.com/adt/core}name")
                        obj_type = obj.get("{http://www.sap.com/adt/core}type")
                        if name and obj_type:
                            objects.append({"name": name, "type": obj_type})
                except ET.ParseError:
                    pass
                return {"ok": True, "objects": objects, "raw": resp.text[:1000]}
            else:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_program_source(self, program_name: str) -> dict:
        """Obtiene el código fuente de un programa/report ABAP."""
        try:
            url = self._url(f"/sap/bc/adt/programs/programs/{program_name.upper()}/source/main")
            resp = self.session.get(url, headers={"Accept": "text/plain"}, timeout=30)
            if resp.status_code == 200:
                return {"ok": True, "source": resp.text, "program": program_name}
            else:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_include_source(self, include_name: str) -> dict:
        """Obtiene el código fuente de un INCLUDE ABAP."""
        include_name = include_name.upper()
        try:
            url = self._url(f"/sap/bc/adt/programs/includes/{include_name}/source/main")
            resp = self.session.get(url, headers={"Accept": "text/plain"}, timeout=30)
            if resp.status_code == 200:
                return {"ok": True, "source": resp.text, "include": include_name}
            else:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_table_definition(self, table_name: str) -> dict:
        """
        Obtiene la definición (metadata) de una tabla del diccionario ABAP.
        Intenta múltiples endpoints ADT:
        1. /sap/bc/adt/ddic/tables/{name} — tablas transparentes
        2. /sap/bc/adt/ddic/structures/{name} — estructuras y pool/cluster tables
        3. /sap/bc/adt/repository/informationsystem/search — como último recurso
        """
        table_name = table_name.upper()

        # Intento 1: endpoint de tablas transparentes
        try:
            url = self._url(f"/sap/bc/adt/ddic/tables/{table_name}")
            resp = self.session.get(url, timeout=20)
            if resp.status_code == 200:
                return {"ok": True, "definition": resp.text, "table": table_name,
                        "source": "ddic/tables"}
        except Exception:
            pass

        # Intento 2: endpoint de estructuras (Accept correcto del ADT discovery)
        accept_types = [
            "application/vnd.sap.adt.blues.v1+xml",
            "application/vnd.sap.adt.ddic.structures.v2+xml",
            "application/vnd.sap.adt.ddic.structures+xml",
        ]
        for accept in accept_types:
            try:
                url = self._url(f"/sap/bc/adt/ddic/structures/{table_name}")
                resp = self.session.get(url, headers={"Accept": accept}, timeout=20)
                if resp.status_code == 200:
                    return {"ok": True, "definition": resp.text, "table": table_name,
                            "source": "ddic/structures"}
            except Exception:
                pass

        # Intento 3: endpoint de data elements
        try:
            url = self._url(f"/sap/bc/adt/ddic/dataelements/{table_name}")
            resp = self.session.get(
                url,
                headers={"Accept": "application/vnd.sap.adt.dataelements.v1+xml"},
                timeout=20,
            )
            if resp.status_code == 200:
                return {"ok": True, "definition": resp.text, "table": table_name,
                        "source": "ddic/dataelements"}
        except Exception:
            pass

        return {
            "ok": False,
            "table": table_name,
            "message": (
                f"Tabla {table_name} no accesible via ADT DDIC endpoints. "
                "Puede ser una pool/cluster table o tabla de sistema. "
                "Consultar el steering file 08-sap-system-tables.md para campos conocidos, "
                "o usar SE11 en SAP GUI para verificar la estructura."
            ),
        }

    def check_adt_capabilities(self) -> dict:
        """Consulta el endpoint ADT discovery para listar todos los servicios disponibles en el sistema."""
        try:
            url = self._url("/sap/bc/adt/discovery")
            resp = self.session.get(url, timeout=20)
            if resp.status_code == 200:
                # Extraer colecciones/servicios disponibles
                services = []
                try:
                    root = ET.fromstring(resp.text)
                    # ADT discovery usa Atom format
                    ns = {
                        "app": "http://www.w3.org/2007/app",
                        "atom": "http://www.w3.org/2005/Atom",
                        "adtcore": "http://www.sap.com/adt/core",
                    }
                    for workspace in root.findall(".//app:workspace", ns):
                        ws_title = workspace.find("atom:title", ns)
                        ws_name = ws_title.text if ws_title is not None else "unknown"
                        for collection in workspace.findall("app:collection", ns):
                            href = collection.get("href", "")
                            col_title = collection.find("atom:title", ns)
                            title = col_title.text if col_title is not None else ""
                            # Buscar accepts (qué métodos soporta)
                            accepts = [a.text for a in collection.findall("app:accept", ns) if a.text]
                            services.append({
                                "workspace": ws_name,
                                "title": title,
                                "href": href,
                                "accepts": accepts,
                            })
                except ET.ParseError:
                    return {"ok": True, "raw": resp.text[:3000], "parse_error": True}
                return {"ok": True, "services_count": len(services), "services": services}
            else:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    # ──────────────────────────────────────────────
    # Métodos de escritura (CREATE / UPDATE / ACTIVATE)
    # ──────────────────────────────────────────────

    def _fetch_csrf_token(self) -> Optional[str]:
        """Obtiene un CSRF token necesario para operaciones de escritura."""
        try:
            resp = self.session.get(
                self._url("/sap/bc/adt/discovery"),
                headers={"X-CSRF-Token": "Fetch"},
                timeout=15,
            )
            return resp.headers.get("X-CSRF-Token") or resp.headers.get("x-csrf-token")
        except Exception:
            return None

    def _lock_object(self, object_url: str, csrf_token: str) -> dict:
        """Bloquea un objeto ABAP para edición. Retorna el lock handle."""
        try:
            resp = self.session.post(
                self._url(object_url),
                params={"_action": "LOCK", "accessMode": "MODIFY"},
                headers={
                    "X-CSRF-Token": csrf_token,
                    "X-sap-adt-sessiontype": "stateful",
                },
                timeout=15,
            )
            if resp.status_code == 200:
                # El lock handle viene en el body
                lock_handle = resp.text.strip()
                # A veces viene como XML, extraer el valor
                if "<LOCK_HANDLE>" in resp.text:
                    start = resp.text.index("<LOCK_HANDLE>") + len("<LOCK_HANDLE>")
                    end = resp.text.index("</LOCK_HANDLE>")
                    lock_handle = resp.text[start:end].strip()
                return {"ok": True, "lock_handle": lock_handle}
            else:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _unlock_object(self, object_url: str, lock_handle: str, csrf_token: str) -> dict:
        """Desbloquea un objeto ABAP."""
        try:
            resp = self.session.post(
                self._url(object_url),
                params={"_action": "UNLOCK", "lockHandle": lock_handle},
                headers={"X-CSRF-Token": csrf_token},
                timeout=15,
            )
            return {"ok": resp.status_code in (200, 204)}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def create_interface(self, interface_name: str, description: str, package: str,
                         transport: str, source_code: str) -> dict:
        """Crea una interfaz ABAP OO nueva en SAP (INTF/OI)."""
        interface_name = interface_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            # Paso 1: Crear el objeto interfaz
            create_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<intf:abapInterface xmlns:intf="http://www.sap.com/adt/oo/interfaces" '
                'xmlns:adtcore="http://www.sap.com/adt/core" '
                'xmlns:abapsource="http://www.sap.com/adt/abapsource" '
                'xmlns:abapoo="http://www.sap.com/adt/oo" '
                'abapoo:modeled="false" '
                'abapsource:fixPointArithmetic="true" '
                'abapsource:activeUnicodeCheck="true" '
                f'adtcore:description="{description}" '
                f'adtcore:language="EN" '
                f'adtcore:name="{interface_name}" '
                f'adtcore:type="INTF/OI" '
                f'adtcore:responsible="{self.username}">'
                f'<adtcore:packageRef adtcore:name="{package}"/>'
                '</intf:abapInterface>'
            )

            params = {}
            if transport:
                params["corrNr"] = transport

            resp = self.session.post(
                self._url("/sap/bc/adt/oo/interfaces"),
                data=create_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/vnd.sap.adt.oo.interfaces.v2+xml",
                },
                params=params,
                timeout=30,
            )

            if resp.status_code not in (200, 201):
                return {
                    "ok": False, "step": "create",
                    "status": resp.status_code,
                    "message": resp.text[:500],
                }

            # Paso 2: Escribir el código fuente
            object_url = f"/sap/bc/adt/oo/interfaces/{interface_name.lower()}"
            source_url = f"{object_url}/source/main"

            csrf_token2 = self._fetch_csrf_token()
            lock_result = self._lock_object(object_url, csrf_token2)
            if not lock_result.get("ok"):
                return {"ok": False, "step": "lock", "detail": lock_result}
            lock_handle = lock_result["lock_handle"]

            write_params = {"lockHandle": lock_handle}
            if transport:
                write_params["corrNr"] = transport

            write_resp = self.session.put(
                self._url(source_url),
                data=source_code.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token2,
                    "Content-Type": "text/plain; charset=utf-8",
                },
                params=write_params,
                timeout=30,
            )
            self._unlock_object(object_url, lock_handle, csrf_token2)

            if write_resp.status_code not in (200, 204):
                return {
                    "ok": False, "step": "write",
                    "status": write_resp.status_code,
                    "message": write_resp.text[:500],
                }

            # Paso 3: Activar
            activate_result = self.activate_object(interface_name, "INTF/OI")
            return {
                "ok": activate_result.get("ok", False),
                "interface": interface_name,
                "created": True,
                "activated": activate_result.get("ok", False),
                "activate_detail": activate_result,
            }

        except Exception as e:
            return {"ok": False, "message": str(e)}

    @staticmethod
    def _split_class_source(source_code: str):
        """
        Separa el source_code de una clase en (definition_part, implementation_part).
        Busca el primer 'CLASS ... IMPLEMENTATION.' para hacer el split.
        Retorna (definition, implementation) como strings.
        """
        import re
        # Buscar el inicio del bloque IMPLEMENTATION (case-insensitive)
        pattern = re.compile(
            r'^(CLASS\s+\S+\s+IMPLEMENTATION\s*\.)',
            re.IGNORECASE | re.MULTILINE
        )
        match = pattern.search(source_code)
        if match:
            definition = source_code[:match.start()].rstrip()
            implementation = source_code[match.start():]
            return definition, implementation
        # Si no hay IMPLEMENTATION, todo es definition
        return source_code, ""

    def _write_class_include(self, object_url: str, include_type: str,
                              content: str, lock_handle: str,
                              csrf_token: str, transport: str) -> dict:
        """Escribe un include específico de una clase (definitions o implementations)."""
        include_url = f"{object_url}/includes/{include_type}"
        params = {"lockHandle": lock_handle}
        if transport:
            params["corrNr"] = transport
        resp = self.session.put(
            self._url(include_url),
            data=content.encode("utf-8"),
            headers={
                "X-CSRF-Token": csrf_token,
                "Content-Type": "text/plain; charset=utf-8",
            },
            params=params,
            timeout=30,
        )
        return {"ok": resp.status_code in (200, 204),
                "status": resp.status_code,
                "message": resp.text[:300] if resp.status_code not in (200, 204) else ""}

    def create_class(self, class_name: str, description: str, package: str,
                     transport: str, source_code: str,
                     is_final: bool = True, for_testing: bool = False) -> dict:
        """Crea una clase ABAP OO nueva en SAP (CLAS/OC).
        Escribe definition e implementation en includes separados."""
        class_name = class_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            final_attr = "true" if is_final else "false"
            # Paso 1: Crear el objeto clase
            create_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<class:abapClass xmlns:class="http://www.sap.com/adt/oo/classes" '
                'xmlns:adtcore="http://www.sap.com/adt/core" '
                'xmlns:abapsource="http://www.sap.com/adt/abapsource" '
                'xmlns:abapoo="http://www.sap.com/adt/oo" '
                f'class:final="{final_attr}" '
                'class:abstract="false" '
                'class:visibility="public" '
                'class:category="generalObjectType" '
                'abapoo:modeled="false" '
                'abapsource:fixPointArithmetic="true" '
                'abapsource:activeUnicodeCheck="true" '
                f'adtcore:description="{description}" '
                f'adtcore:language="EN" '
                f'adtcore:name="{class_name}" '
                f'adtcore:type="CLAS/OC" '
                f'adtcore:responsible="{self.username}">'
                f'<adtcore:packageRef adtcore:name="{package}"/>'
                '</class:abapClass>'
            )

            params = {}
            if transport:
                params["corrNr"] = transport

            resp = self.session.post(
                self._url("/sap/bc/adt/oo/classes"),
                data=create_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/vnd.sap.adt.oo.classes.v2+xml",
                },
                params=params,
                timeout=30,
            )

            if resp.status_code not in (200, 201):
                return {
                    "ok": False, "step": "create",
                    "status": resp.status_code,
                    "message": resp.text[:500],
                }

            # Paso 2: Separar y escribir definition + implementation en includes separados
            object_url = f"/sap/bc/adt/oo/classes/{class_name.lower()}"
            definition, implementation = self._split_class_source(source_code)

            csrf_token2 = self._fetch_csrf_token()
            lock_result = self._lock_object(object_url, csrf_token2)
            if not lock_result.get("ok"):
                return {"ok": False, "step": "lock", "detail": lock_result}
            lock_handle = lock_result["lock_handle"]

            # Escribir definitions
            def_result = self._write_class_include(
                object_url, "definitions", definition, lock_handle, csrf_token2, transport)
            if not def_result.get("ok"):
                self._unlock_object(object_url, lock_handle, csrf_token2)
                return {"ok": False, "step": "write_definitions", "detail": def_result}

            # Escribir implementations (si hay)
            if implementation:
                impl_result = self._write_class_include(
                    object_url, "implementations", implementation, lock_handle, csrf_token2, transport)
                if not impl_result.get("ok"):
                    self._unlock_object(object_url, lock_handle, csrf_token2)
                    return {"ok": False, "step": "write_implementations", "detail": impl_result}

            self._unlock_object(object_url, lock_handle, csrf_token2)

            # Paso 3: Activar
            activate_result = self.activate_object(class_name, "CLAS/OC")
            return {
                "ok": activate_result.get("ok", False),
                "class": class_name,
                "created": True,
                "activated": activate_result.get("ok", False),
                "activate_detail": activate_result,
            }

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_class_source(self, class_name: str, source_code: str,
                            transport: str = "") -> dict:
        """Actualiza el código fuente de una clase ABAP existente.
        Escribe definition e implementation en includes separados."""
        class_name = class_name.upper()
        object_url = f"/sap/bc/adt/oo/classes/{class_name.lower()}"
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            definition, implementation = self._split_class_source(source_code)

            lock_result = self._lock_object(object_url, csrf_token)
            if not lock_result.get("ok"):
                return {"ok": False, "step": "lock", "detail": lock_result}
            lock_handle = lock_result["lock_handle"]

            def_result = self._write_class_include(
                object_url, "definitions", definition, lock_handle, csrf_token, transport)
            if not def_result.get("ok"):
                self._unlock_object(object_url, lock_handle, csrf_token)
                return {"ok": False, "step": "write_definitions", "detail": def_result}

            if implementation:
                impl_result = self._write_class_include(
                    object_url, "implementations", implementation, lock_handle, csrf_token, transport)
                if not impl_result.get("ok"):
                    self._unlock_object(object_url, lock_handle, csrf_token)
                    return {"ok": False, "step": "write_implementations", "detail": impl_result}

            self._unlock_object(object_url, lock_handle, csrf_token)

            return {"ok": True, "class": class_name, "message": "Código fuente actualizado"}

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_interface_source(self, interface_name: str, source_code: str,
                                transport: str = "") -> dict:
        """Actualiza el código fuente de una interfaz ABAP existente."""
        interface_name = interface_name.upper()
        object_url = f"/sap/bc/adt/oo/interfaces/{interface_name.lower()}"
        source_url = f"{object_url}/source/main"
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            lock_result = self._lock_object(object_url, csrf_token)
            if not lock_result.get("ok"):
                return {"ok": False, "step": "lock", "detail": lock_result}
            lock_handle = lock_result["lock_handle"]

            params = {"lockHandle": lock_handle}
            if transport:
                params["corrNr"] = transport

            resp = self.session.put(
                self._url(source_url),
                data=source_code.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "text/plain; charset=utf-8",
                },
                params=params,
                timeout=30,
            )
            self._unlock_object(object_url, lock_handle, csrf_token)

            if resp.status_code in (200, 204):
                return {"ok": True, "interface": interface_name, "message": "Código fuente actualizado"}
            else:
                return {
                    "ok": False, "step": "write",
                    "status": resp.status_code,
                    "message": resp.text[:500],
                }
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def create_program(self, program_name: str, description: str, package: str,
                       transport: str, source_code: str) -> dict:
        """Crea un programa ABAP nuevo en SAP."""
        program_name = program_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            # Paso 1: Crear el objeto programa
            create_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<program:abapProgram xmlns:program="http://www.sap.com/adt/programs/programs" '
                'xmlns:adtcore="http://www.sap.com/adt/core" '
                f'adtcore:description="{description}" '
                f'adtcore:language="EN" '
                f'adtcore:name="{program_name}" '
                f'adtcore:type="PROG/P" '
                f'adtcore:responsible="{self.username}">'
                f'<adtcore:packageRef adtcore:name="{package}"/>'
                '</program:abapProgram>'
            )

            resp = self.session.post(
                self._url("/sap/bc/adt/programs/programs"),
                data=create_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/vnd.sap.adt.programs.programs.v2+xml",
                    "X-sap-adt-sessiontype": "stateful",
                },
                params={"corrNr": transport} if transport else {},
                timeout=30,
            )

            if resp.status_code not in (200, 201):
                return {
                    "ok": False, "step": "create",
                    "status": resp.status_code,
                    "message": resp.text[:500],
                }

            # Paso 2: Escribir el código fuente
            write_result = self.update_program_source(program_name, source_code, transport)
            if not write_result.get("ok"):
                return write_result

            # Paso 3: Activar
            activate_result = self.activate_object(program_name, "PROG/P")
            return {
                "ok": activate_result.get("ok", False),
                "program": program_name,
                "created": True,
                "activated": activate_result.get("ok", False),
                "activate_detail": activate_result,
            }

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_program_source(self, program_name: str, source_code: str,
                              transport: str = "") -> dict:
        """Actualiza el código fuente de un programa existente."""
        program_name = program_name.upper()
        object_url = f"/sap/bc/adt/programs/programs/{program_name}"
        source_url = f"{object_url}/source/main"
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            # Lock
            lock_result = self._lock_object(object_url, csrf_token)
            if not lock_result.get("ok"):
                return {"ok": False, "step": "lock", "detail": lock_result}
            lock_handle = lock_result["lock_handle"]

            # Write source
            params = {"lockHandle": lock_handle}
            if transport:
                params["corrNr"] = transport

            resp = self.session.put(
                self._url(source_url),
                data=source_code.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "text/plain; charset=utf-8",
                },
                params=params,
                timeout=30,
            )

            # Unlock
            self._unlock_object(object_url, lock_handle, csrf_token)

            if resp.status_code in (200, 204):
                return {"ok": True, "program": program_name, "message": "Código fuente actualizado"}
            else:
                return {
                    "ok": False, "step": "write",
                    "status": resp.status_code,
                    "message": resp.text[:500],
                }

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_program_from_file(self, program_name: str, file_path: str,
                                  transport: str = "") -> dict:
        """Lee código fuente desde un archivo local y lo sube a SAP.
        Workaround para el límite de tamaño de parámetros MCP."""
        try:
            import os
            if not os.path.isabs(file_path):
                # Resolver relativo al directorio del MCP server
                base_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(base_dir, file_path)

            if not os.path.exists(file_path):
                return {"ok": False, "message": f"Archivo no encontrado: {file_path}"}

            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            if not source_code.strip():
                return {"ok": False, "message": f"Archivo vacío: {file_path}"}

            line_count = source_code.count("\n") + 1
            result = self.update_program_source(program_name, source_code, transport)
            if result.get("ok"):
                result["file_path"] = file_path
                result["lines_uploaded"] = line_count
                result["message"] = f"Código fuente actualizado desde archivo ({line_count} líneas)"
            return result

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_function_module_source(self, function_group: str, function_name: str,
                                      source_code: str, transport: str = "") -> dict:
        """Actualiza el código fuente de un Function Module existente."""
        function_group = function_group.lower()
        function_name = function_name.lower()
        object_url = f"/sap/bc/adt/functions/groups/{function_group}/fmodules/{function_name}"
        source_url = f"{object_url}/source/main"
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            # Lock the function module
            lock_result = self._lock_object(object_url, csrf_token)
            if not lock_result.get("ok"):
                return {"ok": False, "step": "lock", "detail": lock_result}
            lock_handle = lock_result["lock_handle"]

            # Write source
            params = {"lockHandle": lock_handle}
            if transport:
                params["corrNr"] = transport

            resp = self.session.put(
                self._url(source_url),
                data=source_code.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "text/plain; charset=utf-8",
                },
                params=params,
                timeout=30,
            )

            # Unlock
            self._unlock_object(object_url, lock_handle, csrf_token)

            if resp.status_code in (200, 204):
                return {"ok": True, "function": function_name.upper(),
                        "message": "Código fuente del FM actualizado"}
            else:
                return {
                    "ok": False, "step": "write",
                    "status": resp.status_code,
                    "message": resp.text[:500],
                }

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def activate_object(self, object_name: str, object_type: str = "PROG/P") -> dict:
        """Activa un objeto ABAP (programa, clase, interfaz, etc.)."""
        object_name = object_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            # El body de activación es XML con la lista de objetos a activar
            activate_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<adtcore:objectReferences xmlns:adtcore="http://www.sap.com/adt/core">'
                f'<adtcore:objectReference adtcore:name="{object_name}" '
                f'adtcore:type="{object_type}"/>'
                '</adtcore:objectReferences>'
            )

            resp = self.session.post(
                self._url("/sap/bc/adt/activation"),
                data=activate_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/xml",
                },
                params={"method": "activate", "preauditRequested": "true"},
                timeout=30,
            )

            if resp.status_code in (200, 204):
                # Verificar si hay errores en la respuesta
                has_errors = "severity=\"error\"" in resp.text.lower() if resp.text else False
                return {
                    "ok": not has_errors,
                    "object": object_name,
                    "message": "Activado exitosamente" if not has_errors else "Activación con errores",
                    "detail": resp.text[:500] if has_errors else "",
                }
            else:
                return {
                    "ok": False, "status": resp.status_code,
                    "message": resp.text[:500],
                }

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def run_abap_unit(self, object_url: str) -> dict:
        """Ejecuta ABAP Unit tests para un objeto dado."""
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            # Body XML para ejecutar tests
            run_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<aunit:runConfiguration xmlns:aunit="http://www.sap.com/adt/aunit">'
                '<external>'
                '<coverage active="false"/>'
                '</external>'
                '<options>'
                '<uriType value="semantic"/>'
                '<testDeterminationStrategy sameProgram="true" assignedTests="false" '
                'allTestClasses="false"/>'
                '<testRiskLevels harmless="true" dangerous="true" critical="true"/>'
                '<testDurations short="true" medium="true" long="true"/>'
                '</options>'
                f'<adtcore:objectSets xmlns:adtcore="http://www.sap.com/adt/core">'
                f'<objectSet kind="inclusive">'
                f'<adtcore:objectReferences>'
                f'<adtcore:objectReference adtcore:uri="{object_url}"/>'
                f'</adtcore:objectReferences>'
                f'</objectSet>'
                f'</adtcore:objectSets>'
                '</aunit:runConfiguration>'
            )

            resp = self.session.post(
                self._url("/sap/bc/adt/abapunit/testruns"),
                data=run_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/vnd.sap.adt.abapunit.testruns.config.v4+xml",
                    "Accept": "application/xml",
                },
                timeout=60,
            )

            if resp.status_code == 200:
                return {"ok": True, "results": resp.text[:3000]}
            else:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def create_transport_request(self, description: str, request_type: str = "K",
                                   target: str = "", reference_object_uri: str = "") -> dict:
        """
        Crea una orden de transporte en SAP vía ADT CTS API.
        Paso 1: transportchecks para obtener DEVCLASS del objeto
        Paso 2: crear el transporte con esos datos

        reference_object_uri: URI ADT del objeto real que origina el transporte
        (p.ej. "/sap/bc/adt/programs/includes/zcl_my_object"). Requerido para que
        el DEVCLASS detectado corresponda al objeto correcto — no hay un default
        seguro aquí, a diferencia de versiones anteriores de este cliente.
        """
        try:
            if not reference_object_uri:
                return {"ok": False, "message": "reference_object_uri es requerido"}

            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            ref_uri = reference_object_uri

            # Paso 1: Transport check para obtener DEVCLASS
            check_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
                '<asx:values>'
                '<DATA>'
                '<DEVCLASS/>'
                '<OPERATION>I</OPERATION>'
                f'<URI>{ref_uri}</URI>'
                '</DATA>'
                '</asx:values>'
                '</asx:abap>'
            )

            check_resp = self.session.post(
                self._url("/sap/bc/adt/cts/transportchecks"),
                data=check_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Accept": "application/vnd.sap.as+xml;charset=UTF-8;dataname=com.sap.adt.transport.service.checkData",
                    "Content-Type": "application/vnd.sap.as+xml; charset=UTF-8; dataname=com.sap.adt.transport.service.checkData",
                },
                timeout=30,
            )

            devclass = ""
            check_info = ""
            if check_resp.status_code == 200:
                check_info = check_resp.text[:1500]
                # Extraer DEVCLASS de la respuesta
                if "<DEVCLASS>" in check_resp.text:
                    start = check_resp.text.index("<DEVCLASS>") + len("<DEVCLASS>")
                    end = check_resp.text.index("</DEVCLASS>")
                    devclass = check_resp.text[start:end].strip()

            # Paso 2: Crear el transporte con CTS Project
            # Solo algunos sistemas SAP requieren CTS Project — self.cts_project viene
            # de config, no se hardcodea. Si está vacío, se omite el elemento.
            cts_project_element = (
                f'<CTS_PROJECT>{self.cts_project}</CTS_PROJECT>' if self.cts_project else ''
            )

            create_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
                '<asx:values>'
                '<DATA>'
                f'<DEVCLASS>{devclass}</DEVCLASS>'
                f'<REQUEST_TEXT>{description}</REQUEST_TEXT>'
                f'<REF>{ref_uri}</REF>'
                '<OPERATION>I</OPERATION>'
                f'{cts_project_element}'
                '</DATA>'
                '</asx:values>'
                '</asx:abap>'
            )

            params = {"transportLayer": self.transport_layer} if self.transport_layer else {}

            resp = self.session.post(
                self._url("/sap/bc/adt/cts/transports"),
                data=create_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Accept": "text/plain",
                    "Content-Type": "application/vnd.sap.as+xml; charset=UTF-8; dataname=com.sap.adt.CreateCorrectionRequest",
                },
                params=params,
                timeout=30,
            )

            if resp.status_code in (200, 201):
                transport_number = resp.text.strip().split("/")[-1] if resp.text else ""
                return {
                    "ok": True,
                    "transport": transport_number,
                    "description": description,
                    "devclass": devclass,
                    "type": "Workbench" if request_type == "K" else "Customizing",
                    "raw_response": resp.text[:500],
                }
            else:
                return {
                    "ok": False,
                    "status": resp.status_code,
                    "message": resp.text[:500],
                    "check_info": check_info,
                    "devclass_found": devclass,
                }

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def test_endpoint(self, path: str, method: str = "GET") -> dict:
        """Prueba un endpoint ADT específico para verificar si está disponible."""
        try:
            url = self._url(path)
            if method.upper() == "GET":
                resp = self.session.get(url, timeout=15)
            elif method.upper() == "OPTIONS":
                resp = self.session.options(url, timeout=15)
            elif method.upper() == "HEAD":
                resp = self.session.head(url, timeout=15)
            else:
                return {"ok": False, "message": f"Método {method} no soportado en test"}
            return {
                "ok": resp.status_code < 400,
                "status": resp.status_code,
                "headers": dict(resp.headers),
                "body_preview": resp.text[:5000] if resp.text else "",
            }
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def syntax_check(self, object_url: str) -> dict:
        """
        Ejecuta syntax check de un objeto ABAP vía ADT.
        object_url: URI ADT del objeto. Ej:
          - /sap/bc/adt/programs/programs/zr_sd_quick_orders
          - /sap/bc/adt/functions/groups/zsd_pros_int/fmodules/zsd_pros_currency_rate_get
          - /sap/bc/adt/oo/classes/zcl_sd_stock_query
        Retorna lista de errores/warnings encontrados.
        """
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "No se pudo obtener CSRF token"}

            # ADT syntax check usa el endpoint checkruns con checkObjectList
            check_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<chkrun:checkObjectList xmlns:chkrun="http://www.sap.com/adt/checkrun" '
                'xmlns:adtcore="http://www.sap.com/adt/core">'
                f'<chkrun:checkObject adtcore:uri="{object_url}" chkrun:version="active"/>'
                '</chkrun:checkObjectList>'
            )

            resp = self.session.post(
                self._url("/sap/bc/adt/checkruns"),
                data=check_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/vnd.sap.adt.checkobjects+xml",
                    "Accept": "application/vnd.sap.adt.checkmessages+xml",
                },
                params={"reporters": "abapCheckRun"},
                timeout=30,
            )

            if resp.status_code == 200:
                # Parsear mensajes de error/warning
                messages = []
                try:
                    root = ET.fromstring(resp.text)
                    for elem in root.iter():
                        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                        if tag in ("checkMessage", "message"):
                            msg_type = ""
                            msg_text = ""
                            msg_line = ""
                            for attr_name, attr_val in elem.attrib.items():
                                clean_attr = attr_name.split("}")[-1] if "}" in attr_name else attr_name
                                if clean_attr in ("type", "severity"):
                                    msg_type = attr_val
                                elif clean_attr in ("shortDescription", "text", "description", "shortText"):
                                    msg_text = attr_val
                                elif clean_attr == "line":
                                    msg_line = attr_val
                                elif clean_attr == "uri" and "start=" in attr_val:
                                    try:
                                        msg_line = attr_val.split("start=")[1].split(",")[0]
                                    except (IndexError, ValueError):
                                        pass
                            if msg_text:
                                messages.append({
                                    "type": msg_type,
                                    "line": msg_line,
                                    "text": msg_text,
                                })
                except ET.ParseError:
                    pass

                has_errors = any(m.get("type", "").upper() in ("E", "ERROR", "W", "WARNING")
                                 for m in messages)
                return {
                    "ok": True,
                    "has_errors": has_errors,
                    "message_count": len(messages),
                    "messages": messages,
                    "raw": resp.text[:2000] if not messages else "",
                }
            else:
                return {
                    "ok": False,
                    "status": resp.status_code,
                    "message": resp.text[:500],
                }

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_transport_xml_raw(self, transport_number: str) -> dict:
        """Retorna el XML crudo del endpoint CTS para diagnóstico — permite ver la estructura real de tags."""
        transport_number = transport_number.upper()
        try:
            url = self._url("/sap/bc/adt/cts/transportrequests")
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}

            # Extraer solo el fragmento XML de la OT solicitada para no devolver 49KB
            xml_text = resp.text
            start_marker = f'tm:number="{transport_number}"'
            idx = xml_text.find(start_marker)
            if idx == -1:
                return {"ok": False, "message": f"OT {transport_number} no encontrada en el XML"}

            # Retornar 3000 chars desde donde aparece la OT
            fragment = xml_text[max(0, idx - 50): idx + 3000]
            return {
                "ok": True,
                "transport": transport_number,
                "xml_fragment": fragment,
                "total_xml_size": len(xml_text),
            }
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_transport_details(self, transport_number: str) -> dict:
        """Obtiene los detalles y objetos de una orden de transporte específica."""
        transport_number = transport_number.upper()
        try:
            url = self._url("/sap/bc/adt/cts/transportrequests")
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}

            try:
                root = ET.fromstring(resp.text)
                TM = "http://www.sap.com/cts/adt/tm"
                ADTCORE = "http://www.sap.com/adt/core"

                # Buscar el request específico
                for req in root.iter():
                    tag = req.tag.split("}")[-1] if "}" in req.tag else req.tag
                    if tag == "request":
                        number = req.get(f"{{{TM}}}number", "")
                        if number == transport_number:
                            owner = req.get(f"{{{TM}}}owner", "")
                            desc = req.get(f"{{{TM}}}desc", "")
                            status = req.get(f"{{{TM}}}status", "")
                            target = req.get(f"{{{TM}}}target", "")

                            # Buscar tasks dentro del request
                            tasks = []
                            for child in req.iter():
                                child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                                if child_tag == "task":
                                    task_number = child.get(f"{{{TM}}}number", "")
                                    task_owner = child.get(f"{{{TM}}}owner", "")
                                    task_desc = child.get(f"{{{TM}}}desc", "")
                                    task_status = child.get(f"{{{TM}}}status", "")

                                    # Buscar objetos dentro de la task
                                    # SAP CTS usa tm:abap_object (con guión bajo)
                                    objects = []
                                    for obj in child.iter():
                                        obj_tag = obj.tag.split("}")[-1] if "}" in obj.tag else obj.tag
                                        if obj_tag in ("abap_object", "abapObject", "objectReference", "object"):
                                            # Intentar todos los atributos posibles según namespace
                                            obj_name = (
                                                obj.get(f"{{{TM}}}name") or
                                                obj.get(f"{{{ADTCORE}}}name") or
                                                obj.get("name") or ""
                                            )
                                            obj_type = (
                                                obj.get(f"{{{TM}}}type") or
                                                obj.get(f"{{{ADTCORE}}}type") or
                                                obj.get("type") or ""
                                            )
                                            obj_pgmid = obj.get(f"{{{TM}}}pgmid", obj.get("pgmid", ""))
                                            obj_lock = obj.get(f"{{{TM}}}lockflag", obj.get("lockflag", ""))
                                            obj_desc = (
                                                obj.get(f"{{{TM}}}obj_info") or
                                                obj.get(f"{{{TM}}}desc") or
                                                obj.get(f"{{{ADTCORE}}}description") or
                                                obj.get("description") or ""
                                            )
                                            obj_wbtype = obj.get(f"{{{TM}}}wbtype", obj.get("wbtype", ""))
                                            if obj_name:
                                                objects.append({
                                                    "name": obj_name,
                                                    "type": obj_type,
                                                    "wbtype": obj_wbtype,
                                                    "pgmid": obj_pgmid,
                                                    "locked": obj_lock,
                                                    "description": obj_desc,
                                                })

                                    tasks.append({
                                        "number": task_number,
                                        "owner": task_owner,
                                        "description": task_desc,
                                        "status": task_status,
                                        "objects": objects,
                                    })

                            return {
                                "ok": True,
                                "transport": transport_number,
                                "owner": owner,
                                "description": desc,
                                "status": status,
                                "target": target,
                                "tasks": tasks,
                            }

                return {"ok": False, "message": f"OT {transport_number} no encontrada en la lista de transportes visibles"}

            except ET.ParseError as e:
                return {"ok": False, "message": f"Error parseando XML: {str(e)}"}

        except Exception as e:
            return {"ok": False, "message": str(e)}

    def list_transports(self, user: str = "") -> dict:
        """Lista las órdenes de transporte modificables del usuario actual o uno específico."""
        try:
            url = self._url("/sap/bc/adt/cts/transportrequests")
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}

            # Parsear XML de respuesta
            transports = []
            try:
                root = ET.fromstring(resp.text)
                ns = {
                    "tm": "http://www.sap.com/cts/adt/tm",
                    "adtcore": "http://www.sap.com/adt/core",
                }
                # Buscar todos los requests
                for req in root.iter():
                    tag = req.tag.split("}")[-1] if "}" in req.tag else req.tag
                    if tag == "request":
                        number = req.get("{http://www.sap.com/cts/adt/tm}number", "")
                        owner = req.get("{http://www.sap.com/cts/adt/tm}owner", "")
                        desc = req.get("{http://www.sap.com/cts/adt/tm}desc", "")
                        status = req.get("{http://www.sap.com/cts/adt/tm}status", "")
                        target = req.get("{http://www.sap.com/cts/adt/tm}target", "")
                        # Filtrar por usuario si se especificó
                        if user and owner.upper() != user.upper():
                            continue
                        transports.append({
                            "number": number,
                            "owner": owner,
                            "description": desc,
                            "status": status,
                            "target": target,
                        })
            except ET.ParseError:
                return {"ok": False, "message": "Error parseando XML de transports"}

            return {
                "ok": True,
                "count": len(transports),
                "transports": transports,
            }
        except Exception as e:
            return {"ok": False, "message": str(e)}
