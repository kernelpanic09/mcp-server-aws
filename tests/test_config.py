"""Unit tests for parse_args — pure CLI/env-var parsing, no AWS calls needed."""

from __future__ import annotations

from mcp_server_aws.config import Config, parse_args


def test_defaults_no_env(monkeypatch):
    # Remove env vars so we see the hard-coded fallback values.
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    assert parse_args([]) == Config(
        allow_writes=False,
        region="us-east-1",
        profile=None,
        max_items=100,
        max_log_lines=100,
    )


def test_allow_writes_flag():
    cfg = parse_args(["--allow-writes"])
    assert cfg.allow_writes is True


def test_allow_writes_off_by_default():
    assert parse_args([]).allow_writes is False


def test_region_cli_flag():
    assert parse_args(["--region", "eu-west-1"]).region == "eu-west-1"


def test_region_from_env(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    assert parse_args([]).region == "ap-southeast-1"


def test_cli_region_overrides_env(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    assert parse_args(["--region", "us-west-2"]).region == "us-west-2"


def test_profile_cli_flag():
    assert parse_args(["--profile", "dev"]).profile == "dev"


def test_profile_from_env(monkeypatch):
    monkeypatch.setenv("AWS_PROFILE", "staging")
    assert parse_args([]).profile == "staging"


def test_max_items():
    assert parse_args(["--max-items", "50"]).max_items == 50


def test_max_log_lines():
    assert parse_args(["--max-log-lines", "200"]).max_log_lines == 200
