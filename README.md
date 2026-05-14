# Foundry TPU Estimation Traffic Generator

Generate sustained, realistic Azure AI Foundry traffic so the existing `gpt-5.4`
deployment can be sized for PTU capacity with [ptucalc.com](https://www.ptucalc.com/).

## Why this exists

Provisioned Throughput Unit (PTU) pricing only makes sense when the input data
looks like the production workload. For this project, that means days of calls
against the existing Azure AI Foundry `gpt-5.4` deployment with realistic prompt
sizes, completion behavior, retry behavior, and platform telemetry.

Manually generating that volume of traffic is error-prone and impractical. This
repo automates the workload with an Azure Container Apps Job that runs on a
schedule, jitters each execution, assembles large English-prose prompts from a
bundled corpus, and records the server-reported token usage that matters for
capacity planning.

The business outcome is a Log Analytics CSV export that can be uploaded to
[ptucalc.com](https://www.ptucalc.com/). The calculator then estimates the PTUs
needed for the observed `gpt-5.4` traffic pattern instead of relying on a guess.

## Architecture

The repository provisions everything around an existing Foundry account and
model deployment: Log Analytics, Storage, ACR, a Container Apps environment, a
scheduled Container Apps Job, a user-assigned managed identity, RBAC, and
Diagnostic Settings. The existing Foundry account and deployment are referenced
by parameters and are not recreated.

For the Bicep source of truth, start with [`infra/main.bicep`](infra/main.bicep)
and then follow the module wiring under [`infra/modules/`](infra/modules/).

```text
GitHub Actions (OIDC)
        │
        ▼  (build + push)
Azure Container Registry  ──image──►  Azure Container Apps Job
                                         schedule:  */3 * * * *
                                         parallelism: 1, retries: 0
                                         identity: user-assigned MI
                                                │
                                                ▼  (Bearer via DefaultAzureCredential)
                                       Azure AI Foundry project
                                                │   model deployment: gpt-5.4
                                                │
                                  Diagnostic Settings on Foundry account
                                                │
                              ┌─────────────────┴──────────────────┐
                              ▼                                    ▼
                     Log Analytics workspace            Storage account / blob container
                     (KQL queries, ptucalc data export) (raw JSON archive)
```

Per execution, the Job reads environment-backed config, sleeps for a random
`0..MAX_JITTER_SECONDS` jitter window, samples a target prompt size, lazily
pre-tokenizes the bundled Project Gutenberg corpus, assembles one prompt, and
sends one chat-completion call through `DefaultAzureCredential`. The client logs
server-reported input, output, and total tokens, latency, status, response ID,
finish reason, and `x-ratelimit-*` headers. Foundry Diagnostic Settings route
platform request/response logs and metrics to Log Analytics and Storage.

## Repository layout

```text
.
├── .github/                    # Copilot guidance, squad agent, workflows
├── .squad/                     # squad charters and history
├── azure.yaml
├── Dockerfile
├── infra/
│   ├── main.bicep
│   ├── main.parameters.json
│   └── modules/
│       ├── aca-environment.bicep, aca-job.bicep, acr.bicep
│       ├── foundry-diagnostics.bicep, foundry-rbac.bicep
│       └── log-analytics.bicep, managed-identity.bicep, storage.bicep
├── pyproject.toml
├── src/tpu_est/
│   ├── __main__.py, cli.py, client.py, config.py
│   ├── corpus.py, logging_setup.py, prompt.py
│   └── data/corpus/            # MANIFEST.md, LICENSE.md, bundled *.txt
├── tests/                      # pytest suite
└── uv.lock
```

## Prerequisites

- Azure subscription with permissions to create resource-group-scope resources.
- Existing Azure AI Foundry account and `gpt-5.4` deployment. You need the
  Foundry resource group name, Foundry account name, and inference endpoint.
- GitHub OIDC federated credential configured for the deploying service
  principal. See
  [Configure an app to trust a GitHub repo](https://learn.microsoft.com/entra/workload-id/workload-identity-federation-create-trust-github).
- Azure CLI >= 2.60.
- Azure Developer CLI (`azd`) >= 1.10.
- Docker, optional for `azd up` but useful for local image builds.
- Python 3.13. Install with `pyenv install 3.13` or
  `uv python install 3.13`.
- `uv`; install from the
  [official uv instructions](https://docs.astral.sh/uv/getting-started/installation/).

## Quick start (local)

The project uses `uv` for dependency management and `ruff`, `mypy`, and
`pytest` for the local quality gate defined in [`pyproject.toml`](pyproject.toml).

```powershell
# Windows PowerShell
# If uv was installed with pipx or pip, add the user Scripts directory first.
$env:PATH = "$env:APPDATA\Python\Python314\Scripts;$env:PATH"
uv sync --frozen --all-extras --dev
uv run pytest -q
uv run ruff check .
uv run mypy
```

```bash
# bash / WSL / macOS / Linux
uv sync --frozen --all-extras --dev
uv run pytest -q
uv run ruff check .
uv run mypy
```

Run one call locally after `az login`. The app uses
`DefaultAzureCredential`. Leave `AZURE_CLIENT_ID` **unset locally** so the
chain falls through to your `az login` user/SP token (`AzureCliCredential`);
setting `AZURE_CLIENT_ID` pins the chain to the named user-assigned MI,
which is correct in the deployed Container Apps Job but slow on a laptop
because IMDS will be probed first.

```bash
az login                                   # one-time per machine
export FOUNDRY_ENDPOINT='https://<account>.services.ai.azure.com/models'
export MODEL_DEPLOYMENT='gpt-5.4'
export MIN_TOKENS=1000          # smaller for local sanity
export MAX_TOKENS=2000
export MAX_JITTER_SECONDS=0
export LOG_LEVEL=DEBUG
uv run python -m tpu_est run-once
```

For PowerShell one-shot runs, use the same variable names as `$env:NAME = 'value'`.

> **Note:** The corpus pre-tokenizes about 3.24 million `o200k_base` tokens
> lazily on the first call in a process. Expect the first run to spend about
> 30 seconds building the token stream before it contacts Foundry.

### Where to set the env vars (run + debug)

Three idiomatic options — pick whichever fits your loop:

1. **`.env` file (recommended for VS Code)**
   - Copy the template: `Copy-Item .env.example .env` (or `cp .env.example .env`).
     `.env` is gitignored; `.env.example` is the only `.env*` allowed in git.
   - Fill in `FOUNDRY_ENDPOINT`, `MODEL_DEPLOYMENT`, and `AZURE_CLIENT_ID`.
   - Run via VS Code → **Run and Debug** → **"Run once (local, .env)"**
     (defined in [`.vscode/launch.json`](.vscode/launch.json)). The launch
     config sets `envFile` so the debugger and breakpoints get the variables
     for free. The companion [`.vscode/settings.json`](.vscode/settings.json)
     also points the integrated terminal's Python at `.env` via
     `python.envFile`, so plain `python -m tpu_est run-once` in a fresh
     VS Code terminal works too.
2. **PowerShell session vars** (when running outside VS Code):
   ```powershell
   $env:FOUNDRY_ENDPOINT = 'https://<account>.services.ai.azure.com/models'
   $env:MODEL_DEPLOYMENT = 'gpt-5.4'
   $env:AZURE_CLIENT_ID  = '<user-assigned-mi-client-id>'
   $env:MIN_TOKENS       = '1000'
   $env:MAX_TOKENS       = '2000'
   $env:MAX_JITTER_SECONDS = '0'
   $env:LOG_LEVEL        = 'DEBUG'
   python -m tpu_est run-once
   ```
   Or batch-source from `.env` in a one-liner:
   ```powershell
   Get-Content .env | Where-Object { $_ -and -not $_.StartsWith('#') } |
     ForEach-Object { $n,$v = $_ -split '=',2; [Environment]::SetEnvironmentVariable($n, $v) }
   ```
3. **Inline for a single command** (CI-style, no persisted state):
   ```bash
   FOUNDRY_ENDPOINT=... MODEL_DEPLOYMENT=gpt-5.4 \
     uv run python -m tpu_est run-once
   ```

> **Authenticate locally to Foundry with `az login`.** Don't set
> `AZURE_CLIENT_ID` on your laptop. With it unset, `DefaultAzureCredential`
> uses `AzureCliCredential` and your `az login` identity reaches Foundry
> directly — provided your user / SP has `Cognitive Services User` (or
> equivalent) on the Foundry account. The deployed Container Apps Job *does*
> set `AZURE_CLIENT_ID` so the credential chain pins to the bound
> user-assigned Managed Identity instead.

> **Warning:** `config.py` is the **only** module that reads `os.environ`.
> Don't `os.environ.get(...)` anywhere else — every other consumer takes
> values as constructor parameters or function arguments.

> **Smoke test without a real endpoint:** Use the
> **"Run once (smoke — bogus endpoint)"** launch config (or set
> `FOUNDRY_ENDPOINT=https://example-bogus.services.ai.azure.com/models`).
> The app exits 1 with a structured `run_failed` log line; this is the
> fastest way to confirm the full pipeline (config → jitter → corpus →
> prompt → SDK call boundary) works locally.

## Deploy with `azd up`

Create or select an `azd` environment, set the required Foundry references, and
run the full provision-and-deploy flow.

```bash
azd env new prod --location swedencentral
azd env set FOUNDRY_RESOURCE_GROUP_NAME 'rg-foundry'
azd env set FOUNDRY_ACCOUNT_NAME 'my-foundry-account'
azd env set FOUNDRY_ENDPOINT 'https://my-foundry-account.services.ai.azure.com/models'
# MODEL_DEPLOYMENT defaults to gpt-5.4; override if needed:
# azd env set MODEL_DEPLOYMENT 'gpt-5.4'
azd up
```

Environment values used by [`infra/main.parameters.json`](infra/main.parameters.json):

| Variable | Required | Purpose |
|---|---:|---|
| `AZURE_ENV_NAME` | yes | `azd` environment name; used for resource naming. |
| `AZURE_LOCATION` | yes | Azure region, for example `swedencentral`. |
| `FOUNDRY_RESOURCE_GROUP_NAME` | yes | Resource group containing the existing Foundry account. |
| `FOUNDRY_ACCOUNT_NAME` | yes | Existing Foundry account name. |
| `FOUNDRY_ENDPOINT` | yes | Inference endpoint passed to the job. |
| `MODEL_DEPLOYMENT` | no | Deployment name; defaults to `gpt-5.4`. |

`azd up` runs `azd provision` and then `azd deploy`. After the Azure resources
exist, code-only changes normally need only `azd deploy`.

## Configuration reference

[`src/tpu_est/config.py`](src/tpu_est/config.py) is the source of truth for all
runtime environment variables consumed by `tpu_est`. Do not read `os.environ`
elsewhere in the package.

| Variable | Default | Validation and use |
|---|---:|---|
| `FOUNDRY_ENDPOINT` | none | Required, non-blank. Azure AI Foundry inference endpoint. |
| `MODEL_DEPLOYMENT` | none | Required, non-blank. Deployment name passed as the chat-completion model. |
| `AZURE_CLIENT_ID` | none (optional) | If set, pins `DefaultAzureCredential` to the named user-assigned Managed Identity (production: ACA Job). **Leave unset locally** so the chain falls through to `AzureCliCredential` from `az login`. |
| `MIN_TOKENS` | `30000` | Integer, `>= 1`. Lower bound for sampled prompt size. |
| `MAX_TOKENS` | `700000` | Integer, `>= MIN_TOKENS`. Upper bound for sampled prompt size. |
| `MAX_JITTER_SECONDS` | `179` | Integer, `0 <= value < 600`. Each run sleeps uniformly from `0..value` seconds. |
| `AUTH_RETRY_SECONDS` | `60` | Integer, `>= 0`. Delay before the one retry after a 401 or 403. |
| `API_VERSION` | `2025-05-01` | Azure OpenAI / Foundry inference REST API version sent on every request. |
| `LOG_LEVEL` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `RANDOM_SEED` | none | Optional integer. Makes jitter and prompt sampling deterministic for tests/debugging. |

The deployed Job sets these values in
[`infra/modules/aca-job.bicep`](infra/modules/aca-job.bicep). Local execution
must set the required variables explicitly.

## CI/CD

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pull requests,
`main` pushes, and manual dispatch. It installs Python 3.13 with `uv`, runs
`uv sync --frozen --all-extras --dev`, then checks Ruff linting, Ruff formatting,
Mypy strict typing, and Pytest.

[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) runs on `main`
pushes and manual dispatch. It logs into Azure with GitHub OIDC, selects or
creates the `azd` environment, sets the Foundry `azd` variables, then runs
`azd provision --no-prompt` and `azd deploy --no-prompt`.

Required GitHub repository secrets for deployment:

| Secret | Purpose |
|---|---|
| `AZURE_CLIENT_ID` | Service-principal client ID with a federated credential from this repo. |
| `AZURE_TENANT_ID` | Azure tenant ID. |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID. |

Required GitHub repository variables for deployment:

| Variable | Purpose |
|---|---|
| `AZURE_ENV_NAME` | `azd` environment name, for example `prod`. |
| `AZURE_LOCATION` | Azure region, for example `swedencentral`. |
| `FOUNDRY_RESOURCE_GROUP_NAME` | Resource group containing the existing Foundry account. |
| `FOUNDRY_ACCOUNT_NAME` | Existing Foundry account name. |
| `FOUNDRY_ENDPOINT` | Full inference endpoint URL. |
| `MODEL_DEPLOYMENT` | Optional; defaults to `gpt-5.4` through Bicep parameters. |

> **Warning:** Deployment auth is OIDC-only. Do not add long-lived Azure client
> secrets to this repository.

## Telemetry → ptucalc.com workflow

Let the Job run for at least 24-48 hours before exporting. The default schedule
is every three minutes, so one full day gives roughly 480 data points before
any failed or throttled runs are filtered out.

Current Microsoft monitoring docs list Azure OpenAI resource logs for
`Microsoft.CognitiveServices/accounts` in `AzureDiagnostics` under categories
such as `RequestResponse` and `AzureOpenAIRequestUsage`. Some workspaces expose
resource-specific tables such as `AOAIRequestResponseLogs`. Table names and JSON
payload paths can vary by region, subscription onboarding date, and diagnostic
setting mode.

Start by inspecting the schema in your workspace:

```kusto
union isfuzzy=true
  (AOAIRequestResponseLogs | take 5),
  (AzureDiagnostics | where ResourceProvider == "MICROSOFT.COGNITIVESERVICES" | where Category in ("RequestResponse", "AzureOpenAIRequestUsage") | take 5)
```

If `AOAIRequestResponseLogs` exists, this is the preferred export shape:

```kusto
AOAIRequestResponseLogs
| where TimeGenerated >= ago(7d)
| extend Props = todynamic(column_ifexists("properties_s", "{}")), RequestParameters = todynamic(Props.requestParameters), DeploymentFromColumn = tostring(column_ifexists("DeploymentName", ""))
| extend DeploymentName = iff(isnotempty(DeploymentFromColumn), DeploymentFromColumn, iff(isnotempty(tostring(RequestParameters.deployment)), tostring(RequestParameters.deployment), tostring(RequestParameters.model)))
| where DeploymentName == "gpt-5.4"
| extend PromptTokens = toint(RequestParameters.input_token_count), CompletionTokens = toint(RequestParameters.output_token_count)
| project TimeGenerated, DeploymentName, DurationMs = toint(column_ifexists("DurationMs", int(null))), PromptTokens, CompletionTokens, TotalTokens = PromptTokens + CompletionTokens
| order by TimeGenerated asc
```

If your workspace only has `AzureDiagnostics`, use this fallback and adjust the
column extraction after inspecting `properties_s`:

```kusto
AzureDiagnostics
| where TimeGenerated >= ago(7d)
| where ResourceProvider == "MICROSOFT.COGNITIVESERVICES"
| where Category in ("RequestResponse", "AzureOpenAIRequestUsage")
| extend Props = todynamic(properties_s), RequestParameters = todynamic(Props.requestParameters), Usage = todynamic(Props.usage)
| extend DeploymentName = case(isnotempty(tostring(column_ifexists("ModelDeploymentName_s", ""))), tostring(column_ifexists("ModelDeploymentName_s", "")), isnotempty(tostring(column_ifexists("DeploymentName_s", ""))), tostring(column_ifexists("DeploymentName_s", "")), isnotempty(tostring(RequestParameters.deployment)), tostring(RequestParameters.deployment), tostring(RequestParameters.model))
| where DeploymentName == "gpt-5.4"
| extend PromptTokens = toint(case(isnotempty(tostring(RequestParameters.input_token_count)), tostring(RequestParameters.input_token_count), isnotempty(tostring(Usage.prompt_tokens)), tostring(Usage.prompt_tokens), tostring(column_ifexists("ProcessedPromptTokens_d", ""))))
| extend CompletionTokens = toint(case(isnotempty(tostring(RequestParameters.output_token_count)), tostring(RequestParameters.output_token_count), isnotempty(tostring(Usage.completion_tokens)), tostring(Usage.completion_tokens), tostring(column_ifexists("GeneratedTokens_d", ""))))
| extend DurationMs = toint(case(isnotempty(tostring(column_ifexists("DurationMs", ""))), tostring(column_ifexists("DurationMs", "")), isnotempty(tostring(column_ifexists("DurationMs_d", ""))), tostring(column_ifexists("DurationMs_d", "")), tostring(Props.durationMs)))
| project TimeGenerated, DeploymentName, DurationMs, PromptTokens, CompletionTokens, TotalTokens = PromptTokens + CompletionTokens
| order by TimeGenerated asc
```

> **Note:** If the token expressions return nulls, run `take 1 | project *` and
> inspect the dynamic payload. Microsoft documents the current monitoring model
> at [Monitor Azure OpenAI](https://learn.microsoft.com/azure/ai-services/openai/how-to/monitor-openai)
> and the reference table at
> [Azure OpenAI monitoring data reference](https://learn.microsoft.com/azure/ai-services/openai/monitor-openai-reference).

Export the query result to CSV from Log Analytics, upload it to
[ptucalc.com](https://www.ptucalc.com/), choose the `gpt-5.4` model, and review
the PTU recommendation.

Column mapping for ptucalc:

| ptucalc input | CSV column | Notes |
|---|---|---|
| Timestamp | `TimeGenerated` | Keep UTC ordering; export ascending. |
| Model/deployment | `DeploymentName` | Select `gpt-5.4` in ptucalc. |
| Input tokens | `PromptTokens` | Prefer server-reported values over local `tiktoken` estimates. |
| Output tokens | `CompletionTokens` | Completion size is intentionally not capped by this app. |
| Total tokens | `TotalTokens` | Sum of input and output tokens. |
| Latency | `DurationMs` | Useful for review, even if not required by the calculator. |

## Operational guide

### Pause traffic

Disable the Container Apps Job schedule in the Azure portal to prevent future
cron executions. To stop an active execution, run:

```bash
az containerapp job stop --name <jobname> --resource-group <rg>
```

### Cost control

> **Warning:** There is no `MAX_DAILY_CALLS` cost cap in v1. The only built-in
> rate guard is the `*/3 * * * *` cron schedule, approximately 480 runs per day.

Expected daily input tokens are approximately:

```text
daily_input_tokens ~= 480 * mean_prompt_tokens
```

With the deployed defaults, `mean_prompt_tokens = (30000 + 700000) / 2 = 365000`,
so the generator can send about 175.2 million input tokens per day, plus model
completion tokens. Convert that token volume with the current `gpt-5.4` price
for your region and deployment type before leaving it unattended.

### Troubleshooting first 401 or 403

The first execution after deployment may fail while RBAC propagates. The client
retries once after `AUTH_RETRY_SECONDS` seconds, defaulting to 60 seconds. If it
still fails after about two minutes, verify that the user-assigned managed
identity has the `Cognitive Services User` role on the Foundry account. The role
assignment is defined in
[`infra/modules/foundry-rbac.bicep`](infra/modules/foundry-rbac.bicep).

### Verifying telemetry

Count recent Foundry diagnostic rows:

```kusto
union isfuzzy=true
    (AOAIRequestResponseLogs
     | where TimeGenerated > ago(1h)
     | project TimeGenerated, SourceTable = "AOAIRequestResponseLogs"),
    (AzureDiagnostics
     | where TimeGenerated > ago(1h)
     | where ResourceProvider == "MICROSOFT.COGNITIVESERVICES"
     | where Category in ("RequestResponse", "AzureOpenAIRequestUsage")
     | project TimeGenerated, SourceTable = "AzureDiagnostics")
| summarize Rows = count() by SourceTable
```

If Foundry rows are delayed, also check the app console stream for `call_complete`
JSON lines emitted by [`src/tpu_est/cli.py`](src/tpu_est/cli.py).

### Updating image

Use `azd deploy` for code-only updates after the first successful `azd up`, or
push to `main` and let the deployment workflow build and deploy the image.

## Project conventions

- Squad roles and ownership boundaries live under [`.squad/agents/`](.squad/agents/).
- Runtime configuration is explicit: all `os.environ` reads belong in
  [`src/tpu_est/config.py`](src/tpu_est/config.py).
- Server-reported `usage.*` values are the source of truth for token analysis;
  local `tiktoken` counts are prompt-construction estimates.
- The corpus is bundled in the image, not fetched at runtime.
- Tests should not call real Azure resources; SDK behavior is mocked at the
  client boundary.

## License & attribution

The bundled corpus is cleaned public-domain prose from Project Gutenberg. See
[`src/tpu_est/data/corpus/LICENSE.md`](src/tpu_est/data/corpus/LICENSE.md) and
[`src/tpu_est/data/corpus/MANIFEST.md`](src/tpu_est/data/corpus/MANIFEST.md) for
per-title attribution and token counts.

The package metadata is MIT-friendly, but the repository does not currently
include a top-level license file. Add one before making the repo public or
redistributing it outside the current private context.
