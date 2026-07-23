# Bedrock API Feature Tests

Verify third-party model API features on Amazon Bedrock, organized into two parallel sections:

- **`claude/`** — Anthropic API features via the `bedrock-runtime` **InvokeModel** API.
- **`gpt/`** — OpenAI GPT-5.6 features via the `bedrock-mantle` **Responses** API.

## Feature Guides

| Provider | Guide |
|----------|-------|
| Anthropic (Claude) | [中文](ANTHROPIC_API_ON_BEDROCK_CN.md) · [English](ANTHROPIC_API_ON_BEDROCK_EN.md) |
| OpenAI (GPT-5.6) | [中文](OPENAI_API_ON_BEDROCK_CN.md) · [English](OPENAI_API_ON_BEDROCK_EN.md) |

## Prerequisites

- Python 3.12+ (`uv sync` to install deps: `boto3`, `anthropic`, `openai`)
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- **Claude section**: access to `global.anthropic.claude-sonnet-4-6` in `us-east-1`
- **OpenAI section**: a **Bedrock API key** in the `AWS_BEARER_TOKEN_BEDROCK` env var, and access to `openai.gpt-5.6-terra` on the `bedrock-mantle` endpoint in `us-east-1`

## Setup

```bash
uv sync
```

## Run

```bash
# Claude section (24 tests, InvokeModel)
uv run python claude/run_all_tests.py

# OpenAI section (9 tests, Responses API)
uv run python gpt/run_all_tests.py

# A single test
uv run python gpt/test_08_web_search.py
```

## OpenAI (GPT-5.6) Test List

| # | Test | Feature | Result |
|---|------|---------|:---:|
| 01 | `test_01_basic.py` | Responses API basic | ✅ |
| 02 | `test_02_streaming.py` | Streaming (SSE) | ✅ |
| 03 | `test_03_tool_use.py` | Client-side tool use (function calling) | ✅ |
| 04 | `test_04_reasoning.py` | Reasoning (effort control) | ✅ |
| 05 | `test_05_structured_outputs.py` | Structured outputs (JSON schema) | ✅ |
| 06 | `test_06_vision.py` | Vision (image input) | ✅ |
| 07 | `test_07_prompt_caching.py` | Prompt caching | ✅ |
| 08 | `test_08_web_search.py` | Web search (server-side hosted tool) | ❌ not functional |
| 09 | `test_09_capability_matrix.py` | Capability double-check vs OpenAI compat table | ✅ |

The three tiers (`openai.gpt-5.6-terra` / `-sol` / `-luna`) are configured in [`gpt/helpers.py`](gpt/helpers.py); Terra is the default. See the [OpenAI feature guide](OPENAI_API_ON_BEDROCK_EN.md) for details, especially [why web search does not work](OPENAI_API_ON_BEDROCK_EN.md#5-web-search--not-functional) and the [full capability double-check](OPENAI_API_ON_BEDROCK_EN.md#6-capability-double-check-vs-openais-table).

## Claude Test List

24 tests (`claude/test_01`–`test_24`) covering the Anthropic Messages API on Bedrock — Messages, streaming, tool use, thinking, prompt caching, vision, PDF, citations, structured outputs, computer-use tools, and version-specific changes. See the [Anthropic feature guide](ANTHROPIC_API_ON_BEDROCK_EN.md).

## Configuration

- Claude: edit `claude/helpers.py` (`REGION`, `MODEL_ID`).
- OpenAI: edit `gpt/helpers.py` (`REGION`, `MODEL_ID` = `TERRA`/`SOL`/`LUNA`).
