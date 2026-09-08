"""
ServiceNow REST client — Table API + Attachment API.
Basic auth. Read and write operations.
Used by servicenow_server.py (MCP server).
"""

import io
import re
import zipfile
from xml.etree import ElementTree as ET

import requests
from requests.auth import HTTPBasicAuth


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class ServiceNowClient:
    def __init__(self, instance: str, username: str, password: str, timeout: int = 30):
        self.instance = (instance or "").rstrip("/")
        self.auth = HTTPBasicAuth(username, password)
        self.timeout = timeout
        self.session = requests.Session()
        self._json_headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # ── low-level ────────────────────────────────────────────
    def _get(self, path, params=None, stream=False):
        url = f"{self.instance}{path}"
        return self.session.get(url, auth=self.auth, params=params,
                                headers={"Accept": "application/json"},
                                timeout=self.timeout, stream=stream)

    def _post(self, path, body):
        url = f"{self.instance}{path}"
        return self.session.post(url, auth=self.auth, json=body,
                                 headers=self._json_headers, timeout=self.timeout)

    def _patch(self, path, body):
        url = f"{self.instance}{path}"
        return self.session.patch(url, auth=self.auth, json=body,
                                  headers=self._json_headers, timeout=self.timeout)

    @staticmethod
    def _err(resp):
        try:
            j = resp.json()
            msg = j.get("error", {}).get("message") or j.get("error", {}).get("detail") or resp.text
        except Exception:
            msg = resp.text
        return {"ok": False, "status": resp.status_code, "message": msg}

    # ── connectivity ─────────────────────────────────────────
    def ping(self):
        try:
            r = self._get("/api/now/table/sys_user", params={"sysparm_limit": 1,
                                                              "sysparm_fields": "sys_id"})
            if r.status_code == 200:
                return {"ok": True, "instance": self.instance, "message": "Connection OK"}
            return self._err(r)
        except requests.RequestException as e:
            return {"ok": False, "message": f"Connection failed: {e}"}

    # ── generic query (read) ─────────────────────────────────
    def query(self, table, query="", fields="", limit=100, offset=0, display_value="false"):
        params = {"sysparm_limit": limit, "sysparm_offset": offset,
                  "sysparm_display_value": display_value,
                  "sysparm_exclude_reference_link": "true"}
        if query:
            params["sysparm_query"] = query
        if fields:
            params["sysparm_fields"] = fields
        try:
            r = self._get(f"/api/now/table/{table}", params=params)
            if r.status_code != 200:
                return self._err(r)
            records = r.json().get("result", [])
            return {"ok": True, "table": table, "count": len(records), "records": records}
        except requests.RequestException as e:
            return {"ok": False, "message": f"Query failed: {e}"}

    def get_record(self, table, number, fields="", display_value="all"):
        res = self.query(table, query=f"number={number}", fields=fields,
                         limit=1, display_value=display_value)
        if not res.get("ok"):
            return res
        if not res["records"]:
            return {"ok": False, "message": f"{number} not found in {table}"}
        return {"ok": True, "table": table, "record": res["records"][0]}

    def _resolve_sys_id(self, table, number):
        res = self.query(table, query=f"number={number}", fields="sys_id", limit=1)
        if not res.get("ok") or not res["records"]:
            return None
        return res["records"][0].get("sys_id")

    def find_user(self, name_or_username, limit=20):
        q = (f"nameLIKE{name_or_username}^ORuser_name={name_or_username}"
             f"^ORemail={name_or_username}")
        return self.query("sys_user", query=q,
                          fields="sys_id,user_name,name,email,active",
                          limit=limit)

    # ── write ────────────────────────────────────────────────
    def create_record(self, table, fields: dict):
        try:
            r = self._post(f"/api/now/table/{table}", fields)
            if r.status_code in (200, 201):
                rec = r.json().get("result", {})
                return {"ok": True, "table": table,
                        "number": rec.get("number"),
                        "sys_id": rec.get("sys_id"), "record": rec}
            return self._err(r)
        except requests.RequestException as e:
            return {"ok": False, "message": f"Create failed: {e}"}

    def update_record(self, table, sys_id, fields: dict):
        try:
            r = self._patch(f"/api/now/table/{table}/{sys_id}", fields)
            if r.status_code == 200:
                rec = r.json().get("result", {})
                return {"ok": True, "table": table,
                        "number": rec.get("number"),
                        "sys_id": rec.get("sys_id"), "record": rec}
            return self._err(r)
        except requests.RequestException as e:
            return {"ok": False, "message": f"Update failed: {e}"}

    def update_record_by_number(self, table, number, fields: dict):
        sys_id = self._resolve_sys_id(table, number)
        if not sys_id:
            return {"ok": False, "message": f"{number} not found in {table}"}
        return self.update_record(table, sys_id, fields)

    def add_work_note(self, table, number, note, note_field="work_notes"):
        return self.update_record_by_number(table, number, {note_field: note})

    # ── attachments ──────────────────────────────────────────
    def list_attachments(self, table, number):
        sys_id = self._resolve_sys_id(table, number)
        if not sys_id:
            return {"ok": False, "message": f"{number} not found in {table}"}
        params = {"sysparm_query": f"table_name={table}^table_sys_id={sys_id}",
                  "sysparm_fields": "sys_id,file_name,content_type,size_bytes,"
                                    "sys_created_on,sys_created_by"}
        try:
            r = self._get("/api/now/attachment", params=params)
            if r.status_code != 200:
                return self._err(r)
            atts = r.json().get("result", [])
            return {"ok": True, "record": number, "count": len(atts), "attachments": atts}
        except requests.RequestException as e:
            return {"ok": False, "message": f"List attachments failed: {e}"}

    def _download_attachment_bytes(self, attachment_sys_id):
        r = self._get(f"/api/now/attachment/{attachment_sys_id}/file", stream=True)
        r.raise_for_status()
        return r.content

    def extract_docx_text(self, table, number, attachment_sys_id=None):
        """Downloads a .docx attachment and extracts its text (stdlib only)."""
        listing = self.list_attachments(table, number)
        if not listing.get("ok"):
            return listing
        atts = listing["attachments"]
        target = None
        if attachment_sys_id:
            target = next((a for a in atts if a["sys_id"] == attachment_sys_id), None)
        else:
            target = next((a for a in atts
                           if a["file_name"].lower().endswith(".docx")), None)
        if not target:
            return {"ok": False, "message": "No matching .docx attachment found"}
        try:
            data = self._download_attachment_bytes(target["sys_id"])
        except requests.RequestException as e:
            return {"ok": False, "message": f"Download failed: {e}"}
        text = self._docx_to_text(data)
        return {"ok": True, "file_name": target["file_name"], "text": text}

    @staticmethod
    def _docx_to_text(data: bytes) -> str:
        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            return "[Not a valid .docx / corrupt file]"
        parts = []
        targets = [n for n in zf.namelist()
                   if n == "word/document.xml"
                   or re.match(r"word/(header|footer)\d*\.xml$", n)]
        for name in targets:
            try:
                root = ET.fromstring(zf.read(name))
            except (KeyError, ET.ParseError):
                continue
            for para in root.iter(f"{{{W_NS}}}p"):
                buf = []
                for node in para.iter():
                    tag = node.tag.split("}")[-1]
                    if tag == "t" and node.text:
                        buf.append(node.text)
                    elif tag == "tab":
                        buf.append("\t")
                    elif tag == "br":
                        buf.append("\n")
                line = "".join(buf).strip()
                if line:
                    parts.append(line)
        return "\n".join(parts) if parts else "[No extractable text]"
