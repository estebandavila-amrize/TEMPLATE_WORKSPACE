"""
ServiceNow MCP Server — data-driven, mirrors server.py conventions.
Tools defined as a list of dicts. Single list_tools/call_tool dispatch.
Transport: stdio (required by Kiro).

Read tools are always safe. Write tools (create/update/advance/work note)
should only be auto-approved in non-production environments.
"""

import os
import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from servicenow_client import ServiceNowClient

# ──────────────────────────────────────────────
# ServiceNow connection config from environment
# ──────────────────────────────────────────────
SNOW_INSTANCE = os.environ.get("SNOW_INSTANCE", "")
SNOW_USER = os.environ.get("SNOW_USER", "")
SNOW_PASSWORD = os.environ.get("SNOW_PASSWORD", "")
SNOW_ENV = os.environ.get("SNOW_ENV", "QUAL")

snow = ServiceNowClient(
    instance=SNOW_INSTANCE, username=SNOW_USER, password=SNOW_PASSWORD,
)

server = Server(f"servicenow-{SNOW_ENV.lower()}-mcp")
ENV = f"ServiceNow {SNOW_ENV}"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _parse_fields(raw):
    """Accept a dict or a JSON string, return (fields_dict, error_dict_or_None)."""
    if isinstance(raw, dict):
        return raw, None
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            return None, {"ok": False, "message": f"invalid fields JSON: {e}"}
        if not isinstance(parsed, dict):
            return None, {"ok": False, "message": "fields must be a JSON object"}
        return parsed, None
    return None, {"ok": False, "message": "fields is required"}


# ──────────────────────────────────────────────
# Tool handlers
# ──────────────────────────────────────────────

def _h_ping(args):
    return snow.ping()

def _h_query(args):
    table = args.get("table", "")
    if not table:
        return {"ok": False, "message": "table is required"}
    return snow.query(
        table,
        query=args.get("query", ""),
        fields=args.get("fields", ""),
        limit=args.get("limit", 100),
        offset=args.get("offset", 0),
        display_value=args.get("display_value", "false"),
    )

def _h_get_record(args):
    number = args.get("number", "")
    if not number:
        return {"ok": False, "message": "number is required"}
    return snow.get_record(
        number,
        table=args.get("table", ""),
        fields=args.get("fields", ""),
        display_value=args.get("display_value", "all"),
    )

def _h_find_user(args):
    term = args.get("term", "")
    if not term:
        return {"ok": False, "message": "term is required"}
    return snow.find_user(term, fields=args.get("fields", "sys_id,user_name,name,email"))

def _h_list_attachments(args):
    return snow.list_attachments(
        number=args.get("number", ""),
        table=args.get("table", ""),
        sys_id=args.get("sys_id", ""),
    )

def _h_extract_docx(args):
    return snow.extract_docx(
        number=args.get("number", ""),
        table=args.get("table", ""),
        attachment_sys_id=args.get("attachment_sys_id", ""),
    )

def _h_create_record(args):
    table = args.get("table", "")
    if not table:
        return {"ok": False, "message": "table is required"}
    fields, err = _parse_fields(args.get("fields"))
    if err:
        return err
    return snow.create_record(table, fields)

def _h_update_record(args):
    number = args.get("number", "")
    if not number:
        return {"ok": False, "message": "number is required"}
    fields, err = _parse_fields(args.get("fields"))
    if err:
        return err
    return snow.update_record(number, fields, table=args.get("table", ""))

def _h_advance_state(args):
    number = args.get("number", "")
    state = args.get("state", "")
    if not number or not state:
        return {"ok": False, "message": "number and state are required"}
    return snow.advance_state(number, state, table=args.get("table", "change_request"))

def _h_add_work_note(args):
    number = args.get("number", "")
    note = args.get("note", "")
    if not number or not note:
        return {"ok": False, "message": "number and note are required"}
    return snow.add_work_note(number, note, table=args.get("table", ""),
                              field=args.get("field", "work_notes"))


# ──────────────────────────────────────────────
# Data-driven tool registry
# ──────────────────────────────────────────────

TOOLS = [
    {
        "name": "snow_ping",
        "description": f"Verifies connectivity and credentials with {ENV}. Use it to confirm the MCP server can reach ServiceNow.",
        "schema": {"type": "object", "properties": {}, "required": []},
        "handler": _h_ping,
    },
    {
        "name": "snow_query",
        "description": f"Queries any table in {ENV} using an encoded query. Read only. E.g. table=incident, query=active=true^priority<=2.",
        "schema": {"type": "object", "properties": {
            "table": {"type": "string", "description": "Table name. E.g.: incident, change_request, sc_req_item, problem, sys_user"},
            "query": {"type": "string", "description": "Encoded query. E.g.: active=true^priority<=2"},
            "fields": {"type": "string", "description": "Comma-separated fields to return. E.g.: number,short_description,state"},
            "limit": {"type": "integer", "description": "Max records (default 100)"},
            "offset": {"type": "integer", "description": "Paging offset (default 0)"},
            "display_value": {"type": "string", "description": "false (raw), true (labels), or all (both). Default false"},
        }, "required": ["table"]},
        "handler": _h_query,
    },
    {
        "name": "snow_get_record",
        "description": f"Gets a single record by its number in {ENV}. Table is inferred from the prefix (INC/CHG/RITM/REQ/PRB) unless given.",
        "schema": {"type": "object", "properties": {
            "number": {"type": "string", "description": "Record number. E.g.: INC08340528, CHG0435576"},
            "table": {"type": "string", "description": "Table (optional; inferred from number prefix)"},
            "fields": {"type": "string", "description": "Comma-separated fields (optional; default all)"},
            "display_value": {"type": "string", "description": "false / true / all. Default all"},
        }, "required": ["number"]},
        "handler": _h_get_record,
    },
    {
        "name": "snow_find_user",
        "description": f"Searches sys_user in {ENV} by name, username, or email. Returns matching users with their sys_id.",
        "schema": {"type": "object", "properties": {
            "term": {"type": "string", "description": "Search term matched against name/user_name/email"},
            "fields": {"type": "string", "description": "Fields to return (default sys_id,user_name,name,email)"},
        }, "required": ["term"]},
        "handler": _h_find_user,
    },
    {
        "name": "snow_list_attachments",
        "description": f"Lists attachments of a record in {ENV}. Provide a number (+optional table) or a record sys_id.",
        "schema": {"type": "object", "properties": {
            "number": {"type": "string", "description": "Record number. E.g.: INC08340528"},
            "table": {"type": "string", "description": "Table (optional; inferred from number prefix)"},
            "sys_id": {"type": "string", "description": "Record sys_id (alternative to number)"},
        }, "required": []},
        "handler": _h_list_attachments,
    },
    {
        "name": "snow_extract_docx",
        "description": f"Downloads and extracts the plain text of a .docx attachment in {ENV}. Give a record number, or an attachment_sys_id directly.",
        "schema": {"type": "object", "properties": {
            "number": {"type": "string", "description": "Record number whose first .docx will be extracted"},
            "table": {"type": "string", "description": "Table (optional; inferred from number prefix)"},
            "attachment_sys_id": {"type": "string", "description": "Attachment sys_id (bypasses lookup by number)"},
        }, "required": []},
        "handler": _h_extract_docx,
    },
    {
        "name": "snow_create_record",
        "description": f"Creates a record in {ENV} (e.g. change_request). WRITE operation. `fields` is a JSON object of field/value pairs.",
        "schema": {"type": "object", "properties": {
            "table": {"type": "string", "description": "Table to insert into. E.g.: change_request"},
            "fields": {"type": "string", "description": "JSON object of field/value pairs. E.g.: {\"short_description\":\"...\",\"type\":\"Normal Minor\"}"},
        }, "required": ["table", "fields"]},
        "handler": _h_create_record,
    },
    {
        "name": "snow_update_record",
        "description": f"Updates fields on an existing record in {ENV}, identified by its number. WRITE operation. `fields` is a JSON object.",
        "schema": {"type": "object", "properties": {
            "number": {"type": "string", "description": "Record number. E.g.: CHG0435576"},
            "table": {"type": "string", "description": "Table (optional; inferred from number prefix)"},
            "fields": {"type": "string", "description": "JSON object of field/value pairs to update"},
        }, "required": ["number", "fields"]},
        "handler": _h_update_record,
    },
    {
        "name": "snow_advance_state",
        "description": f"Advances the state of a change (or other record) in {ENV}. WRITE operation. State models may be governed by business rules/CAB.",
        "schema": {"type": "object", "properties": {
            "number": {"type": "string", "description": "Record number. E.g.: CHG0435576"},
            "state": {"type": "string", "description": "Target state code. E.g.: -2, 0, 3"},
            "table": {"type": "string", "description": "Table (default change_request)"},
        }, "required": ["number", "state"]},
        "handler": _h_advance_state,
    },
    {
        "name": "snow_add_work_note",
        "description": f"Adds a work note (or comment) to a record in {ENV}. WRITE operation.",
        "schema": {"type": "object", "properties": {
            "number": {"type": "string", "description": "Record number. E.g.: INC08340528"},
            "note": {"type": "string", "description": "Text of the work note / comment"},
            "table": {"type": "string", "description": "Table (optional; inferred from number prefix)"},
            "field": {"type": "string", "description": "Journal field: work_notes (default) or comments"},
        }, "required": ["number", "note"]},
        "handler": _h_add_work_note,
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
    # Surface which environment answered, mirroring the SNOW_ENV convention.
    if isinstance(data, dict):
        data.setdefault("env", SNOW_ENV)
    return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
