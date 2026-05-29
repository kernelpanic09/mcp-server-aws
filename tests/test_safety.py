"""Tests for the safety module: write gating and confirmation tokens."""

import pytest

from mcp_server_aws.config import Config, set_config
from mcp_server_aws.safety import (
    InvalidConfirmationTokenError,
    WritesNotEnabledError,
    make_confirmation_token,
    require_writes,
    verify_confirmation_token,
)


def test_require_writes_raises_when_disabled():
    set_config(Config(allow_writes=False))
    with pytest.raises(WritesNotEnabledError):
        require_writes()


def test_require_writes_passes_when_enabled():
    set_config(Config(allow_writes=True))
    require_writes()  # Should not raise
    set_config(Config())


def test_confirmation_token_format():
    token = make_confirmation_token("stop_ec2", {"instance_id": "i-abc"})
    assert token.startswith("confirm-stop_ec2-")
    assert len(token) > 20


def test_confirmation_token_is_deterministic():
    params = {"instance_id": "i-abc123"}
    t1 = make_confirmation_token("stop_ec2", params)
    t2 = make_confirmation_token("stop_ec2", params)
    assert t1 == t2


def test_confirmation_token_differs_by_params():
    t1 = make_confirmation_token("stop_ec2", {"instance_id": "i-aaa"})
    t2 = make_confirmation_token("stop_ec2", {"instance_id": "i-bbb"})
    assert t1 != t2


def test_confirmation_token_differs_by_operation():
    params = {"cluster": "prod", "service": "api"}
    t1 = make_confirmation_token("restart_ecs", params)
    t2 = make_confirmation_token("delete_ecs", params)
    assert t1 != t2


def test_verify_token_passes():
    params = {"instance_id": "i-abc"}
    token = make_confirmation_token("stop_ec2", params)
    verify_confirmation_token("stop_ec2", params, token)  # Should not raise


def test_verify_token_fails_wrong_token():
    params = {"instance_id": "i-abc"}
    with pytest.raises(InvalidConfirmationTokenError):
        verify_confirmation_token("stop_ec2", params, "confirm-stop_ec2-deadbeef00000000")


def test_verify_token_fails_wrong_instance():
    token = make_confirmation_token("stop_ec2", {"instance_id": "i-aaa"})
    with pytest.raises(InvalidConfirmationTokenError):
        # Token for i-aaa should not work for i-bbb
        verify_confirmation_token("stop_ec2", {"instance_id": "i-bbb"}, token)
