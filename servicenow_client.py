"""
ServiceNow REST Client — SOLID rewrite, mirrors sap_client.py conventions.

Wraps the ServiceNow Table API and Attachment API using HTTP basic auth.
All public methods return a dict with an "ok" key.

Read : query, get_record, find_user, list_attachments, extract_docx
Write: create_record, update_record, advance_state, add_work_note

.docx text extraction uses only the Python standard library (zipfile + xml),
so no external dependencies beyond `requests` are required.
"""

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

# Use the operating system's trust store (Windows cert store) so corporate
# TLS-inspection CAs are trusted without disabling certificate verification.
# Falls back silently if truststore is not installed (keeps default behavior).
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass


# Maps a ServiceNow record number prefix to its table.
_NUMBER_PREFIX_TABLE = {
    "INC": "incident",
    "CHG": "change_request",
    "RITM": "sc_req_item",
    "REQ": "sc_request",
    "PRB": "problem",
    "TASK": "task",
    "CTASK": "change_task",
    "SCTASK": "sc_task",
}


class ServiceNowClient:
    """HTTP client for the ServiceNow Table API and Attachment API."""

    def __init__(self, instance: str, username: str, password: str, timeout: int = 30):
        # Normalize: strip trailing slash so path concatenation is clean.
        self.base_url = (instance or "").rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    # ──────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _table_for_number(self, number: str) -> Optional[str]:
        """Infer the table from a record number prefix (INC..., CHG..., etc.)."""
        m = re.match(r"^([A-Za-z]+)", (number or "").strip())
        if not m:
            return None
        return _NUMBER_PREFIX_TABLE.get(m.group(1).upper())

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """Generic GET returning {"ok": True, "data": <json>} or an error dict."""
        try:
            resp = self.session.get(self._url(path), params=params, timeout=self.timeout)
        except Exception as e:
            return {"ok": False, "message": str(e)}
        return self._parse_json(resp)

    def _parse_json(self, resp: requests.Response) -> dict:
        if resp.status_code in (200, 201):
            try:
                return {"ok": True, "data": resp.json()}
            except ValueError:
                return {"ok": True, "data": resp.text}
        return {
            "ok": False,
            "status": resp.status_code,
            "message": resp.text[:500],
        }

    # ──────────────────────────────────────────────
    # Read operations
    # ──────────────────────────────────────────────

    def ping(self) -> dict:
        """Cheap authenticated call to confirm connectivity and credentials."""
        res = self._get(
            "/api/now/table/sys_user",
            params={"sysparm_limit": 1, "sysparm_fields": "sys_id"},
        )
        if res.get("ok"):
            return {"ok": True, "message": "ServiceNow connection OK", "instance": self.base_url}
        return res

    def query(self, table: str, query: str = "", fields: str = "",
              limit: int = 100, offset: int = 0, display_value: str = "false") -> dict:
        """Query any table with an encoded query. Read only."""
        if not table:
            return {"ok": False, "message": "table is required"}
        params = {
            "sysparm_query": query,
            "sysparm_limit": limit,
            "sysparm_offset": offset,
            "sysparm_display_value": display_value,
        }
        if fields:
            params["sysparm_fields"] = fields
        res = self._get(f"/api/now/table/{table}", params=params)
        if not res.get("ok"):
            return res
        records = res["data"].get("result", []) if isinstance(res["data"], dict) else []
        return {"ok": True, "count": len(records), "records": records}

    def get_record(self, number: str, table: str = "", fields: str = "",
                   display_value: str = "all") -> dict:
        """Fetch a single record by its human number (INC.../CHG...)."""
        if not number:
            return {"ok": False, "message": "number is required"}
        table = table or self._table_for_number(number)
        if not table:
            return {"ok": False, "message": f"Could not infer table from number '{number}'. Pass table explicitly."}
        res = self.query(table, query=f"number={number}", fields=fields,
                         limit=1, display_value=display_value)
        if not res.get("ok"):
            return res
        if not res["records"]:
            return {"ok": False, "message": f"No record found for {number} in {table}"}
        return {"ok": True, "table": table, "record": res["records"][0]}

    def find_user(self, term: str, fields: str = "sys_id,user_name,name,email") -> dict:
        """Search sys_user by name, username, or email. Returns matching users."""
        if not term:
            return {"ok": False, "message": "term is required"}
        q = f"nameLIKE{term}^ORuser_nameLIKE{term}^ORemailLIKE{term}"
        return self.query("sys_user", query=q, fields=fields, limit=25)

    def list_attachments(self, number: str = "", table: str = "", sys_id: str = "") -> dict:
        """List attachments for a record (by number, or by table + sys_id)."""
        if not sys_id:
            if not number:
                return {"ok": False, "message": "Provide either sys_id, or number (+optional table)"}
            table = table or self._table_for_number(number)
            if not table:
                return {"ok": False, "message": f"Could not infer table from number '{number}'."}
            rec = self.query(table, query=f"number={number}", fields="sys_id", limit=1)
            if not rec.get("ok"):
                return rec
            if not rec["records"]:
                return {"ok": False, "message": f"No record found for {number}"}
            sys_id = rec["records"][0].get("sys_id")
        params = {
            "sysparm_query": f"table_sys_id={sys_id}",
            "sysparm_fields": "sys_id,file_name,content_type,size_bytes,table_name",
        }
        res = self._get("/api/now/attachment", params=params)
        if not res.get("ok"):
            return res
        atts = res["data"].get("result", []) if isinstance(res["data"], dict) else []
        return {"ok": True, "count": len(atts), "attachments": atts}

    def download_attachment(self, attachment_sys_id: str) -> dict:
        """Download the raw binary of an attachment. Returns bytes in 'content'."""
        if not attachment_sys_id:
            return {"ok": False, "message": "attachment_sys_id is required"}
        try:
            resp = self.session.get(
                self._url(f"/api/now/attachment/{attachment_sys_id}/file"),
                timeout=self.timeout,
            )
        except Exception as e:
            return {"ok": False, "message": str(e)}
        if resp.status_code == 200:
            return {"ok": True, "content": resp.content}
        return {"ok": False, "status": resp.status_code, "message": resp.text[:300]}

    def extract_docx(self, number: str = "", table: str = "",
                     attachment_sys_id: str = "") -> dict:
        """Download a .docx attachment and extract its plain text (stdlib only)."""
        target = attachment_sys_id
        file_name = None
        if not target:
            listed = self.list_attachments(number=number, table=table)
            if not listed.get("ok"):
                return listed
            docx = next(
                (a for a in listed["attachments"]
                 if (a.get("file_name") or "").lower().endswith(".docx")),
                None,
            )
            if not docx:
                return {"ok": False, "message": "No .docx attachment found on that record"}
            target = docx.get("sys_id")
            file_name = docx.get("file_name")
        dl = self.download_attachment(target)
        if not dl.get("ok"):
            return dl
        try:
            text = self._docx_bytes_to_text(dl["content"])
        except Exception as e:
            return {"ok": False, "message": f"Failed to parse .docx: {e}"}
        return {"ok": True, "file_name": file_name, "attachment_sys_id": target, "text": text}

    @staticmethod
    def _docx_bytes_to_text(data: bytes) -> str:
        """Extract paragraph text from a .docx (Open XML) using zipfile + xml only."""
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            xml_bytes = zf.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        paragraphs = []
        for para in root.iter(f"{ns}p"):
            texts = [node.text for node in para.iter(f"{ns}t") if node.text]
            paragraphs.append("".join(texts))
        return "\n".join(paragraphs).strip()

    # ──────────────────────────────────────────────
    # Write operations
    # ──────────────────────────────────────────────

    def create_record(self, table: str, fields: dict) -> dict:
        """Create a record in a table. `fields` is the field/value payload."""
        if not table:
            return {"ok": False, "message": "table is required"}
        if not isinstance(fields, dict) or not fields:
            return {"ok": False, "message": "fields must be a non-empty object"}
        try:
            resp = self.session.post(
                self._url(f"/api/now/table/{table}"),
                json=fields,
                timeout=self.timeout,
            )
        except Exception as e:
            return {"ok": False, "message": str(e)}
        res = self._parse_json(resp)
        if res.get("ok") and isinstance(res["data"], dict):
            return {"ok": True, "record": res["data"].get("result", {})}
        return res

    def _resolve_sys_id(self, number: str, table: str) -> dict:
        table = table or self._table_for_number(number)
        if not table:
            return {"ok": False, "message": f"Could not infer table from number '{number}'."}
        rec = self.query(table, query=f"number={number}", fields="sys_id", limit=1)
        if not rec.get("ok"):
            return rec
        if not rec["records"]:
            return {"ok": False, "message": f"No record found for {number} in {table}"}
        return {"ok": True, "table": table, "sys_id": rec["records"][0].get("sys_id")}

    def update_record(self, number: str, fields: dict, table: str = "") -> dict:
        """Patch fields on an existing record identified by its number."""
        if not number:
            return {"ok": False, "message": "number is required"}
        if not isinstance(fields, dict) or not fields:
            return {"ok": False, "message": "fields must be a non-empty object"}
        resolved = self._resolve_sys_id(number, table)
        if not resolved.get("ok"):
            return resolved
        table = resolved["table"]
        sys_id = resolved["sys_id"]
        try:
            resp = self.session.patch(
                self._url(f"/api/now/table/{table}/{quote(sys_id)}"),
                json=fields,
                timeout=self.timeout,
            )
        except Exception as e:
            return {"ok": False, "message": str(e)}
        res = self._parse_json(resp)
        if res.get("ok") and isinstance(res["data"], dict):
            return {"ok": True, "record": res["data"].get("result", {})}
        return res

    def advance_state(self, number: str, state: str, table: str = "change_request") -> dict:
        """Advance a change (or any record) to a new state code."""
        if not state:
            return {"ok": False, "message": "state is required"}
        return self.update_record(number, {"state": state}, table=table)

    def add_work_note(self, number: str, note: str, table: str = "",
                      field: str = "work_notes") -> dict:
        """Append a work note (default) or comment to a record's journal field."""
        if not note:
            return {"ok": False, "message": "note is required"}
        return self.update_record(number, {field: note}, table=table)
