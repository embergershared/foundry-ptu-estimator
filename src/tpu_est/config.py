"""Environment-backed configuration for the TPU estimation worker."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

_DEFAULT_MIN_TOKENS: Final[int] = 30_000
_DEFAULT_MAX_TOKENS: Final[int] = 700_000
_DEFAULT_MAX_JITTER_SECONDS: Final[int] = 179
_DEFAULT_AUTH_RETRY_SECONDS: Final[int] = 60
_DEFAULT_LOG_LEVEL: Final[str] = "INFO"
_DEFAULT_API_VERSION: Final[str] = "2025-05-01"
_MIN_TOKENS_LOWER_BOUND: Final[int] = 1
_MIN_JITTER_SECONDS: Final[int] = 0
_MAX_JITTER_SECONDS_EXCLUSIVE_BOUND: Final[int] = 600
_MIN_AUTH_RETRY_SECONDS: Final[int] = 0
_ALLOWED_LOG_LEVELS: Final[frozenset[str]] = frozenset({"DEBUG", "INFO", "WARNING", "ERROR"})


@dataclass(frozen=True)
class AppConfig:
    """Validated runtime configuration for one Container Apps Job execution."""

    foundry_endpoint: str
    model_deployment: str
    min_tokens: int
    max_tokens: int
    max_jitter_seconds: int
    azure_client_id: str | None
    random_seed: int | None
    log_level: str
    auth_retry_seconds: int
    api_version: str


class ConfigError(ValueError):
    """Raised when one or more configuration variables are missing or invalid."""


def load_config(env: Mapping[str, str] | None = None) -> AppConfig:
    """Load and validate application configuration from an environment mapping."""
    source: Mapping[str, str] = dict(os.environ) if env is None else env
    errors: list[str] = []

    foundry_endpoint = _read_required(source, "FOUNDRY_ENDPOINT", errors)
    model_deployment = _read_required(source, "MODEL_DEPLOYMENT", errors)
    azure_client_id = _read_optional_str(source, "AZURE_CLIENT_ID")
    min_tokens = _read_int(source, "MIN_TOKENS", _DEFAULT_MIN_TOKENS, errors)
    max_tokens = _read_int(source, "MAX_TOKENS", _DEFAULT_MAX_TOKENS, errors)
    max_jitter_seconds = _read_int(
        source,
        "MAX_JITTER_SECONDS",
        _DEFAULT_MAX_JITTER_SECONDS,
        errors,
    )
    auth_retry_seconds = _read_int(
        source,
        "AUTH_RETRY_SECONDS",
        _DEFAULT_AUTH_RETRY_SECONDS,
        errors,
    )
    random_seed = _read_optional_int(source, "RANDOM_SEED", errors)
    log_level = _read_log_level(source, errors)
    api_version = _read_optional_str(source, "API_VERSION") or _DEFAULT_API_VERSION

    _validate_token_bounds(min_tokens, max_tokens, errors)
    _validate_jitter_bound(max_jitter_seconds, errors)
    _validate_auth_retry_bound(auth_retry_seconds, errors)

    if errors:
        raise ConfigError(_format_config_error(errors))

    assert foundry_endpoint is not None
    assert model_deployment is not None
    assert min_tokens is not None
    assert max_tokens is not None
    assert max_jitter_seconds is not None
    assert auth_retry_seconds is not None
    assert log_level is not None

    return AppConfig(
        foundry_endpoint=foundry_endpoint,
        model_deployment=model_deployment,
        min_tokens=min_tokens,
        max_tokens=max_tokens,
        max_jitter_seconds=max_jitter_seconds,
        azure_client_id=azure_client_id,
        random_seed=random_seed,
        log_level=log_level,
        auth_retry_seconds=auth_retry_seconds,
        api_version=api_version,
    )


def _read_required(
    env: Mapping[str, str],
    name: str,
    errors: list[str],
) -> str | None:
    raw_value = env.get(name)
    if raw_value is None or not raw_value.strip():
        errors.append(f"{name} is required and must not be blank")
        return None
    return raw_value.strip()


def _read_optional_str(env: Mapping[str, str], name: str) -> str | None:
    raw_value = env.get(name)
    if raw_value is None or not raw_value.strip():
        return None
    return raw_value.strip()


def _read_int(
    env: Mapping[str, str],
    name: str,
    default: int,
    errors: list[str],
) -> int | None:
    raw_value = env.get(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError:
        errors.append(f"{name} must be an integer; got {raw_value!r}")
        return None


def _read_optional_int(
    env: Mapping[str, str],
    name: str,
    errors: list[str],
) -> int | None:
    raw_value = env.get(name)
    if raw_value is None or not raw_value.strip():
        return None

    try:
        return int(raw_value)
    except ValueError:
        errors.append(f"{name} must be an integer; got {raw_value!r}")
        return None


def _read_log_level(env: Mapping[str, str], errors: list[str]) -> str | None:
    log_level = env.get("LOG_LEVEL", _DEFAULT_LOG_LEVEL).strip().upper()
    if log_level in _ALLOWED_LOG_LEVELS:
        return log_level

    allowed_values = ", ".join(sorted(_ALLOWED_LOG_LEVELS))
    errors.append(f"LOG_LEVEL must be one of: {allowed_values}; got {log_level!r}")
    return None


def _validate_token_bounds(
    min_tokens: int | None,
    max_tokens: int | None,
    errors: list[str],
) -> None:
    if min_tokens is not None and min_tokens < _MIN_TOKENS_LOWER_BOUND:
        errors.append("MIN_TOKENS must be >= 1")
    if min_tokens is not None and max_tokens is not None and max_tokens < min_tokens:
        errors.append("MAX_TOKENS must be >= MIN_TOKENS")


def _validate_jitter_bound(max_jitter_seconds: int | None, errors: list[str]) -> None:
    if max_jitter_seconds is None:
        return
    if not _MIN_JITTER_SECONDS <= max_jitter_seconds < _MAX_JITTER_SECONDS_EXCLUSIVE_BOUND:
        errors.append("MAX_JITTER_SECONDS must satisfy 0 <= value < 600")


def _validate_auth_retry_bound(auth_retry_seconds: int | None, errors: list[str]) -> None:
    if auth_retry_seconds is not None and auth_retry_seconds < _MIN_AUTH_RETRY_SECONDS:
        errors.append("AUTH_RETRY_SECONDS must be >= 0")


def _format_config_error(errors: Sequence[str]) -> str:
    return "Invalid configuration: " + "; ".join(errors) + "."
