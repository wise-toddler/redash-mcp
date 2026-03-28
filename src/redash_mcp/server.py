"""Redash MCP Server."""
import csv
import json
import sys
from . import api
from .viz import pie, line, bar, counter

TOOLS = [
    {
        "name": "redash_query",
        "description": "Manage Redash queries. Actions: list, search, get, create, update, archive, delete, run, adhoc, export, schedule",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "search", "get", "create", "update", "archive", "delete", "run", "adhoc", "export", "schedule"]},
                "id": {"type": "integer", "description": "Query ID (for get/update/archive/delete/run/export)"},
                "q": {"type": "string", "description": "Search term (for search)"},
                "name": {"type": "string", "description": "Query name (for create)"},
                "query": {"type": "string", "description": "SQL or MongoDB JSON query (for create/update/adhoc). For MongoDB, use JSON format e.g. {\"collection\": \"my_col\", \"query\": {\"field\": \"value\"}, \"limit\": 50, \"sort\": [{\"name\": \"field\", \"direction\": -1}]}"},
                "data_source_id": {"type": "integer", "description": "Data source ID"},
                "max_rows": {"type": "integer", "default": 200, "description": "Max rows to return for adhoc queries (default 200, prevents huge responses)"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10, "description": "Results per page (default 10, max 250)"},
                "path": {"type": "string", "description": "File path to export results (for export). Supports .csv and .json"},
                "interval": {"type": "integer", "description": "Schedule interval in seconds (for schedule). e.g. 300=5min, 3600=1hr, 86400=daily"},
                "until": {"type": "string", "description": "Schedule end datetime ISO format (for schedule, optional)"},
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
        "description": "Manage dashboard widgets. Actions: add, move, delete",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "move", "delete"]},
                "id": {"type": "integer", "description": "Widget ID (for move/delete)"},
                "dashboard_id": {"type": "integer", "description": "Dashboard ID (for add)"},
                "viz_id": {"type": "integer", "description": "Visualization ID (for add)"},
                "col": {"type": "integer", "description": "Column position 0-5 (for add/move)"},
                "row": {"type": "integer", "description": "Row position (for add/move)"},
                "sizeX": {"type": "integer", "description": "Width in grid units 1-6 (for add/move)"},
                "sizeY": {"type": "integer", "description": "Height in grid units (for add/move)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "redash_alert",
        "description": "Manage Redash alerts. Actions: list, get, create, update, delete",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "get", "create", "update", "delete"]},
                "id": {"type": "integer", "description": "Alert ID (for get/update/delete)"},
                "query_id": {"type": "integer", "description": "Query ID (for create)"},
                "name": {"type": "string", "description": "Alert name (for create/update)"},
                "column": {"type": "string", "description": "Column to monitor (for create)"},
                "op": {"type": "string", "enum": ["greater than", "less than", "equals"], "description": "Condition operator (for create)"},
                "value": {"type": "number", "description": "Threshold value (for create)"},
                "rearm": {"type": "integer", "description": "Seconds before re-triggering (for create/update)"},
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
        return api.execute_adhoc(args["query"], args["data_source_id"], max_rows=args.get("max_rows", 200))
    if action == "schedule":
        schedule = {"interval": args["interval"]}
        if "until" in args:
            schedule["until"] = args["until"]
        return api.update_query(args["id"], schedule=schedule)
    if action == "export":
        result = api.run_query(args["id"], args.get("timeout", 60))
        if "error" in result:
            return result
        rows = result.get("query_result", {}).get("data", {}).get("rows", [])
        cols = result.get("query_result", {}).get("data", {}).get("columns", [])
        path = args["path"]
        if path.endswith(".csv"):
            with open(path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=[c["name"] for c in cols])
                w.writeheader()
                w.writerows(rows)
        else:
            with open(path, "w") as f:
                json.dump(rows, f, default=str, indent=2)
        return {"success": True, "path": path, "rows": len(rows)}
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


def _build_pos(args: dict) -> dict:
    """Build position dict from args."""
    pos = {}
    for k in ("col", "row", "sizeX", "sizeY"):
        if k in args:
            pos[k] = args[k]
    return pos


def handle_widget(args: dict) -> dict:
    action = args["action"]
    if action == "add":
        return api.add_widget(args["dashboard_id"], args["viz_id"], _build_pos(args) or None)
    if action == "move":
        return api.update_widget(args["id"], _build_pos(args))
    if action == "delete":
        api.delete_widget(args["id"])
        return {"success": True}
    return {"error": f"Unknown action: {action}"}


def handle_alert(args: dict) -> dict:
    action = args["action"]
    if action == "list":
        return api.list_alerts()
    if action == "get":
        return api.get_alert(args["id"])
    if action == "create":
        options = {"column": args["column"], "op": args["op"], "value": args["value"]}
        if "rearm" in args:
            options["rearm"] = args["rearm"]
        return api.create_alert(args["query_id"], args["name"], options)
    if action == "update":
        updates = {k: v for k, v in args.items() if k not in ["action", "id"]}
        return api.update_alert(args["id"], **updates)
    if action == "delete":
        api.delete_alert(args["id"])
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
        if name == "redash_alert":
            return handle_alert(args)
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
