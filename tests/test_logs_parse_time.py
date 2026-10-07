"""Unit tests for the pure _parse_time helper in the logs tool.

These exercise the start_time/end_time parsing directly (no AWS/moto),
covering the Unix-timestamp branch, the ISO-8601 branch, and the 'Z' suffix
shorthand that datetime.fromisoformat doesn't accept on its own.
"""

from mcp_server_aws.tools.logs import _parse_time


def test_parse_unix_timestamp_string():
    assert _parse_time("1700000000") == 1700000000


def test_parse_iso_string_with_utc_offset():
    assert _parse_time("2023-11-14T22:13:20+00:00") == 1700000000


def test_parse_iso_string_with_z_suffix():
    # 'Z' is shorthand for +00:00 and must be rewritten before fromisoformat.
    assert _parse_time("2023-11-14T22:13:20Z") == 1700000000


def test_parse_negative_unix_timestamp_string():
    # A leading '-' is valid int() input, so pre-epoch timestamps take the
    # fast path rather than falling through to ISO parsing.
    assert _parse_time("-1") == -1
