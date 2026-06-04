# mcp-server-aws

[![CI](https://github.com/kernelpanic09/mcp-server-aws/actions/workflows/ci.yml/badge.svg)](https://github.com/kernelpanic09/mcp-server-aws/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/kernelpanic09/mcp-server-aws)](LICENSE)
[![Release](https://img.shields.io/github/v/release/kernelpanic09/mcp-server-aws?include_prereleases&sort=semver)](https://github.com/kernelpanic09/mcp-server-aws/releases)
[![Last commit](https://img.shields.io/github/last-commit/kernelpanic09/mcp-server-aws)](https://github.com/kernelpanic09/mcp-server-aws/commits)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple)](https://modelcontextprotocol.io)

An MCP server that lets Claude and other AI clients query AWS resources over stdio.

Connect it to Claude Desktop or Claude Code and you can ask questions like "which
EC2 instances are running in us-west-2?" or "what did I spend on RDS last month?"
without writing any glue code. Everything is read-only by default. Write operations
require an explicit flag at startup and a confirmation token for destructive actions.

---

## Installation

```bash
pip install mcp-server-aws
```

Or with uv:

```bash
uv pip install mcp-server-aws
```

---

## Quick start

Install with uv:

```bash
uv pip install mcp-server-aws
```

Or for local development:

```bash
git clone https://github.com/kernelpanic09/mcp-server-aws
cd mcp-server-aws
uv pip install -e ".[dev]"
```

Make sure AWS credentials are available (env vars, `~/.aws/credentials`, or an
instance role). Then add the server to your AI client.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "aws": {
      "command": "mcp-server-aws",
      "args": []
    }
  }
}
```

### Claude Code

Create or merge into `.claude/mcp.json` in your project:

```json
{
  "mcpServers": {
    "aws": {
      "command": "mcp-server-aws",
      "args": [],
      "env": {
        "AWS_PROFILE": "your-profile"
      }
    }
  }
}
```

### Options

```
mcp-server-aws [--allow-writes] [--region REGION] [--profile PROFILE] [--max-items N]
```

| Flag | Default | Notes |
|------|---------|-------|
| `--allow-writes` | off | Enables tag, stop, and restart tools |
| `--region` | `us-east-1` | Default region for calls that don't specify one |
| `--profile` | boto3 default | AWS credential profile |
| `--max-items` | 100 | Max items per paginated list |

---

## Available tools

### EC2

| Tool | Description |
|------|-------------|
| `list_ec2_instances` | List instances with optional filters |
| `describe_ec2_instance` | Full details for one instance |
| `stop_ec2_instance` | Stop an instance (write, confirmation required) |
| `get_stop_confirmation_token` | Get the token needed to stop an instance |

### S3

| Tool | Description |
|------|-------------|
| `list_s3_buckets` | All buckets with region and creation date |
| `get_s3_bucket_policy` | Bucket policy as parsed JSON |

### IAM

| Tool | Description |
|------|-------------|
| `list_iam_users` | Users with last-login timestamps |
| `list_iam_roles` | All roles |
| `get_iam_role` | Role details with trust policy and attached policies |

### Observability

| Tool | Description |
|------|-------------|
| `get_cloudwatch_metric` | Fetch metric datapoints |
| `query_cloudwatch_logs` | Run a Logs Insights query |

### Compute

| Tool | Description |
|------|-------------|
| `list_eks_clusters` | EKS cluster names in a region |
| `describe_eks_cluster` | Cluster version, endpoint, VPC config |
| `list_lambda_functions` | Functions with runtime and memory |
| `list_rds_instances` | RDS instances with engine and connection info |

### Cost

| Tool | Description |
|------|-------------|
| `get_cost_and_usage` | Cost Explorer query by date range and dimension |

### Networking

| Tool | Description |
|------|-------------|
| `describe_security_group` | Inbound and outbound rules for a security group |

### CloudFormation

| Tool | Description |
|------|-------------|
| `list_cloudformation_stacks` | Active stacks (excludes deleted) |
| `describe_cloudformation_stack` | Stack with outputs and parameters |

### Write tools (require `--allow-writes`)

| Tool | Description |
|------|-------------|
| `tag_resource` | Add or update tags on any ARN-addressable resource |
| `restart_ecs_service` | Force a new ECS service deployment |
| `get_ecs_restart_confirmation_token` | Get the token needed to restart a service |

### Resources

| URI | Description |
|-----|-------------|
| `aws://account/identity` | Account ID and caller identity |
| `aws://regions` | All enabled regions |
| `aws://cost/current-month` | Current month's spend by service |

---

## Safety

The server is read-only by default. All write tools check the `--allow-writes`
flag at call time and return a structured error if it's not set. No credentials
are ever logged or returned in tool output.

Destructive operations (stopping instances, restarting services) require a
confirmation token. The token encodes the operation and target, so you can't
reuse a token across different resources.

Every tool call writes a structured JSON audit line to stderr:

```json
{"ts": "2024-01-15T10:23:45+00:00", "tool": "list_ec2_instances", "params": {"region": "us-east-1"}, "result": "12 instances"}
```

See [docs/safety.md](docs/safety.md) for the IAM policy recommendation and full
security model.

---

## Example prompts

Once connected:

- "Find me all EC2 instances tagged env=prod that are stopped."
- "What's the most expensive AWS service this month?"
- "Show me IAM users who haven't logged in since January."
- "Are any RDS instances publicly accessible?"
- "Search /aws/lambda/my-function logs for errors in the last hour."
- "List all CloudFormation stacks in eu-west-1 that are in ROLLBACK state."
- "Describe the trust policy for the EKS node role. Does anything look off?"
- "What security groups allow inbound SSH from 0.0.0.0/0?"

---

## IAM policy

Minimal read-only policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
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

---

## Development

```bash
# Install dev dependencies
make install

# Run tests
make test

# Format and lint
make fmt
make lint

# Type check
make typecheck

# Run the server locally
make run
make run-with-writes
```

Tests use [moto](https://github.com/getmoto/moto) for AWS mocking - no real
AWS account needed.

---

## Roadmap

Features worth adding:

- **Secrets Manager**: read secret metadata (not values) and rotation status
- **KMS**: list keys, key policies, key rotation status
- **Route 53**: list hosted zones and records
- **VPC**: describe VPCs, subnets, route tables
- **SSM Parameter Store**: read parameters by path (non-SecureString only)
- **ECS**: list clusters, services, tasks
- **ECR**: list repositories and image tags
- **Step Functions**: list and describe state machines
- **SNS/SQS**: list topics/queues, queue depth
- **Config**: query AWS Config rules and compliance state
- **Trusted Advisor**: read advisor findings
- **Multi-account**: assume-role support for querying member accounts in an org

---

## Related Projects

- [agents-platform](https://github.com/kernelpanic09/agents-platform) - an AI agent orchestration platform that can consume MCP servers like this one to give agents tool access to infrastructure without granting them broad shell permissions.
- [terraform-aws-modules](https://github.com/kernelpanic09/terraform-aws-modules) - includes an `iam-roles` module that can provision the read-only IAM role this server needs, with permission boundaries and the right trust policy already wired in.

---

## License

MIT. See [LICENSE](LICENSE).
