# Corpus manifest

Encoder: `tiktoken o200k_base`
Generated: 2026-05-14

| Slug | Title | Author | PG ID | Source URL | SHA-256 (first 16) | Bytes | Chars | Tokens |
|------|-------|--------|-------|------------|--------------------|-------|-------|--------|
| `war-and-peace` | War and Peace | Leo Tolstoy | 2600 | https://www.gutenberg.org/cache/epub/2600/pg2600.txt | `25709930c82b89ce` | 3272440 | 3206589 | 765583 |
| `anna-karenina` | Anna Karenina | Leo Tolstoy | 1399 | https://www.gutenberg.org/cache/epub/1399/pg1399.txt | `e194f4c01657c1d0` | 2008003 | 1964472 | 478611 |
| `moby-dick` | Moby Dick; or, The Whale | Herman Melville | 2701 | https://www.gutenberg.org/cache/epub/2701/pg2701.txt | `948adba2fac40c77` | 1234291 | 1218725 | 305395 |
| `count-of-monte-cristo` | The Count of Monte Cristo | Alexandre Dumas | 1184 | https://www.gutenberg.org/cache/epub/1184/pg1184.txt | `af22743ab8a38dbc` | 2704799 | 2626109 | 641563 |
| `don-quixote` | Don Quixote | Miguel de Cervantes | 996 | https://www.gutenberg.org/cache/epub/996/pg996.txt | `a01c8f632a1af642` | 2327114 | 2297414 | 571203 |
| `bleak-house` | Bleak House | Charles Dickens | 1023 | https://www.gutenberg.org/cache/epub/1023/pg1023.txt | `68ae22fb16148e44` | 1984801 | 1939161 | 481956 |

**Total tokens:** 3244311
**Average tokens per title:** 540718

## Detailed audit trail

The table above is the package manifest consumed by humans. The notes below
make the corpus build auditable without requiring network access at runtime.
Each title was decoded as UTF-8, stripped between the Gutenberg START/END
markers, normalized to LF line endings, collapsed to at most two consecutive
blank lines, and token-counted with `tiktoken.get_encoding("o200k_base")`.

### 1. `war-and-peace`

- Title: War and Peace
- Author: Leo Tolstoy
- Project Gutenberg ID: 2600
- Source URL: https://www.gutenberg.org/cache/epub/2600/pg2600.txt
- Cleaned file: `war-and-peace.txt`
- SHA-256: `25709930c82b89ce118bf5daf938c5fd4a1895df61e4e4722b6c575568073f86`
- SHA-256 first 16: `25709930c82b89ce`
- UTF-8 byte size: 3272440
- Character count: 3206589
- `o200k_base` token count: 765583
- Gutenberg START marker present after cleaning: no
- Gutenberg END marker present after cleaning: no
- Line endings: LF
- Minimum-size check: passed (>= 100,000 characters)
- Runtime use: offline prompt prose for synthetic LLM token-traffic generation

### 2. `anna-karenina`

- Title: Anna Karenina
- Author: Leo Tolstoy
- Project Gutenberg ID: 1399
- Source URL: https://www.gutenberg.org/cache/epub/1399/pg1399.txt
- Cleaned file: `anna-karenina.txt`
- SHA-256: `e194f4c01657c1d0b43521604117e8c4056c4d894acf383d5ac0c9bf42623868`
- SHA-256 first 16: `e194f4c01657c1d0`
- UTF-8 byte size: 2008003
- Character count: 1964472
- `o200k_base` token count: 478611
- Gutenberg START marker present after cleaning: no
- Gutenberg END marker present after cleaning: no
- Line endings: LF
- Minimum-size check: passed (>= 100,000 characters)
- Runtime use: offline prompt prose for synthetic LLM token-traffic generation

### 3. `moby-dick`

- Title: Moby Dick; or, The Whale
- Author: Herman Melville
- Project Gutenberg ID: 2701
- Source URL: https://www.gutenberg.org/cache/epub/2701/pg2701.txt
- Cleaned file: `moby-dick.txt`
- SHA-256: `948adba2fac40c77b5eb9754bb86bf81b4d9d028bb3372f8d331413d3ee27528`
- SHA-256 first 16: `948adba2fac40c77`
- UTF-8 byte size: 1234291
- Character count: 1218725
- `o200k_base` token count: 305395
- Gutenberg START marker present after cleaning: no
- Gutenberg END marker present after cleaning: no
- Line endings: LF
- Minimum-size check: passed (>= 100,000 characters)
- Runtime use: offline prompt prose for synthetic LLM token-traffic generation

### 4. `count-of-monte-cristo`

- Title: The Count of Monte Cristo
- Author: Alexandre Dumas
- Project Gutenberg ID: 1184
- Source URL: https://www.gutenberg.org/cache/epub/1184/pg1184.txt
- Cleaned file: `count-of-monte-cristo.txt`
- SHA-256: `af22743ab8a38dbcb96b80e3861af940fffdc2f89eabe071b860e140422e3025`
- SHA-256 first 16: `af22743ab8a38dbc`
- UTF-8 byte size: 2704799
- Character count: 2626109
- `o200k_base` token count: 641563
- Gutenberg START marker present after cleaning: no
- Gutenberg END marker present after cleaning: no
- Line endings: LF
- Minimum-size check: passed (>= 100,000 characters)
- Runtime use: offline prompt prose for synthetic LLM token-traffic generation

### 5. `don-quixote`

- Title: Don Quixote
- Author: Miguel de Cervantes
- Project Gutenberg ID: 996
- Source URL: https://www.gutenberg.org/cache/epub/996/pg996.txt
- Cleaned file: `don-quixote.txt`
- SHA-256: `a01c8f632a1af64247fcf76669cdf184fb2829d757ef2d8ae468d53f66b7ee13`
- SHA-256 first 16: `a01c8f632a1af642`
- UTF-8 byte size: 2327114
- Character count: 2297414
- `o200k_base` token count: 571203
- Gutenberg START marker present after cleaning: no
- Gutenberg END marker present after cleaning: no
- Line endings: LF
- Minimum-size check: passed (>= 100,000 characters)
- Runtime use: offline prompt prose for synthetic LLM token-traffic generation

### 6. `bleak-house`

- Title: Bleak House
- Author: Charles Dickens
- Project Gutenberg ID: 1023
- Source URL: https://www.gutenberg.org/cache/epub/1023/pg1023.txt
- Cleaned file: `bleak-house.txt`
- SHA-256: `68ae22fb16148e44f56a2f54c34d1d9c923424575b591b2e2cbd22866b043c5a`
- SHA-256 first 16: `68ae22fb16148e44`
- UTF-8 byte size: 1984801
- Character count: 1939161
- `o200k_base` token count: 481956
- Gutenberg START marker present after cleaning: no
- Gutenberg END marker present after cleaning: no
- Line endings: LF
- Minimum-size check: passed (>= 100,000 characters)
- Runtime use: offline prompt prose for synthetic LLM token-traffic generation

