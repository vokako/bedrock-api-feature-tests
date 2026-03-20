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

All ✅ features have been **verified with test scripts** against Bedrock InvokeModel API using `global.anthropic.claude-sonnet-4-6`.

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

**Summary**: 18 out of 29 features are natively supported on Bedrock. The remaining 11 can be implemented via a proxy layer — a reference implementation is available at [anthropic_api_converter](https://github.com/xiehust/anthropic_api_converter).

---

## Natively Supported Features

### Messages API

**What it does**: Core conversation interface for Claude — multi-turn dialogue, system prompts, assistant prefill. Every Claude interaction goes through this API.

**How it works on Bedrock**: The InvokeModel API accepts the exact same JSON format as the Anthropic API. You only need to add `"anthropic_version": "bedrock-2023-05-31"` and use AWS authentication instead of an API key. The Converse API provides a unified interface across all Bedrock models but uses a different JSON format.

> ⚠️ **Breaking Change (Claude 4.6)**: Opus 4.6 and Sonnet 4.6 **no longer support assistant message prefill** (conversations ending with an assistant-role message). Prefill requests return a 400 error: `"This model does not support assistant message prefill"`. Note: Anthropic's documentation only mentions Opus 4.6, but on Bedrock, Sonnet 4.6 also rejects prefill. Alternatives: use [Structured Outputs](#structured-outputs) or system prompt instructions to control output format.

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

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/extended-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking)
- Bedrock docs: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html)

### Adaptive Thinking

**What it does**: Claude dynamically decides whether to think and how deeply, based on task complexity. Unlike Extended Thinking where you set a fixed `budget_tokens`, Adaptive Thinking lets the model allocate thinking resources automatically. You can guide it with the `effort` parameter (`max`/`high`/`medium`/`low`).

**How it works on Bedrock**: Set `thinking: {type: "adaptive"}` in the request body. No beta header required. Only available on Opus 4.6 and Sonnet 4.6. Automatically enables interleaved thinking (thinking between tool calls). Opus 4.6 introduces a new `max` effort level for the highest capability. Sonnet 4.6 is the first Sonnet model to support the effort parameter — consider using `medium` for most Sonnet 4.6 use cases to balance speed, cost, and performance.

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

- Anthropic docs: [https://docs.anthropic.com/en/build-with-claude/context-editing](https://docs.anthropic.com/en/build-with-claude/context-editing)

### Bash Tool

**What it does**: A client-side tool that lets Claude generate bash commands for the client to execute. The model produces `tool_use` blocks with bash commands; the client runs them locally and returns results. Used by Claude Code for running shell commands.

**How it works on Bedrock**: Supported on both InvokeModel and Converse APIs with the `computer-use-2025-01-24` beta header. Tool type: `bash_20250124`.

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
