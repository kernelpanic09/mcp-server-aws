"""CloudWatch Logs Insights tool."""

from __future__ import annotations

import time
from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client
from ..config import get_config


def query_cloudwatch_logs(
    log_group: str,
    query: str,
    start_time: str,
    end_time: str,
    region: str | None = None,
) -> dict[str, Any]:
    """Run a Logs Insights query and wait for results (up to 30s).

    start_time / end_time: ISO 8601 strings or Unix timestamps as strings.
    query: Logs Insights query string, e.g. 'fields @timestamp, @message | limit 20'

    Results are capped at config.max_log_lines.
    """
    from datetime import datetime

    client = get_client("logs", region)
    cfg = get_config()

    def _parse_time(t: str) -> int:
        # Accept Unix timestamps or ISO strings.
        try:
            return int(t)
        except ValueError:
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            return int(dt.timestamp())

    try:
        start = client.start_query(
            logGroupName=log_group,
            startTime=_parse_time(start_time),
            endTime=_parse_time(end_time),
            queryString=query,
        )
        query_id = start["queryId"]
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    # Poll until done or timeout.
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            result = client.get_query_results(queryId=query_id)
        except ClientError as e:
            return {"error": e.response["Error"]["Code"], "message": str(e)}

        status = result.get("status")
        if status in ("Complete", "Failed", "Cancelled"):
            break
        time.sleep(1)

    if status != "Complete":
        return {"error": "QueryFailed", "message": f"Query ended with status: {status}"}

    rows = result.get("results", [])
    truncated = len(rows) > cfg.max_log_lines
    rows = rows[: cfg.max_log_lines]

    # Convert from [{field, value}] format to dicts.
    records = [{field["field"]: field["value"] for field in row} for row in rows]

    return {
        "log_group": log_group,
        "query": query,
        "status": status,
        "records": records,
        "truncated": truncated,
        "statistics": result.get("statistics", {}),
    }
