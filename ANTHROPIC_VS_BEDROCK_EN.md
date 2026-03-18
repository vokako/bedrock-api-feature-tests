<div align="center">

# Anthropic API Feature Compatibility on AWS Bedrock

**Mapping Anthropic API features to AWS Bedrock with implementation guidance**

</div>

---

This document maps each Anthropic Messages API feature to its Bedrock equivalent. For Anthropic-specific features not yet built into Bedrock, it provides implementation guidance using a proxy layer or application layer.

---

> 📌 All features marked ✅ have been verified against Bedrock InvokeModel API (Sonnet 4.6) with corresponding test scripts.

## Overview

| Feature | Anthropic API | Bedrock Converse | Bedrock Invoke | Notes | Test |
|------|:---:|:---:|:---:|:---:|:---:|
| Messages API | ✅ | ✅ | ✅ | — | [test_01](test_01_messages_basic.py) |
| Streaming (SSE) | ✅ | ✅ | ✅ | — | [test_02](test_02_streaming.py) |
| Tool Use | ✅ | ✅ | ✅ | — | [test_03](test_03_tool_use.py) |
| Extended Thinking | ✅ | ✅ | ✅ | — | [test_04](test_04_extended_thinking.py) |
| Adaptive Thinking | ✅ | ✅ | ✅ | — | [test_16](test_16_adaptive_thinking.py) |
| Interleaved Thinking | ✅ | ✅ | ✅ | — | [test_05](test_05_interleaved_thinking.py) |
| Prompt Caching | ✅ | ✅ | ✅ | — | [test_06](test_06_prompt_caching.py) |
| Vision | ✅ | ✅ | ✅ | — | [test_07](test_07_vision.py) |
| PDF Support | ✅ | ✅ | ✅ | — | [test_08](test_08_pdf_support.py) |
| Citations | ✅ | ✅ | ✅ | — | [test_09](test_09_citations.py) |
| Structured Outputs | ✅ | ✅ | ✅ | — | [test_10](test_10_structured_outputs.py) |
| Fine-grained Tool Streaming | ✅ | ✅ | ✅ | — | [test_11](test_11_eager_input_streaming.py) |
| Compaction | ✅ | ✅ | ✅ | — | [test_12](test_12_compaction.py) |
| Context Editing | ✅ | ✅ | ✅ | — | [test_13](test_13_context_editing.py) |
| Tool Search | ✅ | ❌ | ✅ | InvokeModel API only | [test_14](test_14_tool_search.py) |
| Tool Input Examples | ✅ | ❌ | ✅ | InvokeModel API only | [test_15](test_15_tool_input_examples.py) |
| Web Search Tool | ✅ | ❌ | ❌ | Proxy impl. required |
| Web Fetch Tool | ✅ | ❌ | ❌ | Proxy impl. required |
| Code Execution Tool | ✅ | ❌ | ❌ | Proxy impl. required |
| Programmatic Tool Calling | ✅ | ❌ | ❌ | Proxy impl. required |
| Files API | ✅ | ❌ | ❌ | Proxy impl. required |
| Batch Processing | ✅ | ❌ | ❌ | Proxy impl. required |
| Token Counting | ✅ | ❌ | ❌ | Proxy impl. required |
| MCP Connector | ✅ | ❌ | ❌ | Proxy impl. required |
| Memory Tool | ✅ | ❌ | ❌ | Proxy impl. required |
| Bash Tool | ✅ | ✅ | ✅ | — | [test_17](test_17_bash_tool.py) |
| Text Editor Tool | ✅ | ✅ | ✅ | Name mapping | [test_18](test_18_text_editor_tool.py) |
| Computer Use Tool | ✅ | ❌ | ❌ | Proxy impl. required |
| Agent Skills | ✅ | ❌ | ❌ | Proxy impl. required |

---

## Natively Supported on Bedrock

The following features are fully supported on Bedrock. The InvokeModel API is format-equivalent to the Anthropic API (same request/response structure, only requiring the `anthropic_version` field and authentication changes) — no format conversion needed. The Converse API uses a different format and requires Anthropic ↔ Bedrock conversion.

### Messages API

Core conversation interface for Claude, supporting multi-turn dialogue, system prompts, and assistant prefill.

- **Anthropic**: [https://docs.anthropic.com/en/api/messages](https://docs.anthropic.com/en/api/messages)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html)
- InvokeModel API is format-equivalent — direct passthrough. Converse API provides a unified interface but requires format conversion.

### Streaming (SSE)

Server-sent event stream for token-by-token output. Essential for interactive applications.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/streaming](https://docs.anthropic.com/en/build-with-claude/streaming)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModelWithResponseStream.html](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModelWithResponseStream.html) / ConverseStream
- InvokeModelWithResponseStream returns SSE events in the same format as Anthropic. ConverseStream uses Bedrock's own format.

### Tool Use (Function Calling)

Enables Claude to call external tools/functions. Core capability for building agents.

- **Anthropic**: [https://docs.anthropic.com/en/agents-and-tools/tool-use/overview](https://docs.anthropic.com/en/agents-and-tools/tool-use/overview)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages-tool-use.html](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages-tool-use.html)
- Tool definition format is identical under InvokeModel API. Converse API uses a different schema requiring conversion.

### Extended Thinking

Deep reasoning before answering, outputting thinking blocks. Ideal for math, logic, and complex coding.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/extended-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html)
- Both Converse and InvokeModel APIs support the `thinking` parameter.

### Adaptive Thinking

Claude dynamically determines whether and how much to think. Ideal for workloads with varying complexity.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/adaptive-thinking](https://docs.anthropic.com/en/build-with-claude/adaptive-thinking)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html)
- `thinking: {type: "adaptive"}` — no beta header required. Opus 4.6 / Sonnet 4.6 only. Automatically enables interleaved thinking. Use `output_config.effort` (`max`/`high`/`medium`/`low`) to control thinking depth.

### Interleaved Thinking

Thinking between tool calls. Ideal for multi-step agent scenarios.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/extended-thinking#interleaved-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking#interleaved-thinking)
- **Bedrock**: Beta header `interleaved-thinking-2025-05-14` passed through directly.
- Enabled via beta header in manual mode (`thinking.type: "enabled"`). Automatically enabled in adaptive mode.

### Prompt Caching

Caches frequently used system prompts and tool definitions. Significantly reduces latency and cost.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/prompt-caching](https://docs.anthropic.com/en/build-with-claude/prompt-caching)
- **Bedrock**: `cache_control` format is identical under InvokeModel API. Converse API uses `cachePoint` mechanism. TTL supports 5m and 1h.

### Vision (Multimodal)

Image understanding and analysis. Useful for chart interpretation, OCR, UI analysis.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/vision](https://docs.anthropic.com/en/build-with-claude/vision)
- **Bedrock**: Supports base64-encoded image input (JPEG, PNG, GIF, WebP).

### PDF Support

Direct PDF document analysis without text extraction preprocessing.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/pdf-support](https://docs.anthropic.com/en/build-with-claude/pdf-support)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_DocumentUnderstanding_AnthropicClaude_section.html](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_DocumentUnderstanding_AnthropicClaude_section.html)

### Citations

Claude cites specific locations in source documents. Essential for RAG and document Q&A.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/citations](https://docs.anthropic.com/en/build-with-claude/citations)
- **Bedrock**: Supported via Converse API.

### Structured Outputs

Forces Claude to output structured data conforming to a JSON Schema.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/structured-outputs](https://docs.anthropic.com/en/build-with-claude/structured-outputs)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-structured-outputs.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-structured-outputs.html)

### Fine-grained Tool Streaming

Streams tool call parameters without JSON buffering, reducing first-chunk latency. Essential for fast tool permission prompts.

- **Anthropic**: [https://docs.anthropic.com/en/agents-and-tools/tool-use/fine-grained-tool-streaming](https://docs.anthropic.com/en/agents-and-tools/tool-use/fine-grained-tool-streaming)
- **Bedrock**: Supported on all platforms (GA, no beta header required)
- Enable by setting `"eager_input_streaming": true` on tool definitions.
- **Practical impact**: Bedrock buffers the entire tool_use JSON block by default, causing 10-20s delays. Enabling this reduces latency to 1-3s. See [https://github.com/anthropics/claude-code/issues/26941](https://github.com/anthropics/claude-code/issues/26941)

### Compaction

Automatically compresses conversation history to fit the context window.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/compaction](https://docs.anthropic.com/en/build-with-claude/compaction)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-compaction.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-compaction.html)
- Beta header `compact-2026-01-12` passed through directly.

### Context Editing

Edit specific messages in conversation context without resending the entire history.

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/context-editing](https://docs.anthropic.com/en/build-with-claude/context-editing)
- **Bedrock**: Beta header `context-management-2025-06-27` passed through directly.


---

## Features Requiring Proxy Implementation

### 1. Tool Search Tool

Dynamically discover and load tools from a large catalog (up to 10,000) instead of loading all definitions upfront. Ideal for MCP multi-server integrations and large tool libraries.

| Dimension | Description |
|------|------|
| **Anthropic** | `tool_search_tool_regex_20251119` / `tool_search_tool_bm25_20251119`. Server-side tool, returns 3-5 most relevant tools. Supported: Sonnet 4.0+, Opus 4.0+ (not Haiku) |
| **Bedrock** | Not supported via Converse API. Supported via InvokeModel API with `tool-search-tool-2025-10-19` beta header |
| **Notes** | Requires switching to InvokeModel API when using Converse API |

**Implementation Approach**:

- Map Anthropic beta header `advanced-tool-use-2025-11-20` to Bedrock's `tool-search-tool-2025-10-19`
- Automatically switch from Converse API to InvokeModel API
- Only applies to supported models (configured in `beta_header_supported_models`)

**References**:
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/tool-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/tool-search-tool)
- Bedrock: [https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html) (via InvokeModel)
- Reference implementation:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py)
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/converters/anthropic_to_bedrock.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/converters/anthropic_to_bedrock.py)
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/bedrock_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/bedrock_service.py)

---

### 2. Tool Input Examples (input_examples)

Provides example inputs for tool definitions to help Claude understand usage patterns. Useful when tool parameters are complex.

| Dimension | Description |
|------|------|
| **Anthropic** | `input_examples` field in tool definitions. Beta header: `advanced-tool-use-2025-11-20` |
| **Bedrock** | Not supported via Converse API. Supported via InvokeModel API with `tool-examples-2025-10-29` beta header |
| **Notes** | Same as Tool Search, requires InvokeModel API |

**Implementation Approach**: Same as Tool Search — map `advanced-tool-use-2025-11-20` → `tool-examples-2025-10-29`, auto-switch to InvokeModel API.

**References**:
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/implement-tool-use#providing-tool-use-examples](https://docs.anthropic.com/en/agents-and-tools/tool-use/implement-tool-use#providing-tool-use-examples)
- Reference implementation: Same as Tool Search (shared beta header mapping mechanism)

---

### 3. Web Search Tool

Real-time web search with automatic source citations. Ideal for up-to-date Q&A and fact-checking.

| Dimension | Description |
|------|------|
| **Anthropic** | `web_search_20250305` (basic) / `web_search_20260209` (dynamic filtering). Server-side tool. $10/1,000 searches. Supports `max_uses`, `allowed_domains`, `blocked_domains`, `user_location` |
| **Bedrock** | `web_search_20250305` tool type and `web-search-2025-03-05` beta header are accepted but return validation errors — no search backend. `web_search_20260209` is not recognized |
| **Notes** | Web Search can be implemented via proxy layer |

**Implementation Approach**: Implement an agentic loop at the proxy layer:

1. Proxy intercepts `web_search_*` tool definitions, does not pass them to Bedrock
2. When Bedrock returns a web_search tool call (`server_tool_use`), the proxy intercepts it
3. Proxy calls third-party search APIs (Tavily / Brave Search)
4. Injects results in `web_search_tool_result` format
5. Resends message with search results to Bedrock to continue generation
6. Loops until the model stops calling search (agentic loop)

Dynamic filtering (`web_search_20260209`) additionally requires a Docker sandbox.

**References**:
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/web-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-search-tool)
- Reference implementation:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py)
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search/providers.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search/providers.py)

---

### 4. Web Fetch Tool

Fetch full page content from specified URLs (HTML and PDF). Unlike Web Search, this fetches known URLs.

| Dimension | Description |
|------|------|
| **Anthropic** | `web_fetch_20250910` (basic) / `web_fetch_20260209` (dynamic filtering). No additional cost. Supports HTML and PDF |
| **Bedrock** | Not natively supported |
| **Notes** | Web Fetch can be implemented via proxy layer |

**Implementation Approach**: Similar agentic loop as Web Search. Proxy intercepts `web_fetch_*` tool calls, uses httpx to fetch URL content directly (no API Key needed), built-in HTML-to-text conversion, PDF as base64.

**References**:
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/web-fetch-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-fetch-tool)
- Reference implementation:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch_service.py)
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch/providers.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch/providers.py)

---

### 5. Code Execution Tool

Execute Bash commands and file operations in a secure sandbox. Foundation for Web Search/Fetch dynamic filtering and PTC.

| Dimension | Description |
|------|------|
| **Anthropic** | `code_execution_20250825`. Server-side tool. Container: 5GiB RAM, 5GiB disk, 1 CPU, no network. Free when used with web_search/web_fetch 20260209 |
| **Bedrock** | Not natively supported |
| **Notes** | Code Execution container can be provided via proxy layer |

**Implementation Approach**: Manage Docker containers at the proxy layer with an agentic loop:

1. Proxy identifies `code_execution_20250825` tool definitions
2. Implements `bash_code_execution` and `text_editor_code_execution` sub-tools
3. Intercepts code execution calls from Bedrock responses
4. Executes in local Docker containers
5. Injects results and resends to Bedrock
6. Loops until model stops calling code execution

Requires container lifecycle management (creation, reuse, expiration).

**References**:
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/code-execution-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/code-execution-tool)
- Reference implementation:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py)
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/standalone_sandbox.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/standalone_sandbox.py)

---

### 6. Programmatic Tool Calling (PTC)

Claude writes Python code to call client tools programmatically, reducing model round-trips. Ideal for complex agent workflows.

| Dimension | Description |
|------|------|
| **Anthropic** | Depends on Code Execution Tool (`code_execution_20260120`). Key fields: `allowed_callers`, `caller`. Supported: Opus 4.6/4.5, Sonnet 4.6/4.5 |
| **Bedrock** | Not natively supported |
| **Notes** | PTC can be provided via proxy layer with Code Execution environment |

**Implementation Approach**: Implement the complete PTC protocol at the proxy layer:

1. Identify tool definitions with `allowed_callers` containing `code_execution`
2. Filter these tools from requests to Bedrock (Bedrock does not recognize `allowed_callers`)
3. When Bedrock returns `tool_use` with `caller.type == "code_execution"`, proxy intercepts
4. Execute Claude-generated Python code in Docker sandbox
5. When code calls client tools, pause and return `tool_use` to client
6. After client returns `tool_result`, inject back into sandbox
7. Loop until code completes, inject final `code_execution_tool_result`

**References**:
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/programmatic-tool-calling](https://docs.anthropic.com/en/agents-and-tools/tool-use/programmatic-tool-calling)
- Reference implementation:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py)
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/sandbox.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/sandbox.py)

---

### 7–14. Files API, Batch Processing, Token Counting, MCP Connector, Memory Tool, Bash/Text Editor, Computer Use, Agent Skills

For detailed implementation guidance on these features, see the Chinese version ([ANTHROPIC_VS_BEDROCK_CN.md](ANTHROPIC_VS_BEDROCK_CN.md)) which contains complete workaround solutions and reference implementations for each.

Key highlights:
- **Bash Tool / Text Editor Tool**: Natively supported on both InvokeModel and Converse API. Note: Bedrock requires tool name `str_replace_based_edit_tool` (not `text_editor`) and type `text_editor_20250728`.
- **Computer Use Tool**: Not supported on Bedrock (even Opus 4.6). Can be simulated via custom tool definitions.
- **Files API**: Can be implemented via S3 + DynamoDB at the proxy layer.
- **Batch Processing**: Bedrock has its own [Batch Inference Jobs](https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html) with a different API format.


---

## Beta Header Handling on Bedrock

The Anthropic API enables experimental features via the `anthropic-beta` header ([https://docs.anthropic.com/en/api/beta-headers](https://docs.anthropic.com/en/api/beta-headers)). On Bedrock, these require categorized handling:

### Accepted Beta Headers (Bedrock InvokeModel)

| Beta Header | Feature | Verified |
|------------|------|:---:|
| `interleaved-thinking-2025-05-14` | Interleaved Thinking | ✅ |
| `context-management-2025-06-27` | Context Editing | ✅ |
| `compact-2026-01-12` | Compaction | ✅ |
| `computer-use-2025-01-24` | Computer Use (bash + text editor work, computer does not) | ✅ |
| `computer-use-2025-11-24` | Computer Use (new version) | ✅ |
| `context-1m-2025-08-07` | 1M Context Window | ✅ |
| `structured-outputs-2025-11-13` | Structured Outputs | ✅ |
| `token-efficient-tools-2025-02-19` | Token Efficient Tools | ✅ |
| `effort-2025-11-24` | Effort Parameter | ✅ |
| `tool-examples-2025-10-29` | Tool Input Examples | ✅ |
| `tool-search-tool-2025-10-19` | Tool Search | ✅ |
| `fine-grained-tool-streaming-2025-05-14` | Fine-grained Tool Streaming (GA, use `eager_input_streaming` instead) | ✅ |
| `pdfs-2024-09-25` | PDF Support (GA) | ✅ |
| `output-128k-2025-02-19` | 128k Output (GA) | ✅ |
| `token-counting-2024-11-01` | Token Counting | ❌ Header accepted but not functional |
| `mcp-client-2025-11-20` | MCP Connector | ❌ Header accepted but not functional |
| `web-search-2025-03-05` | Web Search | ❌ Header accepted but not functional |

### Headers Requiring Mapping (Different Names on Bedrock)

| Anthropic Header | Bedrock Header | Feature | Notes |
|-----------------|---------------|------|------|
| `advanced-tool-use-2025-11-20` | `tool-examples-2025-10-29` | Tool Input Examples | InvokeModel API only |
| `advanced-tool-use-2025-11-20` | `tool-search-tool-2025-10-19` | Tool Search | InvokeModel API only |

> **Important**: These Bedrock beta headers are only available via InvokeModel API, not Converse API. Automatic API switching is required.

### Rejected Beta Headers ("invalid beta flag")

| Beta Header | Feature |
|------------|------|
| `advanced-tool-use-2025-11-20` | Advanced Tool Use (Anthropic aggregate header; Bedrock requires split headers: `tool-examples-2025-10-29` / `tool-search-tool-2025-10-19`) |
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

Reference implementation: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py)

---

## Claude Code / Agent SDK Integration Notes for Bedrock

When Claude Code or Agent SDK detects a direct Bedrock connection (`CLAUDE_CODE_USE_BEDROCK=1`), it modifies its behavior:

1. **Sends incompatible beta headers**: Claude Code sends beta headers not supported by Bedrock (e.g., `advanced-tool-use-2025-11-20`, `prompt-caching-scope-2026-01-05`), causing "invalid beta flag" errors. LiteLLM published a dedicated incident report and implemented provider-specific filtering. See:
   - [https://github.com/anthropics/claude-code/issues/11672](https://github.com/anthropics/claude-code/issues/11672)
   - [https://docs.litellm.ai/blog/claude-code-beta-headers-incident](https://docs.litellm.ai/blog/claude-code-beta-headers-incident)

2. **max_tokens auto-truncation**: Known issue [https://github.com/anthropics/claude-code/issues/8756](https://github.com/anthropics/claude-code/issues/8756)

3. **Task tool / sub-agent model ID error**: Task tool uses hardcoded Anthropic model IDs (e.g., `.anthropic.claude-sonnet-4-5-20250929-v1:0`, missing `us` prefix), causing "The provided model identifier is invalid" on Bedrock. See [https://github.com/anthropics/claude-code/issues/21235](https://github.com/anthropics/claude-code/issues/21235)

4. **tool_use permission prompt delayed 10-20s**: Claude Code does not set `eager_input_streaming: true` on tool definitions. See [https://github.com/anthropics/claude-code/issues/26941](https://github.com/anthropics/claude-code/issues/26941)

5. **Feature degradation**: Advanced features (PTC, Web Search, Code Execution) are not available when connecting directly to Bedrock

**Workaround**: Use a proxy that masquerades as the Anthropic API (set `CLAUDE_CODE_USE_BEDROCK=0` + custom `ANTHROPIC_BASE_URL`). The proxy layer handles:
- Filtering unsupported beta headers
- Mapping `advanced-tool-use-2025-11-20` → `tool-examples-2025-10-29` / `tool-search-tool-2025-10-19`
- Mapping Anthropic model IDs to Bedrock model IDs
- Auto-injecting `eager_input_streaming: true` on tool definitions

Reference implementation: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/api/messages.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/api/messages.py)
