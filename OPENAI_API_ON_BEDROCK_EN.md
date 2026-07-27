<div align="center">

# OpenAI API on Amazon Bedrock

**Feature compatibility of OpenAI GPT-5.6 on Amazon Bedrock**

[中文版](OPENAI_API_ON_BEDROCK_CN.md)

</div>

---

This document walks through each OpenAI Responses API feature and its support status for the GPT-5.6 tiers (Terra / Sol / Luna) on Amazon Bedrock, along with the access path and behavioral notes. It is the OpenAI counterpart to [ANTHROPIC_API_ON_BEDROCK_EN.md](ANTHROPIC_API_ON_BEDROCK_EN.md).

> 📌 **Verification method**: measured against the Bedrock `bedrock-mantle` endpoint (OpenAI Responses API) using the `openai` Python SDK. Every ✅ has a corresponding test script (`gpt/test_01`–`gpt/test_09`).
> 📅 **Verified**: 2026-07-23; **web search re-investigated and corrected 2026-07-27**. Model `openai.gpt-5.6-terra` in `us-east-1` unless noted (web search cross-checked on all three tiers in `us-east-1` / `us-east-2` / `us-west-2`).
>
> ⚠️ **Correction (2026-07-27)**: an earlier version of this document concluded that hosted web search does not work on Bedrock. That was wrong — it works, and is gated by the `bedrock-websearch:*` IAM permission. The original conclusion came from testing only with a default Bedrock API key, whose IAM user lacks that permission, and the failure is silent. See [§5](#5-web-search--works-but-gated-by-an-iam-permission).

## Table of Contents

- [1. Model Status & Tiers](#1-model-status--tiers)
- [2. Access & Authentication](#2-access--authentication)
- [3. Feature Overview](#3-feature-overview)
- [4. Supported Features (detail)](#4-supported-features-detail)
- [5. Web Search — Works, but Gated by an IAM Permission](#5-web-search--works-but-gated-by-an-iam-permission)
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
| **Web Search (hosted tool)** | ✅¹ | [`test_08`](gpt/test_08_web_search.py) | ¹requires `bedrock-websearch:*` IAM perm; fails **silently** without it (see [§5](#5-web-search--works-but-gated-by-an-iam-permission)) |
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

## 5. Web Search — Works, but Gated by an IAM Permission

**Summary: hosted `web_search` DOES work for GPT-5.6 on Bedrock. It is gated by the `bedrock-websearch:*` IAM permission, and without it the tool fails *silently* — which is easy to misdiagnose as "not supported".**

### The permission

```json
{"Effect": "Allow", "Action": "bedrock-websearch:*", "Resource": "*"}
```

Neither **`AmazonBedrockLimitedAccess`** (what console-generated Bedrock API key users get) nor **`AmazonBedrockFullAccess`** includes it. `bedrock-websearch` is a separate service namespace — not covered by `bedrock:*` or `bedrock-mantle:*`, and absent from botocore's service list.

A Bedrock API key is the long-term credential of a dedicated IAM user called `BedrockAPIKey-<suffix>`, so grant it there:

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

Then verify with [`check_gpt56_web_search.py`](check_gpt56_web_search.py) or `gpt/test_08`. With the permission in place the full OpenAI suite runs **9/9**; without it `test_08` is the only failure.

Verified 2026-07-27 on `openai.gpt-5.6-terra` @ `us-east-1` — same API key, only the IAM policy changed:

| Principal's permissions | `web_search_call` result |
|---|---|
| `AmazonBedrockLimitedAccess` (default for API keys) | `failed`, 0 citations ❌ |
| `AmazonBedrockFullAccess` | `failed` ❌ |
| `BedrockAgentCoreFullAccess` / `bedrock-agentcore:*` | `failed` ❌ |
| `bedrock:*` + `bedrock-mantle:*` | `failed` ❌ |
| **+ `bedrock-websearch:*`** | **`completed`, real citations ✅** |
| `AdministratorAccess` (`Action:"*"`) | `completed` ✅ |

With the permission the model returns real data, e.g. *"NVDA is currently $206.84 USD per share"* citing `investor.nvidia.com`.

### The silent-failure trap

Without `bedrock-websearch:*` the API returns **HTTP 200**, the model plans real queries and emits `web_search_call` items (both `search` and `open_page` actions) — but every one has `status: "failed"`, there are no citations, and the model says "web search is temporarily unavailable". **There is no `AccessDenied`.** Nothing in the response points at permissions.

### Notes

- The auth *mechanism* is irrelevant: a Bedrock API key (bearer) and SigV4 behave identically. What matters is the permissions of the identity behind them. A Bedrock API key decodes to a dedicated IAM user (`BedrockAPIKey-<suffix>`) carrying `AmazonBedrockLimitedAccess`, which is why the bearer path looks broken by default.
- OpenAI's [compatibility guide](https://developers.openai.com/api/docs/guides/amazon-bedrock) lists "Hosted web search → Not available" on Bedrock (as of the 2026-07-13 launch). **That is out of date / does not account for the permission** — it demonstrably works.
- The exact action verb under `bedrock-websearch` is undocumented; `bedrock-websearch:*` is the practical grant. (`Search`, `InvokeWebSearch`, `WebSearch`, `OpenPage`, `Retrieve`, `Query`, `Fetch`, `GetPage`, `Browse`, `PerformSearch` were each tested and are not it.)
- Other hosted tools (`file_search`, `image_generation`, `code_interpreter`, `computer_use_preview`, `shell`, remote MCP via `server_url`) are genuinely unsupported — **hard-rejected with 400** at schema validation, which is permission-independent. See [§6](#6-capability-double-check-vs-openais-table).
- **Claude models cannot do web search on Bedrock at all** — Anthropic's `web_search_20250305` tool type is rejected at validation on both `bedrock-runtime` and `bedrock-mantle`, even with full permissions. See the [Anthropic guide](ANTHROPIC_API_ON_BEDROCK_EN.md).

---

## 6. Capability Double-Check vs OpenAI's Table

Each capability in OpenAI's [OpenAI models in Amazon Bedrock](https://developers.openai.com/api/docs/guides/amazon-bedrock) feature table (as of the 2026-07-13 launch) was exercised directly against `openai.gpt-5.6-terra` in `us-east-1`. Every claim matched **except hosted web search**, which works once `bedrock-websearch:*` is granted (see §5). Consolidated in [`test_09`](gpt/test_09_capability_matrix.py).

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
| Hosted web search | Not available | **works** given `bedrock-websearch:*`; silently `failed` without it | ❌ doc is stale |
| Hosted file search | Not available | **400** tool type not supported | ✅ |
| Image generation tool | Not available | **400** tool type not supported | ✅ |
| Code interpreter | Not available | **400** tool type not supported | ✅ |
| Computer use | Not available | **400** tool type not supported | ✅ |
| Shell tool | Not available | **400** tool type not supported | ✅ |
| Remote MCP servers (`server_url`) | Not available | **400** "use a connector ARN instead" | ✅ |

### Two nuances the flat table doesn't show

1. **Web search is mislabeled in OpenAI's table, and its failure mode is a trap.** `web_search` / `web_search_preview` are *accepted at validation* and actually **work** — provided the caller holds `bedrock-websearch:*`. Without that permission they fail at execution (`status="failed"`) with **no AccessDenied**, which looks identical to "unsupported". Every other hosted tool (`file_search`, `image_generation`, `code_interpreter`, `computer_use_preview`, `shell`) is *hard-rejected with a 400* before inference — those really are unsupported, permission-independent.

2. **The API reports its own supported tool-type allow-list.** The 400 messages state: *"Supported tool types are: `function`, `mcp`, `custom`, `namespace`, `tool_search`."* Note `web_search` is **not** in this list (consistent with "not available"), yet it is inconsistently accepted rather than rejected. `namespace` is a supported type not mentioned in OpenAI's table at all.

### Endpoint / API / region facts

| Item | Status | Note |
|------|:---:|------|
| `bedrock-runtime` endpoint | ❌ | GPT-5.6 is `bedrock-mantle` only |
| `Invoke` / `Converse` / `Chat Completions` APIs | ❌ | `Responses` only |
| Geo / Global cross-region inference | ❌ | In-region only |
| Audio / Speech / Video input; Embedding / Image / Speech / Video output | ❌ | Text+image in, text out only |
| `openai.gpt-5.6-sol` in `us-west-2` | ❌ (measured) | 404 as of 2026-07-23, despite the model card |
