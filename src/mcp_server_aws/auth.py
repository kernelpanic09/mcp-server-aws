"""AWS session management - thin wrapper around boto3's credential chain."""

from __future__ import annotations

import boto3
from botocore.session import Session as BotocoreSession

from .config import get_config


def get_session(region: str | None = None, profile: str | None = None) -> boto3.Session:
    """Return a boto3 Session, preferring explicit args over global config.

    Credential resolution order (boto3 default chain):
      1. Environment variables (AWS_ACCESS_KEY_ID, etc.)
      2. AWS config file (~/.aws/credentials)
      3. IAM role via IMDS (EC2/ECS/Lambda)
    """
    cfg = get_config()
    return boto3.Session(
        region_name=region or cfg.region,
        profile_name=profile or cfg.profile,
    )


def get_client(service: str, region: str | None = None) -> "boto3.client":
    return get_session(region=region).client(service)
