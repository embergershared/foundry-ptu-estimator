# Project Context

- **Project:** foundry-tpu-est-data
- **Created:** 2026-05-14

## Core Context

Agent DevOps initialized and ready for work.

## Recent Updates

📌 Hired on 2026-05-14 to own all Bicep modules, the Dockerfile, and the GitHub Actions CI/CD workflows.

## Learnings

Initial setup complete.

📌 2026-05-14: Created `.github/workflows/ci.yml` (46 LOC) for PR/main/manual CI. Verification: YAML parsed OK with PyYAML via `uv run --with pyyaml`; `uv sync --frozen --all-extras --dev`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, and `uv run pytest -v` all passed (29 tests). `actionlint` was not on PATH. Note: the requested bare `uv run python -c "import yaml..."` parse command cannot run in the locked project environment because PyYAML is not a project dependency; no workflow deviation.
2026-05-14 - Created infra/modules/aca-job.bicep (117 LOC); az bicep build and lint passed with no output.

📌 2026-05-14: Authored azd subscription deployment wiring. Created `infra/main.bicep` (125 LOC), `infra/main.parameters.json` (12 LOC), and `azure.yaml` (13 LOC). Modified `infra/modules/storage.bicep` (37 LOC) to default `allowSharedKeyAccess` to true for Diagnostic Settings storage archive writes. Also modified `infra/modules/acr.bicep` (34 LOC) to use stable `Microsoft.Authorization/roleAssignments@2022-04-01` because Bicep 0.43.8 emitted BCP081 for the previous preview API and the required `infra/main.bicep` build had to be warning-free. Verification passed: `az bicep build --file .\infra\modules\storage.bicep`, `az bicep build --file .\infra\main.bicep`, JSON parse OK, PyYAML parse OK, azd CLI validation OK, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, and `uv run pytest -q`. azd service host kept as `containerapp`; current azd v1 schema/docs list `containerapp` and no dedicated `containerappjob` host.

📌 2026-05-14: Authored `.github/workflows/deploy.yml` (82 LOC) for OIDC-based Azure deployment on `main` pushes and manual dispatch. Verification: deploy YAML parsed OK with PyYAML via `uv run --with pyyaml`; `.github/workflows/ci.yml` parsed OK; `actionlint` was not on PATH; optional `git diff --stat` could not run because this workspace has no `.git` directory. Deviations: used `AZD_ENVIRONMENT` from `${{ inputs.azd_environment || vars.AZURE_ENV_NAME }}` so manual dispatch input controls both GitHub Environment gating and azd environment selection; action majors and azd OIDC flags otherwise match the requested contract.
