"""IAM tools: users, roles."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client
from ..config import get_config


def _iso(dt: Any) -> str:
    return dt.isoformat() if hasattr(dt, "isoformat") else str(dt)


def list_iam_users() -> dict[str, Any]:
    """List all IAM users with last activity timestamps."""
    client = get_client("iam")
    cfg = get_config()
    users: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("list_users")
        for page in paginator.paginate():
            for u in page.get("Users", []):
                users.append(
                    {
                        "username": u["UserName"],
                        "user_id": u["UserId"],
                        "arn": u["Arn"],
                        "created": _iso(u.get("CreateDate", "")),
                        "password_last_used": _iso(u.get("PasswordLastUsed", "never")),
                        "path": u.get("Path"),
                    }
                )
                if len(users) >= cfg.max_items:
                    return {"users": users, "truncated": True}
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    return {"users": users, "truncated": False}


def list_iam_roles() -> dict[str, Any]:
    """List all IAM roles."""
    client = get_client("iam")
    cfg = get_config()
    roles: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("list_roles")
        for page in paginator.paginate():
            for r in page.get("Roles", []):
                roles.append(
                    {
                        "role_name": r["RoleName"],
                        "role_id": r["RoleId"],
                        "arn": r["Arn"],
                        "created": _iso(r.get("CreateDate", "")),
                        "description": r.get("Description", ""),
                        "max_session_duration": r.get("MaxSessionDuration"),
                        "path": r.get("Path"),
                    }
                )
                if len(roles) >= cfg.max_items:
                    return {"roles": roles, "truncated": True}
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    return {"roles": roles, "truncated": False}


def get_iam_role(role_name: str) -> dict[str, Any]:
    """Return full details for a single IAM role, including attached policies."""
    client = get_client("iam")
    try:
        resp = client.get_role(RoleName=role_name)
        role = resp["Role"]
        data: dict[str, Any] = {
            "role_name": role["RoleName"],
            "role_id": role["RoleId"],
            "arn": role["Arn"],
            "created": _iso(role.get("CreateDate", "")),
            "description": role.get("Description", ""),
            "max_session_duration": role.get("MaxSessionDuration"),
            "assume_role_policy": role.get("AssumeRolePolicyDocument"),
            "tags": {t["Key"]: t["Value"] for t in role.get("Tags", [])},
        }
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    # Fetch attached managed policies separately.
    try:
        attached = client.list_attached_role_policies(RoleName=role_name)
        data["attached_policies"] = [
            {"name": p["PolicyName"], "arn": p["PolicyArn"]}
            for p in attached.get("AttachedPolicies", [])
        ]
    except ClientError:
        data["attached_policies"] = []

    return data
