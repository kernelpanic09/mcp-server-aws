"""S3 tools: list buckets and fetch bucket policies."""

from __future__ import annotations

import json
from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client


def list_s3_buckets() -> dict[str, Any]:
    """List all S3 buckets in the account with basic metadata."""
    client = get_client("s3")
    try:
        resp = client.list_buckets()
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    buckets = []
    for b in resp.get("Buckets", []):
        entry: dict[str, Any] = {
            "name": b["Name"],
            "creation_date": b["CreationDate"].isoformat()
            if hasattr(b.get("CreationDate"), "isoformat")
            else str(b.get("CreationDate", "")),
        }
        # Best-effort: fetch region and versioning without failing the whole list.
        try:
            loc = client.get_bucket_location(Bucket=b["Name"])
            entry["region"] = loc.get("LocationConstraint") or "us-east-1"
        except ClientError:
            entry["region"] = "unknown"

        buckets.append(entry)

    return {"buckets": buckets, "count": len(buckets)}


def get_s3_bucket_policy(bucket_name: str) -> dict[str, Any]:
    """Return the bucket policy for the given bucket, parsed as JSON."""
    client = get_client("s3")
    try:
        resp = client.get_bucket_policy(Bucket=bucket_name)
        policy_str = resp.get("Policy", "{}")
        return {
            "bucket": bucket_name,
            "policy": json.loads(policy_str),
        }
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "NoSuchBucketPolicy":
            return {"bucket": bucket_name, "policy": None, "message": "No policy attached"}
        return {"error": code, "message": str(e)}
