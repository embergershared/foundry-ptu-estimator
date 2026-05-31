# Azure deployment details

This file records the non-secret Azure deployment details for the `tpu-est-dep` environment.

## Subscription and environment

| Item | Value |
|---|---|
| Subscription ID | `4c88693f-5cc9-4f30-9d1e-d58d4221cf25` |
| Azure location | `swedencentral` |
| azd environment | `tpu-est-dep` |
| Application resource group | `rg-tpu-est-dep` |
| Existing Foundry resource group | `rg-swc-s3-ai-msfoundry-demo-02` |
| Model deployment | `gpt-5.4` |
| Foundry endpoint | `https://zava-shopping-agent-resource.openai.azure.com/openai/v1` |
| GitHub OIDC app registration | `github-foundry-tpu-estimator-tpu-est-dep` |
| GitHub OIDC client ID | `b6123d3c-fad8-413a-8a33-81b1391499ec` |
| Tenant ID | `c4c9004b-43cc-4303-bfbf-0a5f7e1d0139` |

## Portal links

| Resource | Type | Portal link |
|---|---|---|
| `rg-tpu-est-dep` | Resource group | [Open](https://portal.azure.com/#@/resource/subscriptions/4c88693f-5cc9-4f30-9d1e-d58d4221cf25/resourceGroups/rg-tpu-est-dep/overview) |
| `rg-swc-s3-ai-msfoundry-demo-02` | Foundry resource group | [Open](https://portal.azure.com/#@/resource/subscriptions/4c88693f-5cc9-4f30-9d1e-d58d4221cf25/resourceGroups/rg-swc-s3-ai-msfoundry-demo-02/overview) |
| `caj-tpu-est-dep` | Container Apps Job | [Open](https://portal.azure.com/#@/resource/subscriptions/4c88693f-5cc9-4f30-9d1e-d58d4221cf25/resourceGroups/rg-tpu-est-dep/providers/Microsoft.App/jobs/caj-tpu-est-dep/overview) |
| `cae-tpu-est-dep` | Container Apps environment | [Open](https://portal.azure.com/#@/resource/subscriptions/4c88693f-5cc9-4f30-9d1e-d58d4221cf25/resourceGroups/rg-tpu-est-dep/providers/Microsoft.App/managedEnvironments/cae-tpu-est-dep/overview) |
| `crl774tzpe76sw6` | Azure Container Registry | [Open](https://portal.azure.com/#@/resource/subscriptions/4c88693f-5cc9-4f30-9d1e-d58d4221cf25/resourceGroups/rg-tpu-est-dep/providers/Microsoft.ContainerRegistry/registries/crl774tzpe76sw6/overview) |
| `id-tpu-est-dep` | User-assigned managed identity | [Open](https://portal.azure.com/#@/resource/subscriptions/4c88693f-5cc9-4f30-9d1e-d58d4221cf25/resourceGroups/rg-tpu-est-dep/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-tpu-est-dep/overview) |
| `log-tpu-est-dep` | Log Analytics workspace | [Open](https://portal.azure.com/#@/resource/subscriptions/4c88693f-5cc9-4f30-9d1e-d58d4221cf25/resourceGroups/rg-tpu-est-dep/providers/Microsoft.OperationalInsights/workspaces/log-tpu-est-dep/overview) |
| `stl774tzpe76sw6` | Storage account | [Open](https://portal.azure.com/#@/resource/subscriptions/4c88693f-5cc9-4f30-9d1e-d58d4221cf25/resourceGroups/rg-tpu-est-dep/providers/Microsoft.Storage/storageAccounts/stl774tzpe76sw6/overview) |
| `zava-shopping-agent-resource` | Existing Foundry AI Services account | [Open](https://portal.azure.com/#@/resource/subscriptions/4c88693f-5cc9-4f30-9d1e-d58d4221cf25/resourceGroups/rg-swc-s3-ai-msfoundry-demo-02/providers/Microsoft.CognitiveServices/accounts/zava-shopping-agent-resource/overview) |

## Application resources

| Name | Type | Resource group | Location |
|---|---|---|---|
| `caj-tpu-est-dep` | `Microsoft.App/jobs` | `rg-tpu-est-dep` | `swedencentral` |
| `cae-tpu-est-dep` | `Microsoft.App/managedEnvironments` | `rg-tpu-est-dep` | `swedencentral` |
| `crl774tzpe76sw6` | `Microsoft.ContainerRegistry/registries` | `rg-tpu-est-dep` | `swedencentral` |
| `id-tpu-est-dep` | `Microsoft.ManagedIdentity/userAssignedIdentities` | `rg-tpu-est-dep` | `swedencentral` |
| `log-tpu-est-dep` | `Microsoft.OperationalInsights/workspaces` | `rg-tpu-est-dep` | `swedencentral` |
| `stl774tzpe76sw6` | `Microsoft.Storage/storageAccounts` | `rg-tpu-est-dep` | `swedencentral` |

## Existing Foundry resource

| Name | Type | Kind | Resource group | Location |
|---|---|---|---|---|
| `zava-shopping-agent-resource` | `Microsoft.CognitiveServices/accounts` | `AIServices` | `rg-swc-s3-ai-msfoundry-demo-02` | `swedencentral` |

## Deployment settings

| Setting | Value |
|---|---|
| Container image | `crl774tzpe76sw6.azurecr.io/worker:latest` |
| Job schedule | `*/3 * * * *` |
| Parallelism | `1` |
| Replica retry limit | `0` |
| `MIN_TOKENS` | `30000` |
| `MAX_TOKENS` | `700000` |
| `MAX_JITTER_SECONDS` | `179` |
| `AUTH_RETRY_SECONDS` | `60` |
| `API_VERSION` | `2025-05-01` |
| `LOG_LEVEL` | `INFO` |

## Identity and diagnostics

- The Container Apps Job uses user-assigned managed identity `id-tpu-est-dep`.
- `id-tpu-est-dep` has `AcrPull` on `crl774tzpe76sw6`.
- `id-tpu-est-dep` has `Cognitive Services User` on `zava-shopping-agent-resource`.
- GitHub Actions OIDC uses app registration `github-foundry-tpu-estimator-tpu-est-dep`.
- The OIDC federated credential subject is `repo:embergershared/foundry-tpu-estimator:environment:tpu-est-dep`.
- Foundry diagnostic setting `foundry-tpu-est-diag` sends `allLogs`, `audit`, and `AllMetrics` to:
  - Log Analytics workspace `log-tpu-est-dep`
  - Storage account `stl774tzpe76sw6`

## GitHub repository configuration still needed

GitHub CLI is not installed in this environment, so repository secrets and variables were not set automatically.
Configure these in GitHub before running the deploy workflow:

| Type | Name | Value |
|---|---|---|
| Secret | `AZURE_CLIENT_ID` | `b6123d3c-fad8-413a-8a33-81b1391499ec` |
| Secret | `AZURE_TENANT_ID` | `c4c9004b-43cc-4303-bfbf-0a5f7e1d0139` |
| Secret | `AZURE_SUBSCRIPTION_ID` | `4c88693f-5cc9-4f30-9d1e-d58d4221cf25` |
| Variable | `AZURE_ENV_NAME` | `tpu-est-dep` |
| Variable | `AZURE_LOCATION` | `swedencentral` |
| Variable | `FOUNDRY_RESOURCE_GROUP_NAME` | `rg-swc-s3-ai-msfoundry-demo-02` |
| Variable | `FOUNDRY_ACCOUNT_NAME` | `zava-shopping-agent-resource` |
| Variable | `FOUNDRY_ENDPOINT` | `https://zava-shopping-agent-resource.openai.azure.com/openai/v1` |
| Variable | `MODEL_DEPLOYMENT` | `gpt-5.4` |

No secrets are recorded in this file.
