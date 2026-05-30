"""Tests for S3 tools."""

import json

from mcp_server_aws.tools.s3 import get_s3_bucket_policy, list_s3_buckets


def test_list_s3_buckets_empty(aws_mock):
    result = list_s3_buckets()
    assert result["buckets"] == []
    assert result["count"] == 0


def test_list_s3_buckets_returns_bucket(s3_client, aws_mock):
    s3_client.create_bucket(Bucket="my-test-bucket")
    result = list_s3_buckets()
    assert result["count"] == 1
    assert result["buckets"][0]["name"] == "my-test-bucket"


def test_list_s3_multiple_buckets(s3_client, aws_mock):
    for name in ["alpha", "beta", "gamma"]:
        s3_client.create_bucket(Bucket=name)
    result = list_s3_buckets()
    names = {b["name"] for b in result["buckets"]}
    assert names == {"alpha", "beta", "gamma"}


def test_get_bucket_policy_no_policy(s3_client, aws_mock):
    s3_client.create_bucket(Bucket="plain-bucket")
    result = get_s3_bucket_policy("plain-bucket")
    assert result["policy"] is None
    assert "No policy" in result["message"]


def test_get_bucket_policy_with_policy(s3_client, aws_mock):
    s3_client.create_bucket(Bucket="policy-bucket")
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::policy-bucket/*",
            }
        ],
    }
    s3_client.put_bucket_policy(Bucket="policy-bucket", Policy=json.dumps(policy))
    result = get_s3_bucket_policy("policy-bucket")
    assert result["policy"]["Version"] == "2012-10-17"
    assert result["policy"]["Statement"][0]["Effect"] == "Allow"


def test_get_bucket_policy_nonexistent_bucket(aws_mock):
    result = get_s3_bucket_policy("no-such-bucket")
    assert "error" in result
