"""Azure AI Foundry chat completions client wrapper."""

import time
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus
from typing import Final, Protocol, cast

import structlog
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    ChatCompletions,
    ChatRequestMessage,
    CompletionsFinishReason,
    SystemMessage,
    UserMessage,
)
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError

_RATE_LIMIT_REQUESTS_HEADER: Final = "x-ratelimit-remaining-requests"
_RATE_LIMIT_TOKENS_HEADER: Final = "x-ratelimit-remaining-tokens"
_NS_PER_MS: Final = 1_000_000
_AUTH_RETRY_STATUSES: Final = {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}
_COGNITIVE_SERVICES_SCOPE: Final = "https://cognitiveservices.azure.com/.default"


@dataclass(frozen=True)
class CallResult:
    """Telemetry captured from a synchronous Foundry chat completion call."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    http_status: int
    model_deployment: str
    response_id: str | None
    finish_reason: str | None
    ratelimit_remaining_requests: int | None
    ratelimit_remaining_tokens: int | None


class _HttpResponseLike(Protocol):
    headers: Mapping[str, object]


class _PipelineResponseLike(Protocol):
    http_response: _HttpResponseLike


class _ResponseCarrier(Protocol):
    _response: _PipelineResponseLike | None


class FoundryClient:
    """Synchronous wrapper around Azure AI Inference chat completions."""

    def __init__(
        self,
        *,
        endpoint: str,
        model_deployment: str,
        credential: TokenCredential,
        retry_on_auth_error_seconds: int = 60,
        api_version: str | None = None,
    ) -> None:
        """Create and retain a chat completions client for the configured deployment."""
        self._model_deployment = model_deployment
        self._retry_on_auth_error_seconds = retry_on_auth_error_seconds
        client_kwargs: dict[str, object] = {
            "endpoint": endpoint,
            "credential": credential,
            "credential_scopes": [_COGNITIVE_SERVICES_SCOPE],
        }
        if api_version is not None:
            client_kwargs["api_version"] = api_version
        self._client = ChatCompletionsClient(**client_kwargs)  # type: ignore[arg-type]

    def complete(self, *, system: str, user: str) -> CallResult:
        """Synchronous chat completion with one retry on transient auth propagation errors."""
        try:
            return self._complete_once(system=system, user=user)
        except HttpResponseError as error:
            if error.status_code not in _AUTH_RETRY_STATUSES:
                raise

            structlog.get_logger().warning(
                "auth_error_retry",
                http_status=error.status_code,
                retry_delay_seconds=self._retry_on_auth_error_seconds,
            )
            time.sleep(self._retry_on_auth_error_seconds)

        return self._complete_once(system=system, user=user)

    def _complete_once(self, *, system: str, user: str) -> CallResult:
        messages: list[ChatRequestMessage] = [SystemMessage(system), UserMessage(user)]
        start_ns = time.monotonic_ns()
        response = self._client.complete(model=self._model_deployment, messages=messages)
        latency_ms = (time.monotonic_ns() - start_ns) // _NS_PER_MS
        remaining_requests, remaining_tokens = _extract_rate_limit_headers(response)

        return CallResult(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            latency_ms=latency_ms,
            http_status=int(HTTPStatus.OK),
            model_deployment=self._model_deployment,
            response_id=_optional_str_attribute(response, "id"),
            finish_reason=_finish_reason(response),
            ratelimit_remaining_requests=remaining_requests,
            ratelimit_remaining_tokens=remaining_tokens,
        )


def _extract_rate_limit_headers(response: ChatCompletions) -> tuple[int | None, int | None]:
    response_carrier = cast(_ResponseCarrier, response)
    if not hasattr(response_carrier, "_response"):
        return None, None
    pipeline_response = response_carrier._response
    if pipeline_response is None:
        return None, None

    if not hasattr(pipeline_response, "http_response"):
        return None, None
    http_response = pipeline_response.http_response
    if http_response is None or not hasattr(http_response, "headers"):
        return None, None

    return (
        _parse_int_header(http_response.headers, _RATE_LIMIT_REQUESTS_HEADER),
        _parse_int_header(http_response.headers, _RATE_LIMIT_TOKENS_HEADER),
    )


def _parse_int_header(headers: Mapping[str, object], name: str) -> int | None:
    direct_value = headers.get(name)
    if direct_value is not None:
        return _parse_optional_int(direct_value)

    lower_name = name.lower()
    for header_name, value in headers.items():
        if header_name.lower() == lower_name:
            return _parse_optional_int(value)
    return None


def _parse_optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return None

    stripped_value = value.strip()
    if not stripped_value:
        return None

    try:
        return int(stripped_value)
    except ValueError:
        return None


def _finish_reason(response: ChatCompletions) -> str | None:
    if not response.choices:
        return None

    finish_reason = response.choices[0].finish_reason
    if isinstance(finish_reason, CompletionsFinishReason):
        return finish_reason.value
    if isinstance(finish_reason, Enum):
        return cast(str, finish_reason.value)
    return finish_reason


def _optional_str_attribute(response: ChatCompletions, name: str) -> str | None:
    value = getattr(response, name, None)
    if isinstance(value, str):
        return value
    return None
