# Example prompts

These work once the MCP server is connected to Claude Desktop or Claude Code.

## Cost analysis

```
What did I spend on AWS last month? Break it down by service.
```

```
Which EC2 instances are costing the most? Compare their instance types.
```

```
Show me the daily spend trend for the last two weeks.
```

## EC2 and compute

```
List all running EC2 instances in us-west-2 and tell me which ones don't have a Name tag.
```

```
Find EC2 instances tagged env=prod that are stopped. Why might they be stopped?
```

```
What's the CPU utilization on instance i-0abc1234 over the last hour?
```

## IAM and security

```
List IAM users who haven't logged in since January. Flag any that have admin policies attached.
```

```
Show me the trust policy for the EKS node role. Does it look correct?
```

```
Which IAM roles have wildcard (*) in their attached policies?
```

## Logs and observability

```
Search /aws/lambda/my-function logs for ERROR in the last 24 hours.
```

```
Run this Logs Insights query on /aws/ecs/my-service for the past hour:
fields @timestamp, @message | filter @message like /exception/ | limit 50
```

## Infrastructure review

```
List all CloudFormation stacks in eu-west-1 and tell me which ones are in ROLLBACK state.
```

```
Describe the my-prod-cluster EKS cluster. What Kubernetes version is it running?
```

```
Are any of my RDS instances publicly accessible? List them.
```

## Security groups

```
Show me the inbound rules for sg-0abc123. Is port 22 open to 0.0.0.0/0?
```

## Write operations (requires --allow-writes)

Write operations require starting the server with `--allow-writes`. The server
also requires a confirmation token for destructive actions - Claude will walk
you through getting the token first.

```
Stop instance i-0deadbeef. Walk me through the confirmation process.
```

```
Tag all instances in the staging VPC with cost-center=engineering.
```

```
Force a new deployment on the api service in the prod ECS cluster.
```
