"""RDS tool: list DB instances."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client
from ..config import get_config


def list_rds_instances(region: str | None = None) -> dict[str, Any]:
    """List RDS DB instances with engine, status, and size info."""
    client = get_client("rds", region)
    cfg = get_config()
    instances: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("describe_db_instances")
        for page in paginator.paginate():
            for db in page.get("DBInstances", []):
                instances.append(
                    {
                        "identifier": db.get("DBInstanceIdentifier"),
                        "engine": db.get("Engine"),
                        "engine_version": db.get("EngineVersion"),
                        "status": db.get("DBInstanceStatus"),
                        "instance_class": db.get("DBInstanceClass"),
                        "storage_gb": db.get("AllocatedStorage"),
                        "storage_type": db.get("StorageType"),
                        "multi_az": db.get("MultiAZ"),
                        "publicly_accessible": db.get("PubliclyAccessible"),
                        "endpoint": db.get("Endpoint", {}).get("Address"),
                        "port": db.get("Endpoint", {}).get("Port"),
                        "db_name": db.get("DBName"),
                        "vpc_id": db.get("DBSubnetGroup", {}).get("VpcId"),
                        "created": db.get("InstanceCreateTime", "").isoformat()
                        if hasattr(db.get("InstanceCreateTime", ""), "isoformat")
                        else str(db.get("InstanceCreateTime", "")),
                        "tags": {
                            t["Key"]: t["Value"]
                            for t in db.get("TagList", [])
                        },
                    }
                )
                if len(instances) >= cfg.max_items:
                    return {"instances": instances, "truncated": True}
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    return {"instances": instances, "truncated": False}
