# Tool reference

All tools return JSON-serializable dicts. On AWS API errors, the response
contains `error` (the error code) and `message` (the full error string) instead
of crashing the server.

Paginated calls collect up to `--max-items` results (default: 100) and set
`"truncated": true` when there are more.

---

## EC2

### `list_ec2_instances`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `region` | string | No | Defaults to server startup region |
| `filters` | JSON string | No | boto3 filter format: `[{"Name":"instance-state-name","Values":["running"]}]` |

Returns a list of instances with: `instance_id`, `instance_type`, `state`,
`availability_zone`, `private_ip`, `public_ip`, `launch_time`, `tags`, `image_id`,
`key_name`, `vpc_id`, `subnet_id`.

### `describe_ec2_instance`

| Parameter | Type | Required |
|-----------|------|----------|
| `instance_id` | string | Yes |
| `region` | string | No |

Returns everything from `list_ec2_instances` plus `security_groups`,
`block_devices`, `iam_instance_profile`, and `monitoring`.

### `stop_ec2_instance` (write)

| Parameter | Type | Required |
|-----------|------|----------|
| `instance_id` | string | Yes |
| `confirmation_token` | string | Yes |
| `region` | string | No |

Call `get_stop_confirmation_token(instance_id)` first to get the token.
Requires `--allow-writes`.

### `get_stop_confirmation_token`

| Parameter | Type | Required |
|-----------|------|----------|
| `instance_id` | string | Yes |

Returns the token string to pass to `stop_ec2_instance`.

---

## S3

### `list_s3_buckets`

No parameters. Returns all buckets with name, creation date, and region.

### `get_s3_bucket_policy`

| Parameter | Type | Required |
|-----------|------|----------|
| `bucket_name` | string | Yes |

Returns the parsed policy JSON, or `null` if no policy is attached.

---

## IAM

### `list_iam_users`

No parameters. Returns users with `username`, `arn`, `created`,
`password_last_used`.

### `list_iam_roles`

No parameters. Returns roles with `role_name`, `arn`, `created`, `description`.

### `get_iam_role`

| Parameter | Type | Required |
|-----------|------|----------|
| `role_name` | string | Yes |

Returns full role details including `assume_role_policy` (trust policy) and
`attached_policies`.

---

## CloudWatch Metrics

### `get_cloudwatch_metric`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `namespace` | string | Yes | e.g. `AWS/EC2` |
| `metric_name` | string | Yes | e.g. `CPUUtilization` |
| `dimensions` | JSON string | No | `[{"Name":"InstanceId","Value":"i-abc"}]` |
| `period` | int | No | Seconds, default 300 |
| `statistic` | string | No | Average, Sum, Minimum, Maximum, SampleCount |
| `start_time` | string | Yes | ISO 8601 |
| `end_time` | string | Yes | ISO 8601 |
| `region` | string | No | |

---

## CloudWatch Logs

### `query_cloudwatch_logs`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `log_group` | string | Yes | e.g. `/aws/lambda/my-function` |
| `query` | string | Yes | Logs Insights query string |
| `start_time` | string | Yes | ISO 8601 or Unix timestamp string |
| `end_time` | string | Yes | ISO 8601 or Unix timestamp string |
| `region` | string | No | |

Waits up to 30 seconds for the query to complete. Results capped at
`--max-items` (default 100 records).

---

## EKS

### `list_eks_clusters`

| Parameter | Type | Required |
|-----------|------|----------|
| `region` | string | No |

### `describe_eks_cluster`

| Parameter | Type | Required |
|-----------|------|----------|
| `name` | string | Yes |
| `region` | string | No |

Returns: status, Kubernetes version, endpoint, VPC config, logging config, tags.

---

## Lambda

### `list_lambda_functions`

| Parameter | Type | Required |
|-----------|------|----------|
| `region` | string | No |

Returns: name, runtime, handler, memory, timeout, last modified, execution role.

---

## Cost Explorer

### `get_cost_and_usage`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `start_date` | string | Yes | YYYY-MM-DD |
| `end_date` | string | Yes | YYYY-MM-DD |
| `granularity` | string | No | DAILY, MONTHLY, HOURLY |
| `group_by` | JSON string | No | `[{"Type":"DIMENSION","Key":"SERVICE"}]` |

Uses unblended cost in USD. Always queries us-east-1 (CE is a global service).

---

## CloudFormation

### `list_cloudformation_stacks`

| Parameter | Type | Required |
|-----------|------|----------|
| `region` | string | No |

Excludes deleted stacks.

### `describe_cloudformation_stack`

| Parameter | Type | Required |
|-----------|------|----------|
| `name` | string | Yes |
| `region` | string | No |

Returns: status, parameters, outputs, capabilities, role ARN, tags.

---

## RDS

### `list_rds_instances`

| Parameter | Type | Required |
|-----------|------|----------|
| `region` | string | No |

Returns: identifier, engine, version, status, instance class, storage, multi-AZ,
public accessibility, endpoint, port.

---

## Security Groups

### `describe_security_group`

| Parameter | Type | Required |
|-----------|------|----------|
| `group_id` | string | Yes | e.g. `sg-0abc1234` |
| `region` | string | No | |

Returns inbound and outbound rule lists, each with protocol, port range, CIDR,
and referenced group IDs.

---

## Write tools (require `--allow-writes`)

### `tag_resource`

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `arn` | string | Yes | Any ARN-addressable resource |
| `tags` | JSON string | Yes | `{"key": "value"}` |

Uses the Resource Groups Tagging API, which works across most AWS services.

### `restart_ecs_service`

| Parameter | Type | Required |
|-----------|------|----------|
| `cluster` | string | Yes |
| `service` | string | Yes |
| `confirmation_token` | string | Yes |
| `region` | string | No |

Forces a new deployment (rolling). Call `get_ecs_restart_confirmation_token`
first to get the token.

### `get_ecs_restart_confirmation_token`

| Parameter | Type | Required |
|-----------|------|----------|
| `cluster` | string | Yes |
| `service` | string | Yes |

---

## Resources

Resources are read-only data endpoints that AI clients can access without
calling a tool.

| URI | Description |
|-----|-------------|
| `aws://account/identity` | Current account ID, user ID, and ARN |
| `aws://regions` | All enabled AWS regions |
| `aws://cost/current-month` | Current month's spend by service |
