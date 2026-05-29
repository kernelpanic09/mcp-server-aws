"""Cost Explorer tool."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client


def get_cost_and_usage(
    start_date: str,
    end_date: str,
    granularity: str = "MONTHLY",
    group_by: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Query Cost Explorer for spend in the given date range.

    start_date / end_date: YYYY-MM-DD strings.
    granularity: DAILY, MONTHLY, or HOURLY.
    group_by: e.g. [{"Type": "DIMENSION", "Key": "SERVICE"}]
    """
    # Cost Explorer is only available in us-east-1.
    client = get_client("ce", "us-east-1")

    kwargs: dict[str, Any] = {
        "TimePeriod": {"Start": start_date, "End": end_date},
        "Granularity": granularity,
        "Metrics": ["UnblendedCost", "UsageQuantity"],
    }
    if group_by:
        kwargs["GroupBy"] = group_by

    try:
        resp = client.get_cost_and_usage(**kwargs)
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    results = []
    for period in resp.get("ResultsByTime", []):
        entry: dict[str, Any] = {
            "start": period["TimePeriod"]["Start"],
            "end": period["TimePeriod"]["End"],
            "estimated": period.get("Estimated", False),
        }
        if group_by and period.get("Groups"):
            entry["groups"] = [
                {
                    "keys": g["Keys"],
                    "cost_usd": g["Metrics"]["UnblendedCost"]["Amount"],
                }
                for g in period["Groups"]
            ]
        else:
            entry["cost_usd"] = period["Total"]["UnblendedCost"]["Amount"]
            entry["cost_unit"] = period["Total"]["UnblendedCost"]["Unit"]

        results.append(entry)

    return {"results": results, "granularity": granularity}
