"""CloudFormation tools: list and describe stacks."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client
from ..config import get_config


def _summarize_stack(s: dict[str, Any]) -> dict[str, Any]:
    return {
        "stack_name": s.get("StackName"),
        "stack_id": s.get("StackId"),
        "status": s.get("StackStatus"),
        "created": s.get("CreationTime", "").isoformat()
        if hasattr(s.get("CreationTime", ""), "isoformat")
        else str(s.get("CreationTime", "")),
        "updated": s.get("LastUpdatedTime", "").isoformat()
        if hasattr(s.get("LastUpdatedTime", ""), "isoformat")
        else str(s.get("LastUpdatedTime", "")),
        "description": s.get("Description", ""),
        "tags": {t["Key"]: t["Value"] for t in s.get("Tags", [])},
    }


def list_cloudformation_stacks(region: str | None = None) -> dict[str, Any]:
    """List all non-deleted CloudFormation stacks."""
    client = get_client("cloudformation", region)
    cfg = get_config()
    stacks: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("list_stacks")
        # Exclude deleted stacks by default.
        active_statuses = [
            "CREATE_COMPLETE", "CREATE_FAILED", "CREATE_IN_PROGRESS",
            "ROLLBACK_COMPLETE", "ROLLBACK_FAILED", "ROLLBACK_IN_PROGRESS",
            "UPDATE_COMPLETE", "UPDATE_IN_PROGRESS", "UPDATE_ROLLBACK_COMPLETE",
            "UPDATE_ROLLBACK_FAILED", "UPDATE_ROLLBACK_IN_PROGRESS",
            "REVIEW_IN_PROGRESS", "IMPORT_COMPLETE", "IMPORT_IN_PROGRESS",
            "IMPORT_ROLLBACK_COMPLETE", "IMPORT_ROLLBACK_FAILED",
            "IMPORT_ROLLBACK_IN_PROGRESS",
        ]
        for page in paginator.paginate(StackStatusFilter=active_statuses):
            for s in page.get("StackSummaries", []):
                stacks.append(_summarize_stack(s))
                if len(stacks) >= cfg.max_items:
                    return {"stacks": stacks, "truncated": True}
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    return {"stacks": stacks, "truncated": False}


def describe_cloudformation_stack(name: str, region: str | None = None) -> dict[str, Any]:
    """Return full details for a CloudFormation stack, including outputs and parameters."""
    client = get_client("cloudformation", region)
    try:
        resp = client.describe_stacks(StackName=name)
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    stacks = resp.get("Stacks", [])
    if not stacks:
        return {"error": "NotFound", "message": f"Stack {name} not found"}

    s = stacks[0]
    data = _summarize_stack(s)
    data["parameters"] = [
        {"key": p["ParameterKey"], "value": p.get("ParameterValue", "")}
        for p in s.get("Parameters", [])
    ]
    data["outputs"] = [
        {
            "key": o["OutputKey"],
            "value": o.get("OutputValue", ""),
            "description": o.get("Description", ""),
            "export_name": o.get("ExportName"),
        }
        for o in s.get("Outputs", [])
    ]
    data["capabilities"] = s.get("Capabilities", [])
    data["role_arn"] = s.get("RoleARN")
    return data
