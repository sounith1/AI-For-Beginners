# Nextcloud Notes MCP Server — Setup Guide

## Prerequisites

- Python 3.11+
- Nextcloud instance with the **Notes** app installed
- A Nextcloud **app password** (recommended over your main password)

---

## 1. Generate a Nextcloud App Password

1. Log in to your Nextcloud web UI
2. Go to **Settings → Security → Devices & sessions**
3. Create a new app password — copy it, you'll only see it once

---

## 2. Install Dependencies

```bash
cd nextcloud-notes-mcp
pip install -r requirements.txt
```

---

## 3. Configure Claude Code

Add the following to your Claude Code MCP config file.

**Location:**
- macOS / Linux: `~/.claude/claude_desktop_config.json`
- Or project-level: `.mcp.json` in your repo root

```json
{
  "mcpServers": {
    "nextcloud-notes": {
      "command": "python",
      "args": ["/absolute/path/to/nextcloud-notes-mcp/server.py"],
      "env": {
        "NEXTCLOUD_URL": "https://your-nextcloud.example.com",
        "NEXTCLOUD_USERNAME": "your_username",
        "NEXTCLOUD_PASSWORD": "your_app_password"
      }
    }
  }
}
```

Replace the path and credentials with your actual values.

---

## 4. Restart Claude Code

After saving the config, restart Claude Code. You should see `nextcloud-notes` listed as an available MCP server.

---

## Available Tools

| Tool | Description |
|---|---|
| `list_notes` | List all notes; optional `category` filter |
| `get_note` | Fetch full content of a note by ID |
| `create_note` | Create a note with title, content, category |
| `update_note` | Update any field of an existing note |
| `delete_note` | Permanently delete a note by ID |
| `search_notes` | Full-text search across titles and content |

---

## Example Prompts (once configured)

```
List all my notes in the "Work" category.

Create a note titled "Meeting Notes 2026-03-02" with today's agenda.

Search my notes for anything mentioning "project deadline".

Update note 42 — change its category to "Archive".
```

---

## Security Notes

- Always use an **app password**, never your main Nextcloud password
- The `.mcp.json` file containing credentials should be added to `.gitignore`
- Consider using a secrets manager or shell env vars instead of hardcoding in the config file
