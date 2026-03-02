#!/usr/bin/env python3
"""
Nextcloud Notes MCP Server

Exposes Nextcloud Notes as tools for Claude Code via the Model Context Protocol.
Configure with environment variables:
  NEXTCLOUD_URL       - Base URL of your Nextcloud instance (e.g. https://cloud.example.com)
  NEXTCLOUD_USERNAME  - Your Nextcloud username
  NEXTCLOUD_PASSWORD  - Your Nextcloud password or app password (recommended)
"""

import os
import sys
import json
import asyncio
import httpx
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NEXTCLOUD_URL = os.environ.get("NEXTCLOUD_URL", "").rstrip("/")
NEXTCLOUD_USERNAME = os.environ.get("NEXTCLOUD_USERNAME", "")
NEXTCLOUD_PASSWORD = os.environ.get("NEXTCLOUD_PASSWORD", "")

NOTES_API = f"{NEXTCLOUD_URL}/apps/notes/api/v1"


def _check_config() -> str | None:
    """Return an error string if required env vars are missing."""
    missing = [
        var
        for var, val in [
            ("NEXTCLOUD_URL", NEXTCLOUD_URL),
            ("NEXTCLOUD_USERNAME", NEXTCLOUD_USERNAME),
            ("NEXTCLOUD_PASSWORD", NEXTCLOUD_PASSWORD),
        ]
        if not val
    ]
    if missing:
        return f"Missing required environment variables: {', '.join(missing)}"
    return None


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        auth=(NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD),
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        timeout=30.0,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _note_summary(note: dict) -> dict:
    """Return a compact representation of a note."""
    return {
        "id": note.get("id"),
        "title": note.get("title", "(untitled)"),
        "category": note.get("category", ""),
        "favorite": note.get("favorite", False),
        "modified": note.get("modified"),
    }


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

app = Server("nextcloud-notes")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_notes",
            description="List all notes on the Nextcloud server. Optionally filter by category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Only return notes from this category. Omit to list all notes.",
                    },
                    "exclude_content": {
                        "type": "boolean",
                        "description": "If true, omit note body from results (faster for large note sets). Default false.",
                    },
                },
            },
        ),
        types.Tool(
            name="get_note",
            description="Retrieve the full content of a single note by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The numeric ID of the note.",
                    }
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="create_note",
            description="Create a new note on the Nextcloud server.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the note.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Body content of the note (Markdown supported).",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category / folder for the note. Omit for root.",
                    },
                    "favorite": {
                        "type": "boolean",
                        "description": "Mark the note as a favorite. Default false.",
                    },
                },
                "required": ["title", "content"],
            },
        ),
        types.Tool(
            name="update_note",
            description="Update an existing note. Only provided fields are changed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The numeric ID of the note to update.",
                    },
                    "title": {"type": "string", "description": "New title."},
                    "content": {"type": "string", "description": "New body content."},
                    "category": {"type": "string", "description": "New category."},
                    "favorite": {"type": "boolean", "description": "Update favorite status."},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="delete_note",
            description="Permanently delete a note by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The numeric ID of the note to delete.",
                    }
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="search_notes",
            description="Search notes by matching a query string against titles and content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search for in note titles and content.",
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether the search is case-sensitive. Default false.",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    config_error = _check_config()
    if config_error:
        return [types.TextContent(type="text", text=f"Configuration error: {config_error}")]

    try:
        result = await _dispatch(name, arguments)
        return [types.TextContent(type="text", text=result)]
    except httpx.HTTPStatusError as exc:
        return [types.TextContent(
            type="text",
            text=f"Nextcloud API error {exc.response.status_code}: {exc.response.text}",
        )]
    except httpx.RequestError as exc:
        return [types.TextContent(type="text", text=f"Network error: {exc}")]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Unexpected error: {exc}")]


async def _dispatch(name: str, args: dict[str, Any]) -> str:
    async with _client() as client:
        if name == "list_notes":
            return await _list_notes(client, args)
        if name == "get_note":
            return await _get_note(client, args)
        if name == "create_note":
            return await _create_note(client, args)
        if name == "update_note":
            return await _update_note(client, args)
        if name == "delete_note":
            return await _delete_note(client, args)
        if name == "search_notes":
            return await _search_notes(client, args)
        return f"Unknown tool: {name}"


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def _list_notes(client: httpx.AsyncClient, args: dict) -> str:
    params: dict[str, Any] = {}
    if "category" in args and args["category"]:
        params["category"] = args["category"]
    if args.get("exclude_content"):
        params["exclude"] = "content"

    resp = await client.get(f"{NOTES_API}/notes", params=params)
    resp.raise_for_status()
    notes = resp.json()

    if not notes:
        return "No notes found."

    summaries = [_note_summary(n) for n in notes]
    lines = [f"Found {len(summaries)} note(s):\n"]
    for s in summaries:
        fav = " ★" if s["favorite"] else ""
        cat = f" [{s['category']}]" if s["category"] else ""
        lines.append(f"  ID {s['id']}{fav}{cat}: {s['title']}")
    return "\n".join(lines)


async def _get_note(client: httpx.AsyncClient, args: dict) -> str:
    note_id = args["id"]
    resp = await client.get(f"{NOTES_API}/notes/{note_id}")
    resp.raise_for_status()
    note = resp.json()

    fav = " ★" if note.get("favorite") else ""
    cat = note.get("category", "")
    header = f"# {note.get('title', '(untitled)')}{fav}"
    if cat:
        header += f"\nCategory: {cat}"
    header += f"\nID: {note_id}  |  Modified: {note.get('modified')}\n"
    return f"{header}\n{note.get('content', '')}"


async def _create_note(client: httpx.AsyncClient, args: dict) -> str:
    payload = {
        "title": args["title"],
        "content": args["content"],
        "category": args.get("category", ""),
        "favorite": args.get("favorite", False),
    }
    resp = await client.post(f"{NOTES_API}/notes", json=payload)
    resp.raise_for_status()
    note = resp.json()
    return f"Note created successfully.\nID: {note['id']}\nTitle: {note['title']}"


async def _update_note(client: httpx.AsyncClient, args: dict) -> str:
    note_id = args["id"]

    # Fetch existing note first so we only send changed fields
    resp = await _retry_get(note_id)
    existing = resp

    payload: dict[str, Any] = {
        "title": args.get("title", existing.get("title", "")),
        "content": args.get("content", existing.get("content", "")),
        "category": args.get("category", existing.get("category", "")),
        "favorite": args.get("favorite", existing.get("favorite", False)),
    }

    async with _client() as client2:
        resp2 = await client2.put(f"{NOTES_API}/notes/{note_id}", json=payload)
        resp2.raise_for_status()
        note = resp2.json()

    return f"Note updated successfully.\nID: {note['id']}\nTitle: {note['title']}"


async def _retry_get(note_id: int) -> dict:
    async with _client() as c:
        r = await c.get(f"{NOTES_API}/notes/{note_id}")
        r.raise_for_status()
        return r.json()


async def _delete_note(client: httpx.AsyncClient, args: dict) -> str:
    note_id = args["id"]
    resp = await client.delete(f"{NOTES_API}/notes/{note_id}")
    resp.raise_for_status()
    return f"Note {note_id} deleted successfully."


async def _search_notes(client: httpx.AsyncClient, args: dict) -> str:
    query: str = args["query"]
    case_sensitive: bool = args.get("case_sensitive", False)

    resp = await client.get(f"{NOTES_API}/notes")
    resp.raise_for_status()
    notes = resp.json()

    def matches(note: dict) -> bool:
        haystack = f"{note.get('title', '')} {note.get('content', '')}"
        needle = query
        if not case_sensitive:
            haystack = haystack.lower()
            needle = needle.lower()
        return needle in haystack

    hits = [n for n in notes if matches(n)]

    if not hits:
        return f'No notes matched "{query}".'

    lines = [f'Found {len(hits)} note(s) matching "{query}":\n']
    for n in hits:
        s = _note_summary(n)
        fav = " ★" if s["favorite"] else ""
        cat = f" [{s['category']}]" if s["category"] else ""
        lines.append(f"  ID {s['id']}{fav}{cat}: {s['title']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
