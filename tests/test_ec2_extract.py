"""Unit tests for the pure _extract_instance helper.

These exercise the field-normalization logic directly (no AWS/moto), covering
the branches that the moto-backed tests don't reliably hit: the LaunchTime
isoformat fallback, absent optional fields, and tag list -> dict conversion.
"""

from datetime import UTC, datetime

from mcp_server_aws.tools.ec2 import _extract_instance


def test_extract_full_instance():
    raw = {
        "InstanceId": "i-abc123",
        "InstanceType": "t3.micro",
        "State": {"Name": "running"},
        "Placement": {"AvailabilityZone": "us-east-1a"},
        "PrivateIpAddress": "10.0.0.5",
        "PublicIpAddress": "203.0.113.7",
        "LaunchTime": datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        "Tags": [{"Key": "Name", "Value": "web"}, {"Key": "env", "Value": "prod"}],
        "ImageId": "ami-00000000",
        "KeyName": "deploy-key",
        "VpcId": "vpc-111",
        "SubnetId": "subnet-222",
    }

    result = _extract_instance(raw)

    assert result["instance_id"] == "i-abc123"
    assert result["instance_type"] == "t3.micro"
    assert result["state"] == "running"
    assert result["availability_zone"] == "us-east-1a"
    assert result["private_ip"] == "10.0.0.5"
    assert result["public_ip"] == "203.0.113.7"
    # datetime should be serialized via isoformat().
    assert result["launch_time"] == "2026-01-02T03:04:05+00:00"
    assert result["tags"] == {"Name": "web", "env": "prod"}
    assert result["image_id"] == "ami-00000000"
    assert result["key_name"] == "deploy-key"
    assert result["vpc_id"] == "vpc-111"
    assert result["subnet_id"] == "subnet-222"


def test_extract_minimal_instance_defaults_to_none():
    # An almost-empty payload should not raise and should default optionals.
    result = _extract_instance({"InstanceId": "i-empty"})

    assert result["instance_id"] == "i-empty"
    assert result["instance_type"] is None
    # State/Placement default to {} so nested .get() yields None, not KeyError.
    assert result["state"] is None
    assert result["availability_zone"] is None
    assert result["private_ip"] is None
    assert result["public_ip"] is None
    # Missing LaunchTime falls through to str("") == "".
    assert result["launch_time"] == ""
    # No Tags key -> empty dict, never None.
    assert result["tags"] == {}


def test_extract_non_datetime_launch_time_is_stringified():
    # If LaunchTime arrives as a plain string, it should be passed through as-is.
    result = _extract_instance({"InstanceId": "i-str", "LaunchTime": "2026-01-01T00:00:00Z"})
    assert result["launch_time"] == "2026-01-01T00:00:00Z"
