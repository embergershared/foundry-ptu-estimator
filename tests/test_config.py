"""Configuration loading tests for tpu_est.config."""

from __future__ import annotations

import pytest

from tpu_est.config import AppConfig, ConfigError, load_config

_VALID_FOUNDRY_ENDPOINT = "https://example.cognitiveservices.azure.com"
_VALID_MODEL_DEPLOYMENT = "gpt-5.4"
_VALID_AZURE_CLIENT_ID = "00000000-0000-0000-0000-000000000000"
_VALID_MIN_TOKENS = 30_000
_VALID_MAX_TOKENS = 700_000
_VALID_MAX_JITTER_SECONDS = 179
_VALID_AUTH_RETRY_SECONDS = 60
_VALID_RANDOM_SEED = 42
_VALID_LOG_LEVEL = "INFO"
_DEFAULT_RANDOM_SEED = None
_REQUIRED_ENV_NAMES = ("FOUNDRY_ENDPOINT", "MODEL_DEPLOYMENT")
_REQUIRED_NAMES_REGEX = "FOUNDRY_ENDPOINT.*MODEL_DEPLOYMENT"
_NON_NUMERIC_MIN_TOKENS = "abc"
_HIGHER_MIN_TOKENS = "200"
_LOWER_MAX_TOKENS = "100"
_NEGATIVE_JITTER_SECONDS = "-1"
_TOO_LARGE_JITTER_SECONDS = "1000"
_INVALID_LOG_LEVEL = "TRACE"


def _required_env() -> dict[str, str]:
    return {
        "FOUNDRY_ENDPOINT": _VALID_FOUNDRY_ENDPOINT,
        "MODEL_DEPLOYMENT": _VALID_MODEL_DEPLOYMENT,
    }


def test_load_config_allows_missing_azure_client_id_for_local_dev() -> None:
    """AZURE_CLIENT_ID is optional so DefaultAzureCredential can use az login locally."""
    config = load_config(_required_env())

    assert config.azure_client_id is None


def test_load_config_treats_blank_azure_client_id_as_unset() -> None:
    """A blank AZURE_CLIENT_ID is normalised to None rather than rejected."""
    env = _required_env() | {"AZURE_CLIENT_ID": "   "}

    config = load_config(env)

    assert config.azure_client_id is None


def test_load_config_rejects_missing_required() -> None:
    """load_config reports all missing required environment variables."""
    with pytest.raises(ConfigError, match=_REQUIRED_NAMES_REGEX):
        load_config({})


def test_load_config_rejects_blank_required(valid_env: dict[str, str]) -> None:
    """load_config rejects blank required environment variables."""
    blank_env = valid_env | {name: "" for name in _REQUIRED_ENV_NAMES}

    with pytest.raises(ConfigError, match=_REQUIRED_NAMES_REGEX):
        load_config(blank_env)


def test_load_config_rejects_non_numeric(valid_env: dict[str, str]) -> None:
    """load_config rejects non-integer numeric fields."""
    env = valid_env | {"MIN_TOKENS": _NON_NUMERIC_MIN_TOKENS}

    with pytest.raises(ConfigError, match="MIN_TOKENS"):
        load_config(env)


def test_load_config_rejects_max_below_min(valid_env: dict[str, str]) -> None:
    """load_config rejects a maximum token count below the minimum."""
    env = valid_env | {"MIN_TOKENS": _HIGHER_MIN_TOKENS, "MAX_TOKENS": _LOWER_MAX_TOKENS}

    with pytest.raises(ConfigError, match=r"MAX_TOKENS.*MIN_TOKENS"):
        load_config(env)


def test_load_config_rejects_negative_jitter(valid_env: dict[str, str]) -> None:
    """load_config rejects negative jitter seconds."""
    env = valid_env | {"MAX_JITTER_SECONDS": _NEGATIVE_JITTER_SECONDS}

    with pytest.raises(ConfigError, match="MAX_JITTER_SECONDS"):
        load_config(env)


def test_load_config_rejects_too_large_jitter(valid_env: dict[str, str]) -> None:
    """load_config rejects jitter seconds beyond the allowed upper bound."""
    env = valid_env | {"MAX_JITTER_SECONDS": _TOO_LARGE_JITTER_SECONDS}

    with pytest.raises(ConfigError, match="MAX_JITTER_SECONDS"):
        load_config(env)


def test_load_config_rejects_invalid_log_level(valid_env: dict[str, str]) -> None:
    """load_config rejects unsupported log levels."""
    env = valid_env | {"LOG_LEVEL": _INVALID_LOG_LEVEL}

    with pytest.raises(ConfigError, match="LOG_LEVEL"):
        load_config(env)


def test_load_config_accepts_valid(valid_env: dict[str, str]) -> None:
    """load_config parses a fully valid environment."""
    config = load_config(valid_env)

    assert isinstance(config, AppConfig)
    assert config.foundry_endpoint == _VALID_FOUNDRY_ENDPOINT
    assert config.model_deployment == _VALID_MODEL_DEPLOYMENT
    assert config.azure_client_id == _VALID_AZURE_CLIENT_ID
    assert config.min_tokens == _VALID_MIN_TOKENS
    assert config.max_tokens == _VALID_MAX_TOKENS
    assert config.max_jitter_seconds == _VALID_MAX_JITTER_SECONDS
    assert config.auth_retry_seconds == _VALID_AUTH_RETRY_SECONDS
    assert config.random_seed == _VALID_RANDOM_SEED
    assert config.log_level == _VALID_LOG_LEVEL


def test_load_config_uses_defaults() -> None:
    """load_config supplies documented defaults for omitted optional variables."""
    config = load_config(_required_env())

    assert config.foundry_endpoint == _VALID_FOUNDRY_ENDPOINT
    assert config.model_deployment == _VALID_MODEL_DEPLOYMENT
    assert config.azure_client_id is None
    assert config.min_tokens == _VALID_MIN_TOKENS
    assert config.max_tokens == _VALID_MAX_TOKENS
    assert config.max_jitter_seconds == _VALID_MAX_JITTER_SECONDS
    assert config.auth_retry_seconds == _VALID_AUTH_RETRY_SECONDS
    assert config.log_level == _VALID_LOG_LEVEL
    assert config.random_seed is _DEFAULT_RANDOM_SEED
