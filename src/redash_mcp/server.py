"""Redash MCP Server."""
import json
import sys
from . import api
from .viz import pie, line, bar, counter

TOOLS = [
    {
        "name": "redash_query",
        "description": "Manage Redash queries. Actions: list, search, get, create, update, archive, delete, run, adhoc",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "search", "get", "create", "update", "archive", "delete", "run", "adhoc"]},
                "id": {"type": "integer", "description": "Query ID (for get/update/archive/delete/run)"},
                "q": {"type": "string", "description": "Search term (for search)"},
                "name": {"type": "string", "description": "Query name (for create)"},
                "query": {"type": "string", "description": "SQL query (for create/update/adhoc)"},
                "data_source_id": {"type": "integer", "description": "Data source ID"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10, "description": "Results per page (default 10, max 250)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "redash_dashboard",
        "description": "Manage Redash dashboards. Actions: list, get, create, publish, delete",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "get", "create", "publish", "delete"]},
                "id": {"type": "integer", "description": "Dashboard ID"},
                "name": {"type": "string", "description": "Dashboard name (for create)"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10, "description": "Results per page (default 10, max 250)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "redash_widget",
        "description": "Manage dashboard widgets. Actions: add, delete",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "delete"]},
                "id": {"type": "integer", "description": "Widget ID (for delete)"},
                "dashboard_id": {"type": "integer", "description": "Dashboard ID (for add)"},
                "viz_id": {"type": "integer", "description": "Visualization ID (for add)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "redash_viz",
        "description": "Create visualizations. Types: pie, line, bar, counter",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["pie", "line", "bar", "counter"]},
                "query_id": {"type": "integer"},
                "name": {"type": "string"},
                "x": {"type": "string", "description": "X-axis column"},
                "y": {"type": "string", "description": "Y column(s) - comma separated for multiple"},
                "datetime": {"type": "boolean", "default": True, "description": "X-axis is datetime (for line)"},
                "stacked": {"type": "boolean", "default": False, "description": "Stacked bars (for bar)"},
                "suffix": {"type": "string", "default": "", "description": "Suffix (for counter)"},
            },
            "required": ["type", "query_id", "name"]
        }
    },
    {
        "name": "redash_data_sources",
        "description": "List all available data sources",
        "inputSchema": {"type": "object", "properties": {}}
    },
]


def _condense_queries(data: dict) -> dict:
    """Return condensed query list with essential fields only."""
    if "results" in data:
        data["results"] = [
            {"id": q["id"], "name": q["name"], "data_source_id": q.get("data_source_id"), "created_at": q.get("created_at")}
            for q in data["results"]
        ]
    return data


def handle_query(args: dict) -> dict:
    action = args["action"]
    if action == "list":
        return _condense_queries(api.list_queries(args.get("page", 1), args.get("page_size", 10)))
    if action == "search":
        return _condense_queries(api.search_queries(args["q"]))
    if action == "get":
        return api.get_query(args["id"])
    if action == "create":
        return api.create_query(args["name"], args["query"], args["data_source_id"], args.get("description", ""))
    if action == "update":
        return api.update_query(args["id"], **{k: v for k, v in args.items() if k not in ["action", "id"]})
    if action == "archive":
        return api.archive_query(args["id"])
    if action == "delete":
        api.delete_query(args["id"])
        return {"success": True}
    if action == "run":
        return api.run_query(args["id"], args.get("timeout", 60))
    if action == "adhoc":
        return api.execute_adhoc(args["query"], args["data_source_id"])
    return {"error": f"Unknown action: {action}"}


def _condense_dashboards(data: dict) -> dict:
    """Return condensed dashboard list with essential fields only."""
    if "results" in data:
        data["results"] = [
            {"id": d["id"], "name": d["name"], "slug": d.get("slug"), "created_at": d.get("created_at")}
            for d in data["results"]
        ]
    return data


def handle_dashboard(args: dict) -> dict:
    action = args["action"]
    if action == "list":
        return _condense_dashboards(api.list_dashboards(args.get("page", 1), args.get("page_size", 10)))
    if action == "get":
        return api.get_dashboard(args["id"])
    if action == "create":
        return api.create_dashboard(args["name"])
    if action == "publish":
        return api.publish_dashboard(args["id"])
    if action == "delete":
        api.delete_dashboard(args["id"])
        return {"success": True}
    return {"error": f"Unknown action: {action}"}


def handle_widget(args: dict) -> dict:
    action = args["action"]
    if action == "add":
        return api.add_widget(args["dashboard_id"], args["viz_id"])
    if action == "delete":
        api.delete_widget(args["id"])
        return {"success": True}
    return {"error": f"Unknown action: {action}"}


def handle_viz(args: dict) -> dict:
    t, qid, name = args["type"], args["query_id"], args["name"]
    y_cols = [c.strip() for c in args.get("y", "").split(",")] if args.get("y") else []
    if t == "pie":
        return pie(qid, name, args["x"], y_cols[0] if y_cols else args["x"])
    if t == "line":
        return line(qid, name, args["x"], y_cols, args.get("datetime", True))
    if t == "bar":
        return bar(qid, name, args["x"], y_cols, args.get("stacked", False))
    if t == "counter":
        return counter(qid, name, args.get("x", ""), args.get("suffix", ""))
    return {"error": f"Unknown type: {t}"}


def handle_tool(name: str, args: dict) -> dict:
    try:
        if name == "redash_query":
            return handle_query(args)
        if name == "redash_dashboard":
            return handle_dashboard(args)
        if name == "redash_widget":
            return handle_widget(args)
        if name == "redash_viz":
            return handle_viz(args)
        if name == "redash_data_sources":
            return api.get_data_sources()
        return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main entry point for MCP server."""
    for ln in sys.stdin:
        try:
            msg = json.loads(ln)
        except json.JSONDecodeError:
            continue

        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "initialize":
            res = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "redash-mcp", "version": "0.1.0"}
            }
        elif method == "tools/list":
            res = {"tools": TOOLS}
        elif method == "tools/call":
            params = msg.get("params", {})
            result = handle_tool(params.get("name", ""), params.get("arguments", {}))
            res = {"content": [{"type": "text", "text": json.dumps(result, default=str)}]}
        else:
            res = {}

        response = {"jsonrpc": "2.0", "id": msg_id, "result": res}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
