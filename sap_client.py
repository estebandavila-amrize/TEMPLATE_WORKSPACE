"""
SAP ADT Client — Clean SOLID rewrite.
Single-responsibility helpers: _get_source, _write_source, _post_with_csrf.
All public methods return dict with "ok" key.
"""

import os
import re
import time
import base64
import requests
import xml.etree.ElementTree as ET
from typing import Optional
from requests.auth import HTTPBasicAuth


class SAPADTClient:
    """HTTP client for SAP ABAP Development Tools (ADT) REST API."""

    def __init__(self, host: str, client: str, username: str, password: str, secure: bool = False):
        self.base_url = f"{'https' if secure else 'http'}://{host}"
        self.client = client
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({
            "sap-client": client,
            "Accept": "application/xml",
        })

    # ──────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _fetch_csrf_token(self) -> Optional[str]:
        """GET /sap/bc/adt/discovery with X-CSRF-Token: Fetch."""
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
        """POST with _action=LOCK. Returns {"ok": True, "lock_handle": str}."""
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
                handle = resp.text.strip()
                if "<LOCK_HANDLE>" in resp.text:
                    start = resp.text.index("<LOCK_HANDLE>") + len("<LOCK_HANDLE>")
                    end = resp.text.index("</LOCK_HANDLE>")
                    handle = resp.text[start:end].strip()
                return {"ok": True, "lock_handle": handle}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _unlock_object(self, object_url: str, lock_handle: str, csrf_token: str):
        """POST with _action=UNLOCK. Fire-and-forget."""
        try:
            self.session.post(
                self._url(object_url),
                params={"_action": "UNLOCK", "lockHandle": lock_handle},
                headers={"X-CSRF-Token": csrf_token},
                timeout=15,
            )
        except Exception:
            pass

    def _get_source(self, path: str) -> dict:
        """Generic GET for any /source/main endpoint. Returns {"ok": True, "source": str}."""
        try:
            resp = self.session.get(
                self._url(path),
                headers={"Accept": "text/plain"},
                timeout=30,
            )
            if resp.status_code == 200:
                return {"ok": True, "source": resp.text}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _write_source(self, object_uri: str, source_code: str, transport: str = "") -> dict:
        """Lock → PUT /source/main → Unlock cycle for programs and interfaces."""
        source_url = object_uri if "/source/main" in object_uri else f"{object_uri}/source/main"
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            lock_result = self._lock_object(object_uri, csrf_token)
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
            self._unlock_object(object_uri, lock_handle, csrf_token)

            if resp.status_code in (200, 204):
                return {"ok": True}
            return {"ok": False, "step": "write", "status": resp.status_code, "message": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _post_with_csrf(self, path: str, data=None, headers=None, params=None, timeout=30) -> requests.Response:
        """POST that fetches a CSRF token first. Used by sql_query, enhancements, usage_references, package_contents."""
        csrf_token = self._fetch_csrf_token()
        hdrs = headers or {}
        hdrs["X-CSRF-Token"] = csrf_token or ""
        return self.session.post(
            self._url(path),
            data=data,
            headers=hdrs,
            params=params,
            timeout=timeout,
        )

    @staticmethod
    def _split_class_source(source_code: str):
        """Split class source into (definition, implementation) parts."""
        pattern = re.compile(r'^(CLASS\s+\S+\s+IMPLEMENTATION\s*\.)', re.IGNORECASE | re.MULTILINE)
        match = pattern.search(source_code)
        if match:
            return source_code[:match.start()].rstrip(), source_code[match.start():]
        return source_code, ""

    def _write_class_include(self, object_url: str, include_type: str,
                              content: str, lock_handle: str, csrf_token: str, transport: str) -> dict:
        """Write a specific class include (definitions or implementations)."""
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

    # ──────────────────────────────────────────────
    # Public read-only source methods (all delegate to _get_source)
    # ──────────────────────────────────────────────

    def ping(self) -> dict:
        """Verify connectivity via ADT discovery endpoint."""
        try:
            resp = self.session.get(self._url("/sap/bc/adt/discovery"), timeout=15)
            return {
                "ok": resp.status_code == 200,
                "status": resp.status_code,
                "message": "Successfully connected to SAP ADT" if resp.status_code == 200 else resp.text[:200],
            }
        except Exception as e:
            return {"ok": False, "status": 0, "message": str(e)}

    def get_program_source(self, program_name: str) -> dict:
        program_name = program_name.upper()
        result = self._get_source(f"/sap/bc/adt/programs/programs/{program_name}/source/main")
        if result.get("ok"):
            result["program"] = program_name
        return result

    def get_class_source(self, class_name: str) -> dict:
        class_name = class_name.upper()
        result = self._get_source(f"/sap/bc/adt/oo/classes/{class_name.lower()}/source/main")
        if result.get("ok"):
            result["class"] = class_name
        return result

    def get_include_source(self, include_name: str) -> dict:
        include_name = include_name.upper()
        result = self._get_source(f"/sap/bc/adt/programs/includes/{include_name}/source/main")
        if result.get("ok"):
            result["include"] = include_name
        return result

    def get_interface_source(self, interface_name: str) -> dict:
        interface_name = interface_name.upper()
        result = self._get_source(f"/sap/bc/adt/oo/interfaces/{interface_name.lower()}/source/main")
        if result.get("ok"):
            result["interface"] = interface_name
        return result

    def get_function_module_source(self, function_group: str, function_name: str) -> dict:
        fg = function_group.upper()
        fm = function_name.upper()
        result = self._get_source(f"/sap/bc/adt/functions/groups/{fg.lower()}/fmodules/{fm.lower()}/source/main")
        if result.get("ok"):
            result["function"] = fm
        return result

    def get_function_group_source(self, function_group: str) -> dict:
        fg = function_group.upper()
        result = self._get_source(f"/sap/bc/adt/functions/groups/{fg.lower()}/source/main")
        if result.get("ok"):
            result["function_group"] = fg
        return result

    def get_structure_source(self, structure_name: str) -> dict:
        structure_name = structure_name.upper()
        result = self._get_source(f"/sap/bc/adt/ddic/structures/{structure_name.lower()}/source/main")
        if result.get("ok"):
            result["structure"] = structure_name
        return result

    def get_cds_view_source(self, cds_view_name: str) -> dict:
        cds_view_name = cds_view_name.upper()
        result = self._get_source(f"/sap/bc/adt/ddic/ddl/sources/{cds_view_name}/source/main")
        if result.get("ok"):
            result["cds_view"] = cds_view_name
        return result

    def get_source_by_uri(self, uri: str) -> dict:
        """Fetch ABAP source by direct ADT URI path."""
        if not uri.startswith("/sap/bc/adt/"):
            return {"ok": False, "message": "URI must start with /sap/bc/adt/"}
        result = self._get_source(uri)
        if result.get("ok"):
            result["uri"] = uri
        return result

    # ──────────────────────────────────────────────
    # Dictionary / metadata reads
    # ──────────────────────────────────────────────

    def get_table_definition(self, table_name: str) -> dict:
        """Get DDIC table definition trying multiple ADT endpoints."""
        table_name = table_name.upper()
        # Attempt 1: transparent tables
        try:
            url = self._url(f"/sap/bc/adt/ddic/tables/{table_name}")
            resp = self.session.get(url, timeout=20)
            if resp.status_code == 200:
                return {"ok": True, "definition": resp.text, "table": table_name, "source": "ddic/tables"}
        except Exception:
            pass
        # Attempt 2: structures endpoint with multiple accept types
        for accept in [
            "application/vnd.sap.adt.blues.v1+xml",
            "application/vnd.sap.adt.ddic.structures.v2+xml",
            "application/vnd.sap.adt.ddic.structures+xml",
        ]:
            try:
                url = self._url(f"/sap/bc/adt/ddic/structures/{table_name}")
                resp = self.session.get(url, headers={"Accept": accept}, timeout=20)
                if resp.status_code == 200:
                    return {"ok": True, "definition": resp.text, "table": table_name, "source": "ddic/structures"}
            except Exception:
                pass
        # Attempt 3: data elements
        try:
            url = self._url(f"/sap/bc/adt/ddic/dataelements/{table_name}")
            resp = self.session.get(url, headers={"Accept": "application/vnd.sap.adt.dataelements.v1+xml"}, timeout=20)
            if resp.status_code == 200:
                return {"ok": True, "definition": resp.text, "table": table_name, "source": "ddic/dataelements"}
        except Exception:
            pass
        return {"ok": False, "table": table_name,
                "message": f"Table {table_name} not accessible via ADT DDIC endpoints."}

    def get_transaction_info(self, transaction_name: str) -> dict:
        """Get transaction info (package, application)."""
        transaction_name = transaction_name.upper()
        try:
            encoded = requests.utils.quote(transaction_name, safe="")
            url = self._url(
                f"/sap/bc/adt/repository/informationsystem/objectproperties/values"
                f"?uri=%2Fsap%2Fbc%2Fadt%2Fvit%2Fwb%2Fobject_type%2Ftrant%2Fobject_name%2F{encoded}"
                f"&facet=package&facet=appl"
            )
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                return {"ok": True, "data": resp.text, "transaction": transaction_name}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def search_objects(self, query: str, max_results: int = 20) -> dict:
        """Quick search for ABAP objects by name pattern."""
        try:
            url = self._url("/sap/bc/adt/repository/informationsystem/search")
            params = {"operation": "quickSearch", "query": query, "maxResults": max_results}
            resp = self.session.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                objects = []
                try:
                    root = ET.fromstring(resp.text)
                    for obj in root.iter():
                        name = obj.get("{http://www.sap.com/adt/core}name")
                        obj_type = obj.get("{http://www.sap.com/adt/core}type")
                        if name and obj_type:
                            objects.append({"name": name, "type": obj_type})
                except ET.ParseError:
                    pass
                return {"ok": True, "objects": objects, "raw": resp.text[:1000]}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_package_contents(self, package_name: str) -> dict:
        """Get objects in a development package via nodestructure POST (requires CSRF)."""
        package_name = package_name.upper()
        try:
            resp = self._post_with_csrf(
                "/sap/bc/adt/repository/nodestructure",
                data="",
                headers={
                    "Content-Type": "application/xml",
                    "Accept": "application/xml",
                },
                params={
                    "parent_type": "DEVC/K",
                    "parent_name": package_name,
                    "withShortDescriptions": "true",
                },
                timeout=30,
            )
            if resp.status_code == 200:
                objects = []
                try:
                    root = ET.fromstring(resp.text)
                    for node in root.iter():
                        tag = node.tag.split("}")[-1] if "}" in node.tag else node.tag
                        if tag == "SEU_ADT_REPOSITORY_OBJ_NODE":
                            obj_name = obj_type = obj_desc = obj_uri = ""
                            for child in node:
                                ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                                if ctag == "OBJECT_NAME" and child.text:
                                    obj_name = child.text.strip()
                                elif ctag == "OBJECT_TYPE" and child.text:
                                    obj_type = child.text.strip()
                                elif ctag == "DESCRIPTION" and child.text:
                                    obj_desc = child.text.strip()
                                elif ctag == "OBJECT_URI" and child.text:
                                    obj_uri = child.text.strip()
                            if obj_name:
                                objects.append({"name": obj_name, "type": obj_type,
                                                "description": obj_desc, "uri": obj_uri})
                except ET.ParseError:
                    return {"ok": True, "raw": resp.text[:3000], "parse_error": True}
                return {"ok": True, "package": package_name, "objects_count": len(objects), "objects": objects}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_usage_references(self, object_type: str, object_name: str, function_group: str = "") -> dict:
        """Where-used list for an ABAP object."""
        object_name = object_name.upper()
        ot = object_type.lower()
        path_map = {
            "class": f"/sap/bc/adt/oo/classes/{object_name.lower()}/source/main",
            "clas": f"/sap/bc/adt/oo/classes/{object_name.lower()}/source/main",
            "program": f"/sap/bc/adt/programs/programs/{object_name}/source/main",
            "prog": f"/sap/bc/adt/programs/programs/{object_name}/source/main",
            "include": f"/sap/bc/adt/programs/includes/{object_name}/source/main",
            "interface": f"/sap/bc/adt/oo/interfaces/{object_name.lower()}/source/main",
            "table": f"/sap/bc/adt/ddic/tables/{object_name}/source/main",
            "structure": f"/sap/bc/adt/ddic/structures/{object_name}/source/main",
        }
        if ot in ("function_module", "fm"):
            if not function_group:
                return {"ok": False, "message": "function_group is required for function_module"}
            fg = function_group.upper()
            src_path = f"/sap/bc/adt/functions/groups/{fg.lower()}/fmodules/{object_name.lower()}/source/main"
        else:
            src_path = path_map.get(ot)
        if not src_path:
            return {"ok": False, "message": f"Unsupported object_type: {object_type}"}

        try:
            # Fetch CSRF from the source endpoint
            full_url = self._url(src_path)
            resp_csrf = self.session.get(full_url, headers={"X-CSRF-Token": "Fetch", "Accept": "text/plain"}, timeout=15)
            token = resp_csrf.headers.get("X-CSRF-Token") or resp_csrf.headers.get("x-csrf-token")
            if not token:
                return {"ok": False, "message": "Failed to obtain CSRF token for where-used"}

            uri_param = f"{src_path}?version=active#start=1,0"
            body = (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<usageReferenceRequest xmlns="http://www.sap.com/adt/ris/usageReferences"/>'
            )
            resp = self.session.post(
                self._url("/sap/bc/adt/repository/informationsystem/usageReferences"),
                params={"uri": uri_param},
                headers={
                    "X-CSRF-Token": token,
                    "Accept": "application/vnd.sap.adt.repository.usagereferences.result.v1+xml",
                    "Content-Type": "application/vnd.sap.adt.repository.usagereferences.request.v1+xml",
                },
                data=body,
                timeout=60,
            )
            if resp.status_code != 200:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}

            references = []
            obj_pattern = re.compile(r'adtcore:name="([^"]*)"[^>]*adtcore:type="([^"]*)"', re.DOTALL)
            for match in obj_pattern.finditer(resp.text):
                if match.group(1):
                    references.append({"name": match.group(1), "type": match.group(2)})
            return {"ok": True, "object": object_name, "object_type": object_type,
                    "references_count": len(references), "references": references}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_enhancements(self, object_name: str, program_context: str = "") -> dict:
        """Get enhancement implementations for a program or include."""
        object_name = object_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            obj_type = None
            enh_url = None

            # Try as program first
            prog_url = self._url(f"/sap/bc/adt/programs/programs/{object_name}")
            resp = self.session.get(prog_url, timeout=15)
            if resp.status_code == 200:
                obj_type = "program"
                enh_url = self._url(f"/sap/bc/adt/programs/programs/{object_name}/source/main/enhancements/elements")
            else:
                # Try as include
                inc_url = self._url(f"/sap/bc/adt/programs/includes/{object_name}")
                resp = self.session.get(inc_url, timeout=15)
                if resp.status_code == 200:
                    obj_type = "include"
                    context = ""
                    if program_context:
                        context = f"/sap/bc/adt/programs/programs/{program_context.upper()}"
                    else:
                        ctx_match = re.search(r'include:contextRef[^>]+adtcore:uri="([^"]+)"', resp.text)
                        if ctx_match:
                            context = ctx_match.group(1)
                    enh_url = self._url(f"/sap/bc/adt/programs/includes/{object_name}/source/main/enhancements/elements")
                    if context:
                        enh_url += f"?context={context}"

            if not enh_url:
                return {"ok": False, "message": f"Object {object_name} not found as program or include"}

            resp_enh = self.session.get(
                enh_url,
                headers={"Accept": "application/vnd.sap.adt.enhancement.v1+xml"},
                timeout=30,
            )
            if resp_enh.status_code != 200:
                return {"ok": False, "status": resp_enh.status_code, "message": resp_enh.text[:500]}

            enhancements = []
            idx = 0
            for match in re.finditer(r'<enh:source[^>]*>([^<]*)</enh:source>', resp_enh.text):
                before = resp_enh.text[:match.start()]
                name_match = re.search(r'adtcore:name="([^"]*)"[^>]*$', before)
                enh_name = name_match.group(1) if name_match else f"enhancement_{idx + 1}"
                b64_source = match.group(1)
                source_code = ""
                if b64_source:
                    try:
                        source_code = base64.b64decode(b64_source).decode("utf-8")
                    except Exception:
                        source_code = b64_source
                enhancements.append({"name": enh_name, "source_code": source_code})
                idx += 1

            return {"ok": True, "object_name": object_name, "object_type": obj_type,
                    "enhancement_count": len(enhancements), "enhancements": enhancements}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_sql_query(self, sql_query: str, max_rows: int = 100) -> dict:
        """Execute freestyle SQL via ADT Data Preview. Covers both table contents and complex queries."""
        if not sql_query:
            return {"ok": False, "message": "sql_query is required"}
        try:
            resp = self._post_with_csrf(
                "/sap/bc/adt/datapreview/freestyle",
                data=sql_query.encode("utf-8"),
                headers={
                    "Content-Type": "text/plain; charset=utf-8",
                    "Accept": "application/vnd.sap.adt.datapreview.table.v1+xml",
                },
                params={"rowNumber": max_rows},
                timeout=60,
            )
            if resp.status_code != 200:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}

            xml_data = resp.text
            total_rows_m = re.search(r'<dataPreview:totalRows>(\d+)</dataPreview:totalRows>', xml_data)
            total_rows = int(total_rows_m.group(1)) if total_rows_m else 0
            exec_time_m = re.search(r'<dataPreview:queryExecutionTime>([\d.]+)</dataPreview:queryExecutionTime>', xml_data)
            exec_time = float(exec_time_m.group(1)) if exec_time_m else 0.0

            # Extract columns
            columns = []
            for cm in re.finditer(r'<dataPreview:metadata[^>]*>', xml_data):
                col_text = cm.group(0)
                name_m = re.search(r'dataPreview:name="([^"]+)"', col_text)
                type_m = re.search(r'dataPreview:type="([^"]+)"', col_text)
                if name_m:
                    columns.append({"name": name_m.group(1), "type": type_m.group(1) if type_m else "UNKNOWN"})

            # Extract column data
            column_sections = re.findall(r'<dataPreview:columns>.*?</dataPreview:columns>', xml_data, re.DOTALL)
            column_data = {}
            for idx, section in enumerate(column_sections):
                if idx < len(columns):
                    col_name = columns[idx]["name"]
                    data_matches = re.findall(r'<dataPreview:data[^>]*>(.*?)</dataPreview:data>', section)
                    column_data[col_name] = [re.sub(r'<[^>]+>', '', m).strip() if m else None for m in data_matches]

            # Convert to rows
            rows = []
            if column_data:
                max_row_count = max(len(arr) for arr in column_data.values())
                for row_idx in range(max_row_count):
                    row = {}
                    for col in columns:
                        vals = column_data.get(col["name"], [])
                        row[col["name"]] = vals[row_idx] if row_idx < len(vals) else None
                    rows.append(row)

            return {"ok": True, "sql_query": sql_query, "execution_time_ms": exec_time,
                    "total_rows": total_rows, "row_count": len(rows), "columns": columns, "rows": rows}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_includes_list(self, object_name: str, object_type: str = "program") -> dict:
        """Recursively discover all INCLUDEs within a program or include."""
        object_name = object_name.upper()
        if object_type not in ("program", "include"):
            return {"ok": False, "message": "object_type must be 'program' or 'include'"}

        def _fetch_src(name: str, ot: str) -> str:
            if ot == "program":
                path = f"/sap/bc/adt/programs/programs/{name}/source/main"
            else:
                path = f"/sap/bc/adt/programs/includes/{name}/source/main"
            try:
                resp = self.session.get(self._url(path), headers={"Accept": "text/plain"}, timeout=30)
                return resp.text if resp.status_code == 200 else ""
            except Exception:
                return ""

        def _parse_includes(source: str) -> list:
            includes = []
            for line in source.split("\n"):
                clean = re.sub(r'\s+', ' ', line).strip().upper()
                if clean.startswith("INCLUDE ") and "." in clean:
                    m = re.match(r'^INCLUDE\s+([A-Z0-9_]+)\s*\.', clean)
                    if m and m.group(1) not in includes:
                        includes.append(m.group(1))
            return includes

        try:
            all_includes = set()
            visited = set()

            def _recurse(name: str, ot: str):
                key = f"{ot}:{name}"
                if key in visited:
                    return
                visited.add(key)
                source = _fetch_src(name, ot)
                if not source:
                    return
                for inc in _parse_includes(source):
                    all_includes.add(inc)
                    _recurse(inc, "include")

            _recurse(object_name, object_type)
            return {"ok": True, "object_name": object_name, "object_type": object_type,
                    "includes_count": len(all_includes), "includes": sorted(all_includes)}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    # ──────────────────────────────────────────────
    # Write / Create operations
    # ──────────────────────────────────────────────

    def create_program(self, program_name: str, description: str, package: str,
                       transport: str, source_code: str) -> dict:
        """Create a new ABAP program, write source, and activate."""
        program_name = program_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

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
                return {"ok": False, "step": "create", "status": resp.status_code, "message": resp.text[:500]}

            write_result = self.update_program_source(program_name, source_code, transport)
            if not write_result.get("ok"):
                return write_result

            activate_result = self.activate_object(program_name, "PROG/P")
            return {"ok": activate_result.get("ok", False), "program": program_name,
                    "created": True, "activated": activate_result.get("ok", False),
                    "activate_detail": activate_result}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_program_source(self, program_name: str, source_code: str, transport: str = "") -> dict:
        """Update source of an existing ABAP program via _write_source."""
        program_name = program_name.upper()
        object_url = f"/sap/bc/adt/programs/programs/{program_name}"
        result = self._write_source(object_url, source_code, transport)
        if result.get("ok"):
            result["program"] = program_name
            result["message"] = "Source code updated"
        return result

    def update_program_from_file(self, program_name: str, file_path: str, transport: str = "") -> dict:
        """Read source from a local file and upload to SAP."""
        try:
            if not os.path.isabs(file_path):
                base_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(base_dir, file_path)
            if not os.path.exists(file_path):
                return {"ok": False, "message": f"File not found: {file_path}"}
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            if not source_code.strip():
                return {"ok": False, "message": f"Empty file: {file_path}"}
            line_count = source_code.count("\n") + 1
            result = self.update_program_source(program_name, source_code, transport)
            if result.get("ok"):
                result["file_path"] = file_path
                result["lines_uploaded"] = line_count
                result["message"] = f"Source code updated from file ({line_count} lines)"
            return result
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_function_module_source(self, function_group: str, function_name: str,
                                      source_code: str, transport: str = "") -> dict:
        """Update source of an existing Function Module via _write_source."""
        fg = function_group.lower()
        fm = function_name.lower()
        object_url = f"/sap/bc/adt/functions/groups/{fg}/fmodules/{fm}"
        result = self._write_source(object_url, source_code, transport)
        if result.get("ok"):
            result["function"] = function_name.upper()
            result["message"] = "FM source code updated"
        return result

    def create_interface(self, interface_name: str, description: str, package: str,
                         transport: str, source_code: str) -> dict:
        """Create a new ABAP OO interface, write source, and activate."""
        interface_name = interface_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

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
                return {"ok": False, "step": "create", "status": resp.status_code, "message": resp.text[:500]}

            # Write source via _write_source
            object_url = f"/sap/bc/adt/oo/interfaces/{interface_name.lower()}"
            write_result = self._write_source(object_url, source_code, transport)
            if not write_result.get("ok"):
                return {"ok": False, "step": "write", "detail": write_result}

            activate_result = self.activate_object(interface_name, "INTF/OI")
            return {"ok": activate_result.get("ok", False), "interface": interface_name,
                    "created": True, "activated": activate_result.get("ok", False),
                    "activate_detail": activate_result}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_interface_source(self, interface_name: str, source_code: str, transport: str = "") -> dict:
        """Update source of an existing ABAP interface via _write_source."""
        interface_name = interface_name.upper()
        object_url = f"/sap/bc/adt/oo/interfaces/{interface_name.lower()}"
        result = self._write_source(object_url, source_code, transport)
        if result.get("ok"):
            result["interface"] = interface_name
            result["message"] = "Source code updated"
        return result

    def create_structure(self, structure_name: str, description: str, package: str,
                         transport: str, source_code: str) -> dict:
        """Create a new DDIC structure/table in SAP via ADT, write DDL source, and activate.
        source_code should be in DDL format, e.g.:
          @EndUserText.label : 'My Table'
          define type zmy_table {
            key mandt : mandt not null;
            key id    : sysuuid_x16 not null;
            name      : char40;
          }
        """
        structure_name = structure_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            # Step 1: Try creating via POST with blues content type
            create_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<blue:blueSource xmlns:blue="http://www.sap.com/wbobj/blue" '
                'xmlns:adtcore="http://www.sap.com/adt/core" '
                'xmlns:abapsource="http://www.sap.com/adt/abapsource" '
                'abapsource:fixPointArithmetic="false" '
                'abapsource:activeUnicodeCheck="false" '
                f'adtcore:description="{description}" '
                f'adtcore:language="EN" '
                f'adtcore:name="{structure_name}" '
                f'adtcore:type="TABL/DS" '
                f'adtcore:responsible="{self.username}">'
                f'<adtcore:packageRef adtcore:name="{package}"/>'
                '</blue:blueSource>'
            )
            params = {}
            if transport:
                params["corrNr"] = transport

            # Try multiple content types for creation
            content_types = [
                "application/vnd.sap.adt.blues.v1+xml",
                "application/vnd.sap.adt.ddic.structures.v2+xml",
                "application/vnd.sap.adt.ddic.structures+xml",
                "application/xml",
            ]
            resp = None
            for ct in content_types:
                resp = self.session.post(
                    self._url("/sap/bc/adt/ddic/structures"),
                    data=create_xml.encode("utf-8"),
                    headers={
                        "X-CSRF-Token": csrf_token,
                        "Content-Type": ct,
                    },
                    params=params,
                    timeout=30,
                )
                if resp.status_code in (200, 201):
                    break

            if resp.status_code not in (200, 201):
                return {"ok": False, "step": "create", "status": resp.status_code, "message": resp.text[:500]}

            # Step 2: Write the DDL source
            object_url = f"/sap/bc/adt/ddic/structures/{structure_name.lower()}"
            write_result = self._write_source(object_url, source_code, transport)
            if not write_result.get("ok"):
                return {"ok": False, "step": "write", "detail": write_result}

            # Step 3: Activate
            activate_result = self.activate_object(structure_name, "TABL/DS")
            return {"ok": activate_result.get("ok", False), "structure": structure_name,
                    "created": True, "activated": activate_result.get("ok", False),
                    "activate_detail": activate_result}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_structure_source(self, structure_name: str, source_code: str, transport: str = "") -> dict:
        """Update DDL source of an existing DDIC structure/table via _write_source."""
        structure_name = structure_name.upper()
        object_url = f"/sap/bc/adt/ddic/structures/{structure_name.lower()}"
        result = self._write_source(object_url, source_code, transport)
        if result.get("ok"):
            result["structure"] = structure_name
            result["message"] = "Structure updated"
        return result

    def create_class(self, class_name: str, description: str, package: str,
                     transport: str, source_code: str, is_final: bool = True) -> dict:
        """Create a new ABAP OO class, write source (def+impl includes), and activate."""
        class_name = class_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            final_attr = "true" if is_final else "false"
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
                return {"ok": False, "step": "create", "status": resp.status_code, "message": resp.text[:500]}

            # Write via includes (definition + implementation)
            object_url = f"/sap/bc/adt/oo/classes/{class_name.lower()}"
            definition, implementation = self._split_class_source(source_code)

            csrf_token2 = self._fetch_csrf_token()
            lock_result = self._lock_object(object_url, csrf_token2)
            if not lock_result.get("ok"):
                return {"ok": False, "step": "lock", "detail": lock_result}
            lock_handle = lock_result["lock_handle"]

            def_result = self._write_class_include(object_url, "definitions", definition, lock_handle, csrf_token2, transport)
            if not def_result.get("ok"):
                self._unlock_object(object_url, lock_handle, csrf_token2)
                return {"ok": False, "step": "write_definitions", "detail": def_result}

            if implementation:
                impl_result = self._write_class_include(object_url, "implementations", implementation, lock_handle, csrf_token2, transport)
                if not impl_result.get("ok"):
                    self._unlock_object(object_url, lock_handle, csrf_token2)
                    return {"ok": False, "step": "write_implementations", "detail": impl_result}

            self._unlock_object(object_url, lock_handle, csrf_token2)

            activate_result = self.activate_object(class_name, "CLAS/OC")
            return {"ok": activate_result.get("ok", False), "class": class_name,
                    "created": True, "activated": activate_result.get("ok", False),
                    "activate_detail": activate_result}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def update_class_source(self, class_name: str, source_code: str, transport: str = "") -> dict:
        """Update class source. Strategy 1: /source/main PUT. Fallback: separate includes."""
        class_name = class_name.upper()
        object_url = f"/sap/bc/adt/oo/classes/{class_name.lower()}"
        source_url = f"{object_url}/source/main"
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            definition, implementation = self._split_class_source(source_code)

            # Strategy 1: Try /source/main (works on ECC 7.50)
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
                headers={"X-CSRF-Token": csrf_token, "Content-Type": "text/plain; charset=utf-8"},
                params=params,
                timeout=30,
            )
            if resp.status_code in (200, 204):
                self._unlock_object(object_url, lock_handle, csrf_token)
                return {"ok": True, "class": class_name, "message": "Source code updated via /source/main"}

            # Unlock from failed attempt
            self._unlock_object(object_url, lock_handle, csrf_token)

            # Strategy 2: Write definitions then re-lock for implementations
            csrf_token = self._fetch_csrf_token()
            lock_result = self._lock_object(object_url, csrf_token)
            if not lock_result.get("ok"):
                return {"ok": False, "step": "lock_for_def", "detail": lock_result}
            lock_handle = lock_result["lock_handle"]

            def_result = self._write_class_include(object_url, "definitions", definition, lock_handle, csrf_token, transport)
            self._unlock_object(object_url, lock_handle, csrf_token)
            if not def_result.get("ok"):
                return {"ok": False, "step": "write_definitions", "detail": def_result}

            if implementation:
                csrf_token = self._fetch_csrf_token()
                lock_result = self._lock_object(object_url, csrf_token)
                if not lock_result.get("ok"):
                    return {"ok": False, "step": "lock_for_impl", "detail": lock_result}
                lock_handle = lock_result["lock_handle"]
                impl_result = self._write_class_include(object_url, "implementations", implementation, lock_handle, csrf_token, transport)
                self._unlock_object(object_url, lock_handle, csrf_token)
                if not impl_result.get("ok"):
                    return {"ok": False, "step": "write_implementations", "detail": impl_result}

            return {"ok": True, "class": class_name, "message": "Source code updated"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    # ──────────────────────────────────────────────
    # Patch, Delete, Activate, Syntax Check, Unit Tests
    # ──────────────────────────────────────────────

    def patch_source(self, object_uri: str, operations: list, transport: str = "") -> dict:
        """Apply patch operations to ABAP source without replacing the entire file."""
        if not object_uri or not operations:
            return {"ok": False, "message": "object_uri and operations are required"}
        try:
            source_url = object_uri if "/source/main" in object_uri else f"{object_uri}/source/main"
            resp = self.session.get(self._url(source_url), headers={"Accept": "text/plain"}, timeout=30)
            if resp.status_code != 200:
                return {"ok": False, "step": "get_source", "status": resp.status_code, "message": resp.text[:300]}
            original_source = resp.text
            new_source = original_source

            # Separate line-based and text-based operations
            line_ops = [op for op in operations if op.get("type") in ("insert", "replace", "delete")]
            text_ops = [op for op in operations if op.get("type") == "search_replace"]

            # Apply line-based operations (reverse order to preserve indices)
            if line_ops:
                lines = new_source.split("\n")
                sorted_ops = sorted(line_ops, key=lambda o: o.get("from_line", o.get("after_line", 0)), reverse=True)
                for op in sorted_ops:
                    op_type = op.get("type")
                    if op_type == "insert":
                        after = op.get("after_line", 0)
                        content = op.get("content", "")
                        new_lines = content.split("\n")
                        lines = lines[:after] + new_lines + lines[after:]
                    elif op_type == "replace":
                        from_l = op.get("from_line", 1) - 1
                        to_l = op.get("to_line", from_l + 1)
                        content = op.get("content", "")
                        new_lines = content.split("\n")
                        lines = lines[:from_l] + new_lines + lines[to_l:]
                    elif op_type == "delete":
                        from_l = op.get("from_line", 1) - 1
                        to_l = op.get("to_line", from_l + 1)
                        lines = lines[:from_l] + lines[to_l:]
                new_source = "\n".join(lines)

            # Apply text-based operations
            for op in text_ops:
                search = op.get("search", "")
                replace_str = op.get("replace", "")
                if search:
                    if op.get("all", False):
                        new_source = new_source.replace(search, replace_str)
                    else:
                        new_source = new_source.replace(search, replace_str, 1)

            if new_source == original_source:
                return {"ok": True, "message": "No changes applied (source unchanged)", "changed": False}

            # Write back
            write_result = self._write_source(object_uri, new_source, transport)
            if write_result.get("ok"):
                old_count = original_source.count("\n") + 1
                new_count = new_source.count("\n") + 1
                return {"ok": True, "changed": True, "operations_applied": len(operations),
                        "line_delta": new_count - old_count, "old_line_count": old_count, "new_line_count": new_count}
            return write_result
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def delete_object(self, object_uri: str, transport: str = "") -> dict:
        """Delete an ABAP object. IRREVERSIBLE."""
        if not object_uri:
            return {"ok": False, "message": "object_uri is required"}
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            lock_result = self._lock_object(object_uri, csrf_token)
            if not lock_result.get("ok"):
                return {"ok": False, "step": "lock", "detail": lock_result}
            lock_handle = lock_result["lock_handle"]

            params = {"lockHandle": lock_handle}
            if transport:
                params["corrNr"] = transport

            resp = self.session.delete(
                self._url(object_uri),
                headers={"X-CSRF-Token": csrf_token},
                params=params,
                timeout=30,
            )
            if resp.status_code in (200, 204):
                return {"ok": True, "deleted": True, "uri": object_uri}
            self._unlock_object(object_uri, lock_handle, csrf_token)
            return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def activate_object(self, object_name: str, object_type: str = "PROG/P") -> dict:
        """Activate an ABAP object."""
        object_name = object_name.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            activate_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<adtcore:objectReferences xmlns:adtcore="http://www.sap.com/adt/core">'
                f'<adtcore:objectReference adtcore:name="{object_name}" adtcore:type="{object_type}"/>'
                '</adtcore:objectReferences>'
            )
            resp = self.session.post(
                self._url("/sap/bc/adt/activation"),
                data=activate_xml.encode("utf-8"),
                headers={"X-CSRF-Token": csrf_token, "Content-Type": "application/xml"},
                params={"method": "activate", "preauditRequested": "true"},
                timeout=30,
            )
            if resp.status_code in (200, 204):
                has_errors = "severity=\"error\"" in resp.text.lower() if resp.text else False
                return {"ok": not has_errors, "object": object_name,
                        "message": "Activated successfully" if not has_errors else "Activation with errors",
                        "detail": resp.text[:500] if has_errors else ""}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def syntax_check(self, object_url: str) -> dict:
        """Run syntax check on an ABAP object via ADT checkruns."""
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

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
                messages = []
                try:
                    root = ET.fromstring(resp.text)
                    for elem in root.iter():
                        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                        if tag in ("checkMessage", "message"):
                            msg_type = msg_text = msg_line = ""
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
                                messages.append({"type": msg_type, "line": msg_line, "text": msg_text})
                except ET.ParseError:
                    pass
                has_errors = any(m.get("type", "").upper() in ("E", "ERROR", "W", "WARNING") for m in messages)
                return {"ok": True, "has_errors": has_errors, "message_count": len(messages),
                        "messages": messages, "raw": resp.text[:2000] if not messages else ""}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def run_abap_unit(self, object_url: str) -> dict:
        """Execute ABAP Unit tests for an object."""
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            run_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<aunit:runConfiguration xmlns:aunit="http://www.sap.com/adt/aunit">'
                '<external><coverage active="false"/></external>'
                '<options>'
                '<uriType value="semantic"/>'
                '<testDeterminationStrategy sameProgram="true" assignedTests="false" allTestClasses="false"/>'
                '<testRiskLevels harmless="true" dangerous="true" critical="true"/>'
                '<testDurations short="true" medium="true" long="true"/>'
                '</options>'
                '<adtcore:objectSets xmlns:adtcore="http://www.sap.com/adt/core">'
                '<objectSet kind="inclusive">'
                '<adtcore:objectReferences>'
                f'<adtcore:objectReference adtcore:uri="{object_url}"/>'
                '</adtcore:objectReferences>'
                '</objectSet>'
                '</adtcore:objectSets>'
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
            return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    # ──────────────────────────────────────────────
    # Transport operations
    # ──────────────────────────────────────────────

    def create_transport(self, description: str, request_type: str = "K", target: str = "") -> dict:
        """Create a transport request (Workbench or Customizing)."""
        cts_project = os.environ.get("SAP_CTS_PROJECT", "")
        transport_layer = os.environ.get("SAP_TRANSPORT_LAYER", "")
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            ref_uri = "/sap/bc/adt/cts/transports"
            check_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
                '<asx:values><DATA>'
                '<DEVCLASS/>'
                '<OPERATION>I</OPERATION>'
                f'<URI>{ref_uri}</URI>'
                '</DATA></asx:values></asx:abap>'
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
            if check_resp.status_code == 200 and "<DEVCLASS>" in check_resp.text:
                start = check_resp.text.index("<DEVCLASS>") + len("<DEVCLASS>")
                end = check_resp.text.index("</DEVCLASS>")
                devclass = check_resp.text[start:end].strip()

            # Build CTS_PROJECT element only if configured
            cts_project_xml = f'<CTS_PROJECT>{cts_project}</CTS_PROJECT>' if cts_project else ''
            create_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
                '<asx:values><DATA>'
                f'<DEVCLASS>{devclass}</DEVCLASS>'
                f'<REQUEST_TEXT>{description}</REQUEST_TEXT>'
                f'<REF>{ref_uri}</REF>'
                '<OPERATION>I</OPERATION>'
                f'{cts_project_xml}'
                '</DATA></asx:values></asx:abap>'
            )
            params = {}
            if transport_layer:
                params["transportLayer"] = transport_layer

            resp = self.session.post(
                self._url("/sap/bc/adt/cts/transports"),
                data=create_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Accept": "text/plain",
                    "Content-Type": "application/vnd.sap.as+xml; charset=UTF-8; dataname=com.sap.adt.CreateCorrectionRequest",
                },
                params=params if params else None,
                timeout=30,
            )
            if resp.status_code in (200, 201):
                transport_number = resp.text.strip().split("/")[-1] if resp.text else ""
                return {"ok": True, "transport": transport_number, "description": description,
                        "devclass": devclass, "type": "Workbench" if request_type == "K" else "Customizing"}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def list_transports(self, user: str = "") -> dict:
        """List modifiable transport requests."""
        try:
            url = self._url("/sap/bc/adt/cts/transportrequests")
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}

            transports = []
            try:
                root = ET.fromstring(resp.text)
                TM = "http://www.sap.com/cts/adt/tm"
                for req in root.iter():
                    tag = req.tag.split("}")[-1] if "}" in req.tag else req.tag
                    if tag == "request":
                        number = req.get(f"{{{TM}}}number", "")
                        owner = req.get(f"{{{TM}}}owner", "")
                        desc = req.get(f"{{{TM}}}desc", "")
                        status = req.get(f"{{{TM}}}status", "")
                        target_sys = req.get(f"{{{TM}}}target", "")
                        if user and owner.upper() != user.upper():
                            continue
                        transports.append({"number": number, "owner": owner,
                                           "description": desc, "status": status, "target": target_sys})
            except ET.ParseError:
                return {"ok": False, "message": "Error parsing transport XML"}
            return {"ok": True, "count": len(transports), "transports": transports}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_transport_details(self, transport_number: str) -> dict:
        """Get details and objects of a specific transport request."""
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
                for req in root.iter():
                    tag = req.tag.split("}")[-1] if "}" in req.tag else req.tag
                    if tag == "request":
                        number = req.get(f"{{{TM}}}number", "")
                        if number != transport_number:
                            continue
                        owner = req.get(f"{{{TM}}}owner", "")
                        desc = req.get(f"{{{TM}}}desc", "")
                        status = req.get(f"{{{TM}}}status", "")
                        target_sys = req.get(f"{{{TM}}}target", "")
                        tasks = []
                        for child in req.iter():
                            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                            if child_tag == "task":
                                task_number = child.get(f"{{{TM}}}number", "")
                                task_owner = child.get(f"{{{TM}}}owner", "")
                                task_desc = child.get(f"{{{TM}}}desc", "")
                                task_status = child.get(f"{{{TM}}}status", "")
                                objects = []
                                for obj in child.iter():
                                    obj_tag = obj.tag.split("}")[-1] if "}" in obj.tag else obj.tag
                                    if obj_tag in ("abap_object", "abapObject", "objectReference", "object"):
                                        obj_name = obj.get(f"{{{TM}}}name") or obj.get(f"{{{ADTCORE}}}name") or obj.get("name") or ""
                                        obj_type = obj.get(f"{{{TM}}}type") or obj.get(f"{{{ADTCORE}}}type") or obj.get("type") or ""
                                        obj_pgmid = obj.get(f"{{{TM}}}pgmid", obj.get("pgmid", ""))
                                        obj_lock = obj.get(f"{{{TM}}}lockflag", obj.get("lockflag", ""))
                                        obj_desc = obj.get(f"{{{TM}}}obj_info") or obj.get(f"{{{TM}}}desc") or obj.get(f"{{{ADTCORE}}}description") or ""
                                        obj_wbtype = obj.get(f"{{{TM}}}wbtype", obj.get("wbtype", ""))
                                        if obj_name:
                                            objects.append({"name": obj_name, "type": obj_type, "wbtype": obj_wbtype,
                                                           "pgmid": obj_pgmid, "locked": obj_lock, "description": obj_desc})
                                tasks.append({"number": task_number, "owner": task_owner,
                                              "description": task_desc, "status": task_status, "objects": objects})
                        return {"ok": True, "transport": transport_number, "owner": owner,
                                "description": desc, "status": status, "target": target_sys, "tasks": tasks}
                return {"ok": False, "message": f"Transport {transport_number} not found in visible transport list"}
            except ET.ParseError as e:
                return {"ok": False, "message": f"Error parsing XML: {str(e)}"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def get_transport_xml_raw(self, transport_number: str) -> dict:
        """Return raw XML fragment for a transport (diagnostic)."""
        transport_number = transport_number.upper()
        try:
            url = self._url("/sap/bc/adt/cts/transportrequests")
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}
            xml_text = resp.text
            start_marker = f'tm:number="{transport_number}"'
            idx = xml_text.find(start_marker)
            if idx == -1:
                return {"ok": False, "message": f"Transport {transport_number} not found in XML"}
            fragment = xml_text[max(0, idx - 50): idx + 3000]
            return {"ok": True, "transport": transport_number, "xml_fragment": fragment, "total_xml_size": len(xml_text)}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def release_transport(self, transport_number: str) -> dict:
        """Release a transport request or task."""
        transport_number = transport_number.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            url = self._url(f"/sap/bc/adt/cts/transportrequests/{transport_number}/newreleasejobs")
            resp = self.session.post(
                url,
                headers={"X-CSRF-Token": csrf_token, "Accept": "application/xml"},
                timeout=60,
            )
            if resp.status_code not in (200, 201, 202):
                return {"ok": False, "status": resp.status_code, "message": resp.text[:500], "transport": transport_number}

            time.sleep(2)
            details = self.get_transport_details(transport_number)
            if details.get("ok"):
                status = details.get("status", "")
                released = status.upper() in ("R", "L", "RELEASED")
                return {"ok": True, "transport": transport_number, "released": released, "status": status,
                        "warning": "" if released else "ADT returned 200 but transport is still modifiable."}
            return {"ok": True, "transport": transport_number, "released": True, "note": "Released but could not verify status"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def add_to_transport(self, object_uri: str, transport_number: str) -> dict:
        """Register an ABAP object in a transport request."""
        if not object_uri or not transport_number:
            return {"ok": False, "message": "object_uri and transport_number are required"}
        transport_number = transport_number.upper()
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            check_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
                '<asx:values><DATA>'
                '<DEVCLASS/>'
                '<OPERATION>I</OPERATION>'
                f'<URI>{object_uri}</URI>'
                '</DATA></asx:values></asx:abap>'
            )
            resp = self.session.post(
                self._url("/sap/bc/adt/cts/transportchecks"),
                data=check_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Accept": "application/vnd.sap.as+xml;charset=UTF-8;dataname=com.sap.adt.transport.service.checkData",
                    "Content-Type": "application/vnd.sap.as+xml; charset=UTF-8; dataname=com.sap.adt.transport.service.checkData",
                },
                params={"corrNr": transport_number},
                timeout=30,
            )
            if resp.status_code in (200, 201):
                return {"ok": True, "object_uri": object_uri, "transport": transport_number, "added": True}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def create_transport_task(self, parent_transport: str, description: str, owner: str = "") -> dict:
        """Create a task under an existing transport request."""
        parent_transport = parent_transport.upper()
        if not parent_transport or not description:
            return {"ok": False, "message": "parent_transport and description are required"}
        try:
            csrf_token = self._fetch_csrf_token()
            if not csrf_token:
                return {"ok": False, "message": "Failed to obtain CSRF token"}

            task_owner = owner.upper() if owner else self.username.upper()
            create_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
                '<asx:values><DATA>'
                f'<PARENT>{parent_transport}</PARENT>'
                f'<REQUEST_TEXT>{description}</REQUEST_TEXT>'
                f'<OWNER>{task_owner}</OWNER>'
                '<TYPE>Q</TYPE>'
                '</DATA></asx:values></asx:abap>'
            )
            resp = self.session.post(
                self._url("/sap/bc/adt/cts/transports"),
                data=create_xml.encode("utf-8"),
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Accept": "text/plain",
                    "Content-Type": "application/vnd.sap.as+xml; charset=UTF-8; dataname=com.sap.adt.CreateCorrectionRequest",
                },
                timeout=30,
            )
            if resp.status_code in (200, 201):
                task_number = resp.text.strip().split("/")[-1] if resp.text else ""
                return {"ok": True, "task_number": task_number, "parent_transport": parent_transport,
                        "owner": task_owner, "description": description}
            return {"ok": False, "status": resp.status_code, "message": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "message": str(e)}
