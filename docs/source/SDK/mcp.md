# MCP Server

Reachy Mini exposes its controls as an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server, mountable on the existing daemon. This lets any MCP-compatible AI assistant — OpenClaw, Claude Desktop, Cursor, and others — control the robot directly.

## Setup

Install the optional dependency and start the daemon with the flag:

```bash
pip install reachy_mini[openclaw]
reachy-mini-daemon --enable-mcp
```

The MCP server is now available at `http://localhost:8000/mcp`.

## Available Tools

All angles are in **degrees**.

| Tool | Description |
|------|-------------|
| `goto` | Move head (yaw/pitch/roll), body, antennas over a given duration |
| `wake_up` | Wake up the robot |
| `goto_sleep` | Put the robot to sleep |
| `stop_move` | Stop a running move by UUID |
| `play_recorded_move` | Play a named move from a HuggingFace dataset |
| `get_state` | Get current head pose, body yaw, antenna positions, motor mode |
| `get_motor_status` | Get current motor control mode |
| `set_motor_mode` | Set motor mode: `enabled`, `disabled`, `gravity_compensation` |

## Connecting

### OpenClaw (via mcporter)

```bash
npx mcporter config add reachy-mini http://localhost:8000/mcp
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "reachy-mini": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Cursor / other MCP clients

Point them at `http://localhost:8000/mcp` using HTTP transport.
