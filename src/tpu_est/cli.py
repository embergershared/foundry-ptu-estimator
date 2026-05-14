"""CLI orchestration for a single TPU estimation worker execution."""

from __future__ import annotations

import random
import time
from typing import Final

import structlog
import tiktoken
from azure.identity import DefaultAzureCredential

from tpu_est.client import FoundryClient
from tpu_est.config import AppConfig, ConfigError
from tpu_est.corpus import Corpus
from tpu_est.logging_setup import configure_logging
from tpu_est.prompt import build_prompt

_SYSTEM_PROMPT: Final[str] = (
    "You are a careful reader. Summarize the supplied passage in two short sentences."
)
_SUCCESS_EXIT_CODE: Final[int] = 0
_HANDLED_FAILURE_EXIT_CODE: Final[int] = 1
_CONFIG_ERROR_EXIT_CODE: Final[int] = 2


def run_once(config: AppConfig) -> int:
    """Run one jittered prompt generation and Foundry chat completion."""
    try:
        configure_logging(config.log_level)
        logger = structlog.get_logger()

        rng = (
            random.Random(config.random_seed) if config.random_seed is not None else random.Random()
        )
        jitter_seconds = rng.randint(0, config.max_jitter_seconds)
        logger.info("jitter_sleep", seconds=jitter_seconds)
        time.sleep(jitter_seconds)

        target_tokens = rng.randint(config.min_tokens, config.max_tokens)
        corpus = Corpus(tiktoken.get_encoding("o200k_base"))
        prompt = build_prompt(target_tokens=target_tokens, corpus=corpus, rng=rng)
        logger.info(
            "prompt_built",
            target_tokens=target_tokens,
            actual_tokens=prompt.actual_tokens,
            chars=len(prompt.text),
        )

        credential = (
            DefaultAzureCredential(managed_identity_client_id=config.azure_client_id)
            if config.azure_client_id
            else DefaultAzureCredential()
        )
        client = FoundryClient(
            endpoint=config.foundry_endpoint,
            model_deployment=config.model_deployment,
            credential=credential,
            retry_on_auth_error_seconds=config.auth_retry_seconds,
            api_version=config.api_version,
        )
        result = client.complete(system=_SYSTEM_PROMPT, user=prompt.text)
        logger.info(
            "call_complete",
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
            latency_ms=result.latency_ms,
            http_status=result.http_status,
            model_deployment=result.model_deployment,
            response_id=result.response_id,
            finish_reason=result.finish_reason,
            ratelimit_remaining_requests=result.ratelimit_remaining_requests,
            ratelimit_remaining_tokens=result.ratelimit_remaining_tokens,
            target_tokens=target_tokens,
            actual_tokens=prompt.actual_tokens,
        )
        return _SUCCESS_EXIT_CODE
    except ConfigError as error:
        structlog.get_logger().error("config_error", exc_message=str(error))
        return _CONFIG_ERROR_EXIT_CODE
    except Exception as error:
        structlog.get_logger().exception(
            "run_failed",
            exc_type=type(error).__name__,
            exc_message=str(error),
        )
        return _HANDLED_FAILURE_EXIT_CODE
