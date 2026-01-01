"""Redash MCP - Model Context Protocol server for Redash."""
from .api import (
    get_data_sources,
    list_queries, search_queries, get_query, create_query, update_query, archive_query, delete_query,
    execute_adhoc, run_query,
    list_dashboards, get_dashboard, create_dashboard, publish_dashboard, delete_dashboard,
    create_viz, update_viz,
    add_widget, delete_widget,
)
from .viz import pie, line, bar, counter
from .server import main

__version__ = "0.1.0"
__all__ = [
    "get_data_sources",
    "list_queries", "search_queries", "get_query", "create_query", "update_query", "archive_query", "delete_query",
    "execute_adhoc", "run_query",
    "list_dashboards", "get_dashboard", "create_dashboard", "publish_dashboard", "delete_dashboard",
    "create_viz", "update_viz",
    "add_widget", "delete_widget",
    "pie", "line", "bar", "counter",
    "main",
]
