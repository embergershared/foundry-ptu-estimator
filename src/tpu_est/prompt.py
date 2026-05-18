"""Token-counted prompt assembly.

Builds prose prompts of an exact target token count by sampling a contiguous
random window from the bundled corpus token stream. The window is over-sampled
by a small margin and re-encoded so the returned string round-trips to exactly
`target_tokens` tokens under the caller's tiktoken encoder.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Final

from tpu_est.corpus import Corpus

_OVERSAMPLE_MARGIN: Final = 16


@dataclass(frozen=True)
class AssembledPrompt:
    """A prose prompt sized exactly to a target token count."""

    text: str
    target_tokens: int
    actual_tokens: int


def build_prompt(
    *,
    target_tokens: int,
    corpus: Corpus,
    rng: random.Random,
) -> AssembledPrompt:
    """Assemble a prose prompt of exactly `target_tokens` tokens.

    The returned `AssembledPrompt.actual_tokens` is guaranteed to equal
    `target_tokens` for the encoder bound to `corpus`. `ValueError` is raised
    if `target_tokens` cannot fit inside the bundled corpus (with margin).
    """
    if target_tokens <= 0:
        raise ValueError(f"target_tokens must be positive, got {target_tokens}")

    window = target_tokens + _OVERSAMPLE_MARGIN
    tokens = corpus.tokens(min_count=window)
    capacity = len(tokens) - _OVERSAMPLE_MARGIN
    if target_tokens > capacity:
        raise ValueError(
            f"target_tokens={target_tokens} exceeds corpus capacity ({capacity}); "
            f"add more titles or lower the upper bound."
        )

    start = rng.randint(0, len(tokens) - window)
    raw_slice = corpus.encoder.decode(tokens[start : start + window])
    re_encoded = corpus.encoder.encode(raw_slice)[:target_tokens]
    text = corpus.encoder.decode(re_encoded)
    actual = len(corpus.encoder.encode(text))
    if actual != target_tokens:
        raise RuntimeError(
            f"Prompt assembly failed: target={target_tokens}, actual={actual}. "
            f"Encoder may not round-trip cleanly for this slice."
        )
    return AssembledPrompt(
        text=text,
        target_tokens=target_tokens,
        actual_tokens=actual,
    )
