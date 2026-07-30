<div align="center">

# OpenAI API on Amazon Bedrock

**Feature compatibility of OpenAI GPT-5.6 on Amazon Bedrock**

[中文版](OPENAI_API_ON_BEDROCK_CN.md)

</div>

---

This document walks through each OpenAI Responses API feature and its support status for the GPT-5.6 tiers (Terra / Sol / Luna) on Amazon Bedrock, along with the access path and behavioral notes. It is the OpenAI counterpart to [ANTHROPIC_API_ON_BEDROCK_EN.md](ANTHROPIC_API_ON_BEDROCK_EN.md).

> 📌 **Verification method**: measured against the Bedrock `bedrock-mantle` endpoint (OpenAI Responses API) using the `openai` Python SDK. Every ✅ has a corresponding test script (`gpt/test_01`–`gpt/test_09`).
> 📅 **Verified**: 2026-07-23; **web search re-investigated and corrected 2026-07-27; re-tested 2026-07-30**. Model `openai.gpt-5.6-terra` in `us-east-1` unless noted.
>
> ⚠️ **Update (2026-07-30)**: hosted web search (`web_search` / `web_search_preview`) is now **hard-rejected with 400** — the same behavior as other unsupported hosted tools. This is a regression from 2026-07-27 when it worked with `bedrock-websearch:*`. Bedrock appears to have removed `web_search` from the accepted tool-type list. See [§5](#5-web-search--no-longer-works-regression-since-2026-07-30).
>
> ~~**Correction (2026-07-27)**: an earlier version of this document concluded that hosted web search does not work on Bedrock. That was wrong — it worked when gated by `bedrock-websearch:*`. As of 2026-07-30 Bedrock has reverted this: the tool type is now rejected at validation.~~

## Table of Contents

- [1. Model Status & Tiers](#1-model-status--tiers)
- [2. Access & Authentication](#2-access--authentication)
- [3. Feature Overview](#3-feature-overview)
- [4. Supported Features (detail)](#4-supported-features-detail)
- [5. Web Search — No Longer Works (Regression since 2026-07-30)](#5-web-search--no-longer-works-regression-since-2026-07-30)
- [6. Capability Double-Check vs OpenAI's Table](#6-capability-double-check-vs-openais-table)

---

## 1. Model Status & Tiers

GPT-5.6 launched on Bedrock on **2026-07-13** in three tiers. All three share a **272K-token context window**, take **text + image** input, produce **text** output, and are reached the same way (only the model ID changes).

| Tier | Model ID | Positioning (model card) |
|------|----------|--------------------------|
| **Sol** | `openai.gpt-5.6-sol` | Most capable — frontier reasoning, SOTA agentic (coding, cybersecurity, research) |
| **Terra** | `openai.gpt-5.6-terra` | Balanced, everyday production; better than GPT-5.5 at lower cost (project default) |
| **Luna** | `openai.gpt-5.6-luna` | Fast & affordable — classification, summarization, routing, real-time |

**Model-card feature support** (same for all three tiers): Server-side tool calling ✅ · Projects ✅ · Prompt caching ✅.

**Regional availability** (model cards list `us-east-1`, `us-east-2`, `us-west-2`, in-region only; no Geo/Global cross-region inference).
> ⚠️ **Measured deviation (2026-07-23)**: `openai.gpt-5.6-sol` returned `404 model does not exist` in `us-west-2`, while it works in `us-east-1` / `us-east-2`. The us-west-2 rollout appears incomplete versus the model card. Terra was verified in `us-east-1`.

Service tier: **Standard** only (Priority / Flex / Reserved are not offered for these models).

---

## 2. Access & Authentication

Unlike the Anthropic models (reached via `bedrock-runtime` InvokeModel / Messages), GPT-5.6 is served **only through the `bedrock-mantle` endpoint using the OpenAI Responses API**.

- **Base URL**: `https://bedrock-mantle.<region>.api.aws/openai/v1`
  > ⚠️ GPT-5.6 uses the **`openai/v1`** path. This differs from the plain **`v1`** path used by other models (e.g. `gpt-oss-120b`) on the same endpoint. Using `/v1` for GPT-5.6 yields a 404.
- **Auth**: a **Bedrock API key** (bearer token) passed as `OPENAI_API_KEY`. AWS SigV4 credentials are also documented for raw HTTP requests, but the OpenAI SDK path requires the API key. In this project the key is read from the `AWS_BEARER_TOKEN_BEDROCK` environment variable.
- **API**: `Responses` only. `Chat Completions`, `Invoke`, and `Converse` are **not** supported.

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://bedrock-mantle.us-east-1.api.aws/openai/v1",
    api_key=os.environ["AWS_BEARER_TOKEN_BEDROCK"],  # Bedrock API key
)
resp = client.responses.create(model="openai.gpt-5.6-terra", input="Hello!")
print(resp.output_text)
```

See [`gpt/helpers.py`](gpt/helpers.py) for the shared client used by the tests.

---

## 3. Feature Overview

| Feature | Status | Test | Notes |
|---------|:---:|------|-------|
| Basic Responses (non-streaming) | ✅ | [`test_01`](gpt/test_01_basic.py) | `responses.create`, `status="completed"` |
| Streaming (SSE) | ✅ | [`test_02`](gpt/test_02_streaming.py) | `response.output_text.delta` events |
| Client-side Tool Use (function calling) | ✅ | [`test_03`](gpt/test_03_tool_use.py) | `type:"function"`, returns `function_call` |
| Reasoning (effort control) | ✅ | [`test_04`](gpt/test_04_reasoning.py) | `reasoning={"effort": ...}`, emits `reasoning` item |
| Structured Outputs (JSON schema) | ✅ | [`test_05`](gpt/test_05_structured_outputs.py) | `text.format.type="json_schema"`, `strict=True` |
| Vision (image input) | ✅ | [`test_06`](gpt/test_06_vision.py) | `input_image` data URL |
| Prompt Caching | ✅ | [`test_07`](gpt/test_07_prompt_caching.py) | `prompt_cache_key`, cache hit on repeat |
| File input (PDF) | ✅ | [`test_09`](gpt/test_09_capability_matrix.py) | `input_file` data URL; text extracted |
| Conversation state | ✅ | [`test_09`](gpt/test_09_capability_matrix.py) | `previous_response_id` recalls prior turn |
| Reasoning effort `max` | ✅ | [`test_09`](gpt/test_09_capability_matrix.py) | `reasoning={"effort":"max"}` accepted |
| Client-side `tool_search` | ✅ | [`test_09`](gpt/test_09_capability_matrix.py) | tool type accepted |
| **Web Search (hosted tool)** | ❌² | [`test_08`](gpt/test_08_web_search.py) | ²hard **400** "tool type not supported" as of 2026-07-30; previously worked with `bedrock-websearch:*` (see [§5](#5-web-search--no-longer-works-regression-since-2026-07-30)) |
| Other hosted tools (file_search / image_generation / code_interpreter / computer_use / shell) | ❌ | [`test_09`](gpt/test_09_capability_matrix.py) | hard **400** "tool type not supported" |
| Remote MCP (`server_url`) / non-Standard service tier | ❌ | [`test_09`](gpt/test_09_capability_matrix.py) | **400**; use connector ARN / on-demand only |
| Server-side custom tools — Lambda / AgentCore Gateway (`mcp` + connector ARN) | ➖ | — | Documented as supported; not exercised here (requires deploying a Lambda/Gateway) |

Legend: ✅ works · ❌ does not work · ➖ not tested here. See [§6](#6-capability-double-check-vs-openais-table) for the full double-check against OpenAI's official table.

---

## 4. Supported Features (detail)

### Basic Responses
`client.responses.create(model=..., input=...)` returns a response with `status="completed"` and `output_text`. Usage is reported under `usage.input_tokens` / `output_tokens`, with `input_tokens_details.{cache_write_tokens,cached_tokens}` and `output_tokens_details.reasoning_tokens`.

### Streaming
Passing `stream=True` yields OpenAI Responses SSE events. Observed sequence includes `response.created` → `response.in_progress` → `response.output_item.added` → `response.content_part.added` → `response.output_text.delta` (repeated) → `response.output_text.done` → `response.content_part.done` → `response.output_item.done` → `response.completed`. Reconstruct text by concatenating the `.delta` fields of `response.output_text.delta`.

### Client-side Tool Use (function calling)
Tools use the Responses shape `{"type":"function","name":...,"description":...,"parameters":{...}}` (note: `name`/`parameters` are top-level, not nested under a `function` key). When the model decides to call a tool, the output contains a `function_call` item with `.name` and a JSON-string `.arguments`.

### Reasoning
`reasoning={"effort": "low"|"medium"|"high"}` controls the thinking budget. The output contains a `reasoning` item followed by a `message`, and `usage.output_tokens_details.reasoning_tokens` is populated. (17 × 23 → "391" verified.)

### Structured Outputs
Pass `text={"format": {"type":"json_schema","name":...,"strict":True,"schema":{...}}}`. `output_text` is a JSON string that conforms to the schema. Verified with a `{name, age}` schema returning valid parseable JSON.

### Vision (image input)
Send multimodal content with `{"type":"input_image","image_url":"data:image/png;base64,..."}` alongside `input_text`. A locally-generated solid-red PNG was correctly described as "Red". (Image input only; image *output* is not supported.)

### Prompt Caching
Send a large shared prefix (via `instructions`) twice with the same `prompt_cache_key`. Observed: first call `cache_write_tokens=5524, cached_tokens=0`; second/third calls `cache_write_tokens=0, cached_tokens=5524` — a reproducible cache hit. Caching keys off the common prefix; supplying `prompt_cache_key` makes hits reliable.

---

## 5. Web Search — No Longer Works (Regression since 2026-07-30)

**Summary: as of 2026-07-30, hosted `web_search` is hard-rejected with 400 "The 'web_search' tool is not supported." — the same behavior as other unsupported hosted tools. This is a regression: it previously worked (2026-07-27) when the caller held `bedrock-websearch:*`.**

### Current behavior (2026-07-30)

```
Error code: 400 - {'error': {'code': 'validation_error',
  'message': "The 'web_search' tool is not supported.",
  'param': None, 'type': 'invalid_request_error'}}
```

Both `web_search` and `web_search_preview` tool types are rejected at schema validation — identical to `file_search`, `code_interpreter`, etc. The `bedrock-websearch:*` IAM permission is irrelevant since the request never reaches the inference layer.

### Historical behavior (2026-07-27, no longer current)

<details>
<summary>Click to expand — prior findings for reference</summary>

On 2026-07-27, `web_search` was accepted at validation and actually worked when the caller held `bedrock-websearch:*`. Without the permission it failed silently (HTTP 200, `web_search_call.status="failed"`, no AccessDenied). The following permission matrix was measured:

| Principal's permissions | `web_search_call` result |
|---|---|
| `AmazonBedrockLimitedAccess` (default for API keys) | `failed`, 0 citations ❌ |
| `AmazonBedrockFullAccess` | `failed` ❌ |
| `BedrockAgentCoreFullAccess` / `bedrock-agentcore:*` | `failed` ❌ |
| `bedrock:*` + `bedrock-mantle:*` | `failed` ❌ |
| **+ `bedrock-websearch:*`** | **`completed`, real citations ✅** |
| `AdministratorAccess` (`Action:"*"`) | `completed` ✅ |

This behavior is no longer reproducible as of 2026-07-30.

</details>

### Notes

- The change affects all three tiers (Terra, Sol, Luna) — Terra verified directly.
- OpenAI's [compatibility guide](https://developers.openai.com/api/docs/guides/amazon-bedrock) lists "Hosted web search → Not available" which now matches measured behavior again.
- **Claude models also cannot do web search on Bedrock** — Anthropic's `web_search_20250305` tool type is rejected at validation on both endpoints. See the [Anthropic guide](ANTHROPIC_API_ON_BEDROCK_EN.md).
- Other hosted tools (`file_search`, `image_generation`, `code_interpreter`, `computer_use_preview`, `shell`) remain unsupported (400 hard reject) as before.

---

## 6. Capability Double-Check vs OpenAI's Table

Each capability in OpenAI's [OpenAI models in Amazon Bedrock](https://developers.openai.com/api/docs/guides/amazon-bedrock) feature table (as of the 2026-07-13 launch) was exercised directly against `openai.gpt-5.6-terra` in `us-east-1`. As of 2026-07-30, all claims now match (web search was previously an exception but Bedrock has reverted its support — see §5). Consolidated in [`test_09`](gpt/test_09_capability_matrix.py).

| OpenAI doc capability | Doc → Bedrock | Measured behavior | Match |
|-----------------------|:---:|-------------------|:---:|
| Text generation | Available | works | ✅ |
| Image input | Available | "Red" PNG identified | ✅ |
| File input | Available (supported types) | number extracted from PDF | ✅ |
| Structured outputs | Available | schema-valid JSON | ✅ |
| Function calling | Available | `function_call` returned | ✅ |
| Streaming | Available | `output_text.delta` events | ✅ |
| Reasoning effort (incl. `max`) | Available | `effort="max"` → correct answer | ✅ |
| Persisted reasoning / conversation state | Available | `previous_response_id` recalls prior turn | ✅ |
| Prompt caching | Implicit + explicit | cache hit reproduced | ✅ |
| Client-side `tool_search` | Available | tool type accepted | ✅ |
| Custom tools (Lambda / AgentCore connector) | Available | `mcp`+connector ARN is the only accepted MCP form | ✅ (not fully exercised) |
| Audio input / WebSocket / Pro mode / Multi-agent / Programmatic tool calling | Not available | not tested (no clean probe) | ➖ |
| Service tiers | On-demand only | `service_tier="flex"` → **400** | ✅ |
| Hosted web search | Not available | **400** "tool type not supported" (as of 2026-07-30; previously worked with `bedrock-websearch:*` on 2026-07-27) | ✅ (now matches) |
| Hosted file search | Not available | **400** tool type not supported | ✅ |
| Image generation tool | Not available | **400** tool type not supported | ✅ |
| Code interpreter | Not available | **400** tool type not supported | ✅ |
| Computer use | Not available | **400** tool type not supported | ✅ |
| Shell tool | Not available | **400** tool type not supported | ✅ |
| Remote MCP servers (`server_url`) | Not available | **400** "use a connector ARN instead" | ✅ |

### Two nuances the flat table doesn't show

1. **Web search had a brief window of availability (2026-07-13 to ~2026-07-30).** Between launch and 2026-07-30, `web_search` / `web_search_preview` were *accepted at validation* and actually **worked** — provided the caller held `bedrock-websearch:*`. As of 2026-07-30, they are hard-rejected with 400 like other unsupported hosted tools. This may have been an unintended exposure that was subsequently locked down, or a temporary regression.

2. **The API reports its own supported tool-type allow-list.** The 400 messages state: *"Supported tool types are: `function`, `mcp`, `custom`, `namespace`, `tool_search`."* Note `web_search` is **not** in this list. `namespace` is a supported type not mentioned in OpenAI's table at all.

### Endpoint / API / region facts

| Item | Status | Note |
|------|:---:|------|
| `bedrock-runtime` endpoint | ❌ | GPT-5.6 is `bedrock-mantle` only |
| `Invoke` / `Converse` / `Chat Completions` APIs | ❌ | `Responses` only |
| Geo / Global cross-region inference | ❌ | In-region only |
| Audio / Speech / Video input; Embedding / Image / Speech / Video output | ❌ | Text+image in, text out only |
| `openai.gpt-5.6-sol` in `us-west-2` | ❌ (measured) | 404 as of 2026-07-23, despite the model card |
