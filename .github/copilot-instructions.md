# Copilot instructions — foundry-tpu-est-data

A Python Azure Container Apps **Job** that periodically sends one realistic
chat-completion call to an existing Azure AI Foundry `gpt-5.4` deployment so
its telemetry can drive Provisioned Throughput Unit (PTU) sizing via
[ptucalc.com](https://www.ptucalc.com/). Read [`README.md`](../README.md) for
the deployment workflow and KQL queries; this file is the contributor cheatsheet.

## Build, test, lint

The project uses **`uv`** (Python 3.13) for dependency management and runs
all tooling through `uv run`. On Windows, `uv` may not be on `PATH`; the install
location is typically `%APPDATA%\Python\Python3xx\Scripts`. Prepend it before
running anything:

```powershell
$env:PATH = "$env:APPDATA\Python\Python314\Scripts;$env:PATH"
```

| Task | Command |
|---|---|
| Install all deps from lockfile | `uv sync --frozen --all-extras --dev` |
| Run the full PR gate | `uv run ruff check . ; uv run ruff format --check . ; uv run mypy ; uv run pytest -v` |
| Lint | `uv run ruff check .` |
| Auto-format | `uv run ruff format .` |
| Type-check (strict) | `uv run mypy` |
| Run all tests (29 today) | `uv run pytest -v` |
| **Run a single test** | `uv run pytest tests/test_prompt_sizing.py::test_build_prompt_hits_target_within_margin -v` |
| One-shot local execution | `uv run python -m tpu_est run-once` (requires env vars — see below) |
| Build the container image | `docker build -t tpu-est:dev .` |
| Build a Bicep module | `az bicep build --file .\infra\modules\<name>.bicep` |
| Build the full template | `az bicep build --file .\infra\main.bicep` |
| Deploy everything | `azd up` (after `azd env set` for the Foundry-side parameters) |

CI runs the same lint+type+test pipeline on every PR (`.github/workflows/ci.yml`).
CD on push-to-`main` runs `azd provision` then `azd deploy` via OIDC
(`.github/workflows/deploy.yml`).

## Architecture (only the non-obvious bits)

- **Single-execution worker.** Each Container Apps Job replica runs
  `python -m tpu_est run-once`, which `run_once()` in `src/tpu_est/cli.py`
  orchestrates: load config → in-job random sleep `0..MAX_JITTER_SECONDS` →
  pick `target_tokens ~ U(MIN_TOKENS, MAX_TOKENS)` → assemble exact-sized prompt
  → call Foundry → emit one structured JSON log line → exit 0/1/2.
  Cron `*/3 * * * *` lives in the Bicep, not in code.
- **Tokenizer is `tiktoken o200k_base`** (closest public encoder for GPT-5.x). It
  may differ from server counts by a few percent; the canonical truth is the
  server-reported `usage.*` and rate-limit headers we log via
  `CallResult` (see `src/tpu_est/client.py`).
- **Prompt sizing** in `src/tpu_est/prompt.py` uses an **oversample-margin
  re-encode** loop to land exactly on `target_tokens`. The corpus
  (`src/tpu_est/data/corpus/*.txt`, ~3.2M tokens of public-domain books) is lazily
  pre-tokenized once and cached on the `Corpus` instance — first call ≈ 30s.
- **Auth path is fixed**: `DefaultAzureCredential(managed_identity_client_id=AZURE_CLIENT_ID)`
  resolves the user-assigned MI bound to the Job. The MI is granted
  `Cognitive Services User` on the Foundry account by `infra/modules/foundry-rbac.bicep`.
- **First-run 401/403 retry**: MI role propagation can take a minute. `FoundryClient`
  retries the call once after `AUTH_RETRY_SECONDS` (default 60s) on 401/403.
- **Diagnostic Settings** on the Foundry account
  (`infra/modules/foundry-diagnostics.bicep`) ship `categoryGroup: allLogs` +
  `audit` + `AllMetrics` to **both** the Log Analytics workspace and a Storage
  blob container (`foundry-diagnostics`). Storage is configured with
  `allowSharedKeyAccess: true` because the Diagnostic Settings publishing path
  still requires shared-key auth — leave it on.
- **Cross-RG deployment.** `infra/main.bicep` is `targetScope = 'subscription'`,
  creates the app RG, and invokes `foundry-rbac` and `foundry-diagnostics` with
  `scope: resourceGroup(foundryResourceGroupName)` so they target the
  pre-existing Foundry RG (which we never modify otherwise).

## Conventions (enforced by reviewers)

- **Only `src/tpu_est/config.py` may read `os.environ`.** Every other module
  takes its inputs as constructor parameters / function arguments. Tests rely on
  this: they pass an `env` mapping to `load_config(env=...)` instead of patching.
- **`AppConfig` is a frozen dataclass** validated at construction; missing /
  invalid env vars raise a single `ConfigError` listing all failures, and
  `__main__.py` exits 2 (config error) vs 1 (handled runtime failure) vs 0 (success).
- **Logging is structlog → JSON to stdout** (`logging_setup.configure_logging`).
  Never `print()` for telemetry. Container Apps captures stdout into
  `ContainerAppConsoleLogs_CL`; the JSON shape is what we KQL-query.
- **No `max_completion_tokens` cap** on the chat call — we deliberately exercise
  the model's default output size. Don't add one without updating the plan.
- **There is no `MAX_DAILY_CALLS` circuit breaker in v1.** The cron `*/3 * * * *`
  is the only rate guard (≈480 runs/day). To pause traffic, disable the ACA Job
  in the portal or `az containerapp job stop ...` — don't add a code-level cap
  without an external counter store.
- **Bicep modules** never declare `targetScope`; cross-RG scoping happens in
  `main.bicep`. Modules that touch existing resources use
  `Microsoft.CognitiveServices/accounts@2024-10-01 existing`. Diagnostic settings
  use `categoryGroup` ('allLogs'/'audit'), not enumerated category names — those
  drift across Foundry/AI Services renames.
- **Squad workspace** (`.squad/`, `.copilot/skills/`, `.github/agents/squad.agent.md`,
  `.github/workflows/squad-*.yml`) is owned by Squad CLI. Don't hand-edit
  except via the recorded charters/histories.

## Where to look when…

- Setting env vars for local run/debug → copy [`.env.example`](../.env.example)
  to `.env` (gitignored), or use the **"Run once (local, .env)"** entry in
  [`.vscode/launch.json`](../.vscode/launch.json). Detail in
  [`README.md`](../README.md) § "Where to set the env vars".
- Adding a new env var → `src/tpu_est/config.py` (`AppConfig`, `load_config`,
  defaults, validators) **and** `infra/modules/aca-job.bicep` (`env` block) **and**
  `README.md` configuration table — all three must agree.
- Changing prompt-size bounds → defaults in `config.py`; the
  `aca-job.bicep` parameter defaults; `README.md` configuration table.
- Adding a Bicep resource → new module under `infra/modules/`; wire it in
  `infra/main.bicep` (set `scope:` if cross-RG); add an output to
  `main.bicep` if azd or downstream tooling needs it.
- Updating telemetry fields → extend `CallResult` in `client.py`, log them in
  `cli.run_once`, and update the KQL queries in `README.md`.
- New tests → `tests/`. Mock the SDK at `tpu_est.client.ChatCompletionsClient`;
  patch `tpu_est.cli.time.sleep` to avoid real waits; reuse the session-scoped
  `corpus` fixture from `tests/conftest.py` to amortize pre-tokenization.

## Pitfalls

- Don't run `pytest` directly — use `uv run pytest` so the locked dev deps are used.
- Don't bump tiktoken across major versions without verifying the `o200k_base`
  encoder still produces stable counts for the bundled corpus.
- The first deploy may emit one or two 401/403s in the first couple of minutes
  while the role assignment propagates; the client's one-shot retry after 60s
  usually absorbs them. If you still see auth failures after ~5 minutes,
  re-check the `Cognitive Services User` assignment on the Foundry account.
