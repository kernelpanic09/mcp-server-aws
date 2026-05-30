"""EC2 tools: list and describe instances."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client
from ..config import get_config
from ..safety import (
    InvalidConfirmationTokenError,
    WritesNotEnabledError,
    make_confirmation_token,
    require_writes,
    verify_confirmation_token,
)


def _extract_instance(i: dict[str, Any]) -> dict[str, Any]:
    """Pull the fields we actually care about from a raw EC2 instance dict."""
    return {
        "instance_id": i.get("InstanceId"),
        "instance_type": i.get("InstanceType"),
        "state": i.get("State", {}).get("Name"),
        "availability_zone": i.get("Placement", {}).get("AvailabilityZone"),
        "private_ip": i.get("PrivateIpAddress"),
        "public_ip": i.get("PublicIpAddress"),
        "launch_time": i.get("LaunchTime", "").isoformat()
        if hasattr(i.get("LaunchTime", ""), "isoformat")
        else str(i.get("LaunchTime", "")),
        "tags": {t["Key"]: t["Value"] for t in i.get("Tags", [])},
        "image_id": i.get("ImageId"),
        "key_name": i.get("KeyName"),
        "vpc_id": i.get("VpcId"),
        "subnet_id": i.get("SubnetId"),
    }


def list_ec2_instances(
    region: str | None = None,
    filters: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """List EC2 instances with optional filters.

    filters follow the boto3 format: [{"Name": "instance-state-name", "Values": ["running"]}]
    """
    client = get_client("ec2", region)
    cfg = get_config()
    kwargs: dict[str, Any] = {}
    if filters:
        kwargs["Filters"] = filters

    instances: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("describe_instances")
        for page in paginator.paginate(**kwargs):
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    instances.append(_extract_instance(inst))
                    if len(instances) >= cfg.max_items:
                        return {"instances": instances, "truncated": True}
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    return {"instances": instances, "truncated": False}


def describe_ec2_instance(
    instance_id: str,
    region: str | None = None,
) -> dict[str, Any]:
    """Return full details for a single EC2 instance."""
    client = get_client("ec2", region)
    try:
        resp = client.describe_instances(InstanceIds=[instance_id])
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    reservations = resp.get("Reservations", [])
    if not reservations:
        return {"error": "NotFound", "message": f"Instance {instance_id} not found"}

    inst = reservations[0]["Instances"][0]
    data = _extract_instance(inst)

    # Add security groups and block devices for the full-detail view.
    data["security_groups"] = [
        {"id": sg["GroupId"], "name": sg["GroupName"]} for sg in inst.get("SecurityGroups", [])
    ]
    data["block_devices"] = [
        {
            "device": bd["DeviceName"],
            "volume_id": bd.get("Ebs", {}).get("VolumeId"),
            "delete_on_termination": bd.get("Ebs", {}).get("DeleteOnTermination"),
        }
        for bd in inst.get("BlockDeviceMappings", [])
    ]
    data["iam_instance_profile"] = inst.get("IamInstanceProfile", {}).get("Arn")
    data["monitoring"] = inst.get("Monitoring", {}).get("State")
    return data


def stop_ec2_instance(
    instance_id: str,
    confirmation_token: str,
    region: str | None = None,
) -> dict[str, Any]:
    """Stop a running EC2 instance.

    Requires --allow-writes and a valid confirmation_token.
    Call make_stop_confirmation() first to get the token.
    """
    try:
        require_writes()
        verify_confirmation_token("stop_ec2", {"instance_id": instance_id}, confirmation_token)
    except WritesNotEnabledError as e:
        return {"error": "WritesNotEnabled", "message": str(e)}
    except InvalidConfirmationTokenError as e:
        return {"error": "InvalidConfirmationToken", "message": str(e)}

    client = get_client("ec2", region)
    try:
        resp = client.stop_instances(InstanceIds=[instance_id])
        change = resp["StoppingInstances"][0]
        return {
            "instance_id": change["InstanceId"],
            "previous_state": change["PreviousState"]["Name"],
            "current_state": change["CurrentState"]["Name"],
        }
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}


def get_stop_confirmation_token(instance_id: str) -> dict[str, str]:
    """Return the confirmation token needed to call stop_ec2_instance."""
    token = make_confirmation_token("stop_ec2", {"instance_id": instance_id})
    return {
        "confirmation_token": token,
        "instruction": f"Pass this token as confirmation_token to stop_ec2_instance('{instance_id}', ...)",
    }
