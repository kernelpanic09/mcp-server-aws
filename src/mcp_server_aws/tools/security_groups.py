"""EC2 Security Group tool."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client


def describe_security_group(group_id: str, region: str | None = None) -> dict[str, Any]:
    """Return inbound and outbound rules for a security group."""
    client = get_client("ec2", region)
    try:
        resp = client.describe_security_groups(GroupIds=[group_id])
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    groups = resp.get("SecurityGroups", [])
    if not groups:
        return {"error": "NotFound", "message": f"Security group {group_id} not found"}

    g = groups[0]

    def _format_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for r in rules:
            rule: dict[str, Any] = {
                "protocol": r.get("IpProtocol"),
                "from_port": r.get("FromPort"),
                "to_port": r.get("ToPort"),
                "cidr_ipv4": [ip["CidrIp"] for ip in r.get("IpRanges", [])],
                "cidr_ipv6": [ip["CidrIpv6"] for ip in r.get("Ipv6Ranges", [])],
                "referenced_groups": [
                    g["GroupId"] for g in r.get("UserIdGroupPairs", [])
                ],
                "description": (r.get("IpRanges") or [{}])[0].get("Description", "")
                if r.get("IpRanges")
                else "",
            }
            out.append(rule)
        return out

    return {
        "group_id": g.get("GroupId"),
        "group_name": g.get("GroupName"),
        "description": g.get("Description"),
        "vpc_id": g.get("VpcId"),
        "owner_id": g.get("OwnerId"),
        "inbound_rules": _format_rules(g.get("IpPermissions", [])),
        "outbound_rules": _format_rules(g.get("IpPermissionsEgress", [])),
        "tags": {t["Key"]: t["Value"] for t in g.get("Tags", [])},
    }
