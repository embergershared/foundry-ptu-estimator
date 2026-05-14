"""Bundled Project Gutenberg corpus access.

Loads the cleaned `.txt` files shipped under `tpu_est.data.corpus` and exposes a
single concatenated token stream pre-encoded with a caller-supplied tiktoken
encoder. The token stream is built lazily on first access and cached for the
process lifetime.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tiktoken import Encoding

_CORPUS_PACKAGE = "tpu_est.data.corpus"


@dataclass(frozen=True)
class CorpusEntry:
    """A single bundled title: its slug and cleaned UTF-8 text."""

    slug: str
    text: str


def iter_entries() -> Iterator[CorpusEntry]:
    """Yield every bundled `.txt` file as a `CorpusEntry`, sorted by slug."""
    corpus_dir = files(_CORPUS_PACKAGE)
    paths = sorted(
        (path for path in corpus_dir.iterdir() if path.name.endswith(".txt")),
        key=lambda path: path.name,
    )
    for path in paths:
        slug = path.name.removesuffix(".txt")
        yield CorpusEntry(slug=slug, text=path.read_text(encoding="utf-8"))


class Corpus:
    """Lazy, pre-tokenized concatenation of every bundled title.

    The concatenated token stream is built on first access and cached. Use
    `tokens()` to read it. The encoder is held by reference so callers can
    decode slices consistently.
    """

    def __init__(self, encoder: Encoding) -> None:
        """Bind the corpus to a tiktoken encoder; tokens are not built yet."""
        self._encoder = encoder
        self._tokens: list[int] | None = None
        self._slugs: tuple[str, ...] | None = None

    @property
    def encoder(self) -> Encoding:
        """The bound tiktoken encoder."""
        return self._encoder

    @property
    def slugs(self) -> tuple[str, ...]:
        """Slugs of every bundled title, in sorted order."""
        if self._slugs is None:
            self._build()
        assert self._slugs is not None
        return self._slugs

    def tokens(self) -> list[int]:
        """The concatenated token stream across every bundled title."""
        if self._tokens is None:
            self._build()
        assert self._tokens is not None
        return self._tokens

    @property
    def token_count(self) -> int:
        """Total number of tokens across every bundled title."""
        return len(self.tokens())

    def _build(self) -> None:
        slugs: list[str] = []
        token_stream: list[int] = []
        for entry in iter_entries():
            slugs.append(entry.slug)
            token_stream.extend(self._encoder.encode(entry.text))
        if not slugs:
            raise RuntimeError(f"No corpus files found in package '{_CORPUS_PACKAGE}'.")
        self._slugs = tuple(slugs)
        self._tokens = token_stream
