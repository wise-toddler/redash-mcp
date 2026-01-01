"""Redash API functions."""
import time
import requests
from .config import URL, HEADERS, TIMEOUT


def _get(endpoint: str, params: dict = None) -> dict:
    return requests.get(f"{URL}{endpoint}", headers=HEADERS, params=params, timeout=TIMEOUT).json()


def _post(endpoint: str, data: dict = None) -> dict:
    return requests.post(f"{URL}{endpoint}", headers=HEADERS, json=data or {}, timeout=TIMEOUT).json()


def _delete(endpoint: str) -> dict | None:
    r = requests.delete(f"{URL}{endpoint}", headers=HEADERS, timeout=TIMEOUT)
    return r.json() if r.content else None


# Data Sources
def get_data_sources() -> list:
    """List all data sources."""
    return _get("/api/data_sources")


# Queries
def list_queries(page: int = 1, page_size: int = 25) -> dict:
    """List all queries (paginated)."""
    return _get("/api/queries", {"page": page, "page_size": page_size})


def search_queries(q: str) -> dict:
    """Search queries by name."""
    return _get("/api/queries", {"q": q})


def get_query(query_id: int) -> dict:
    """Get query details."""
    return _get(f"/api/queries/{query_id}")


def create_query(name: str, query: str, data_source_id: int, description: str = "") -> dict:
    """Create a new query."""
    return _post("/api/queries", {"name": name, "query": query, "data_source_id": data_source_id, "description": description})


def update_query(query_id: int, **kwargs) -> dict:
    """Update an existing query."""
    return _post(f"/api/queries/{query_id}", kwargs)


def archive_query(query_id: int) -> dict:
    """Archive (soft-delete) a query."""
    return _post(f"/api/queries/{query_id}", {"is_archived": True})


def delete_query(query_id: int) -> dict | None:
    """Permanently delete a query."""
    return _delete(f"/api/queries/{query_id}")


def execute_adhoc(query: str, data_source_id: int) -> dict:
    """Execute ad-hoc query without saving."""
    return _post("/api/query_results", {"query": query, "data_source_id": data_source_id})


# Dashboards
def list_dashboards(page: int = 1, page_size: int = 25) -> dict:
    """List all dashboards (paginated)."""
    return _get("/api/dashboards", {"page": page, "page_size": page_size})


def get_dashboard(dashboard_id: int) -> dict:
    """Get dashboard details with widgets."""
    return _get(f"/api/dashboards/{dashboard_id}")


def create_dashboard(name: str) -> dict:
    """Create a new dashboard."""
    return _post("/api/dashboards", {"name": name})


def publish_dashboard(dashboard_id: int) -> dict:
    """Publish dashboard (remove draft status)."""
    return _post(f"/api/dashboards/{dashboard_id}", {"is_draft": False})


def delete_dashboard(dashboard_id: int) -> dict | None:
    """Delete a dashboard."""
    return _delete(f"/api/dashboards/{dashboard_id}")


# Visualizations
def create_viz(query_id: int, viz_type: str, name: str, options: dict) -> dict:
    """Create a visualization."""
    return _post("/api/visualizations", {"query_id": query_id, "type": viz_type, "name": name, "options": options})


def update_viz(viz_id: int, **kwargs) -> dict:
    """Update a visualization."""
    return _post(f"/api/visualizations/{viz_id}", kwargs)


# Widgets
def add_widget(dashboard_id: int, viz_id: int) -> dict:
    """Add visualization to dashboard."""
    return _post("/api/widgets", {"dashboard_id": dashboard_id, "visualization_id": viz_id, "width": 1, "options": {}})


def delete_widget(widget_id: int) -> dict | None:
    """Delete widget from dashboard."""
    return _delete(f"/api/widgets/{widget_id}")


# Query Execution
def execute_query(query_id: int) -> dict:
    """Execute query and return job info."""
    return _post(f"/api/queries/{query_id}/results")


def get_job(job_id: str) -> dict:
    """Get job status."""
    return _get(f"/api/jobs/{job_id}")


def get_result(result_id: int) -> dict:
    """Get query result data."""
    return _get(f"/api/query_results/{result_id}")


def run_query(query_id: int, timeout: int = 60) -> dict:
    """Execute query and wait for result."""
    job = execute_query(query_id)
    job_id = job.get("job", {}).get("id")
    if not job_id:
        return job
    for _ in range(timeout):
        time.sleep(1)
        status = get_job(job_id)
        job_status = status.get("job", {}).get("status")
        if job_status in [3, 4]:  # 3=done, 4=failed
            result_id = status.get("job", {}).get("query_result_id")
            return get_result(result_id) if result_id else status
    return {"error": "timeout"}
