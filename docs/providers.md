# LLM providers

The harness uses **exactly one** backend per run, selected with `LLM_PROVIDER` or `--provider`. If that backend fails, the run stops with an error. **There is no fallback** to the other provider.

## Local: Ollama

**Requirements**

- [Ollama](https://ollama.com/) installed and running: `ollama serve`
- Model pulled: `ollama pull llama3.2` (or your chosen model)

**`.env`**

```env
LLM_PROVIDER=local
OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT_SEC=300
```

Ollama exposes an OpenAI-compatible `POST /v1/chat/completions` API. The client:

1. Checks reachability via `GET /api/tags` (fail fast if Ollama is down).
2. Requests JSON via `response_format`; if the model rejects it, retries **once** without `response_format` (still on Ollama — not a switch to OpenRouter).

**Common errors**

| Message | Action |
|---------|--------|
| `Failed to connect to local LLM` | Start `ollama serve` |
| `model … not found (HTTP 404)` | `ollama pull <model>` |
| Invalid JSON in response | Try a stronger model or shorter chunk (`REVIEW_MAX_CHUNK_LINES`) |

## Remote: OpenRouter

**`.env`**

```env
LLM_PROVIDER=remote
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

**Common errors**

| Message | Action |
|---------|--------|
| `OPENROUTER_API_KEY is not set` | Set key or use `LLM_PROVIDER=local` |
| HTTP 401/403 | Check API key |
| HTTP 429 | Rate limit; retry later or reduce `--max-chunks` |

## CLI override

```bash
code-review --provider local ./src
code-review --provider remote ./src
```

Aliases: `ollama` → local, `openrouter` → remote.

## CLI status steps

Progress is printed on **stderr** (unless `-q`):

1. Configuration loaded  
2. Collecting files  
3. Chunking  
4. LLM calls (sub-steps: calling → generating → done)  
5. Merging findings  
6. Generating report  
7. Writing report (when `-o` is used)

The provider name shown in step 4 is **Ollama** or **OpenRouter**, matching the selected mode.