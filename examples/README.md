# Examples

Drop-in configs and prompt ideas for wiring this MCP server into an AI client.

| File | What it's for |
|------|---------------|
| [claude-desktop-config.json](claude-desktop-config.json) | `mcpServers` block for Claude Desktop. Merge into `claude_desktop_config.json` (paths in the file's comment). |
| [claude-code-config.json](claude-code-config.json) | `mcpServers` block for Claude Code. Place in `.claude/mcp.json` (per-project) or `~/.claude/mcp.json` (global), with example `AWS_PROFILE` / region overrides. |
| [usage.md](usage.md) | Copy-paste prompt examples grouped by area: cost analysis, EC2/compute, IAM, logs, infra review, security groups, and write operations. |

Both configs assume `mcp-server-aws` is on your `PATH` (installed via `pip`/`uv`,
see the [main README](../README.md#installation)). To enable write tools, add
`--allow-writes` to `args` - read [Safety](../README.md#safety) first.
