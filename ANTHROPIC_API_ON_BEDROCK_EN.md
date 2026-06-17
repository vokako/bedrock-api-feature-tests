<div align="center">

# Anthropic API on Amazon Bedrock

**Complete feature compatibility guide with verification tests**

[中文版](ANTHROPIC_API_ON_BEDROCK_CN.md)

</div>

---

This document provides a comprehensive mapping of every Anthropic Messages API feature to Amazon Bedrock. Each feature is categorized as:

- ✅ **Natively supported** — works out of the box on Bedrock
- ⚠️ **Supported with differences** — works on Bedrock but requires specific API or header configuration
- 🔧 **Proxy implementation required** — not built into Bedrock, but can be implemented via a proxy/application layer

All ✅ features have been **verified with test scripts** against Bedrock InvokeModel API using `global.anthropic.claude-sonnet-4-6` and `global.anthropic.claude-opus-4-7`.

---

## Background: Two Ways to Call Claude on Bedrock

Bedrock provides two APIs for calling Claude models:

| | InvokeModel API | Converse API |
|---|---|---|
| **Format** | Identical to Anthropic's native API | Bedrock's unified format (works across all Bedrock models) |
| **Conversion needed** | None — same request/response JSON structure | Yes — requires Anthropic ↔ Bedrock format conversion |
| **Beta headers** | Supported via `anthropic_beta` field in request body | Limited support via `additionalModelRequestFields` |
| **Feature coverage** | Full (all Claude features available) | Most features, but some advanced ones (Tool Search, Tool Input Examples) are not available |

**Recommendation**: Use InvokeModel API for maximum feature compatibility with the Anthropic ecosystem. Use Converse API when you need a unified interface across multiple model providers.

---

## Overview

| Feature | Anthropic | Bedrock Converse | Bedrock Invoke | Status | Test |
|---------|:---------:|:----------------:|:--------------:|--------|------|
| Messages API | ✅ | ✅ | ✅ | Natively supported | [test_01](test_01_messages_basic.py) |
| Streaming (SSE) | ✅ | ✅ | ✅ | Natively supported | [test_02](test_02_streaming.py) |
| Tool Use (Function Calling) | ✅ | ✅ | ✅ | Natively supported | [test_03](test_03_tool_use.py) |
| Extended Thinking | ✅ | ✅ | ✅ | Natively supported | [test_04](test_04_extended_thinking.py) |
| Adaptive Thinking | ✅ | ✅ | ✅ | Natively supported | [test_16](test_16_adaptive_thinking.py) |
| Interleaved Thinking | ✅ | ✅ | ✅ | Natively supported | [test_05](test_05_interleaved_thinking.py) |
| Prompt Caching | ✅ | ✅ | ✅ | Natively supported | [test_06](test_06_prompt_caching.py) |
| Vision (Multimodal) | ✅ | ✅ | ✅ | Natively supported | [test_07](test_07_vision.py) |
| PDF Support | ✅ | ✅ | ✅ | Natively supported | [test_08](test_08_pdf_support.py) |
| Citations | ✅ | ✅ | ✅ | Natively supported | [test_09](test_09_citations.py) |
| Structured Outputs | ✅ | ✅ | ✅ | Natively supported | [test_10](test_10_structured_outputs.py) |
| Fine-grained Tool Streaming | ✅ | ✅ | ✅ | Natively supported | [test_11](test_11_eager_input_streaming.py) |
| Compaction | ✅ | ✅ | ✅ | Natively supported | [test_12](test_12_compaction.py) |
| Context Editing | ✅ | ✅ | ✅ | Natively supported | [test_13](test_13_context_editing.py) |
| Bash Tool | ✅ | ✅ | ✅ | Natively supported | [test_17](test_17_bash_tool.py) |
| Text Editor Tool | ✅ | ✅ | ✅ | Name mapping required | [test_18](test_18_text_editor_tool.py) |
| Tool Search | ✅ | ❌ | ✅ | InvokeModel API only | [test_14](test_14_tool_search.py) |
| Tool Input Examples | ✅ | ❌ | ✅ | InvokeModel API only | [test_15](test_15_tool_input_examples.py) |
| Web Search Tool | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Web Fetch Tool | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Code Execution Tool | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Programmatic Tool Calling | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Files API | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Batch Processing | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Token Counting | ✅ | ❌ | ❌ | Bedrock CountTokens API | — |
| MCP Connector | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Memory Tool | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Computer Use Tool | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Agent Skills | ✅ | ❌ | ❌ | 🔧 Proxy implementation | — |
| Claude 4.7 Changes | — | — | ✅ | Opus 4.7 breaking changes verified | [test_21](test_21_claude47_changes.py) |
| Mid-conversation System Messages | ✅ | ❓ | ✅ | Opus 4.8 only; docs say unavailable on Bedrock, but verified working | [test_23](test_23_mid_conversation_system.py) |
| Dynamic Workflows | ✅ | ❌ | ❌ | **Claude Code client feature, not an API feature**; "Bedrock support" means Claude Code using a Bedrock backend | — |

**Summary**: 18 out of 29 features are natively supported on Bedrock. The remaining 11 can be implemented via a proxy layer — a reference implementation is available at [anthropic_api_converter](https://github.com/xiehust/anthropic_api_converter).

---

## Natively Supported Features

### Messages API

**What it does**: Core conversation interface for Claude — multi-turn dialogue, system prompts, assistant prefill. Every Claude interaction goes through this API.

**How it works on Bedrock**: The InvokeModel API accepts the exact same JSON format as the Anthropic API. You only need to add `"anthropic_version": "bedrock-2023-05-31"` and use AWS authentication instead of an API key. The Converse API provides a unified interface across all Bedrock models but uses a different JSON format.

> ⚠️ **Breaking Change (Claude 4.6)**: Opus 4.6 and Sonnet 4.6 **no longer support assistant message prefill** (conversations ending with an assistant-role message). Prefill requests return a 400 error: `"This model does not support assistant message prefill"`. Note: Anthropic's documentation only mentions Opus 4.6, but on Bedrock, Sonnet 4.6 also rejects prefill. Alternatives: use [Structured Outputs](#structured-outputs) or system prompt instructions to control output format.

> ⚠️ **Breaking Changes (Claude Opus 4.7)**: Opus 4.7 introduces additional breaking changes on top of 4.6 (verified via [test_21](test_21_claude47_changes.py)):
> - **Extended thinking removed**: `thinking: {type: "enabled", budget_tokens: N}` returns 400 error. Must migrate to `thinking: {type: "adaptive"}` + `output_config.effort`.
> - **Sampling parameters removed**: `temperature`, `top_p`, `top_k` with non-default values return 400 error. Remove these parameters from requests entirely.
> - **Prefill removed**: Same as 4.6 — assistant message prefill returns 400 error.
> - **Thinking content omitted by default**: Thinking blocks still appear in responses, but the `thinking` field is empty unless you set `thinking.display: "summarized"`.
> - **New tokenizer**: Same text may produce ~1x-1.35x more tokens (up to ~35% increase).
> - **New `xhigh` effort level**: Recommended for coding and agentic use cases.
> - **128k max_tokens GA**: `max_tokens=128000` accepted without any beta header.
> - **Task budgets (beta)**: Enable via `task-budgets-2026-03-13` beta header. Set `task_budget` in `output_config` to let the model self-pace within a token budget.
> - **High-resolution image support**: Max resolution increased from 1568px to 2576px (long edge), image tokens up to ~3x more.

- Anthropic docs: [https://docs.anthropic.com/en/api/messages](https://docs.anthropic.com/en/api/messages)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html)

### Streaming (SSE)

**What it does**: Streams the response token-by-token via Server-Sent Events, so users see output as it's generated rather than waiting for the complete response.

**How it works on Bedrock**: `InvokeModelWithResponseStream` returns SSE events in the same format as the Anthropic API — no conversion needed. `ConverseStream` uses Bedrock's own event format and requires conversion.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/streaming](https://docs.anthropic.com/en/build-with-claude/streaming)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModelWithResponseStream.html](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModelWithResponseStream.html)

### Tool Use (Function Calling)

**What it does**: Allows Claude to call external tools/functions (e.g., database queries, API calls, calculations). This is the core building block for AI agents.

**How it works on Bedrock**: Tool definitions and tool_use/tool_result blocks are identical under InvokeModel API. The Converse API uses a different tool schema format (`toolSpec` instead of `tools`) that requires conversion.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/overview](https://docs.anthropic.com/en/agents-and-tools/tool-use/overview)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages-tool-use.html](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages-tool-use.html)

### Extended Thinking

**What it does**: Claude performs deep reasoning before answering, producing a `thinking` block that shows its step-by-step thought process. Dramatically improves performance on math, logic, and complex coding tasks.

**How it works on Bedrock**: Both Converse and InvokeModel APIs support the `thinking` parameter with `type: "enabled"` and `budget_tokens`. The response includes `thinking` content blocks just like the Anthropic API.

> ⚠️ **Deprecated (Claude 4.6)**: `thinking: {type: "enabled", budget_tokens: N}` is deprecated on Opus 4.6 and Sonnet 4.6. Verified still functional on Bedrock, but will be removed in a future model release. Migrate to [Adaptive Thinking](#adaptive-thinking) (`thinking: {type: "adaptive"}`) with the [effort parameter](#adaptive-thinking).

> 🚫 **Removed (Claude Opus 4.7)**: `thinking: {type: "enabled", budget_tokens: N}` returns 400 error on Opus 4.7. You **must** migrate to [Adaptive Thinking](#adaptive-thinking).

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/extended-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html)

### Adaptive Thinking

**What it does**: Claude dynamically decides whether to think and how deeply, based on task complexity. Unlike Extended Thinking where you set a fixed `budget_tokens`, Adaptive Thinking lets the model allocate thinking resources automatically. You can guide it with the `effort` parameter (`max`/`high`/`medium`/`low`).

**How it works on Bedrock**: Set `thinking: {type: "adaptive"}` in the request body. No beta header required. Only available on Opus 4.6 and Sonnet 4.6. Automatically enables interleaved thinking (thinking between tool calls). Opus 4.6 introduces a new `max` effort level for the highest capability. Sonnet 4.6 is the first Sonnet model to support the effort parameter — consider using `medium` for most Sonnet 4.6 use cases to balance speed, cost, and performance.

**Opus 4.7 updates**: New `xhigh` effort level (recommended for coding and agentic use cases). Adaptive thinking is **off by default** on Opus 4.7 — requests without a `thinking` field produce no thinking blocks. Set `thinking: {type: "adaptive"}` explicitly to enable it. Thinking content is **omitted by default** (`display: "omitted"`) — set `display: "summarized"` to see thinking text in responses.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/adaptive-thinking](https://docs.anthropic.com/en/build-with-claude/adaptive-thinking)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html)

### Interleaved Thinking

**What it does**: In multi-step agent workflows, Claude thinks between tool calls — not just before the first response. After receiving a tool result, Claude can reason about what to do next before making another tool call. This significantly improves agent decision-making quality.

**How it works on Bedrock**: In manual extended thinking mode (`thinking.type: "enabled"`), add the beta header `interleaved-thinking-2025-05-14`. In adaptive thinking mode, interleaved thinking is automatically enabled — no header needed.

> ⚠️ **Deprecated (Claude 4.6)**: The `interleaved-thinking-2025-05-14` beta header is deprecated on Opus 4.6 (safely ignored, no longer required). Sonnet 4.6 continues to support it for manual extended thinking mode. Migrate to adaptive thinking.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/extended-thinking#interleaved-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking#interleaved-thinking)

### Prompt Caching

**What it does**: Caches frequently reused content (system prompts, tool definitions, long documents) so it doesn't need to be reprocessed on every request. Reduces latency by up to 85% and input token costs by up to 90% for cached content.

**How it works on Bedrock**: Under InvokeModel API, the `cache_control` format is identical to Anthropic. Under Converse API, caching uses the `cachePoint` mechanism instead. TTL supports 5 minutes (default) and 1 hour.

> ⚠️ **Automatic Caching not supported on Bedrock**: Anthropic's new top-level `cache_control` feature (setting `"cache_control": {"type": "ephemeral"}` at the request body level, where the system automatically applies the cache breakpoint to the last cacheable block) is not available on Bedrock. All models return `cache_control: Extra inputs are not permitted`. Anthropic's docs explicitly state Bedrock support is "coming later". Currently Bedrock only supports **explicit cache breakpoints** (placing `cache_control` on individual content blocks).

**Workaround for Automatic Caching**: When the proxy receives a request with top-level `cache_control`, convert it to explicit breakpoints:

1. Remove the top-level `cache_control` from the request body
2. Find the last cacheable content block in the request (last block in `system`, last message in `messages`, or last tool in `tools`)
3. Add `cache_control: {"type": "ephemeral"}` to that block (InvokeModel API) or append a `cachePoint: {"type": "default"}` after it (Converse API)
4. This achieves the same effect as Anthropic's automatic mode — the longest prefix up to that point gets cached

For Converse API specifically, Bedrock also supports **Simplified Cache Management**: placing a single `cachePoint` at the end of your static content, and the system automatically looks back up to ~20 content blocks to find the longest matching cache prefix. This means you don't need to predict the optimal checkpoint location — just put one `cachePoint` at the end.

```
// Converse API — single cachePoint at end of static content
"messages": [
    {"role": "user", "content": [
        {"text": "long static content..."},
        {"cachePoint": {"type": "default"}}   // ← system auto-finds best cache match
    ]}
]

// InvokeModel API — cache_control on the last static block
"messages": [
    {"role": "user", "content": [
        {"type": "text", "text": "long static content...", "cache_control": {"type": "ephemeral"}}
    ]}
]
```

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/prompt-caching](https://docs.anthropic.com/en/build-with-claude/prompt-caching)

### Vision (Multimodal)

**What it does**: Claude can understand and analyze images — charts, screenshots, photos, diagrams, handwritten text, etc.

**How it works on Bedrock**: Pass base64-encoded images in the request body. Supports JPEG, PNG, GIF, and WebP formats. Format is identical under InvokeModel API.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/vision](https://docs.anthropic.com/en/build-with-claude/vision)

### PDF Support

**What it does**: Claude can read and analyze PDF documents directly, including text, tables, charts, and images within the PDF. No need to extract text first.

**How it works on Bedrock**: Pass base64-encoded PDF as a `document` content block. Supported on both InvokeModel and Converse APIs.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/pdf-support](https://docs.anthropic.com/en/build-with-claude/pdf-support)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_DocumentUnderstanding_AnthropicClaude_section.html](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_DocumentUnderstanding_AnthropicClaude_section.html)

### Citations

**What it does**: Claude cites specific passages from source documents in its responses, with character-level location references. Essential for RAG applications where you need to verify the source of each claim.

**How it works on Bedrock**: Enable citations on document blocks with `citations: {enabled: true}`. Response includes `char_location` citation objects pointing to exact positions in the source document.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/citations](https://docs.anthropic.com/en/build-with-claude/citations)

### Structured Outputs

**What it does**: Forces Claude to output data conforming to a specific JSON Schema. Guarantees valid, parseable JSON output every time. Essential for data extraction, form filling, and API response generation.

**How it works on Bedrock**: Use `tool_choice: {type: "tool", name: "..."}` to force a specific tool call, where the tool's `input_schema` defines the desired output structure. Alternatively, use `output_config.format` for direct JSON output (see below).

> ⚠️ **Breaking Change (Bedrock)**: The `output_format` parameter is **rejected on all models on Bedrock** — including Sonnet 4.5, Haiku 4.5, and older models — returning a 400 error directing you to use `output_config.format`. This is a Bedrock platform-level change, not model-specific. You must migrate:
> ```json
> // ❌ Old syntax (returns 400 on ALL models on Bedrock)
> "output_format": {"type": "json_schema", ...}
> // ✅ New syntax
> "output_config": {"format": {"type": "json_schema", "schema": {..., "additionalProperties": false}}}
> ```
> Note: All `object` types in the schema must explicitly set `"additionalProperties": false`.
>
> Additionally, `strict: true` on tool definitions is supported, guaranteeing tool parameters strictly conform to the schema. Verified on Sonnet 4.5, Haiku 4.5, Sonnet 4.6, and Opus 4.6.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/structured-outputs](https://docs.anthropic.com/en/build-with-claude/structured-outputs)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-structured-outputs.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-structured-outputs.html)

### Fine-grained Tool Streaming

**What it does**: When Claude calls a tool during streaming, the tool call parameters are streamed immediately without waiting for JSON validation. This dramatically reduces the time before a client can display a tool permission prompt (e.g., "Allow Bash(git status)?").

**How it works on Bedrock**: Set `"eager_input_streaming": true` on each tool definition. This is now GA on all platforms — no beta header required. Without this, Bedrock buffers the entire tool_use JSON block, causing **10-20 second delays** before the tool call is visible to the client. With it, delays drop to **1-3 seconds**.

> ⚠️ **Model compatibility**: The `eager_input_streaming` field is only supported on Claude 4.6 models (Opus 4.6 / Sonnet 4.6). On Sonnet 4.5 and earlier models, this field causes a 400 error (`Extra inputs are not permitted`), even with the `fine-grained-tool-streaming-2025-05-14` beta header. However, Sonnet 4.5 already streams tool input JSON deltas in fine-grained chunks by default (20+ chunks observed), so no extra parameter is needed. Proxy layers should conditionally inject this field based on model version.

> ⚠️ **Not available on Opus 4.7**: On Bedrock, Opus 4.7 also rejects the `eager_input_streaming` field (`Extra inputs are not permitted`), with or without the beta header. This is a Bedrock-side gap, not yet adapted for Opus 4.7.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/fine-grained-tool-streaming](https://docs.anthropic.com/en/agents-and-tools/tool-use/fine-grained-tool-streaming)
- Related issue: [https://github.com/anthropics/claude-code/issues/26941](https://github.com/anthropics/claude-code/issues/26941)

### Compaction

**What it does**: Automatically compresses conversation history when it approaches the context window limit. Instead of failing with a "context too long" error, Claude summarizes older messages to make room for new ones. Critical for long-running agent loops.

**How it works on Bedrock**: Beta header `compact-2026-01-12` is passed through directly.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/compaction](https://docs.anthropic.com/en/build-with-claude/compaction)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-compaction.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-compaction.html)

### Context Editing

**What it does**: Modify specific messages in the conversation history without resending everything. Useful for correcting mistakes or updating information mid-conversation.

**How it works on Bedrock**: Beta header `context-management-2025-06-27` is passed through directly.

> ⚠️ **Not available on Opus 4.7**: On Bedrock, Opus 4.7 rejects message `id` fields (`messages.0.id: Extra inputs are not permitted`). Context Editing is not functional on Opus 4.7 — Bedrock-side gap.

### Bash Tool

**What it does**: A client-side tool that lets Claude generate bash commands for the client to execute. The model produces `tool_use` blocks with bash commands; the client runs them locally and returns results. Used by Claude Code for running shell commands.

**How it works on Bedrock**: Supported on both InvokeModel and Converse APIs with the `computer-use-2025-01-24` beta header. Tool type: `bash_20250124`.

> ⚠️ **Not available on Opus 4.7**: On Bedrock, Opus 4.7 rejects `bash_20250124` and `text_editor_20250728` tool types (`tool type 'xxx' is not supported for this model`), regardless of which `computer-use` beta header is used. Opus 4.6 works normally.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/bash-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/bash-tool)

### Text Editor Tool

**What it does**: A client-side tool that lets Claude create and edit files. The model produces `tool_use` blocks with file operations (create, view, str_replace); the client executes them locally. Used by Claude Code for code editing.

**How it works on Bedrock**: Supported on both InvokeModel and Converse APIs. **Important difference**: On Bedrock, the tool name must be `str_replace_based_edit_tool` (not `text_editor` as on Anthropic), and the type must be `text_editor_20250728` (not `text_editor_20250124`).

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/text-editor-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/text-editor-tool)


---

## Features Supported via InvokeModel API Only

These features work on Bedrock but only through the InvokeModel API (not Converse API). They require specific beta headers that differ from Anthropic's naming.

### Tool Search

**What it does**: When you have hundreds or thousands of tools, loading all definitions into the context window is impractical (consumes tokens and degrades tool selection accuracy). Tool Search lets Claude dynamically discover and load only the 3-5 tools it needs for each request, from a catalog of up to 10,000 tools.

**How it works on Bedrock**: Supported via InvokeModel API only. The Anthropic beta header `advanced-tool-use-2025-11-20` must be mapped to Bedrock's `tool-search-tool-2025-10-19`. If your application uses Converse API, you need to switch to InvokeModel API for requests that include tool search.

> ⚠️ **Not available on Opus 4.7**: On Bedrock, Opus 4.7 rejects `tool_search_tool_regex_20251119` tool type (`not supported for this model`). Opus 4.6 / Sonnet 4.6 work normally.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/tool-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/tool-search-tool)
- Reference implementation: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/converters/anthropic_to_bedrock.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/converters/anthropic_to_bedrock.py) — `_map_beta_headers()`

### Tool Input Examples

**What it does**: Provides example inputs in tool definitions to help Claude understand how to use complex tools correctly. Reduces tool call errors when parameters have specific formats or constraints.

**How it works on Bedrock**: Supported via InvokeModel API only. Map `advanced-tool-use-2025-11-20` → `tool-examples-2025-10-29`. Same mechanism as Tool Search.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/implement-tool-use#providing-tool-use-examples](https://docs.anthropic.com/en/agents-and-tools/tool-use/implement-tool-use#providing-tool-use-examples)

---

## Features Requiring Proxy Implementation

These features are Anthropic server-side tools — Anthropic's infrastructure executes them during inference. Since Bedrock doesn't provide equivalent server-side infrastructure, they need to be implemented in a proxy layer between your application and Bedrock.

A complete reference implementation is available: [anthropic_api_converter](https://github.com/xiehust/anthropic_api_converter)

### Web Search Tool

**What it does**: Claude searches the internet in real-time and cites sources in its response. Available in two versions: `web_search_20250305` (basic) and `web_search_20260209` (with dynamic filtering where Claude writes code to filter search results).

**How to implement**: Build an agentic loop at the proxy layer:
1. Intercept `web_search_*` tool definitions from the request — don't pass them to Bedrock
2. When Bedrock's response includes a `server_tool_use` block calling web_search, intercept it
3. Call a third-party search API (e.g., [Tavily](https://tavily.com), [Brave Search](https://brave.com/search/api/))
4. Inject the search results as `web_search_tool_result` into the conversation
5. Send the updated conversation back to Bedrock for Claude to continue
6. Repeat until Claude stops searching

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/web-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-search-tool)
- Reference: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py)

### Web Fetch Tool

**What it does**: Claude fetches the full content of a specific URL (HTML pages or PDF documents). Unlike Web Search which searches by keywords, Web Fetch retrieves a known URL. No additional API cost on Anthropic.

**How to implement**: Same agentic loop pattern as Web Search. The proxy intercepts `web_fetch_*` tool calls and uses httpx (or similar) to fetch the URL content directly — no third-party API key needed. HTML is converted to plain text; PDFs are passed as base64.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/web-fetch-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-fetch-tool)
- Reference: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch_service.py)

### Code Execution Tool

**What it does**: Claude executes Bash commands and file operations in a secure, sandboxed container (5GiB RAM, 5GiB disk, no network access). Used for data analysis, chart generation, complex calculations, and file processing. Also the foundation for Web Search/Fetch dynamic filtering and Programmatic Tool Calling.

**How to implement**: Manage Docker containers at the proxy layer. When Bedrock's response includes code execution tool calls, run them in a local Docker container and inject the results back. Requires container lifecycle management (creation, reuse, expiration after ~4.5 minutes of inactivity).

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/code-execution-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/code-execution-tool)
- Reference: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py)

### Programmatic Tool Calling (PTC)

**What it does**: Instead of Claude making one tool call at a time (requiring a model round-trip for each), Claude writes Python code that calls multiple tools programmatically in a sandbox. This dramatically reduces latency and token consumption for multi-tool workflows. For example, checking budget compliance across 20 employees goes from 20 round-trips to 1.

**How to implement**: The proxy implements the full PTC protocol:
1. Filter tools with `allowed_callers: ["code_execution"]` from Bedrock requests
2. When Claude generates code that calls tools, the proxy executes it in a Docker sandbox
3. Tool calls from within the code are paused and returned to the client for execution
4. Client results are injected back into the sandbox to continue
5. Final output is returned as `code_execution_tool_result`

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/programmatic-tool-calling](https://docs.anthropic.com/en/agents-and-tools/tool-use/programmatic-tool-calling)
- Reference: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py)

### Files API

**What it does**: Upload files once and reference them by `file_id` across multiple API requests, avoiding repeated large file transfers. Supports PDF, images, text, and datasets (for Code Execution). Max 500MB per file, 100GB per organization.

**How to implement**: Build a file storage service using S3 (storage) + DynamoDB (metadata). Provide compatible `/v1/files` REST endpoints. When a Messages request references a `file_id`, read the file from S3 and inline it as the appropriate content block (`document`, `image`, or `container_upload`).

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/files](https://docs.anthropic.com/en/build-with-claude/files)

### Batch Processing

**What it does**: Process large volumes of requests asynchronously with a 50% discount. Results are available within 24 hours. Ideal for data labeling, document processing, and benchmarking.

**How to implement**: Bedrock has its own [Batch Inference Jobs](https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html) via `CreateModelInvocationJob` API, but the interface differs from Anthropic's. You can either adapt to Bedrock's batch format directly, or build a proxy that accepts Anthropic's `/v1/messages/batches` format and converts to Bedrock batch jobs internally.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/batch-processing](https://docs.anthropic.com/en/build-with-claude/batch-processing)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html](https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html)

### Token Counting

**What it does**: Estimate token usage before sending a request. Useful for cost control and context window management.

**How it works on Bedrock**: Bedrock provides a native `CountTokens` API ([docs](https://docs.aws.amazon.com/bedrock/latest/userguide/count-tokens.html)) that is free to use. It supports both InvokeModel and Converse input formats. Verified working on: Claude 3.5 Haiku, Sonnet 4, Sonnet 4.5, Haiku 4.5, Sonnet 4.6, and Opus 4.6.

> ⚠️ **Important limitation**: CountTokens API **only supports in-region model IDs** (e.g., `anthropic.claude-sonnet-4-6`). Cross-region (`us.anthropic.claude-sonnet-4-6`) and global (`global.anthropic.claude-sonnet-4-6`) prefixes return `The provided model doesn't support counting tokens`. Proxy layers must strip the `us.`/`eu.`/`global.` prefix when calling CountTokens.

> ⚠️ **Opus 4.7 not supported by CountTokens**: Both `anthropic.claude-opus-4-7` and `global.anthropic.claude-opus-4-7` return "doesn't support counting tokens". Opus 4.7 currently only has global deployment with no in-region model ID, so CountTokens API is unavailable. Use a local tokenizer for estimation.

**How to implement**: Build a `POST /v1/messages/count_tokens` endpoint in the proxy layer that converts Anthropic-format requests to Bedrock's CountTokens API format. Use in-region model IDs (strip cross-region/global prefixes). Fall back to local tokenizer estimation for unsupported models.

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/token-counting](https://docs.anthropic.com/en/build-with-claude/token-counting)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/count-tokens.html](https://docs.aws.amazon.com/bedrock/latest/userguide/count-tokens.html)

### MCP Connector

**What it does**: Connect to remote MCP (Model Context Protocol) servers directly in the API request, without implementing MCP client-side. Claude can discover and use tools from MCP servers like GitHub, Slack, databases, etc.

**How to implement**: Build an MCP client at the proxy layer. Parse `mcp_servers` from the request, connect to each server via MCP protocol, fetch tool lists, inject them into the request, and relay tool calls/results between Claude and the MCP servers.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/mcp-connector](https://docs.anthropic.com/en/agents-and-tools/mcp-connector)
- MCP specification: [https://modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification)

### Memory Tool

**What it does**: Claude can persist memories across conversations — user preferences, project context, past decisions. Enables personalized, stateful assistants.

**How to implement**: Build a memory storage service (e.g., DynamoDB or Redis). Intercept `memory_20250801` tool calls and execute CRUD operations locally. For semantic search over memories, integrate a vector database like Amazon OpenSearch.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/memory-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/memory-tool)

### Computer Use Tool

**What it does**: Claude operates a computer GUI — mouse clicks, keyboard input, screenshots. Used for UI automation and RPA.

**How it works on Bedrock**: The `computer_20250124` tool type is **not accepted** by Bedrock (even on Opus 4.6). Note that Bash Tool and Text Editor Tool (which share the same `computer-use-2025-01-24` beta header) DO work on Bedrock — only the screen-control `computer` tool type is rejected.

**How to implement**: Convert the `computer_20250124` tool to a custom tool with an equivalent `input_schema` (containing `action`, `coordinate`, etc. fields). The model can still generate similar tool calls, but you lose Anthropic's specialized computer-use training optimizations.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/tool-use/computer-use-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/computer-use-tool)
- Reference: [https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo)

### Agent Skills

**What it does**: Modular capability packages containing instructions, scripts, and resource files. Extends Claude with reusable professional capabilities (data analysis workflows, domain-specific templates).

**How to implement**: Requires Code Execution Tool as a foundation (see above). Parse skill definitions, inject instructions into the system prompt, preload scripts into the Code Execution container.

- Anthropic docs: [https://docs.anthropic.com/en/agents-and-tools/agent-skills/overview](https://docs.anthropic.com/en/agents-and-tools/agent-skills/overview)


---

## Beta Header Reference

The Anthropic API uses `anthropic-beta` headers to enable experimental features. On Bedrock, these headers have different support levels. The following table is based on actual testing against Bedrock InvokeModel API.

### Accepted by Bedrock

| Beta Header | Feature | Works |
|------------|---------|:-----:|
| `interleaved-thinking-2025-05-14` | Interleaved Thinking | ✅ | Deprecated on Opus 4.6 (adaptive thinking auto-enables it); still supported on Sonnet 4.6 |
| `context-management-2025-06-27` | Context Editing | ✅ |
| `compact-2026-01-12` | Compaction | ✅ |
| `computer-use-2025-01-24` | Bash + Text Editor (computer tool itself not supported) | ✅ |
| `computer-use-2025-11-24` | Computer Use (new version) | ✅ |
| `context-1m-2025-08-07` | 1M Context Window | ✅ |
| `structured-outputs-2025-11-13` | Structured Outputs | ✅ |
| `token-efficient-tools-2025-02-19` | Token Efficient Tools | ✅ |
| `effort-2025-11-24` | Effort Parameter | ✅ |
| `tool-examples-2025-10-29` | Tool Input Examples (InvokeModel only) | ✅ |
| `tool-search-tool-2025-10-19` | Tool Search (InvokeModel only) | ✅ |
| `fine-grained-tool-streaming-2025-05-14` | Fine-grained Tool Streaming (now GA) | ✅ |
| `task-budgets-2026-03-13` | Task Budgets (new in Opus 4.7) | ✅ |

> ⚠️ **Opus 4.7 functional gaps**: All beta headers above are accepted by Bedrock on Opus 4.7 (no "invalid beta flag" error), but functional testing with real payloads reveals several features are **not working** on Opus 4.7 (Bedrock-side gap, not yet adapted):
> - `computer-use-2025-01-24` / `computer-use-2025-11-24`: bash/text_editor tool types return `not supported for this model`
> - `context-management-2025-06-27`: message `id` field returns `Extra inputs are not permitted`
> - `tool-search-tool-2025-10-19`: tool_search tool types return `not supported for this model`
> - `fine-grained-tool-streaming-2025-05-14`: `eager_input_streaming` field returns `Extra inputs are not permitted`
> - `token-efficient-tools-2025-02-19`: no effect — input_tokens identical with/without header (built-in for Claude 4+)
>
> These features work normally on Opus 4.6 / Sonnet 4.6. `tool-examples-2025-10-29` and `effort` (now GA) are fully functional on Opus 4.7.
| `pdfs-2024-09-25` | PDF Support (now GA) | ✅ |
| `output-128k-2025-02-19` | 128k Output (now GA) | ✅ |
| `token-counting-2024-11-01` | Token Counting | ❌ Accepted but not functional (Bedrock has native CountTokens API — no header needed) |
| `mcp-client-2025-11-20` | MCP Connector | ❌ Accepted but not functional |
| `web-search-2025-03-05` | Web Search | ❌ Accepted but not functional |

### Requires Mapping

| Anthropic Header | Bedrock Header | Feature |
|-----------------|---------------|---------|
| `advanced-tool-use-2025-11-20` | `tool-examples-2025-10-29` | Tool Input Examples |
| `advanced-tool-use-2025-11-20` | `tool-search-tool-2025-10-19` | Tool Search |

> **Note**: Anthropic uses `advanced-tool-use-2025-11-20` as an aggregate header. Bedrock rejects this header and requires the individual feature headers instead. These only work via InvokeModel API, not Converse API.

### Rejected by Bedrock ("invalid beta flag")

| Beta Header | Feature |
|------------|---------|
| `advanced-tool-use-2025-11-20` | Advanced Tool Use (use split headers above) |
| `prompt-caching-scope-2026-01-05` | Prompt Caching Scope |
| `redact-thinking-2026-02-12` | Thinking Redaction |
| `files-api-2025-04-14` | Files API |
| `code-execution-2025-05-22` | Code Execution (legacy) |
| `code-execution-2025-08-25` | Code Execution |
| `max-tokens-3-5-sonnet-2024-07-15` | Max Tokens 3.5 Sonnet |
| `message-batches-2024-09-24` | Message Batches |
| `web-fetch-2025-09-10` | Web Fetch |
| `fast-mode-2026-02-01` | Fast Mode |
| `skills-2025-10-02` | Agent Skills |

---

## Claude Code on Bedrock: Integration Notes

When Claude Code detects a direct Bedrock connection (`CLAUDE_CODE_USE_BEDROCK=1`), several issues arise. These are well-documented in the community:

### 1. Incompatible Beta Headers

Claude Code sends beta headers that Bedrock rejects (e.g., `advanced-tool-use-2025-11-20`, `prompt-caching-scope-2026-01-05`), causing "invalid beta flag" errors. This affected many users and LiteLLM published a dedicated [incident report](https://docs.litellm.ai/blog/claude-code-beta-headers-incident) with a provider-specific filtering solution.

- [https://github.com/anthropics/claude-code/issues/11672](https://github.com/anthropics/claude-code/issues/11672)

### 2. max_tokens Auto-Truncation

Claude Code may automatically reduce `max_tokens` when it detects Bedrock, limiting output length.

- [https://github.com/anthropics/claude-code/issues/8756](https://github.com/anthropics/claude-code/issues/8756)

### 3. Sub-Agent Model ID Error

The Task tool (for spawning sub-agents) uses hardcoded Anthropic model IDs like `.anthropic.claude-sonnet-4-5-20250929-v1:0` — missing the required `us` prefix for Bedrock. This breaks all custom agents and sub-agents on Bedrock.

- [https://github.com/anthropics/claude-code/issues/21235](https://github.com/anthropics/claude-code/issues/21235)

### 4. Slow Tool Permission Prompts (10-20s delay)

Claude Code doesn't set `eager_input_streaming: true` on tool definitions, so Bedrock buffers the entire tool_use JSON block before streaming it. Permission prompts that appear in 1-3s on Anthropic API take 10-20s on Bedrock.

- [https://github.com/anthropics/claude-code/issues/26941](https://github.com/anthropics/claude-code/issues/26941)

### 5. Missing Advanced Features

PTC, Web Search, Code Execution, and other server-side tools are not available when connecting directly to Bedrock.

### Recommended Solution

Use a proxy that masquerades as the Anthropic API:

```bash
export CLAUDE_CODE_USE_BEDROCK=0
export ANTHROPIC_BASE_URL=http://your-proxy-endpoint
export ANTHROPIC_API_KEY=sk-your-proxy-key
```

The proxy handles:
- Filtering/mapping incompatible beta headers
- Converting Anthropic model IDs to Bedrock model IDs
- Auto-injecting `eager_input_streaming: true` on all tool definitions
- Implementing server-side tools (Web Search, Code Execution, PTC) via agentic loops

Reference implementation: [https://github.com/xiehust/anthropic_api_converter](https://github.com/xiehust/anthropic_api_converter)


---

### Mid-conversation System Messages (Opus 4.8)

Insert a `{"role": "system"}` entry into the `messages` array to add system instructions partway through a conversation **without editing the top-level `system` field**, preserving the prompt cache for the prefix. Introduced in Opus 4.8; no beta header required.

| Aspect | Details |
|--------|---------|
| **Anthropic** | Opus 4.8 only. A `role: system` entry must immediately follow a `user` turn (or an `assistant` turn ending in server tool use), and must be the last entry or precede an `assistant` turn. It cannot sit between a `tool_use` block and its `tool_result` |
| **Bedrock** | **Anthropic docs state "not available on Amazon Bedrock", but empirically (InvokeModel + mantle) it works on Opus 4.8**: the `role:system` entry is accepted and its instruction is honored. Opus 4.7 returns 400 `role 'system' is not supported on this model` |
| **Difference** | Behaviorally matches the first-party API (empirically); docs and observed behavior disagree — verify before relying on it |

**Verified findings (2026-06-17, `global.anthropic.claude-opus-4-8`, see [test_23](test_23_mid_conversation_system.py)):**

1. **Opus 4.7**: `role:system` in `messages` → 400 `role 'system' is not supported on this model` (4.8-only feature)
2. **Opus 4.8**: accepts and **honors** a benign system instruction (test: "end every reply with `###MANGO###`" → model complied)
3. **Cache preserved**: after a cached prefix (top-level `system`, needs ≥ 4096 tokens), appending a mid-sys entry yields `cache_read_input_tokens=9117` on the next request — the prefix cache is not invalidated ✅
4. **Operator priority is not absolute**: in a hard conflict (system "one word only" vs user "write three paragraphs"), the model surfaces the conflict and leans toward the user rather than blindly enforcing the system instruction. Benign, non-adversarial instructions are honored reliably

> ⚠️ Testing note: an adversarial instruction ("ignore the user's question") triggers the model's anti-override training and is resisted, which can be mistaken for "feature not working". Use neutral instructions to assess availability.

**Reference**: [https://docs.anthropic.com/en/build-with-claude/mid-conversation-system-messages](https://docs.anthropic.com/en/build-with-claude/mid-conversation-system-messages) (note: this page states Bedrock is unsupported, contradicting this repo's measured results)


---

### Dynamic Workflows (Opus 4.8) — a Claude Code client feature, not an API feature

Anthropic markets Dynamic Workflows as "available on the Anthropic API, Amazon Bedrock, Vertex AI, and Microsoft Foundry", which is **easily misread as a new Bedrock API capability**. In reality:

> "Bedrock support" = **Claude Code (the client) can run Dynamic Workflows when configured with a Bedrock backend**. It does **not** mean the Bedrock InvokeModel/Messages API gained a dynamic-workflow field or endpoint.

**Where it lives:**

```
Claude Code (client)
  ├── Claude writes a JS orchestration script
  ├── workflow runtime (inside the Claude Code process) executes it
  └── the script spawns N subagents
        └── each subagent → ordinary InvokeModel call → Bedrock backend
```

All orchestration, parallel scheduling, and script execution happen in the Claude Code client. Bedrock only sees a stream of **ordinary InvokeModel requests** and has no awareness of "Dynamic Workflows".

| Aspect | Details |
|--------|---------|
| **Nature** | Claude Code client orchestration (research preview), not a model API feature |
| **API layer** | Bedrock InvokeModel/Messages has **no corresponding field**; cannot be enabled via an API call |
| **How to use** | Claude Code (CLI/Desktop/IDE), requires ≥ v2.1.154; trigger with the `ultracode` keyword, "use a workflow", or `/effort ultracode`; inspect with `/workflows` |
| **Programmatic** | Only via Claude Code's `claude -p` (headless) or the Agent SDK — still the client layer |
| **Bedrock limitation** | The bundled `/deep-research` depends on WebSearch, which is unavailable on the Bedrock backend → web-based workflows are incomplete; code-only workflows (edit files / run tests / parallel audits) work |

> Contrast: [Mid-conversation System Messages](#mid-conversation-system-messages-opus-48) is a **real API feature** (a `role:system` entry in `messages`), verified working on Bedrock Opus 4.8; Dynamic Workflows is a **client feature** where "Bedrock support" only means the client can target a Bedrock backend.

**References**:
- Claude Code docs: [https://docs.claude.com/en/docs/claude-code/workflows](https://docs.claude.com/en/docs/claude-code/workflows)
- Announcement: [https://claude.com/blog/introducing-dynamic-workflows-in-claude-code](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code)
