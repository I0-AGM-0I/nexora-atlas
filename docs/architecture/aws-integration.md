# AWS Integration Architecture - NEXORA ATLAS

## 1. Architectural Role
The AWS Integration layer is responsible for authenticating, fetching, and normalizing cloud billing data from Amazon Web Services into the ATLAS data model.

## 2. Core Principles
- **Read-Only Least Privilege**: ATLAS requires strictly read-only IAM permissions (`ce:GetCostAndUsage`, `ce:GetDimensionValues`, `organizations:ListAccounts`, `ec2:DescribeInstances`). No destructive, modifying, or launching actions are permitted.
- **Provider Abstraction**: All AWS SDK (`boto3`) calls are encapsulated behind the `CloudProvider` interface in `apps/api/app/integrations/aws/`. Route handlers never directly import `boto3`.
- **API Boundaries**:
  - `POST /api/v1/integrations/aws/test`: Validates IAM credentials and returns `CONNECTED` or `FAILED` with diagnostics.
  - `POST /api/v1/integrations/aws/sync`: Dispatches a background `SyncJob` to pull daily/monthly cost and usage data.
  - `GET /api/v1/sync/jobs`: Queries sync status and history.
- **Robustness**: Implements exponential backoff, rate limiting handling for AWS Cost Explorer limits, and deterministic pagination.
- **Zero Secret Commits**: Credentials are provided exclusively via environment variables or encrypted secrets, never returned in API payloads or logged.
