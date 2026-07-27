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
- **Web search (`gpt/test_08`) additionally needs the `bedrock-websearch:*` IAM permission** — see [Web search permission](#web-search-permission) below

## Setup

```bash
uv sync
```

## Run

```bash
# Claude section (25 tests, InvokeModel)
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
| 08 | `test_08_web_search.py` | Web search (server-side hosted tool) | ✅ needs `bedrock-websearch:*` ¹ |
| 09 | `test_09_capability_matrix.py` | Capability double-check vs OpenAI compat table | ✅ |

All 9 pass once the [web search permission](#web-search-permission) is granted.

¹ Web search **works**, but only if the calling identity holds `bedrock-websearch:*`. Without it the call returns HTTP 200 with `web_search_call.status="failed"` and no `AccessDenied` — a silent failure that looks like the feature is unsupported. Neither `AmazonBedrockLimitedAccess` (the default for Bedrock API key users) nor `AmazonBedrockFullAccess` grants it.

The three tiers (`openai.gpt-5.6-terra` / `-sol` / `-luna`) are configured in [`gpt/helpers.py`](gpt/helpers.py); Terra is the default. See the [OpenAI feature guide](OPENAI_API_ON_BEDROCK_EN.md) for details, especially [the web search IAM permission trap](OPENAI_API_ON_BEDROCK_EN.md#5-web-search--works-but-gated-by-an-iam-permission) and the [full capability double-check](OPENAI_API_ON_BEDROCK_EN.md#6-capability-double-check-vs-openais-table).

## Claude Test List

25 tests (`claude/test_01`–`test_25`) covering the Anthropic Messages API on Bedrock — Messages, streaming, tool use, thinking, prompt caching, vision, PDF, citations, structured outputs, computer-use tools, and version-specific changes. `test_25` is a cross-model feature matrix covering **Claude Opus 5** (released 2026-07-24) through Haiku 4.5. See the [Anthropic feature guide](ANTHROPIC_API_ON_BEDROCK_EN.md).

Known environment-dependent results:

- `test_20_count_tokens` needs the `bedrock:CountTokens` IAM permission, which the default Bedrock API key user lacks. Note CountTokens is also genuinely unsupported on `bedrock-runtime` for Opus 5 / Sonnet 5 / Opus 4.8 (it does work for them on `bedrock-mantle`).
- `test_24_image_limits` and `test_25_cross_model_matrix` are multi-minute sweeps; the runner allows them 900s.
- **Claude cannot use web search on Bedrock at all** — the `web_search_20250305` tool type is rejected at validation on every model and on both endpoints, regardless of permissions.

## Web search permission

`gpt/test_08_web_search.py` needs the **`bedrock-websearch:*`** IAM permission on the
calling identity. It is not in `AmazonBedrockLimitedAccess` (what a console-generated
Bedrock API key gets) nor in `AmazonBedrockFullAccess`, and `bedrock-websearch` is a
separate service namespace so `bedrock:*` / `bedrock-mantle:*` do not cover it.

**Without it the failure is silent**: HTTP 200, `web_search_call.status="failed"`,
no citations, and **no `AccessDenied`** — it looks exactly like an unsupported feature.

A Bedrock API key is the long-term credential of a dedicated IAM user named
`BedrockAPIKey-<suffix>`. Grant the permission to that user (replace the name):

```bash
aws iam put-user-policy \
  --user-name BedrockAPIKey-<suffix> \
  --policy-name BedrockWebSearchAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "HostedWebSearchTool",
      "Effect": "Allow",
      "Action": "bedrock-websearch:*",
      "Resource": "*"
    }]
  }'
```

Verify with the dependency-light repro script, which prints each
`web_search_call` status and any citations:

```bash
uv run python check_gpt56_web_search.py
```

Expected once the permission is in place — `status=completed` plus a real citation:

```
web_search_call: status=completed  search='NVDA stock price current Nasdaq official quote'
annotations (citations): [AnnotationURLCitation(url='https://uk.finance.yahoo.com/quote/NVDA/', ...)]
text: NVDA (NVIDIA) was trading at **$209.57 USD** ...
```

The exact action verb under `bedrock-websearch` is undocumented, so `bedrock-websearch:*`
is the practical grant. This gates only the OpenAI hosted web search tool — **Claude
cannot web search on Bedrock at all**, regardless of permissions (the tool type is
rejected at schema validation).

## Configuration

- Claude: edit `claude/helpers.py` (`REGION`, `MODEL_ID`).
- OpenAI: edit `gpt/helpers.py` (`REGION`, `MODEL_ID` = `TERRA`/`SOL`/`LUNA`).
