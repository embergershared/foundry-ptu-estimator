"""Shared pytest fixtures for tpu-est tests."""

from __future__ import annotations

import pytest
import tiktoken

from tpu_est.corpus import Corpus


@pytest.fixture(scope="session")
def corpus() -> Corpus:
    """Build the bundled corpus token stream once per test session."""
    corpus_instance = Corpus(tiktoken.get_encoding("o200k_base"))
    corpus_instance.tokens()
    return corpus_instance


@pytest.fixture
def valid_env() -> dict[str, str]:
    """Return a syntactically valid environment mapping."""
    return {
        "FOUNDRY_ENDPOINT": "https://example.cognitiveservices.azure.com",
        "MODEL_DEPLOYMENT": "gpt-5.4",
        "AZURE_CLIENT_ID": "00000000-0000-0000-0000-000000000000",
        "MIN_TOKENS": "30000",
        "MAX_TOKENS": "700000",
        "MAX_JITTER_SECONDS": "179",
        "AUTH_RETRY_SECONDS": "60",
        "RANDOM_SEED": "42",
        "LOG_LEVEL": "INFO",
    }
