# redash-mcp

Model Context Protocol (MCP) server for [Redash](https://redash.io/) - manage queries, dashboards, and visualizations through AI assistants like Claude.

## Features

- **5 tools, 22 actions** - compressed for minimal context usage
- Full query management (list, search, create, update, archive, delete, run, adhoc)
- Dashboard management (list, get, create, publish, delete)
- Widget management (add, delete)
- Visualization creation (pie, line, bar, counter charts)
- Data source listing

## Installation

```bash
pip install redash-mcp
```

Or with [uvx](https://github.com/astral-sh/uv):

```bash
uvx redash-mcp
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `REDASH_URL` | Yes | Your Redash instance URL (e.g., `https://redash.example.com`) |
| `REDASH_API_KEY` | Yes | Your Redash API key |
| `REDASH_TIMEOUT` | No | Request timeout in seconds (default: 30) |

### Claude Desktop

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "redash": {
      "command": "uvx",
      "args": ["redash-mcp"],
      "env": {
        "REDASH_URL": "https://your-redash-instance.com",
        "REDASH_API_KEY": "your-api-key"
      }
    }
  }
}
```

Or if installed via pip:

```json
{
  "mcpServers": {
    "redash": {
      "command": "redash-mcp",
      "env": {
        "REDASH_URL": "https://your-redash-instance.com",
        "REDASH_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Tools

### `redash_data_sources`
List all available data sources.

### `redash_query`
Manage Redash queries.

| Action | Parameters | Description |
|--------|------------|-------------|
| `list` | `page` | List all queries (paginated) |
| `search` | `q` | Search queries by name |
| `get` | `id` | Get query details |
| `create` | `name`, `query`, `data_source_id` | Create new query |
| `update` | `id`, `query?`, `name?` | Update existing query |
| `archive` | `id` | Archive (soft-delete) query |
| `delete` | `id` | Permanently delete query |
| `run` | `id`, `timeout?` | Execute query and wait for results |
| `adhoc` | `query`, `data_source_id` | Execute SQL without saving |

### `redash_dashboard`
Manage Redash dashboards.

| Action | Parameters | Description |
|--------|------------|-------------|
| `list` | `page` | List all dashboards |
| `get` | `id` | Get dashboard with widgets |
| `create` | `name` | Create new dashboard |
| `publish` | `id` | Publish dashboard (remove draft) |
| `delete` | `id` | Delete dashboard |

### `redash_widget`
Manage dashboard widgets.

| Action | Parameters | Description |
|--------|------------|-------------|
| `add` | `dashboard_id`, `viz_id` | Add visualization to dashboard |
| `delete` | `id` | Remove widget from dashboard |

### `redash_viz`
Create visualizations.

| Type | Parameters | Description |
|------|------------|-------------|
| `pie` | `query_id`, `name`, `x`, `y` | Pie chart |
| `line` | `query_id`, `name`, `x`, `y`, `datetime?` | Line chart |
| `bar` | `query_id`, `name`, `x`, `y`, `stacked?` | Bar chart |
| `counter` | `query_id`, `name`, `x`, `suffix?` | Counter/KPI |

**Note:** For multiple Y columns, pass comma-separated values: `y="count,total,avg"`

## Examples

### Create a dashboard with visualizations

```
1. redash_data_sources() → get data_source_id
2. redash_query(action="create", name="Daily Stats", query="SELECT ...", data_source_id=1)
3. redash_viz(type="line", query_id=123, name="Trend", x="date", y="count")
4. redash_dashboard(action="create", name="My Dashboard")
5. redash_widget(action="add", dashboard_id=456, viz_id=789)
6. redash_dashboard(action="publish", id=456)
```

### Run ad-hoc query

```
redash_query(action="adhoc", query="SELECT COUNT(*) FROM users", data_source_id=1)
```

### Search and update query

```
redash_query(action="search", q="daily")
redash_query(action="update", id=123, query="SELECT ... WHERE date > NOW() - INTERVAL '7 days'")
```

## Python Library Usage

You can also use redash-mcp as a Python library:

```python
import os
os.environ["REDASH_URL"] = "https://your-redash.com"
os.environ["REDASH_API_KEY"] = "your-key"

from redash_mcp import (
    list_queries, create_query, run_query,
    create_dashboard, publish_dashboard,
    line, bar, pie, counter,
    add_widget
)

# Create query
q = create_query("My Query", "SELECT * FROM events", data_source_id=1)

# Create visualization
viz = line(q["id"], "Events Trend", x="date", y=["count"])

# Create dashboard and add widget
d = create_dashboard("My Dashboard")
add_widget(d["id"], viz["id"])
publish_dashboard(d["id"])
```

## Why redash-mcp?

- **Context efficient** - Only 5 tools (~400 tokens) with 22 actions
- **Full-featured** - Queries, dashboards, widgets, and visualizations
- **Production ready** - Proper error handling and timeouts
- **Dual use** - Works as MCP server and Python library

## License

MIT
