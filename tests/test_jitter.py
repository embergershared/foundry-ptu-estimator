"""Jitter and failure-path tests for tpu_est.cli.run_once."""

from __future__ import annotations

import random
from dataclasses import dataclass
from unittest.mock import Mock

from pytest_mock import MockerFixture

from tpu_est.cli import run_once
from tpu_est.client import CallResult
from tpu_est.config import AppConfig
from tpu_est.prompt import AssembledPrompt

_ENDPOINT = "https://example.cognitiveservices.azure.com"
_MODEL_DEPLOYMENT = "gpt-5.4"
_AZURE_CLIENT_ID = "00000000-0000-0000-0000-000000000000"
_MIN_TOKENS = 30_000
_MAX_TOKENS = 700_000
_MIN_JITTER_SECONDS = 0
_MAX_JITTER_SECONDS = 10
_RANDOM_SEED = 7
_AUTH_RETRY_SECONDS = 60
_API_VERSION = "2025-05-01"
_LOG_LEVEL = "INFO"
_SUCCESS_EXIT_CODE = 0
_HANDLED_FAILURE_EXIT_CODE = 1
_ZERO_INT_FIELD = 0


@dataclass(frozen=True)
class _CliMocks:
    sleep: Mock
    client_class: Mock


def _app_config(*, max_jitter_seconds: int = _MAX_JITTER_SECONDS) -> AppConfig:
    return AppConfig(
        foundry_endpoint=_ENDPOINT,
        model_deployment=_MODEL_DEPLOYMENT,
        min_tokens=_MIN_TOKENS,
        max_tokens=_MAX_TOKENS,
        max_jitter_seconds=max_jitter_seconds,
        azure_client_id=_AZURE_CLIENT_ID,
        random_seed=_RANDOM_SEED,
        log_level=_LOG_LEVEL,
        auth_retry_seconds=_AUTH_RETRY_SECONDS,
        api_version=_API_VERSION,
    )


def _call_result(config: AppConfig) -> CallResult:
    return CallResult(
        input_tokens=_ZERO_INT_FIELD,
        output_tokens=_ZERO_INT_FIELD,
        total_tokens=_ZERO_INT_FIELD,
        latency_ms=_ZERO_INT_FIELD,
        http_status=_ZERO_INT_FIELD,
        model_deployment=config.model_deployment,
        response_id=None,
        finish_reason=None,
        ratelimit_remaining_requests=_ZERO_INT_FIELD,
        ratelimit_remaining_tokens=_ZERO_INT_FIELD,
    )


def _stub_prompt(*, target_tokens: int, corpus: object, rng: random.Random) -> AssembledPrompt:
    if corpus is None:
        raise AssertionError("corpus stub must be provided")
    rng_state = rng.getstate()
    assert rng_state is not None
    return AssembledPrompt(text="x", target_tokens=target_tokens, actual_tokens=target_tokens)


def _patch_cli_dependencies(
    mocker: MockerFixture,
    *,
    client_result: CallResult | Exception,
) -> _CliMocks:
    sleep = mocker.patch("tpu_est.cli.time.sleep")
    mocker.patch("tpu_est.cli.DefaultAzureCredential")
    mocker.patch("tpu_est.cli.tiktoken.get_encoding", return_value=object())
    mocker.patch("tpu_est.cli.Corpus", return_value=object())
    mocker.patch("tpu_est.cli.build_prompt", side_effect=_stub_prompt)
    client_class = mocker.patch("tpu_est.cli.FoundryClient")
    if isinstance(client_result, Exception):
        client_class.return_value.complete.side_effect = client_result
    else:
        client_class.return_value.complete.return_value = client_result
    return _CliMocks(sleep=sleep, client_class=client_class)


def test_run_once_jitter_within_bounds(mocker: MockerFixture) -> None:
    """run_once sleeps for deterministic jitter within configured bounds."""
    config = _app_config()
    mocks = _patch_cli_dependencies(mocker, client_result=_call_result(config))

    exit_code = run_once(config)

    assert exit_code == _SUCCESS_EXIT_CODE
    mocks.sleep.assert_called_once()
    sleep_seconds = mocks.sleep.call_args.args[0]
    assert isinstance(sleep_seconds, int)
    assert _MIN_JITTER_SECONDS <= sleep_seconds <= _MAX_JITTER_SECONDS


def test_run_once_returns_1_on_client_failure(mocker: MockerFixture) -> None:
    """run_once returns the handled-failure code when the client raises."""
    config = _app_config(max_jitter_seconds=_MIN_JITTER_SECONDS)
    _patch_cli_dependencies(mocker, client_result=RuntimeError("boom"))

    exit_code = run_once(config)

    assert exit_code == _HANDLED_FAILURE_EXIT_CODE
