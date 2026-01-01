"""Visualization helpers."""
from .api import create_viz


def pie(query_id: int, name: str, x: str, y: str) -> dict:
    """Create a pie chart."""
    return create_viz(query_id, "CHART", name, {
        "globalSeriesType": "pie",
        "columnMapping": {x: "x", y: "y"},
        "legend": {"enabled": True}
    })


def line(query_id: int, name: str, x: str, y: list[str], datetime: bool = True) -> dict:
    """Create a line chart."""
    cols = {x: "x", **{c: "y" for c in y}}
    return create_viz(query_id, "CHART", name, {
        "globalSeriesType": "line",
        "columnMapping": cols,
        "legend": {"enabled": True},
        "xAxis": {"type": "datetime" if datetime else "-"},
        "yAxis": [{"type": "linear"}],
        "sortX": True
    })


def bar(query_id: int, name: str, x: str, y: list[str], stacked: bool = False) -> dict:
    """Create a bar chart."""
    cols = {x: "x", **{c: "y" for c in y}}
    return create_viz(query_id, "CHART", name, {
        "globalSeriesType": "column",
        "columnMapping": cols,
        "legend": {"enabled": True},
        "series": {"stacking": "normal" if stacked else None}
    })


def counter(query_id: int, name: str, col: str, suffix: str = "") -> dict:
    """Create a counter visualization."""
    return create_viz(query_id, "COUNTER", name, {
        "counterColName": col,
        "rowNumber": 1,
        "stringDecimal": 2,
        "stringSuffix": suffix
    })
