"""Retry and telemetry tests for tpu_est.client."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError
from pytest_mock import MockerFixture

from tpu_est.client import CallResult, FoundryClient

_ENDPOINT = "https://example.cognitiveservices.azure.com"
_MODEL_DEPLOYMENT = "gpt-5.4"
_SYSTEM_MESSAGE = "system"
_USER_MESSAGE = "user"
_RETRY_SECONDS = 17
_INPUT_TOKENS = 100
_OUTPUT_TOKENS = 50
_TOTAL_TOKENS = 150
_HTTP_OK = 200
_HTTP_UNAUTHORIZED = 401
_HTTP_INTERNAL_SERVER_ERROR = 500
_RESPONSE_ID = "resp-123"
_RETRY_RESPONSE_ID = "resp-456"
_FINISH_REASON = "stop"
_REMAINING_REQUESTS = 99
_REMAINING_TOKENS = 50_000
_MIN_LATENCY_MS = 0
_SINGLE_CALL_COUNT = 1
_RETRY_CALL_COUNT = 2
_RATE_LIMIT_HEADERS = {
    "x-ratelimit-remaining-requests": str(_REMAINING_REQUESTS),
    "x-ratelimit-remaining-tokens": str(_REMAINING_TOKENS),
}


@dataclass(frozen=True)
class _Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class _Choice:
    finish_reason: str | None


@dataclass(frozen=True)
class _HttpResponse:
    headers: Mapping[str, object]


@dataclass(frozen=True)
class _PipelineResponse:
    http_response: _HttpResponse


@dataclass(frozen=True)
class _FakeResponse:
    usage: _Usage
    choices: list[_Choice]
    id: str
    _response: _PipelineResponse


def _fake_response(response_id: str = _RESPONSE_ID) -> _FakeResponse:
    return _FakeResponse(
        usage=_Usage(
            prompt_tokens=_INPUT_TOKENS,
            completion_tokens=_OUTPUT_TOKENS,
            total_tokens=_TOTAL_TOKENS,
        ),
        choices=[_Choice(finish_reason=_FINISH_REASON)],
        id=response_id,
        _response=_PipelineResponse(http_response=_HttpResponse(headers=_RATE_LIMIT_HEADERS)),
    )


def _http_response_error(status_code: int) -> HttpResponseError:
    error = HttpResponseError(status_code=status_code)
    error.status_code = status_code
    return error


def _client_with_sdk_mock(mocker: MockerFixture) -> tuple[FoundryClient, Mock]:
    client_class = mocker.patch("tpu_est.client.ChatCompletionsClient")
    sdk_client = client_class.return_value
    credential = mocker.Mock(spec=TokenCredential)
    foundry_client = FoundryClient(
        endpoint=_ENDPOINT,
        model_deployment=_MODEL_DEPLOYMENT,
        credential=credential,
        retry_on_auth_error_seconds=_RETRY_SECONDS,
    )
    return foundry_client, sdk_client


def _assert_success_result(result: CallResult, response_id: str = _RESPONSE_ID) -> None:
    assert result.input_tokens == _INPUT_TOKENS
    assert result.output_tokens == _OUTPUT_TOKENS
    assert result.total_tokens == _TOTAL_TOKENS
    assert result.latency_ms >= _MIN_LATENCY_MS
    assert result.http_status == _HTTP_OK
    assert result.model_deployment == _MODEL_DEPLOYMENT
    assert result.response_id == response_id
    assert result.finish_reason == _FINISH_REASON
    assert result.ratelimit_remaining_requests == _REMAINING_REQUESTS
    assert result.ratelimit_remaining_tokens == _REMAINING_TOKENS


def test_complete_succeeds_on_first_try(mocker: MockerFixture) -> None:
    """FoundryClient.complete returns telemetry without retry on first-call success."""
    sleep = mocker.patch("tpu_est.client.time.sleep")
    foundry_client, sdk_client = _client_with_sdk_mock(mocker)
    sdk_client.complete.return_value = _fake_response()

    result = foundry_client.complete(system=_SYSTEM_MESSAGE, user=_USER_MESSAGE)

    _assert_success_result(result)
    assert sdk_client.complete.call_count == _SINGLE_CALL_COUNT
    sleep.assert_not_called()


def test_complete_retries_once_on_401(mocker: MockerFixture) -> None:
    """FoundryClient.complete retries once after an initial 401 response."""
    sleep = mocker.patch("tpu_est.client.time.sleep")
    foundry_client, sdk_client = _client_with_sdk_mock(mocker)
    sdk_client.complete.side_effect = [
        _http_response_error(_HTTP_UNAUTHORIZED),
        _fake_response(response_id=_RETRY_RESPONSE_ID),
    ]

    result = foundry_client.complete(system=_SYSTEM_MESSAGE, user=_USER_MESSAGE)

    _assert_success_result(result, response_id=_RETRY_RESPONSE_ID)
    assert sdk_client.complete.call_count == _RETRY_CALL_COUNT
    sleep.assert_called_once_with(_RETRY_SECONDS)


def test_complete_does_not_retry_on_500(mocker: MockerFixture) -> None:
    """FoundryClient.complete propagates non-auth service errors without sleeping."""
    sleep = mocker.patch("tpu_est.client.time.sleep")
    foundry_client, sdk_client = _client_with_sdk_mock(mocker)
    sdk_client.complete.side_effect = _http_response_error(_HTTP_INTERNAL_SERVER_ERROR)

    with pytest.raises(HttpResponseError):
        foundry_client.complete(system=_SYSTEM_MESSAGE, user=_USER_MESSAGE)

    assert sdk_client.complete.call_count == _SINGLE_CALL_COUNT
    sleep.assert_not_called()


def test_complete_propagates_second_401(mocker: MockerFixture) -> None:
    """FoundryClient.complete propagates an auth error after the single retry is spent."""
    sleep = mocker.patch("tpu_est.client.time.sleep")
    foundry_client, sdk_client = _client_with_sdk_mock(mocker)
    sdk_client.complete.side_effect = [
        _http_response_error(_HTTP_UNAUTHORIZED),
        _http_response_error(_HTTP_UNAUTHORIZED),
    ]

    with pytest.raises(HttpResponseError):
        foundry_client.complete(system=_SYSTEM_MESSAGE, user=_USER_MESSAGE)

    assert sdk_client.complete.call_count == _RETRY_CALL_COUNT
    sleep.assert_called_once_with(_RETRY_SECONDS)
