"""CloudWatch metrics tool."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client


def get_cloudwatch_metric(
    namespace: str,
    metric_name: str,
    dimensions: list[dict[str, str]],
    period: int,
    statistic: str,
    start_time: str,
    end_time: str,
    region: str | None = None,
) -> dict[str, Any]:
    """Fetch a CloudWatch metric's datapoints.

    dimensions: [{"Name": "InstanceId", "Value": "i-abc123"}]
    statistic: one of Average, Sum, Minimum, Maximum, SampleCount
    start_time / end_time: ISO 8601 strings (e.g. "2024-01-01T00:00:00Z")
    period: seconds (e.g. 300 for 5 min)
    """
    from datetime import datetime

    client = get_client("cloudwatch", region)
    try:
        resp = client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=datetime.fromisoformat(start_time.replace("Z", "+00:00")),
            EndTime=datetime.fromisoformat(end_time.replace("Z", "+00:00")),
            Period=period,
            Statistics=[statistic],
        )
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    datapoints = sorted(
        [
            {
                "timestamp": dp["Timestamp"].isoformat(),
                "value": dp.get(statistic),
                "unit": dp.get("Unit"),
            }
            for dp in resp.get("Datapoints", [])
        ],
        key=lambda x: x["timestamp"],
    )

    return {
        "namespace": namespace,
        "metric_name": metric_name,
        "statistic": statistic,
        "period_seconds": period,
        "datapoints": datapoints,
    }
