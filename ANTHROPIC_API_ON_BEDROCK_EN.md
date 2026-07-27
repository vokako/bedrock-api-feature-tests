<div align="center">

# Anthropic API on Amazon Bedrock

**Feature compatibility of the Anthropic API on Amazon Bedrock**

[中文版](ANTHROPIC_API_ON_BEDROCK_CN.md)

</div>

---

This document walks through each Anthropic Messages API feature and its native support status on Amazon Bedrock, along with the behavioral differences between models. For Anthropic-specific features not built into Bedrock, it provides proxy-layer or application-layer implementation strategies.

> 📌 **Verification method**: measured against Bedrock InvokeModel (runtime) and the Messages API (mantle). Every ✅ has a corresponding test script (`claude/test_01`–`claude/test_25`).
> 📅 **Latest full re-verification**: 2026-07-27, adding **Claude Opus 5** and re-running the whole matrix across Opus 5 / Sonnet 5 / Fable 5 / Opus 4.8 / 4.7 / 4.6 / Sonnet 4.6 / Haiku 4.5 ([`claude/test_25`](claude/test_25_cross_model_matrix.py)). Prior full sweep 2026-07-03; image limits 2026-07-06.

## Table of Contents

- [1. Model Status & Cross-Model Differences](#1-model-status--cross-model-differences)
- [2. Feature Overview](#2-feature-overview)
- [3. Natively Supported Features](#3-natively-supported-features)
- [4. Features Requiring Proxy Adaptation](#4-features-requiring-proxy-adaptation)
- [5. Beta Header Handling on Bedrock](#5-beta-header-handling-on-bedrock)
- [6. Claude Code / Agent SDK on Bedrock](#6-claude-code--agent-sdk-on-bedrock)
- [7. Opus 4.8 New Features on Bedrock](#7-opus-48-new-features-on-bedrock)

---

## 1. Model Status & Cross-Model Differences

### Current modern Anthropic models on Bedrock

| Model | Invoke (runtime) model ID | Notes |
|-------|--------------------------|-------|
| Claude Opus 5 | `global.anthropic.claude-opus-5` | Released 2026-07-24. **1M context / 128k output**, knowledge cutoff May 2026. In-Region ID is N/A by design — use `global.`/`us.`. Behaves as new-gen. |
| Claude Sonnet 5 | `global.anthropic.claude-sonnet-5` | Released 2026-06-30, most agentic Sonnet, 1M context / 128k output |
| Claude Fable 5 | `global.anthropic.claude-fable-5` | Mythos-class, requires `provider_data_share` retention (see [FABLE5_PROJECT_SETUP.md](FABLE5_PROJECT_SETUP.md)) |
| Claude Opus 4.8 | `global.anthropic.claude-opus-4-8` | drop-in replacement for 4.7 |
| Claude Opus 4.7 | `global.anthropic.claude-opus-4-7` | |
| Claude Opus 4.6 | `global.anthropic.claude-opus-4-6-v1` | |
| Claude Sonnet 4.6 | `global.anthropic.claude-sonnet-4-6` | |
| Claude Haiku 4.5 | `global.anthropic.claude-haiku-4-5-20251001-v1:0` | |

### Cross-model behavior matrix

Measured via `bedrock-runtime` for all models. Opus 5 column and full re-verification 2026-07-27; prior sweep 2026-07-03. Reproduce with [`claude/test_25`](claude/test_25_cross_model_matrix.py).

**Key takeaway: models split into a "new generation" (Opus 5 / Sonnet 5 / Fable 5 / Opus 4.8 / 4.7) and the "4.6 generation" (Opus 4.6 / Sonnet 4.6 / Haiku 4.5).**

| Feature | Opus 5 | Sonnet 5 | Fable 5 | Opus 4.8 | Opus 4.7 | Opus 4.6 | Sonnet 4.6 | Haiku 4.5 |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Basic invocation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Adaptive Thinking (`type:"adaptive"`+`effort`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ no `effort` |
| Legacy Thinking (`type:"enabled"`+`budget_tokens`) | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ✅ | ✅ | ✅ |
| Sampling params `temperature`/`top_p`/`top_k` | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ✅ | ✅ | ✅ |
| Structured Outputs (`output_config.format`) | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ✅ | ✅ | ✅ |
| Mid-conversation System Messages (`role:system`) | ✅ | ✅ | ✅ | ✅ | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 |
| Assistant Prefill | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Min cacheable prompt length (model-card value) | **512** | 4,096 | 1,024 | 4,096 | 4,096 | 4,096 | 1,024 | 4,096 |

Values from each model's AWS model card ("Min tokens per cache checkpoint", authoritative). Rule: **Opus 5 is 512 (the lowest yet), Fable 5 and Sonnet 4.6 are 1,024, and the rest (Sonnet 5, Opus 4.6/4.7/4.8, Haiku 4.5) are 4,096**. Opus 5's 512 threshold was confirmed empirically: a 466-token prefix produced `cache_creation_input_tokens=0`, a 608-token prefix produced 608. Below this length, `cache_control` does nothing.

### Web search is not available on any Claude model (measured 2026-07-27)

Anthropic's native `web_search_20250305` server tool is **rejected at validation** on Bedrock, on every model tested (Opus 5 / Sonnet 5 / Fable 5 / Opus 4.8 / 4.7 / 4.6 / Sonnet 4.6 / Haiku 4.5) and on **both** access paths:

- `bedrock-runtime` InvokeModel — new-gen returns `tool type 'web_search_20250305' is not supported for this model`; the 4.6 generation returns `Input tag 'web_search_20250305' ... does not match any of the expected tags`, whose message enumerates the full allow-list: `bash_20250124`, `custom`, `memory_20250818`, `text_editor_20250124/20250429/20250728`, `tool_search_tool_bm25(_20251119)`, `tool_search_tool_regex(_20251119)`.
- `bedrock-mantle` `/anthropic/v1/messages` (Opus 5 / Opus 4.8 / Sonnet 5) — same `not supported for this model` rejection.

This is a **schema-level rejection and therefore permission-independent**: it still fails with `AdministratorAccess` and with `bedrock-websearch:*` granted. That contrasts with GPT-5.6, where hosted web search does work once `bedrock-websearch:*` is present — see the [OpenAI guide](OPENAI_API_ON_BEDROCK_EN.md#5-web-search--works-but-gated-by-an-iam-permission). To give Claude web results on Bedrock you must do your own retrieval and pass it in as context.

### Opus 5 specifics (measured 2026-07-27)

- **Model IDs**: runtime requires `global.anthropic.claude-opus-5` (or `us.`); the bare in-region `anthropic.claude-opus-5` raises `ValidationException`. On `bedrock-mantle` use the in-region form `anthropic.claude-opus-5` at `/anthropic/v1/messages` (and `anthropic_version` is required there).
- **Works**: adaptive thinking, interleaved thinking + tool use, streaming, vision, PDF input, tool use, citations, prompt caching, bash / text_editor / memory tools, `tool_search`, mid-conversation system messages, `eager_input_streaming` (inside the tool definition), context editing + compaction + `input_examples` (each with its beta header), and the 1M-context beta header is accepted.
- **Rejected**: legacy `thinking.type:"enabled"`, `temperature` (`deprecated for this model`), `output_config.format`, assistant prefill, `web_search_20250305`.
- **CountTokens differs by endpoint.** On `bedrock-runtime` it is **unsupported** for Opus 5 / Sonnet 5 / Opus 4.8 (`The provided model doesn't support counting tokens.`, confirmed under admin credentials, so not a permission issue) — the model card lists Count tokens as not supported on runtime. On **`bedrock-mantle` it works**: `POST /anthropic/v1/messages/count_tokens` with `anthropic_version` returned `{"input_tokens": 11}` for Opus 5. On runtime, Sonnet 4.6 does support it, using an **in-region** model ID and with `max_tokens` present in the counted body.
- **Prompt caching minimum is 512 tokens** (model card), the lowest of any Claude on Bedrock; 4 checkpoints max, 5-minute and 1-hour TTLs, on `system`/`messages`/`tools`.
- **Adaptive thinking is on by default**; per the model card it can be disabled, but then effort is capped at `high`.
- **Computer use** on Opus 5 uses tool type `computer_20251124` with beta header `computer-use-2025-11-24`.
- **APIs**: `Invoke`, `Converse` and `Messages` are supported; `Responses` and `Chat Completions` are not. Service tiers: Standard and Batch only.
- **Not on mantle**: `anthropic.claude-sonnet-4-6` and `anthropic.claude-opus-4-6-v1` return 404 there; Opus 5 / Opus 4.8 / Sonnet 5 are available.

### Key differences

- **Thinking has always worked — the API just changed.** New-gen models removed legacy `thinking.type:"enabled"` + `budget_tokens` (returns 400) in favor of **adaptive thinking** (`thinking.type:"adaptive"` + `output_config.effort`). Verified working (Sonnet 5 / Opus 4.7 produced thousands of thinking tokens on hard problems). Adaptive decides per request whether to think; easy prompts may emit no thinking block — by design, not a fault. Migration: replace `{"type":"enabled","budget_tokens":N}` with `{"type":"adaptive"}` + `output_config:{"effort":"high"}`.
- **Sampling params removed on new-gen**: `temperature`/`top_p`/`top_k` with non-default values return 400. Guide behavior via prompting instead.
- **Structured Outputs has a "generational reversal"**: `output_config.format` works on the **4.6 generation (including Haiku 4.5)** but returns 400 on all new-gen models. Branch by model — 4.6 gen uses `output_config.format`, new-gen uses **forced tool use** (`tool_choice` forcing a tool + `input_schema`).
- **Mid-conversation system messages**: only **Opus 4.8 / Fable 5 / Sonnet 5** accept and honor `role:system` inside `messages` (see [Section 7](#7-opus-48-new-features-on-bedrock)).
- **Prompt cache minimum varies by model**: **Fable 5 and Sonnet 4.6 are 1,024**; **Sonnet 5, Opus 4.6/4.7/4.8, Haiku 4.5 are 4,096** (from each model card's "Min tokens per cache checkpoint"). Below the threshold, `cache_control` does nothing (`cache_creation_input_tokens=0`). The new-gen tokenizer is more "inflationary" — the same text counts ~1.4–1.7× more tokens than the 4.6 gen.
- **Assistant Prefill**: since Claude 4.6 (including new-gen), a trailing assistant message for prefill returns 400 `This model does not support assistant message prefill`. Only Haiku 4.5 still supports it. Alternative: use [Structured Outputs](#structured-outputs) or a system prompt to control format.

### Opus 4.7 adaptation gaps on Bedrock (summary)

Several features are not yet adapted for Opus 4.7 on Bedrock (the beta header is accepted but real parameters error out). **Opus 4.8 fixed most of these** — use 4.8 or 4.6 if you need them:

| Feature | Opus 4.7 behavior |
|---------|-------------------|
| Computer Use (bash/text_editor) | `tool type ... is not supported for this model` |
| Context Editing (message ID) | `messages.0.id: Extra inputs are not permitted` |
| Tool Search | `tool_search ... not supported for this model` |
| Fine-grained Tool Streaming (`eager_input_streaming`) | ~~previously `Extra inputs are not permitted`~~ re-tested 2026-07-17: now works |
| CountTokens | global-only deployment, no in-region ID, unavailable |
| Mid-conversation system messages | `role 'system' is not supported` (4.8 supports it) |

### Notes on Fable 5 / Sonnet 5

- **Fable 5**: was briefly delisted from Bedrock in 2026-06 (runtime 5xx / mantle 404), then relaunched "back on Amazon Bedrock with stronger guardrails"; re-verified working on runtime + mantle on 2026-07-03. As a Mythos-class model it **requires `provider_data_share` retention** (account or project scope) to invoke — see [FABLE5_PROJECT_SETUP.md](FABLE5_PROJECT_SETUP.md) and [test_22](claude/test_22_fable5.py).
- **Sonnet 5** (2026-06-30): most agentic Sonnet, 1M context / 128k output, same features as Sonnet 4.6 (except Priority Tier). Behaves as new-gen on Bedrock.

---

## 2. Feature Overview

| Feature | Anthropic API | Bedrock Converse | Bedrock Invoke | Difference | Test |
|---------|:---:|:---:|:---:|:---:|:---:|
| Messages API basics | ✅ | ✅ | ✅ | None | [test_01](claude/test_01_messages_basic.py) |
| Streaming (SSE) | ✅ | ✅ | ✅ | None | [test_02](claude/test_02_streaming.py) |
| Tool Use | ✅ | ✅ | ✅ | None | [test_03](claude/test_03_tool_use.py) |
| Extended Thinking (legacy, 4.6 gen only) | ✅ | ✅ | ✅ | Removed on new-gen | [test_04](claude/test_04_extended_thinking.py) |
| Adaptive Thinking | ✅ | ✅ | ✅ | Haiku 4.5 has no effort | [test_16](claude/test_16_adaptive_thinking.py) |
| Interleaved Thinking | ✅ | ✅ | ✅ | None | [test_05](claude/test_05_interleaved_thinking.py) |
| Prompt Caching | ✅ | ✅ | ✅ | Min length varies by model | [test_06](claude/test_06_prompt_caching.py) |
| Vision | ✅ | ✅ | ✅ | Ceiling 600/request; 101–600 non-deterministic (some backends cap at 100); reliable safe limit 100 | [test_07](claude/test_07_vision.py) [test_24](claude/test_24_image_limits.py) |
| PDF Support | ✅ | ✅ | ✅ | None | [test_08](claude/test_08_pdf_support.py) |
| Citations | ✅ | ✅ | ✅ | None | [test_09](claude/test_09_citations.py) |
| Structured Outputs (`output_config.format`) | ✅ | ✅ | ✅ | **4.6 gen only**; new-gen 400 | [test_10](claude/test_10_structured_outputs.py) |
| Fine-grained Tool Streaming | ✅ | ✅ | ✅ | 4.6 series + next-gen (Opus 4.7/4.8, Fable 5; re-tested 2026-07-17) | [test_11](claude/test_11_eager_input_streaming.py) |
| Compaction | ✅ | ✅ | ✅ | None | [test_12](claude/test_12_compaction.py) |
| Context Editing | ✅ | ✅ | ✅ | Opus 4.7 unavailable | [test_13](claude/test_13_context_editing.py) |
| Tool Search | ✅ | ❌ | ✅ | Invoke API only; Opus 4.7 unavailable | [test_14](claude/test_14_tool_search.py) |
| Tool Input Examples | ✅ | ❌ | ✅ | Invoke API only | [test_15](claude/test_15_tool_input_examples.py) |
| Bash Tool | ✅ | ✅ | ✅ | Opus 4.7 unavailable | [test_17](claude/test_17_bash_tool.py) |
| Text Editor Tool | ✅ | ✅ | ✅ | name mapping; Opus 4.7 unavailable | [test_18](claude/test_18_text_editor_tool.py) |
| Claude 4.7 change verification | — | — | ✅ | breaking changes | [test_21](claude/test_21_claude47_changes.py) |
| Claude Fable 5 compatibility | ✅ | — | ✅ | needs `provider_data_share` | [test_22](claude/test_22_fable5.py) |
| Mid-conversation System Messages | ✅ | ❓ | ✅ | new-gen 4.8/Fable5/Sonnet5 only; docs say unsupported but verified | [test_23](claude/test_23_mid_conversation_system.py) |
| Token Counting | ✅ | ❌ | ❌ | Bedrock native CountTokens API (in-region ID only) | [test_20](claude/test_20_count_tokens.py) |
| Web Search Tool | ✅ | ❌ | ❌ | Self-implement | — |
| Web Fetch Tool | ✅ | ❌ | ❌ | Self-implement | — |
| Code Execution Tool | ✅ | ❌ | ❌ | Self-implement | — |
| Programmatic Tool Calling | ✅ | ❌ | ❌ | Self-implement | — |
| Files API | ✅ | ❌ | ❌ | Self-implement | — |
| Batch Processing | ✅ | ❌ | ❌ | Bedrock has a separate API | — |
| MCP Connector | ✅ | ❌ | ❌ | Self-implement | — |
| Memory Tool | ✅ | ❌ | ❌ | Self-implement | — |
| Computer Use Tool | ✅ | ❌ | ❌ | Self-implement | — |
| Agent Skills | ✅ | ❌ | ❌ | Self-implement | — |
| Dynamic Workflows | ✅ | ❌ | ❌ | Claude Code client feature, not an API | — |
| Fast Mode (`speed:"fast"`) | ✅ | ❌ | ❌ | Claude API only | — |

---

## 3. Natively Supported Features

These features are fully supported on Bedrock. The InvokeModel API is largely equivalent to the Anthropic Messages API (same request/response shape, just add the `anthropic_version` field and adjust auth) — no format conversion needed; the Converse API requires Anthropic ↔ Bedrock conversion.

> 📌 Cross-model breaking changes (Thinking / sampling params / prefill / Structured Outputs, etc.) are consolidated in the [cross-model matrix in Section 1](#cross-model-behavior-matrix); this section does not repeat them.

### Messages API basics

Claude's core conversational interface — multi-turn conversations, system prompt.

- **Anthropic**: [messages](https://docs.anthropic.com/en/api/messages)
- **Bedrock**: [model-parameters-anthropic-claude-messages](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html)
- InvokeModel is equivalent to the Anthropic API (pass through directly); Converse needs conversion.

### Streaming (SSE)

Server-sent event stream for token-by-token output.

- **Anthropic**: [streaming](https://docs.anthropic.com/en/build-with-claude/streaming)
- **Bedrock**: `InvokeModelWithResponseStream` SSE format matches Anthropic; ConverseStream uses Bedrock's own format.

### Tool Use (function calling)

Lets Claude call external tools/functions — the core of building agents.

- **Anthropic**: [tool-use/overview](https://docs.anthropic.com/en/agents-and-tools/tool-use/overview)
- **Bedrock**: InvokeModel tool format matches Anthropic; Converse schema differs.
- **Structured output**: new-gen models (Sonnet 5/Fable 5/Opus 4.8/4.7) do not support `output_config.format` — use **forced tool use** (`tool_choice` forcing a tool + `input_schema`) instead.

### Adaptive Thinking (recommended)

Claude dynamically decides whether and how deeply to think, no manual `budget_tokens`. **The only thinking mode on new-gen models.**

- **Anthropic**: [adaptive-thinking](https://docs.anthropic.com/en/build-with-claude/adaptive-thinking)
- **Bedrock**: [claude-messages-adaptive-thinking](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html)
- `thinking: {type: "adaptive"}` — no beta header, auto-enables interleaved thinking, tune with `output_config.effort` (`low`/`medium`/`high`/`xhigh`/`max`).
- New-gen defaults to no thinking (must set `thinking:{type:"adaptive"}` explicitly); thinking content defaults to hidden (`display:"omitted"`), set `display:"summarized"` to see it.
- **Haiku 4.5** does not accept the `output_config.effort` field (otherwise fine).

### Extended Thinking (legacy, 4.6 gen only)

`thinking: {type: "enabled", budget_tokens: N}` for a manual thinking budget. **Only Opus 4.6 / Sonnet 4.6 / Haiku 4.5**; removed on new-gen (returns 400) — migrate to Adaptive Thinking.

- **Anthropic**: [extended-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking)

### Interleaved Thinking

Thinking interleaved between tool calls. Auto-enabled in adaptive mode; in manual extended-thinking mode enable via `interleaved-thinking-2025-05-14` (deprecated on Opus 4.6, still supported on Sonnet 4.6).

- **Anthropic**: [extended-thinking#interleaved-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking#interleaved-thinking)

### Prompt Caching

Caches reused system prompts, tool definitions, etc. **Minimum cacheable length varies by model** (see the [Section 1 matrix](#cross-model-behavior-matrix)).

- **Anthropic**: [prompt-caching](https://docs.anthropic.com/en/build-with-claude/prompt-caching)
- **Bedrock**: InvokeModel `cache_control` matches Anthropic; Converse uses `cachePoint`. TTL 5m and 1h.

> ⚠️ **Bedrock does not support top-level Automatic Caching**: Anthropic's top-level `cache_control` returns `cache_control: Extra inputs are not permitted` on Bedrock ("coming later" per docs). Bedrock only supports **explicit cache breakpoints** (`cache_control` on an individual content block).

**Automatic Caching workaround**: when a proxy receives a top-level `cache_control`, convert to an explicit breakpoint — remove the top-level field and add `cache_control:{"type":"ephemeral"}` on the last cacheable block (InvokeModel) or append `cachePoint:{"type":"default"}` (Converse). Converse also supports **Simplified Cache Management**: put one `cachePoint` at the end of static content and the system searches back ~20 blocks for the longest prefix.

```jsonc
// Converse API
"messages": [{"role":"user","content":[
    {"text":"long static content..."},
    {"cachePoint":{"type":"default"}}
]}]

// InvokeModel API
"messages": [{"role":"user","content":[
    {"type":"text","text":"long static content...","cache_control":{"type":"ephemeral"}}
]}]
```

### Vision (multimodal)

Understand and analyze images.

- **Anthropic**: [vision](https://docs.anthropic.com/en/build-with-claude/vision)
- **Bedrock**: base64 image input (JPEG/PNG/GIF/WebP).

> ⚠️ **Image count limit (complex, non-deterministic on Bedrock)**:
>
> Anthropic API docs specify: 100 images/request for 200k context models, 600 images/request for 1M context models. All current mainstream models on Bedrock have 1M context windows (Opus 4.8/4.7, Sonnet 5/4.6, Fable 5); only older models like Haiku 4.5 are 200k.
>
> Testing (2026-07-06, via `global.*` cross-region inference profiles) revealed three layers of behavior:
>
> 1. **Absolute ceiling = 600**. Sending 601 images is always rejected on every model: `ValidationException: too many images and documents: 601 + 0 > 600`. Matches the Anthropic docs.
> 2. **Between 101–600: enforcement is non-deterministic**. The `global.*` profile routes requests across regional backends, and **some backends enforce a stricter 100-image cap**. The same 200-image request sometimes succeeds and sometimes fails with `too many images and documents: 200 + 0 > 100`. Measured on Sonnet 4.6 @200 images ×6: 4 successes, 2 `>100` rejections.
> 3. **Some models (e.g. Opus 4.8) return transient `ServiceUnavailableException` (5xx)** for large multi-image requests; these succeed on retry — the 5xx is NOT the image-count limit, just server-side busyness.
>
> | Model | Context | Anthropic API Limit | Bedrock Absolute Ceiling | Bedrock Reliable Safe Limit |
> |-------|---------|--------------------|------------------------|---------------------------|
> | Opus 4.8 | 1M | 600 | 600 | **100** |
> | Opus 4.7 | 1M | 600 | 600 | **100** |
> | Sonnet 5 | 1M | 600 | 600 | **100** |
> | Sonnet 4.6 | 1M | 600 | 600 | **100** |
> | Fable 5 | 1M | 600 | 600 | **100** |
>
> **Practical guidance: keep requests to ≤100 images to succeed reliably on Bedrock.** 101–600 may work but can randomly hit a `>100` rejection or transient 5xx; 601+ is always rejected.
>
> Additionally, when a request contains more than 20 images, a stricter per-image dimension limit applies (max 2000px per side); otherwise returns `invalid_request_error`. Per-image size limit is **5 MB** (vs. 10 MB on direct Anthropic API).
>
> Verification: [test_24](claude/test_24_image_limits.py) (tested 2026-07-06)

### PDF Support

Pass PDFs directly for Claude to read and analyze.

- **Anthropic**: [pdf-support](https://docs.anthropic.com/en/build-with-claude/pdf-support)
- **Bedrock**: supports document content blocks.

### Citations

Claude cites specific locations in source documents — for RAG, document Q&A.

- **Anthropic**: [citations](https://docs.anthropic.com/en/build-with-claude/citations)
- **Bedrock**: both InvokeModel (set `citations:{enabled:true}` on a document block) and Converse.

### Structured Outputs

Force output conforming to a JSON Schema.

- **Anthropic**: [structured-outputs](https://docs.anthropic.com/en/build-with-claude/structured-outputs)
- **Bedrock**: [claude-messages-structured-outputs](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-structured-outputs.html)

> ⚠️ **Two key points**:
> 1. The legacy `output_format` parameter is **unavailable platform-wide on Bedrock** (all models 400, telling you to use `output_config.format`). New syntax: `"output_config":{"format":{"type":"json_schema","schema":{..., "additionalProperties":false}}}`; every `object` must set `"additionalProperties":false`.
> 2. **`output_config.format` only works on the 4.6 generation** (Opus 4.6 / Sonnet 4.6 / Haiku 4.5); **new-gen (Sonnet 5 / Fable 5 / Opus 4.8 / 4.7) all return 400** — use forced tool use (`strict:true` tools, verified on the 4.6 gen).

### Fine-grained Tool Streaming

Streams tool-call parameters, cutting first-chunk latency (Bedrock buffers the whole tool_use JSON by default, causing 10-20s; enabling drops it to 1-3s).

- **Anthropic**: [fine-grained-tool-streaming](https://docs.anthropic.com/en/agents-and-tools/tool-use/fine-grained-tool-streaming)
- **Bedrock**: GA platform-wide, no beta header. Set `"eager_input_streaming": true` in tool definitions.
- **Model compatibility**: supported on the 4.6 series and next-gen models (Opus 4.7 / Opus 4.8 / Fable 5 — all verified streaming tool_use input on 2026-07-17; Opus 4.7 initially rejected the field but has since been fixed). Sonnet 4.5 and earlier return 400 (`Extra inputs are not permitted`); Sonnet 4.5 already streams fine-grained by default. Proxies should inject this field per model version.

### Compaction

Auto-compresses conversation history to fit the context window.

- **Anthropic**: [compaction](https://docs.anthropic.com/en/build-with-claude/compaction)
- **Bedrock**: beta header `compact-2026-01-12` passes through.

### Context Editing

Edit specific messages in context without resending the whole history.

- **Anthropic**: [context-editing](https://docs.anthropic.com/en/build-with-claude/context-editing)
- **Bedrock**: beta header `context-management-2025-06-27` passes through. **Opus 4.7 unavailable** (message ID field returns 400).

### Bash Tool / Text Editor Tool

Let Claude run bash commands and edit files (client tools — model emits `tool_use`, client executes).

- **Anthropic**: [bash-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/bash-tool) / [text-editor-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/text-editor-tool)
- **Bedrock**: both InvokeModel and Converse, needs `computer-use-2025-01-24` beta header.
- **name difference**: on Bedrock the text editor name must be `str_replace_based_edit_tool`, type `text_editor_20250728`.
- **Opus 4.7 unavailable**: `bash_20250124` / `text_editor_20250728` return `not supported for this model` (Opus 4.6 fine).

---

## 4. Features Requiring Proxy Adaptation

These have no native Bedrock support and require a proxy layer (e.g. [anthropic_api_converter](https://github.com/xiehust/anthropic_api_converter)).

### 1. Tool Search Tool

Dynamically discover and load tools from a large set (up to 10,000).

| Aspect | Details |
|--------|---------|
| **Anthropic** | `tool_search_tool_regex_20251119` / `tool_search_tool_bm25_20251119`, server-side, returns 3-5 most relevant tools (Sonnet 4.0+/Opus 4.0+, not Haiku) |
| **Bedrock** | Converse unsupported; InvokeModel only, needs `tool-search-tool-2025-10-19`. **Opus 4.7 unavailable** |

**Approach**: map Anthropic `advanced-tool-use-2025-11-20` → Bedrock `tool-search-tool-2025-10-19` and switch from Converse to InvokeModel.

- Anthropic: [tool-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/tool-search-tool)
- Reference: [config.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py) / [anthropic_to_bedrock.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/converters/anthropic_to_bedrock.py) / [bedrock_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/bedrock_service.py)

### 2. Tool Input Examples (`input_examples`)

Provide example inputs to help the model use tools correctly.

| Aspect | Details |
|--------|---------|
| **Anthropic** | `input_examples` field, beta header `advanced-tool-use-2025-11-20` |
| **Bedrock** | Converse unsupported; InvokeModel only, needs `tool-examples-2025-10-29` |

**Approach**: same as Tool Search, map `advanced-tool-use-2025-11-20` → `tool-examples-2025-10-29`, switch to InvokeModel.

- Anthropic: [providing-tool-use-examples](https://docs.anthropic.com/en/agents-and-tools/tool-use/implement-tool-use#providing-tool-use-examples)

### 3. Web Search Tool

Let Claude search the internet for real-time info.

| Aspect | Details |
|--------|---------|
| **Anthropic** | `web_search_20250305` / `web_search_20260209` (dynamic filtering), server-side, $10/1,000 |
| **Bedrock** | Unsupported (header accepted but no search backend) |

**Approach**: proxy-side agentic loop — intercept `web_search_*` calls, run a third-party search API (Tavily/Brave), inject results as `web_search_tool_result`, resend to Bedrock, loop until the model stops searching. The dynamic-filtering version needs a Docker sandbox to run Claude-generated filter code.

- Anthropic: [web-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-search-tool)
- Reference: [web_search_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py) / [providers.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search/providers.py)

### 4. Web Fetch Tool

Fetch full page content (HTML/PDF) from a given URL.

| Aspect | Details |
|--------|---------|
| **Anthropic** | `web_fetch_20250910` / `web_fetch_20260209`, server-side, no extra cost |
| **Bedrock** | Self-implement |

**Approach**: agentic loop similar to Web Search — intercept `web_fetch_*`, fetch with httpx, HTML→text, PDF as base64.

- Anthropic: [web-fetch-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-fetch-tool)
- Reference: [web_fetch_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch_service.py)

### 5. Code Execution Tool

Let Claude run Bash and file operations in a sandbox (also the base dependency for Web Search/Fetch dynamic filtering and PTC).

| Aspect | Details |
|--------|---------|
| **Anthropic** | `code_execution_20250825`, server-side, 5GiB RAM / 1 CPU / no network, beta header `code-execution-2025-08-25` |
| **Bedrock** | Self-implement |

**Approach**: proxy manages Docker containers in an agentic loop — intercept code-execution calls, run in a local container, inject results, resend. Requires container lifecycle management.

- Anthropic: [code-execution-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/code-execution-tool)
- Reference: [standalone_code_execution_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py) / [standalone_sandbox.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/standalone_sandbox.py)

### 6. Programmatic Tool Calling (PTC)

Let Claude write Python to call client tools in bulk in a sandbox, reducing round trips.

| Aspect | Details |
|--------|---------|
| **Anthropic** | Depends on Code Execution (`code_execution_20260120`), key fields `allowed_callers`/`caller` (Opus 4.6/4.5, Sonnet 4.6/4.5) |
| **Bedrock** | Self-implement |

**Approach**: proxy implements the full PTC protocol — filter tools with `allowed_callers` containing `code_execution`, run Claude's Python in a sandbox, pause and return `tool_use` to the client when it calls a client tool, inject the `tool_result` back, finish with `code_execution_tool_result`.

- Anthropic: [programmatic-tool-calling](https://docs.anthropic.com/en/agents-and-tools/tool-use/programmatic-tool-calling)
- Reference: [ptc_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py) / [sandbox.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/sandbox.py)

### 7. Files API

Upload files and reuse them via `file_id` across requests.

| Aspect | Details |
|--------|---------|
| **Anthropic** | beta header `files-api-2025-04-14`, dedicated file endpoints, up to 500MB per file |
| **Bedrock** | Self-implement |

**Approach**: proxy uses S3 storage + DynamoDB (`file_id → S3 key`), exposes `/v1/files` REST; on `file_id` reference, read from S3 and inline as `document`/`image`/`container_upload` blocks.

- Anthropic: [files](https://docs.anthropic.com/en/build-with-claude/files)

### 8. Batch Processing

Async bulk processing at a 50% discount.

| Aspect | Details |
|--------|---------|
| **Anthropic** | `POST /v1/messages/batches`, 50% off, up to 24h |
| **Bedrock** | Has separate [Batch Inference](https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html) with a different interface |

**Approach**: proxy implements the Anthropic Batch API, converting to Bedrock `CreateModelInvocationJob` (S3 JSONL in/out), or a SQS queue + DynamoDB status tracking.

- Anthropic: [batch-processing](https://docs.anthropic.com/en/build-with-claude/batch-processing)

### 9. Token Counting

Estimate token usage before sending.

| Aspect | Details |
|--------|---------|
| **Anthropic** | `POST /v1/messages/count_tokens` |
| **Bedrock** | **Native** [CountTokens API](https://docs.aws.amazon.com/bedrock/latest/userguide/count-tokens.html), free, supports InvokeModel/Converse |

> ⚠️ **Limit**: CountTokens **only supports in-region model IDs** (e.g. `anthropic.claude-sonnet-4-6`); `us.`/`global.` prefixes return `The provided model doesn't support counting tokens` — the proxy must strip prefixes. **Opus 4.7 unsupported** (global-only, no in-region ID). Verified: Claude 3.5 Haiku, Sonnet 4, Sonnet 4.5, Haiku 4.5, Sonnet 4.6, Opus 4.6. See [test_20](claude/test_20_count_tokens.py).

**Approach**: proxy implements `/v1/messages/count_tokens`, converts to Bedrock CountTokens with an in-region ID; falls back to a local tokenizer for unsupported models.

- Anthropic: [token-counting](https://docs.anthropic.com/en/build-with-claude/token-counting)

### 10. MCP Connector

Connect remote MCP servers directly in the API request.

| Aspect | Details |
|--------|---------|
| **Anthropic** | beta header `mcp-client-2025-11-20`, `mcp_servers` field |
| **Bedrock** | Unsupported (parsed but connection errors out) |

**Approach**: proxy implements an MCP client — parse `mcp_servers`, connect via MCP SDK, `tools/list` → tool definitions injected into `tools`, execute via `tools/call` and inject `tool_result`.

- Anthropic: [mcp-connector](https://docs.anthropic.com/en/agents-and-tools/mcp-connector)

### 11. Memory Tool

Let Claude persist memory across sessions.

| Aspect | Details |
|--------|---------|
| **Anthropic** | `memory_20250801` |
| **Bedrock** | Self-implement |

**Approach**: proxy stores memory in DynamoDB/Redis partitioned by `user_id`/`organization_id`, intercepts memory-tool CRUD; search can use a vector store (OpenSearch) for semantic retrieval.

- Anthropic: [memory-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/memory-tool)

### 12. Computer Use Tool

Let Claude operate a computer UI (mouse/keyboard/screenshot).

| Aspect | Details |
|--------|---------|
| **Anthropic** | `computer_20250124`, beta header `computer-use-2025-01-24` |
| **Bedrock** | **Completely unsupported** (InvokeModel rejects `computer_20250124`, even on Opus 4.6) |

**Approach**: convert `computer_20250124` to a plain custom tool (`type:"custom"`) with an equivalent `input_schema`; the client performs screen actions. Downside: loses Anthropic's computer-use optimization.

- Anthropic: [computer-use-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/computer-use-tool)

### 13. Agent Skills

Modular capability packs (instructions + scripts + resources), dependent on Code Execution.

| Aspect | Details |
|--------|---------|
| **Anthropic** | Depends on Code Execution Tool |
| **Bedrock** | Self-implement |

**Approach**: solve the Code Execution gap (item 5) first, then inject skill instructions into the system prompt, preload scripts/resources into the container, and let the model call them via code execution.

- Anthropic: [agent-skills/overview](https://docs.anthropic.com/en/agents-and-tools/agent-skills/overview)

---

## 5. Beta Header Handling on Bedrock

Anthropic enables experimental features via `anthropic-beta` headers. On Bedrock they fall into three categories.

### Pass through (accepted by Bedrock InvokeModel)

| Beta Header | Feature | Notes |
|------------|---------|-------|
| `interleaved-thinking-2025-05-14` | Interleaved Thinking | deprecated on Opus 4.6, still on Sonnet 4.6 |
| `context-management-2025-06-27` | Context Editing | Opus 4.7 unavailable |
| `compact-2026-01-12` | Compaction | |
| `computer-use-2025-01-24` / `-11-24` | Computer Use (bash+text editor work, computer doesn't) | Opus 4.7 unavailable |
| `context-1m-2025-08-07` | 1M Context Window | |
| `structured-outputs-2025-11-13` | Structured Outputs | 4.6 gen only |
| `token-efficient-tools-2025-02-19` | Token Efficient Tools | built into Claude 4+, no effect |
| `effort-2025-11-24` | Effort Parameter (GA) | Haiku 4.5 unsupported |
| `tool-examples-2025-10-29` | Tool Input Examples | Invoke API only |
| `tool-search-tool-2025-10-19` | Tool Search | Invoke API only; Opus 4.7 unavailable |
| `fine-grained-tool-streaming-2025-05-14` | Fine-grained Tool Streaming (GA) | Opus 4.7 unavailable |
| `task-budgets-2026-03-13` | Task Budgets (Opus 4.7+) | |
| `pdfs-2024-09-25` | PDF Support (GA) | |
| `output-128k-2025-02-19` | 128k Output (GA) | |
| `token-counting-2024-11-01` | Token Counting | ❌ non-functional (use native CountTokens API) |
| `mcp-client-2025-11-20` | MCP Connector | ❌ non-functional |
| `web-search-2025-03-05` | Web Search | ❌ tool type rejected at validation on every model, both endpoints (see [§1](#web-search-is-not-available-on-any-claude-model-measured-2026-07-27)) |

### Requires mapping (Bedrock uses a different name, InvokeModel only)

| Anthropic Header | Bedrock Header | Feature |
|-----------------|---------------|---------|
| `advanced-tool-use-2025-11-20` | `tool-examples-2025-10-29` | Tool Input Examples |
| `advanced-tool-use-2025-11-20` | `tool-search-tool-2025-10-19` | Tool Search |

### Explicitly rejected by Bedrock ("invalid beta flag")

`advanced-tool-use-2025-11-20` (aggregate header, must be split), `prompt-caching-scope-2026-01-05`, `redact-thinking-2026-02-12`, `files-api-2025-04-14`, `code-execution-2025-05-22` / `-08-25`, `max-tokens-3-5-sonnet-2024-07-15`, `message-batches-2024-09-24`, `web-fetch-2025-09-10`, `fast-mode-2026-02-01`, `skills-2025-10-02`.

Reference: [config.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py)

---

## 6. Claude Code / Agent SDK on Bedrock

When Claude Code / Agent SDK detects a direct Bedrock connection (`CLAUDE_CODE_USE_BEDROCK=1`), its behavior changes:

1. **Sends incompatible beta headers** (e.g. `advanced-tool-use-2025-11-20`, `prompt-caching-scope-2026-01-05`), causing "invalid beta flag". LiteLLM published an incident report about this. See [issue #11672](https://github.com/anthropics/claude-code/issues/11672), [LiteLLM incident](https://docs.litellm.ai/blog/claude-code-beta-headers-incident).
2. **max_tokens auto-clamping**: [issue #8756](https://github.com/anthropics/claude-code/issues/8756).
3. **Task tool / sub-agent model ID errors**: uses hardcoded Anthropic model IDs (missing `us` prefix), causing "model identifier is invalid". [issue #21235](https://github.com/anthropics/claude-code/issues/21235).
4. **10-20s tool_use permission delay**: does not set `eager_input_streaming:true`. [issue #26941](https://github.com/anthropics/claude-code/issues/26941).
5. **Feature degradation**: PTC, Web Search, Code Execution, etc. are unavailable when connecting directly to Bedrock.

**Workaround**: pose as the Anthropic API via a proxy (`CLAUDE_CODE_USE_BEDROCK=0` + custom `ANTHROPIC_BASE_URL`); the proxy filters/maps beta headers, maps model IDs, and injects `eager_input_streaming:true`. Reference: [messages.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/api/messages.py).

> 💡 With the Mantle endpoint (Claude in Amazon Bedrock), Claude Code uses `CLAUDE_CODE_USE_MANTLE=1` and `anthropic.`-prefixed model IDs (no `global.`/`us.`). For Fable 5 project isolation, see [FABLE5_PROJECT_SETUP.md](FABLE5_PROJECT_SETUP.md).

---

## 7. Opus 4.8 New Features on Bedrock

Opus 4.8 (and Sonnet 5 / Fable 5) ship several new selling points with varying Bedrock support:

| Feature | Bedrock availability |
|---------|:---:|
| Mid-conversation System Messages | ✅ available (4.8/Fable5/Sonnet5) |
| effort=`xhigh` | ✅ available |
| Dynamic Workflows | ⚠️ Claude Code client feature, not an API |
| Fast Mode (`speed:"fast"`) | ❌ unsupported |
| Lower Prompt Cache Min (1024) | ❌ Opus 4.7/4.8/Sonnet5 still 4096; only Fable 5 / Sonnet 4.6 are 1024 |

### Mid-conversation System Messages — ✅ verified working

Insert a `{"role":"system"}` entry into `messages` to add system instructions mid-conversation **without editing the top-level `system` field**, preserving the prefix prompt cache. No beta header.

- **Availability**: **Opus 4.8 / Fable 5 / Sonnet 5** accept and honor it; Opus 4.7 returns `role 'system' is not supported`; the 4.6 gen returns `Unexpected role "system"`.
- **Docs vs measurement**: Anthropic docs say "not available on Amazon Bedrock", but all three models work empirically (InvokeModel + mantle).
- **Placement rules**: a `role:system` entry must immediately follow a `user` turn (or an `assistant` turn ending in server tool use), and be the last entry or precede an `assistant` turn; it cannot sit between a `tool_use` and its `tool_result`.

**Verified findings** (see [test_23](claude/test_23_mid_conversation_system.py)):

1. Accepts and **honors** a benign system instruction ("end every reply with `###MANGO###`" → complied).
2. **Cache preserved**: after a cached prefix (≥4096 tokens), appending a mid-sys entry yields `cache_read_input_tokens=9117` on the next request — prefix cache not invalidated ✅.
3. **Operator priority is not absolute**: in a hard conflict (system "one word only" vs user "write three paragraphs"), the model surfaces the conflict and leans toward the user; only benign, non-adversarial instructions are honored reliably.

> ⚠️ Assess availability with **neutral instructions**. Adversarial phrasing ("ignore the user") triggers the model's resistance and can be mistaken for "not working".
>
> Anthropic: [mid-conversation-system-messages](https://docs.anthropic.com/en/build-with-claude/mid-conversation-system-messages) (states Bedrock unsupported, contradicting this repo's measurements)

### Dynamic Workflows — ⚠️ Claude Code client feature, not an API

Anthropic markets Dynamic Workflows as "available on the Anthropic API / Bedrock / Vertex / Foundry", **easily misread as a new Bedrock API capability**. In reality:

> "Bedrock support" = **Claude Code can run it when configured with a Bedrock backend**, **not** a new dynamic-workflow field in the Bedrock InvokeModel/Messages API.

All orchestration lives in the Claude Code client: Claude writes a JS orchestration script → the client's workflow runtime executes it → it spawns N subagents, each making ordinary InvokeModel calls to Bedrock. Bedrock has no awareness of "Dynamic Workflows".

- **How to use**: Claude Code (CLI/Desktop/IDE, ≥ v2.1.154), trigger via `ultracode` keyword / `/effort ultracode` / `/workflows`.
- **Programmatic**: only via Claude Code's `claude -p` (headless) or the Agent SDK.
- **Bedrock limitation**: the bundled `/deep-research` depends on WebSearch (unavailable on the Bedrock backend), so web workflows are incomplete; code-only workflows work.
- Docs: [introducing-dynamic-workflows](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code)

### Fast Mode — ❌ not available on Bedrock

Set top-level `speed:"fast"` (+ beta header `fast-mode-2026-02-01`) for up to 2.5× output speed at premium pricing (Opus 4.8: $10/$50 per MTok).

- **Anthropic**: research preview, supports Opus 4.8/4.7/4.6, requires account-manager access.
- **Bedrock**: **not supported**. `speed:"fast"` (with or without the beta header) returns 400 `speed: Extra inputs are not permitted`. Docs also state "not available on... Amazon Bedrock".
- Docs: [fast-mode](https://platform.claude.com/docs/en/build-with-claude/fast-mode)

### Lower Prompt Cache Min — ❌ Opus 4.7/4.8/Sonnet 5 still 4096

Anthropic announced Opus 4.8 lowers the minimum cacheable length from 4,096 to 1,024. But **this did not take effect for Opus 4.7/4.8 on Bedrock**.

Official "Min tokens per cache checkpoint" per model card (authoritative):

| Model | Min cacheable length |
|-------|:---:|
| Fable 5 | 1,024 |
| Sonnet 4.6 | 1,024 |
| Sonnet 5 | 4,096 |
| Opus 4.6 / 4.7 / 4.8 | 4,096 |
| Haiku 4.5 | 4,096 |

I.e. **only Fable 5 and Sonnet 4.6 are 1,024; all others are 4,096**. An InvokeModel boundary scan for Opus 4.8 also confirms 4096 (4018 tokens not cached / 4135 tokens cached). Branch cache design by model — below the threshold nothing is cached.

> ⚠️ Note: inferring the minimum from `cache_creation_input_tokens` on the `global.` cross-region endpoint produces noisy/non-monotonic results and is unreliable — rely on each model card's official value.
