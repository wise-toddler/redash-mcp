"""Redash API functions."""
import json
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


def param_options(parameters: dict) -> dict:
    """Build options.parameters from a {name: default_value} dict."""
    return {"parameters": [
        {"name": k, "title": k, "type": "number" if isinstance(v, (int, float)) else "text", "value": v}
        for k, v in parameters.items()
    ]}


def create_query(name: str, query, data_source_id: int, description: str = "", parameters: dict = None) -> dict:
    """Create a new query."""
    if isinstance(query, dict):
        query = json.dumps(query)
    data = {"name": name, "query": query, "data_source_id": data_source_id, "description": description}
    if parameters:
        data["options"] = param_options(parameters)
    return _post("/api/queries", data)


def update_query(query_id: int, **kwargs) -> dict:
    """Update an existing query."""
    return _post(f"/api/queries/{query_id}", kwargs)


def archive_query(query_id: int) -> dict:
    """Archive (soft-delete) a query."""
    return _post(f"/api/queries/{query_id}", {"is_archived": True})


def delete_query(query_id: int) -> dict | None:
    """Permanently delete a query."""
    return _delete(f"/api/queries/{query_id}")


def _normalize_query(query) -> str:
    """Ensure query is a string. Dicts are serialized to JSON (for MongoDB support)."""
    if isinstance(query, dict):
        return json.dumps(query)
    return query


def _post_streamed(endpoint: str, data: dict, max_bytes: int = 10 * 1024 * 1024) -> dict:
    """POST with streamed response, capped at max_bytes to avoid OOM on large results."""
    r = requests.post(f"{URL}{endpoint}", headers=HEADERS, json=data, timeout=TIMEOUT, stream=True)
    raw = b""
    for chunk in r.iter_content(chunk_size=1024 * 64):
        raw += chunk
        if len(raw) > max_bytes:
            break
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Response too large (>10MB). Add filters or limit to your query to reduce result size."}


def _truncate_rows(data: dict, max_rows: int) -> dict:
    """Truncate query result rows if they exceed max_rows."""
    rows = data.get("query_result", {}).get("data", {}).get("rows", [])
    if len(rows) > max_rows:
        data["query_result"]["data"]["rows"] = rows[:max_rows]
        data["query_result"]["data"]["truncated"] = True
        data["query_result"]["data"]["total_rows"] = len(rows)
        data["query_result"]["data"]["returned_rows"] = max_rows
    return data


def _wait_for_job(data: dict, timeout: int) -> dict:
    """If response contains a job, poll until complete. Otherwise return as-is."""
    job_id = data.get("job", {}).get("id")
    if not job_id:
        return data
    for _ in range(timeout):
        time.sleep(1)
        status = get_job(job_id)
        job_status = status.get("job", {}).get("status")
        if job_status in [3, 4]:  # 3=done, 4=failed
            result_id = status.get("job", {}).get("query_result_id")
            return get_result(result_id) if result_id else status
    return {"error": "Query execution timed out"}


def execute_adhoc(query, data_source_id: int, max_rows: int = 200, timeout: int = 60) -> dict:
    """Execute ad-hoc query without saving."""
    query = _normalize_query(query)
    data = _post_streamed("/api/query_results", {"query": query, "data_source_id": data_source_id})
    if "error" in data:
        return data
    if "job" in data:
        data = _wait_for_job(data, timeout)
    return _truncate_rows(data, max_rows)


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
def add_widget(dashboard_id: int, viz_id: int, pos: dict = None) -> dict:
    """Add visualization to dashboard with optional position."""
    data = {"dashboard_id": dashboard_id, "visualization_id": viz_id, "width": 1, "options": {"position": pos or {}}}
    return _post("/api/widgets", data)


def update_widget(widget_id: int, pos: dict) -> dict:
    """Update widget position on dashboard."""
    return _post(f"/api/widgets/{widget_id}", {"options": {"position": pos}})


def delete_widget(widget_id: int) -> dict | None:
    """Delete widget from dashboard."""
    return _delete(f"/api/widgets/{widget_id}")


# Alerts
def list_alerts() -> list:
    """List all alerts."""
    return _get("/api/alerts")


def get_alert(alert_id: int) -> dict:
    """Get alert details."""
    return _get(f"/api/alerts/{alert_id}")


def create_alert(query_id: int, name: str, options: dict) -> dict:
    """Create an alert on a query."""
    return _post("/api/alerts", {"query_id": query_id, "name": name, "options": options})


def update_alert(alert_id: int, **kwargs) -> dict:
    """Update an alert."""
    return _post(f"/api/alerts/{alert_id}", kwargs)


def delete_alert(alert_id: int) -> dict | None:
    """Delete an alert."""
    return _delete(f"/api/alerts/{alert_id}")


# Query Execution
def execute_query(query_id: int, parameters: dict = None) -> dict:
    """Execute query and return job info."""
    body = {"parameters": parameters, "max_age": 0} if parameters else {}
    return _post(f"/api/queries/{query_id}/results", body)


def get_job(job_id: str) -> dict:
    """Get job status."""
    return _get(f"/api/jobs/{job_id}")


def get_result(result_id: int) -> dict:
    """Get query result data."""
    return _get(f"/api/query_results/{result_id}")


def run_query(query_id: int, timeout: int = 60, parameters: dict = None) -> dict:
    """Execute query and wait for result."""
    if not parameters:
        # Redash never applies saved defaults server-side, so send them ourselves
        saved = get_query(query_id).get("options", {}).get("parameters", [])
        parameters = {p["name"]: p["value"] for p in saved if p.get("value") is not None}
    job = execute_query(query_id, parameters)
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
