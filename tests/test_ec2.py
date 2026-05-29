"""Tests for EC2 tools."""

import pytest

from mcp_server_aws.config import Config, set_config
from mcp_server_aws.tools.ec2 import (
    describe_ec2_instance,
    get_stop_confirmation_token,
    list_ec2_instances,
    stop_ec2_instance,
)


def test_list_ec2_instances_empty(aws_mock):
    result = list_ec2_instances()
    assert result["instances"] == []
    assert result["truncated"] is False


def test_list_ec2_instances_returns_instance(running_instance):
    result = list_ec2_instances()
    assert len(result["instances"]) == 1
    inst = result["instances"][0]
    assert inst["instance_id"] == running_instance
    assert inst["instance_type"] == "t3.micro"
    assert inst["state"] == "running"
    assert inst["tags"]["Name"] == "test-box"


def test_list_ec2_instances_filter_by_state(running_instance):
    result = list_ec2_instances(filters=[{"Name": "instance-state-name", "Values": ["stopped"]}])
    assert result["instances"] == []


def test_list_ec2_instances_truncation(ec2_client, aws_mock):
    # Create 5 instances, set max_items to 3 - should truncate.
    ec2_client.run_instances(ImageId="ami-00000000", MinCount=5, MaxCount=5, InstanceType="t2.nano")
    set_config(Config(max_items=3))
    result = list_ec2_instances()
    assert len(result["instances"]) == 3
    assert result["truncated"] is True
    # Restore
    set_config(Config())


def test_describe_ec2_instance(running_instance):
    result = describe_ec2_instance(running_instance)
    assert result["instance_id"] == running_instance
    assert "security_groups" in result
    assert "block_devices" in result


def test_describe_ec2_instance_not_found(aws_mock):
    result = describe_ec2_instance("i-doesnotexist")
    assert "error" in result


def test_stop_requires_writes_disabled(running_instance):
    set_config(Config(allow_writes=False))
    token = get_stop_confirmation_token(running_instance)["confirmation_token"]
    result = stop_ec2_instance(running_instance, token)
    assert result["error"] == "WritesNotEnabled"


def test_stop_with_wrong_token(running_instance):
    set_config(Config(allow_writes=True))
    result = stop_ec2_instance(running_instance, "wrong-token")
    assert result["error"] == "InvalidConfirmationToken"
    set_config(Config())


def test_stop_with_valid_token(running_instance):
    set_config(Config(allow_writes=True))
    token = get_stop_confirmation_token(running_instance)["confirmation_token"]
    result = stop_ec2_instance(running_instance, token)
    assert result["instance_id"] == running_instance
    assert result["previous_state"] == "running"
    set_config(Config())
