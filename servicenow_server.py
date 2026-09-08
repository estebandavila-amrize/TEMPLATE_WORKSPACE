"""
ServiceNow MCP Server — data-driven, mirrors the SAP server pattern.
Tools defined as a list of dicts. Single list_tools/call_tool dispatch.
Transport: stdio (required by Kiro).

Connection config from environment:
  SNOW_INSTANCE   e.g. https://oneservicena.service-now.com
  SNOW_USER       basic-auth username
  SNOW_PASSWORD   basic-auth password
  SNOW_ENV        label for messages (e.g. PRD, QUAL)
"""

import os
import json
import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from servicenow_client import ServiceNowClient

# ──────────────────────────────────────────────
# Connection config from environment
# ──────────────────────────────────────────────
SNOW_INSTANCE = os.environ.get("SNOW_INSTANCE", "")
SNOW_USER = os.environ.get("SNOW_USER", "")
SNOW_PASSWORD = os.environ.get("SNOW_PASSWORD", "")
SNOW_ENV = os.environ.get("SNOW_ENV", "PRD")

snow = ServiceNowClient(instance=SNOW_INSTANCE, username=SNOW_USER, password=SNOW_PASSWORD)

server = Server("servicenow-mcp")
SYS = f"ServiceNow {SNOW_ENV}"


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
    table = args.get("table", "")
    number = args.get("number", "")
    if not table or not number:
        return {"ok": False, "message": "table and number are required"}
    return snow.get_record(table, number, fields=args.get("fields", ""),
                           display_value=args.get("display_value", "all"))


def _h_find_user(args):
    name = args.get("name", "")
    if not name:
        return {"ok": False, "message": "name is required"}
    return snow.find_user(name, limit=args.get("limit", 20))


def _h_create_record(args):
    table = args.get("table", "")
    fields = args.get("fields", {})
    if not table or not isinstance(fields, dict) or not fields:
        return {"ok": False, "message": "table and a non-empty fields object are required"}
    return snow.create_record(table, fields)


def _h_update_record(args):
    table = args.get("table", "")
    number = args.get("number", "")
    fields = args.get("fields", {})
    if not table or not number or not isinstance(fields, dict) or not fields:
        return {"ok": False, "message": "table, number and a non-empty fields object are required"}
    return snow.update_record_by_number(table, number, fields)


def _h_advance_state(args):
    table = args.get("table", "change_request")
    number = args.get("number", "")
    state = args.get("state", "")
    if not number or state == "":
        return {"ok": False, "message": "number and state are required"}
    return snow.update_record_by_number(table, number, {"state": str(state)})


def _h_add_work_note(args):
    table = args.get("table", "")
    number = args.get("number", "")
    note = args.get("note", "")
    if not table or not number or not note:
        return {"ok": False, "message": "table, number and note are required"}
    return snow.add_work_note(table, number, note,
                              note_field=args.get("note_field", "work_notes"))


def _h_list_attachments(args):
    table = args.get("table", "")
    number = args.get("number", "")
    if not table or not number:
        return {"ok": False, "message": "table and number are required"}
    return snow.list_attachments(table, number)


def _h_extract_docx(args):
    table = args.get("table", "")
    number = args.get("number", "")
    if not table or not number:
        return {"ok": False, "message": "table and number are required"}
    return snow.extract_docx_text(table, number,
                                  attachment_sys_id=args.get("attachment_sys_id"))


# ──────────────────────────────────────────────
# Tool catalog (flat schemas — no top-level anyOf/oneOf)
# ──────────────────────────────────────────────
TOOLS = [
    {
        "name": "snow_ping",
        "description": f"Verifies connectivity with {SYS}. Use it to confirm the MCP server can reach ServiceNow.",
        "schema": {"type": "object", "properties": {}, "required": []},
        "handler": _h_ping,
    },
    {
        "name": "snow_query",
        "description": f"Queries any table in {SYS} (READ). Supports encoded queries, field selection, paging and display values. Tables: incident, change_request, sc_req_item, sc_request, problem, sys_user, sys_attachment, etc.",
        "schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name. E.g.: incident, change_request, sc_req_item"},
                "query": {"type": "string", "description": "Encoded query (sysparm_query). E.g.: active=true^priority<=2"},
                "fields": {"type": "string", "description": "Comma-separated fields to return. E.g.: number,short_description,state"},
                "limit": {"type": "integer", "description": "Max records (default 100)"},
                "offset": {"type": "integer", "description": "Starting offset (default 0)"},
                "display_value": {"type": "string", "description": "'true', 'false', or 'all' (value + label). Default 'false'."},
            },
            "required": ["table"],
        },
        "handler": _h_query,
    },
    {
        "name": "snow_get_record",
        "description": f"Gets a single full record by its number (INC..., CHG..., RITM..., PRB...) in {SYS}.",
        "schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name. E.g.: incident, change_request"},
                "number": {"type": "string", "description": "Record number. E.g.: INC08340528"},
                "fields": {"type": "string", "description": "Comma-separated fields (optional; default all)"},
                "display_value": {"type": "string", "description": "'true', 'false', or 'all'. Default 'all'."},
            },
            "required": ["table", "number"],
        },
        "handler": _h_get_record,
    },
    {
        "name": "snow_find_user",
        "description": f"Finds users in {SYS} by name, username or email. Returns sys_id (useful to filter incidents/changes by user).",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Full/partial name, user_name or email. E.g.: hernandez"},
                "limit": {"type": "integer", "description": "Max results (default 20)"},
            },
            "required": ["name"],
        },
        "handler": _h_find_user,
    },
    {
        "name": "snow_list_attachments",
        "description": f"Lists the attachments (metadata) of a record in {SYS}.",
        "schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name. E.g.: incident"},
                "number": {"type": "string", "description": "Record number. E.g.: INC08340528"},
            },
            "required": ["table", "number"],
        },
        "handler": _h_list_attachments,
    },
    {
        "name": "snow_extract_docx",
        "description": f"Downloads a .docx attachment of a record in {SYS} and extracts its text. If attachment_sys_id is omitted, uses the first .docx found.",
        "schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name. E.g.: incident"},
                "number": {"type": "string", "description": "Record number. E.g.: INC08340528"},
                "attachment_sys_id": {"type": "string", "description": "Optional sys_id of a specific attachment"},
            },
            "required": ["table", "number"],
        },
        "handler": _h_extract_docx,
    },
    {
        "name": "snow_create_record",
        "description": f"Creates a record in any table in {SYS} (WRITE). E.g. a change_request. Provide the fields object with the columns to set.",
        "schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name. E.g.: change_request, incident"},
                "fields": {"type": "object", "description": "Object of column:value. E.g.: {\"short_description\":\"...\",\"type\":\"Normal Minor\"}"},
            },
            "required": ["table", "fields"],
        },
        "handler": _h_create_record,
    },
    {
        "name": "snow_update_record",
        "description": f"Updates a record by its number in {SYS} (WRITE). Provide the fields object with the columns to change.",
        "schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name. E.g.: change_request"},
                "number": {"type": "string", "description": "Record number. E.g.: CHG0435576"},
                "fields": {"type": "object", "description": "Object of column:value to update."},
            },
            "required": ["table", "number", "fields"],
        },
        "handler": _h_update_record,
    },
    {
        "name": "snow_advance_state",
        "description": f"Advances the state of a change_request (or other task) in {SYS} by setting the state code. Note: state transitions may be governed by business rules / approval flows.",
        "schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name (default change_request)"},
                "number": {"type": "string", "description": "Record number. E.g.: CHG0435576"},
                "state": {"type": "string", "description": "Target state code. E.g.: 23 (Scheduled), 24 (Implementation), 27 (Closed)"},
            },
            "required": ["number", "state"],
        },
        "handler": _h_advance_state,
    },
    {
        "name": "snow_add_work_note",
        "description": f"Adds a work note (or comment) to a record in {SYS} (WRITE).",
        "schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name. E.g.: incident, change_request"},
                "number": {"type": "string", "description": "Record number. E.g.: INC08340528"},
                "note": {"type": "string", "description": "Text of the work note"},
                "note_field": {"type": "string", "description": "'work_notes' (internal) or 'comments' (customer visible). Default 'work_notes'."},
            },
            "required": ["table", "number", "note"],
        },
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
    return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
