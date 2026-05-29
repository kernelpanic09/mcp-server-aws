"""Shared pytest fixtures using moto for AWS service mocking."""

import os

import boto3
import pytest
from moto import mock_aws

# Point boto3 at fake credentials so moto doesn't complain.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def aws_mock():
    """Start the moto mock context for all AWS services."""
    with mock_aws():
        yield


@pytest.fixture
def ec2_client(aws_mock):
    return boto3.client("ec2", region_name="us-east-1")


@pytest.fixture
def s3_client(aws_mock):
    return boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def iam_client(aws_mock):
    return boto3.client("iam", region_name="us-east-1")


@pytest.fixture
def running_instance(ec2_client):
    """Create a single running EC2 instance and return its ID."""
    resp = ec2_client.run_instances(
        ImageId="ami-00000000",
        MinCount=1,
        MaxCount=1,
        InstanceType="t3.micro",
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": "test-box"}, {"Key": "env", "Value": "staging"}],
            }
        ],
    )
    return resp["Instances"][0]["InstanceId"]
