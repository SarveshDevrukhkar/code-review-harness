# Code Review Harness

LLM-powered code review CLI for **security**, **bugs**, **code quality**, and **best practices**. Use **local Ollama** or **remote OpenRouter** — one provider per run, no automatic fallback.

**Requirements:** Python 3.10+; [Ollama](https://ollama.com/) and/or an [OpenRouter](https://openrouter.ai/) API key.

## Setup

```bash
git clone https://github.com/SarveshDevrukhkar/code-review-harness.git
cd code-review-harness
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env: LLM_PROVIDER and Ollama or OpenRouter settings
```

### Ollama (local)

```bash
ollama serve
ollama pull llama3.2   # or your model
```

### OpenRouter (remote)

Set `OPENROUTER_API_KEY` in `.env`. See [OpenRouter](https://openrouter.ai/).

## Configuration (`.env`)

| Variable | When | Description |
|----------|------|-------------|
| `LLM_PROVIDER` | Always | `local` (Ollama) or `remote` (OpenRouter) |
| `OLLAMA_BASE_URL` | Local | Default `http://127.0.0.1:11434/v1` |
| `OLLAMA_MODEL` | Local | e.g. `llama3.2` |
| `OLLAMA_TIMEOUT_SEC` | Local | Default `300` |
| `OPENROUTER_API_KEY` | Remote | Required for remote |
| `OPENROUTER_MODEL` | Remote | e.g. `openai/gpt-4o-mini` |
| `OPENROUTER_BASE_URL` | Remote | Optional |
| `REVIEW_MAX_FILE_BYTES` | Both | Skip large files |
| `REVIEW_MAX_CHUNK_LINES` | Both | Chunk size |
| `REVIEW_TEMPERATURE` | Both | LLM temperature (default `0.2`) |
| `REVIEW_MAX_TOKENS` | Both | Max tokens per completion (default `4096`) |
| `OPENROUTER_TIMEOUT_SEC` | Remote | Request timeout in seconds (default `120`; `REVIEW_LLM_TIMEOUT_SEC` also accepted) |

See [docs/providers.md](docs/providers.md) for troubleshooting and behavior details.

## Usage

Review a single file or directory:

```bash
code-review ~/Desktop/test.py
code-review . --ext py
```

Override provider for one run:

```bash
code-review --provider local ~/Desktop/test.py
code-review --provider remote ~/Desktop/test.py
```

Git changes:

```bash
code-review --git .
code-review --git --staged .
code-review --git --diff main...HEAD .
```

Review passes:

```bash
code-review . --passes unified
code-review . --passes all
code-review . --passes security,bugs
```

Output (creates `reports/` if missing):

```bash
code-review . --format md -o reports/review.md
code-review . --format both -o reports/my_test_review.md
```

Quiet (no status lines):

```bash
code-review . -q
```

CI gate:

```bash
code-review --git --fail-on high .
```

## CLI status output

Unless `-q` is set, stderr shows steps `[1/7]` … `[7/7]`: config, collect, chunk, LLM calls (Ollama or OpenRouter), merge, generate report, write files.

## Project layout

- `src/code_review_harness/clients/` — Ollama and OpenRouter HTTP clients
- `src/code_review_harness/config.py` — provider validation
- `src/code_review_harness/progress.py` — status steps
- `src/code_review_harness/collector.py` — files and git diff
- `src/code_review_harness/orchestrator.py` — pipeline
- `src/code_review_harness/report/` — Markdown and JSON

Run as module:

```bash
python -m code_review_harness .
```

## Notes

- Keep `.env` out of git (see `.gitignore`).
- Use `--max-chunks` or `--ext` on large trees.
- Findings are model-generated; verify critical issues manually.

## License

[MIT](LICENSE)
