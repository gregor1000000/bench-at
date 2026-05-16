# BENCH-AT

Benchmark for LLMs using German psychological test items. Three subtests:

| Task | Source | Items | Type |
|------|--------|-------|------|
| **Zahlenfolgen** | `data/raw/Zahlenfolgen.pdf` | 9,996 | Number sequences |
| **Wortflüssigkeit** | `data/raw/Wortflüssigkeit.pdf` | 3,441 | Scrambled letters → German word |
| **3000 Figuren Medium** | `data/raw/3000 Figuren Medium.pdf` | 3,000 | Geometric figure assembly |

## Structure

```
data/
  raw/                          ← original PDFs and CSVs (immutable)
  extract/                      ← extraction pipeline
    process_all.py              ← run all extractors
    extract_numbers.py           → data/canonical/numbers/tasks.jsonl
    extract_words.py             → data/canonical/words/tasks.jsonl
    extract_figures.py           → pre-crops each problem → PNG + tasks.jsonl
  canonical/                    ← auto-generated, stable artifacts
    numbers/tasks.jsonl          ← 9,996 tasks with sha256 fingerprints
    words/tasks.jsonl            ← 3,441 tasks with fingerprints
    figures/
      tasks.jsonl               ← 3,000 tasks with fingerprints
      problems/                 ← 3,000 pre-cropped PNGs (0001.png .. 3000.png)

bench_at/
  registry.py                   ← loads canonical JSONL, lookups by type/slot/fp
  llm.py                        ← shared load_env() + call_llm()
  runner.py                     ← batch runner: iterates tasks, calls LLM, writes JSONL
  prompts/
    __init__.py                 ← dispatcher: build_messages(type, task) → LLM messages
    numbers.py                  ← build_prompt(task) → text prompt
    words.py                    ← build_prompt(task) → text prompt
    figures.py                  ← build_messages(task) → multimodal (image + text)

main.py                         ← entry point (3 modes: interactive / batch / process)
evaluation/                     ← batch output JSONL files (auto-created)
```

## Usage

```bash
# Re-extract canonical tasks from raw sources
uv run python main.py process

# Interactive mode — pick tasks by ID
uv run python main.py numbers                    # interactive
uv run python main.py numbers --dryrun           # preview prompt without API call
uv run python main.py words
uv run python main.py figures

# Batch mode — run many tasks, results to JSONL
uv run python main.py run numbers --range 1-50 --model google/gemma-4-26b-it
uv run python main.py run words --all
uv run python main.py run figures --range 1-100 --dryrun

# All selectors accept: 1,3,5-10,42  or "list" to enumerate
```

## Adding a new subtest

1. Drop the PDF in `data/raw/`
2. Write `data/extract/extract_<name>.py` that writes `data/canonical/<name>/tasks.jsonl`
3. Register it in `data/extract/process_all.py`
4. Run `uv run python main.py process`
5. Tasks are now available via `Registry().by_type("<name>")`

## Stable IDs

Every canonical task carries a `fingerprint` = `SHA256(content)[:12]`. Same content → same fingerprint across re-extracts. Solvers, evaluators, and analysis should reference tasks by fingerprint for stable cross-referencing.
