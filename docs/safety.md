# Safety model

## Read-only by default

The server starts in read-only mode. Every write tool checks this at call time
and returns an error without touching AWS:

```
{"error": "WritesNotEnabled", "message": "Write operations are disabled. Start the server with --allow-writes to enable them."}
```

To enable writes, start with:

```bash
mcp-server-aws --allow-writes
```

Consider whether you actually need this. Most day-to-day AI-assisted work
(auditing, troubleshooting, cost analysis) doesn't require it.

## Confirmation tokens for destructive operations

Stopping an instance or restarting a service is irreversible in the short term.
These tools require a two-step process:

1. Call the corresponding `get_*_confirmation_token` tool to get a token.
2. Pass that token as `confirmation_token` in the destructive call.

Tokens are HMAC-style digests derived from the operation name and parameters.
A token for `stop i-abc` cannot be reused for `stop i-xyz`.

```python
# The token encodes what it authorizes.
token = make_confirmation_token("stop_ec2", {"instance_id": "i-abc"})
# "confirm-stop_ec2-a3f2b1c4d5e6f789"
```

## Audit logging

Every tool call writes a structured JSON line to stderr:

```json
{"ts": "2024-01-15T10:23:45+00:00", "tool": "list_ec2_instances", "params": {"region": "us-east-1"}, "result": "12 instances"}
```

Pipe stderr to a file or log aggregator in production. The MCP stdio transport
uses stdout for the protocol, so stderr is safe for logging.

## Sensitive field handling

The tools never return secrets, even if they appear in tag values or environment
variables. If you tag a resource with `ApiKey=abc123`, that will appear in tag
outputs. Don't store secrets in tags.

IAM key material (secret access keys) is never accessible through any of the
tools here. The IAM tools only read user metadata and role configurations, not
credentials.

## IAM policy recommendations

The server only needs read permissions for its read-only tools. Attach a policy
like this to the IAM role or user running the server:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MCPServerReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeRegions",
        "ec2:DescribeSecurityGroups",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketPolicy",
        "iam:ListUsers",
        "iam:ListRoles",
        "iam:GetRole",
        "iam:ListAttachedRolePolicies",
        "logs:StartQuery",
        "logs:GetQueryResults",
        "cloudwatch:GetMetricStatistics",
        "eks:ListClusters",
        "eks:DescribeCluster",
        "lambda:ListFunctions",
        "ce:GetCostAndUsage",
        "cloudformation:ListStacks",
        "cloudformation:DescribeStacks",
        "rds:DescribeDBInstances",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

If you enable `--allow-writes`, add:

```json
{
  "Sid": "MCPServerWrites",
  "Effect": "Allow",
  "Action": [
    "ec2:StopInstances",
    "ecs:UpdateService",
    "tag:TagResources"
  ],
  "Resource": "*"
}
```

Consider scoping the write statement to specific resource ARNs if you want to
limit which instances or services the server can touch.

## Network considerations

The server runs as a local process over stdio. It doesn't open any ports. AWS
API calls go out over HTTPS to the standard AWS endpoints. If you're running
in a VPC with no internet gateway, you'll need VPC endpoints for the services
you want to query.

## Credential chain

The server doesn't handle credentials directly. It calls `boto3.Session()` and
lets boto3 resolve credentials in this order:

1. `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables
2. `~/.aws/credentials` file (profile selected via `--profile` or `AWS_PROFILE`)
3. IAM role via IMDS (works on EC2, ECS, Lambda automatically)

The `--profile` flag or `AWS_PROFILE` env var selects which profile to use.
Running the server on an EC2 instance with an attached IAM role is the cleanest
setup for a always-on deployment.
