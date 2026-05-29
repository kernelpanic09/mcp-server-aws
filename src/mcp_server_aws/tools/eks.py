"""EKS tools: list and describe clusters."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client
from ..config import get_config


def list_eks_clusters(region: str | None = None) -> dict[str, Any]:
    """List all EKS cluster names in a region."""
    client = get_client("eks", region)
    cfg = get_config()
    names: list[str] = []
    try:
        paginator = client.get_paginator("list_clusters")
        for page in paginator.paginate():
            names.extend(page.get("clusters", []))
            if len(names) >= cfg.max_items:
                names = names[: cfg.max_items]
                return {"clusters": names, "truncated": True}
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    return {"clusters": names, "truncated": False}


def describe_eks_cluster(name: str, region: str | None = None) -> dict[str, Any]:
    """Return full details for an EKS cluster."""
    client = get_client("eks", region)
    try:
        resp = client.describe_cluster(name=name)
        c = resp["cluster"]
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    return {
        "name": c.get("name"),
        "arn": c.get("arn"),
        "status": c.get("status"),
        "kubernetes_version": c.get("version"),
        "endpoint": c.get("endpoint"),
        "role_arn": c.get("roleArn"),
        "created": c.get("createdAt", "").isoformat()
        if hasattr(c.get("createdAt", ""), "isoformat")
        else str(c.get("createdAt", "")),
        "vpc_config": c.get("resourcesVpcConfig", {}),
        "logging": c.get("logging", {}),
        "tags": c.get("tags", {}),
        "platform_version": c.get("platformVersion"),
    }
