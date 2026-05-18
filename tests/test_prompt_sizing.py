"""Prompt sizing tests for tpu_est.prompt."""

from __future__ import annotations

import random

import pytest
from pytest_mock import MockerFixture

from tpu_est.corpus import Corpus, CorpusEntry
from tpu_est.prompt import build_prompt

_MIN_TARGET_TOKENS = 30_000
_MEDIUM_TARGET_TOKENS = 100_000
_LARGE_TARGET_TOKENS = 250_000
_EXTRA_LARGE_TARGET_TOKENS = 500_000
_MAX_TARGET_TOKENS = 700_000
_RANDOM_TARGET_SEED = 2026
_RANDOM_TARGET_COUNT = 5
_INVALID_NON_POSITIVE_TARGETS = (0, -1)
_MEANINGFUL_TARGET_TOKENS = 5_000
_MIN_MEANINGFUL_CHARS = 1_000
_PARTIAL_CORPUS_TOKENS = 3
_COMPLETE_CORPUS_TOKENS = 7

_BOUNDARY_TARGET_TOKENS = (
    _MIN_TARGET_TOKENS,
    _MEDIUM_TARGET_TOKENS,
    _LARGE_TARGET_TOKENS,
    _EXTRA_LARGE_TARGET_TOKENS,
    _MAX_TARGET_TOKENS,
)


def _random_target_tokens() -> tuple[int, ...]:
    rng = random.Random(_RANDOM_TARGET_SEED)
    return tuple(
        rng.randint(_MIN_TARGET_TOKENS, _MAX_TARGET_TOKENS) for _ in range(_RANDOM_TARGET_COUNT)
    )


_TARGET_TOKENS = (*_BOUNDARY_TARGET_TOKENS, *_random_target_tokens())


@pytest.mark.parametrize("target_tokens", _TARGET_TOKENS)
def test_build_prompt_matches_target_token_count(corpus: Corpus, target_tokens: int) -> None:
    """build_prompt returns exactly the requested token count."""
    prompt = build_prompt(
        target_tokens=target_tokens,
        corpus=corpus,
        rng=random.Random(target_tokens),
    )

    assert prompt.actual_tokens == target_tokens


@pytest.mark.parametrize("target_tokens", _INVALID_NON_POSITIVE_TARGETS)
def test_build_prompt_rejects_zero_or_negative(corpus: Corpus, target_tokens: int) -> None:
    """build_prompt rejects non-positive token targets."""
    with pytest.raises(ValueError, match="target_tokens must be positive"):
        build_prompt(
            target_tokens=target_tokens,
            corpus=corpus,
            rng=random.Random(_RANDOM_TARGET_SEED),
        )


def test_build_prompt_rejects_too_large(corpus: Corpus) -> None:
    """build_prompt rejects targets that exceed corpus capacity."""
    with pytest.raises(ValueError, match="exceeds corpus capacity"):
        build_prompt(
            target_tokens=corpus.token_count,
            corpus=corpus,
            rng=random.Random(_RANDOM_TARGET_SEED),
        )


def test_build_prompt_returns_meaningful_text(corpus: Corpus) -> None:
    """build_prompt returns substantial prose for a sized prompt."""
    prompt = build_prompt(
        target_tokens=_MEANINGFUL_TARGET_TOKENS,
        corpus=corpus,
        rng=random.Random(_RANDOM_TARGET_SEED),
    )

    assert len(prompt.text) >= _MIN_MEANINGFUL_CHARS


def test_build_prompt_requests_only_required_corpus_tokens(mocker: MockerFixture) -> None:
    """build_prompt avoids full-corpus tokenization for small local debug targets."""
    corpus = mocker.Mock(spec=Corpus)
    encoder = mocker.Mock()
    tokens = list(range(_MEANINGFUL_TARGET_TOKENS + 16))
    corpus.tokens.return_value = tokens
    corpus.encoder = encoder
    encoder.decode.side_effect = ["sample text", "final text"]
    encoder.encode.side_effect = [
        tokens[:_MEANINGFUL_TARGET_TOKENS],
        tokens[:_MEANINGFUL_TARGET_TOKENS],
    ]

    prompt = build_prompt(
        target_tokens=_MEANINGFUL_TARGET_TOKENS,
        corpus=corpus,
        rng=random.Random(_RANDOM_TARGET_SEED),
    )

    corpus.tokens.assert_called_once_with(min_count=_MEANINGFUL_TARGET_TOKENS + 16)
    assert prompt.actual_tokens == _MEANINGFUL_TARGET_TOKENS


def test_corpus_unbounded_tokens_complete_after_partial_build(mocker: MockerFixture) -> None:
    """An unbounded tokens call expands a prior partial local-debug build."""
    encoder = mocker.Mock()
    encoder.encode.side_effect = lambda text: list(range(len(text)))
    mocker.patch(
        "tpu_est.corpus.iter_entries",
        side_effect=lambda: iter(
            (
                CorpusEntry(slug="first", text="abc"),
                CorpusEntry(slug="second", text="defg"),
            )
        ),
    )
    corpus = Corpus(encoder)

    partial_tokens = corpus.tokens(min_count=2)
    complete_tokens = corpus.tokens()

    assert len(partial_tokens) == _PARTIAL_CORPUS_TOKENS
    assert len(complete_tokens) == _COMPLETE_CORPUS_TOKENS
    assert corpus.slugs == ("first", "second")
