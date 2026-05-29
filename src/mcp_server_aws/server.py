"""MCP server entry point - registers all tools and resources."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

from .auth import get_client
from .config import get_config
from .safety import (
    InvalidConfirmationTokenError,
    WritesNotEnabledError,
    make_confirmation_token,
    require_writes,
    verify_confirmation_token,
)
from .tools import (
    cloudformation,
    cloudwatch,
    cost,
    ec2,
    eks,
    iam,
    lambda_,
    logs,
    rds,
    s3,
    security_groups,
)

mcp = FastMCP("mcp-server-aws")


# ---------------------------------------------------------------------------
# Logging helper - structured JSON to stderr so it doesn't pollute stdio MCP.
# ---------------------------------------------------------------------------

def _log(tool: str, params: dict[str, Any], result_summary: str) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "params": params,
        "result": result_summary,
    }
    print(json.dumps(entry), file=sys.stderr)


# ---------------------------------------------------------------------------
# EC2
# ---------------------------------------------------------------------------

@mcp.tool()
def list_ec2_instances(
    region: str = "",
    filters: str = "[]",
) -> dict[str, Any]:
    """List EC2 instances. filters is a JSON string: '[{"Name":"instance-state-name","Values":["running"]}]'"""
    parsed_filters = json.loads(filters) if filters and filters != "[]" else None
    r = region or None
    result = ec2.list_ec2_instances(region=r, filters=parsed_filters)
    _log("list_ec2_instances", {"region": region}, f"{len(result.get('instances', []))} instances")
    return result


@mcp.tool()
def describe_ec2_instance(instance_id: str, region: str = "") -> dict[str, Any]:
    """Return full details for a single EC2 instance."""
    result = ec2.describe_ec2_instance(instance_id, region=region or None)
    _log("describe_ec2_instance", {"instance_id": instance_id}, "ok" if "error" not in result else result["error"])
    return result


@mcp.tool()
def get_stop_confirmation_token(instance_id: str) -> dict[str, Any]:
    """Get the confirmation token required before calling stop_ec2_instance."""
    return ec2.get_stop_confirmation_token(instance_id)


@mcp.tool()
def stop_ec2_instance(
    instance_id: str,
    confirmation_token: str,
    region: str = "",
) -> dict[str, Any]:
    """Stop a running EC2 instance. Requires --allow-writes and a valid confirmation_token from get_stop_confirmation_token."""
    result = ec2.stop_ec2_instance(instance_id, confirmation_token, region=region or None)
    _log("stop_ec2_instance", {"instance_id": instance_id}, "ok" if "error" not in result else result["error"])
    return result


# ---------------------------------------------------------------------------
# S3
# ---------------------------------------------------------------------------

@mcp.tool()
def list_s3_buckets() -> dict[str, Any]:
    """List all S3 buckets in the account."""
    result = s3.list_s3_buckets()
    _log("list_s3_buckets", {}, f"{result.get('count', 0)} buckets")
    return result


@mcp.tool()
def get_s3_bucket_policy(bucket_name: str) -> dict[str, Any]:
    """Return the resource-based policy for an S3 bucket."""
    result = s3.get_s3_bucket_policy(bucket_name)
    _log("get_s3_bucket_policy", {"bucket": bucket_name}, "ok" if "error" not in result else result["error"])
    return result


# ---------------------------------------------------------------------------
# IAM
# ---------------------------------------------------------------------------

@mcp.tool()
def list_iam_users() -> dict[str, Any]:
    """List all IAM users with last-used timestamps."""
    result = iam.list_iam_users()
    _log("list_iam_users", {}, f"{len(result.get('users', []))} users")
    return result


@mcp.tool()
def list_iam_roles() -> dict[str, Any]:
    """List all IAM roles."""
    result = iam.list_iam_roles()
    _log("list_iam_roles", {}, f"{len(result.get('roles', []))} roles")
    return result


@mcp.tool()
def get_iam_role(role_name: str) -> dict[str, Any]:
    """Return full details for an IAM role including attached policies and trust policy."""
    result = iam.get_iam_role(role_name)
    _log("get_iam_role", {"role_name": role_name}, "ok" if "error" not in result else result["error"])
    return result


# ---------------------------------------------------------------------------
# CloudWatch
# ---------------------------------------------------------------------------

@mcp.tool()
def get_cloudwatch_metric(
    namespace: str,
    metric_name: str,
    dimensions: str = "[]",
    period: int = 300,
    statistic: str = "Average",
    start_time: str = "",
    end_time: str = "",
    region: str = "",
) -> dict[str, Any]:
    """Fetch CloudWatch metric datapoints.
    dimensions: JSON string e.g. '[{"Name":"InstanceId","Value":"i-abc"}]'
    statistic: Average | Sum | Minimum | Maximum | SampleCount
    """
    dims = json.loads(dimensions) if dimensions and dimensions != "[]" else []
    result = cloudwatch.get_cloudwatch_metric(
        namespace=namespace,
        metric_name=metric_name,
        dimensions=dims,
        period=period,
        statistic=statistic,
        start_time=start_time,
        end_time=end_time,
        region=region or None,
    )
    _log("get_cloudwatch_metric", {"namespace": namespace, "metric": metric_name}, "ok" if "error" not in result else result["error"])
    return result


# ---------------------------------------------------------------------------
# CloudWatch Logs
# ---------------------------------------------------------------------------

@mcp.tool()
def query_cloudwatch_logs(
    log_group: str,
    query: str,
    start_time: str,
    end_time: str,
    region: str = "",
) -> dict[str, Any]:
    """Run a Logs Insights query. start_time/end_time: ISO 8601 or Unix timestamp strings."""
    result = logs.query_cloudwatch_logs(
        log_group=log_group,
        query=query,
        start_time=start_time,
        end_time=end_time,
        region=region or None,
    )
    _log("query_cloudwatch_logs", {"log_group": log_group}, f"{len(result.get('records', []))} records" if "error" not in result else result["error"])
    return result


# ---------------------------------------------------------------------------
# EKS
# ---------------------------------------------------------------------------

@mcp.tool()
def list_eks_clusters(region: str = "") -> dict[str, Any]:
    """List all EKS cluster names in a region."""
    result = eks.list_eks_clusters(region=region or None)
    _log("list_eks_clusters", {"region": region}, f"{len(result.get('clusters', []))} clusters")
    return result


@mcp.tool()
def describe_eks_cluster(name: str, region: str = "") -> dict[str, Any]:
    """Return full details for an EKS cluster."""
    result = eks.describe_eks_cluster(name, region=region or None)
    _log("describe_eks_cluster", {"name": name}, "ok" if "error" not in result else result["error"])
    return result


# ---------------------------------------------------------------------------
# Lambda
# ---------------------------------------------------------------------------

@mcp.tool()
def list_lambda_functions(region: str = "") -> dict[str, Any]:
    """List all Lambda functions with runtime and memory details."""
    result = lambda_.list_lambda_functions(region=region or None)
    _log("list_lambda_functions", {"region": region}, f"{len(result.get('functions', []))} functions")
    return result


# ---------------------------------------------------------------------------
# Cost Explorer
# ---------------------------------------------------------------------------

@mcp.tool()
def get_cost_and_usage(
    start_date: str,
    end_date: str,
    granularity: str = "MONTHLY",
    group_by: str = "",
) -> dict[str, Any]:
    """Query Cost Explorer. Dates: YYYY-MM-DD. granularity: DAILY|MONTHLY|HOURLY.
    group_by: JSON string e.g. '[{"Type":"DIMENSION","Key":"SERVICE"}]'
    """
    gb = json.loads(group_by) if group_by else None
    result = cost.get_cost_and_usage(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
        group_by=gb,
    )
    _log("get_cost_and_usage", {"start": start_date, "end": end_date}, "ok" if "error" not in result else result["error"])
    return result


# ---------------------------------------------------------------------------
# CloudFormation
# ---------------------------------------------------------------------------

@mcp.tool()
def list_cloudformation_stacks(region: str = "") -> dict[str, Any]:
    """List all active CloudFormation stacks in a region."""
    result = cloudformation.list_cloudformation_stacks(region=region or None)
    _log("list_cloudformation_stacks", {"region": region}, f"{len(result.get('stacks', []))} stacks")
    return result


@mcp.tool()
def describe_cloudformation_stack(name: str, region: str = "") -> dict[str, Any]:
    """Return full details for a CloudFormation stack including outputs and parameters."""
    result = cloudformation.describe_cloudformation_stack(name, region=region or None)
    _log("describe_cloudformation_stack", {"name": name}, "ok" if "error" not in result else result["error"])
    return result


# ---------------------------------------------------------------------------
# RDS
# ---------------------------------------------------------------------------

@mcp.tool()
def list_rds_instances(region: str = "") -> dict[str, Any]:
    """List RDS DB instances with engine, status, and connection info."""
    result = rds.list_rds_instances(region=region or None)
    _log("list_rds_instances", {"region": region}, f"{len(result.get('instances', []))} instances")
    return result


# ---------------------------------------------------------------------------
# Security Groups
# ---------------------------------------------------------------------------

@mcp.tool()
def describe_security_group(group_id: str, region: str = "") -> dict[str, Any]:
    """Return inbound and outbound rules for a VPC security group."""
    result = security_groups.describe_security_group(group_id, region=region or None)
    _log("describe_security_group", {"group_id": group_id}, "ok" if "error" not in result else result["error"])
    return result


# ---------------------------------------------------------------------------
# Write tools: tagging and ECS service restart
# ---------------------------------------------------------------------------

@mcp.tool()
def tag_resource(arn: str, tags: str) -> dict[str, Any]:
    """Add or update tags on any ARN-addressable AWS resource.
    tags: JSON string e.g. '{"env":"prod","owner":"alice"}'
    Requires --allow-writes.
    """
    try:
        require_writes()
    except WritesNotEnabledError as e:
        return {"error": "WritesNotEnabled", "message": str(e)}

    parsed_tags = json.loads(tags)
    tag_list = [{"Key": k, "Value": v} for k, v in parsed_tags.items()]

    # Tag via the Resource Groups Tagging API which works across most services.
    client = get_client("resourcegroupstaggingapi")
    try:
        client.tag_resources(ResourceARNList=[arn], Tags=parsed_tags)
        _log("tag_resource", {"arn": arn}, "ok")
        return {"arn": arn, "tags_applied": parsed_tags}
    except Exception as e:
        return {"error": type(e).__name__, "message": str(e)}


@mcp.tool()
def restart_ecs_service(
    cluster: str,
    service: str,
    confirmation_token: str,
    region: str = "",
) -> dict[str, Any]:
    """Force a new deployment on an ECS service (rolling restart).
    Get confirmation_token from get_ecs_restart_confirmation_token first.
    Requires --allow-writes.
    """
    try:
        require_writes()
        verify_confirmation_token(
            "restart_ecs", {"cluster": cluster, "service": service}, confirmation_token
        )
    except WritesNotEnabledError as e:
        return {"error": "WritesNotEnabled", "message": str(e)}
    except InvalidConfirmationTokenError as e:
        return {"error": "InvalidConfirmationToken", "message": str(e)}

    client = get_client("ecs", region or None)
    try:
        resp = client.update_service(
            cluster=cluster,
            service=service,
            forceNewDeployment=True,
        )
        svc = resp.get("service", {})
        _log("restart_ecs_service", {"cluster": cluster, "service": service}, "ok")
        return {
            "cluster": cluster,
            "service": service,
            "status": svc.get("status"),
            "running_count": svc.get("runningCount"),
            "desired_count": svc.get("desiredCount"),
        }
    except Exception as e:
        return {"error": type(e).__name__, "message": str(e)}


@mcp.tool()
def get_ecs_restart_confirmation_token(cluster: str, service: str) -> dict[str, str]:
    """Get the confirmation token needed before calling restart_ecs_service."""
    token = make_confirmation_token("restart_ecs", {"cluster": cluster, "service": service})
    return {
        "confirmation_token": token,
        "instruction": f"Pass this as confirmation_token to restart_ecs_service('{cluster}', '{service}', ...)",
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("aws://account/identity")
def account_identity() -> str:
    """Current account ID and caller identity."""
    client = get_client("sts")
    try:
        resp = client.get_caller_identity()
        data = {
            "account_id": resp.get("Account"),
            "user_id": resp.get("UserId"),
            "arn": resp.get("Arn"),
        }
    except Exception as e:
        data = {"error": str(e)}
    return json.dumps(data, indent=2)


@mcp.resource("aws://regions")
def aws_regions() -> str:
    """All AWS regions available to this account."""
    client = get_client("ec2")
    try:
        resp = client.describe_regions(AllRegions=False)
        regions = sorted(r["RegionName"] for r in resp.get("Regions", []))
    except Exception as e:
        regions = []
    return json.dumps({"regions": regions}, indent=2)


@mcp.resource("aws://cost/current-month")
def current_month_cost() -> str:
    """Spend so far this calendar month, broken down by service."""
    from datetime import date

    today = date.today()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()

    result = cost.get_cost_and_usage(
        start_date=start,
        end_date=end,
        granularity="MONTHLY",
        group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    return json.dumps(result, indent=2)
