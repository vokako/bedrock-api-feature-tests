<div align="center">

# Anthropic API Features on AWS Bedrock

**Anthropic API 各特性在 AWS Bedrock 上的支持情况**

</div>

---

本文档逐一梳理 Anthropic Messages API 的每个特性，说明其在 AWS Bedrock 上的原生支持状态。对于存在差异（Gap）的特性，指出可行的 Workaround 方向及参考实现。

---

## 总览

| 特性 | Anthropic API | Bedrock Converse | Bedrock Invoke | Gap | 验证 |
|------|:---:|:---:|:---:|:---:|:---:|
| Messages API 基础 | ✅ | ✅ | ✅ | 无 | [test_01](test_01_messages_basic.py) |
| Streaming (SSE) | ✅ | ✅ | ✅ | 无 | [test_02](test_02_streaming.py) |
| Tool Use | ✅ | ✅ | ✅ | 无 | [test_03](test_03_tool_use.py) |
| Extended Thinking | ✅ | ✅ | ✅ | 无 | [test_04](test_04_extended_thinking.py) |
| Adaptive Thinking | ✅ | ✅ | ✅ | 无 | [test_16](test_16_adaptive_thinking.py) |
| Interleaved Thinking | ✅ | ✅ | ✅ | 无 | [test_05](test_05_interleaved_thinking.py) |
| Prompt Caching | ✅ | ✅ | ✅ | 无 | [test_06](test_06_prompt_caching.py) |
| Vision | ✅ | ✅ | ✅ | 无 | [test_07](test_07_vision.py) |
| PDF Support | ✅ | ✅ | ✅ | 无 | [test_08](test_08_pdf_support.py) |
| Citations | ✅ | ✅ | ✅ | 无 | [test_09](test_09_citations.py) |
| Structured Outputs | ✅ | ✅ | ✅ | 无 | [test_10](test_10_structured_outputs.py) |
| Fine-grained Tool Streaming | ✅ | ✅ | ✅ | 无 | [test_11](test_11_eager_input_streaming.py) |
| Compaction | ✅ | ✅ | ✅ | 无 | [test_12](test_12_compaction.py) |
| Context Editing | ✅ | ✅ | ✅ | 无 | [test_13](test_13_context_editing.py) |
| Tool Search | ✅ | ❌ | ✅ | Converse 不支持 | [test_14](test_14_tool_search.py) |
| Tool Input Examples | ✅ | ❌ | ✅ | Converse 不支持 | [test_15](test_15_tool_input_examples.py) |
| Web Search Tool | ✅ | ❌ | ❌ | **完全不支持** |
| Web Fetch Tool | ✅ | ❌ | ❌ | **完全不支持** |
| Code Execution Tool | ✅ | ❌ | ❌ | **完全不支持** |
| Programmatic Tool Calling | ✅ | ❌ | ❌ | **完全不支持** |
| Files API | ✅ | ❌ | ❌ | **完全不支持** |
| Batch Processing | ✅ | ❌ | ❌ | **完全不支持** |
| Token Counting | ✅ | ❌ | ❌ | **完全不支持** |
| MCP Connector | ✅ | ❌ | ❌ | **完全不支持** |
| Memory Tool | ✅ | ❌ | ❌ | **完全不支持** |
| Bash Tool | ✅ | ❌ | ✅ | Converse 不支持 | [test_17](test_17_bash_tool.py) |
| Text Editor Tool | ✅ | ❌ | ✅ | Converse 不支持 | [test_18](test_18_text_editor_tool.py) |
| Computer Use Tool | ✅ | ❌ | ❌ | **完全不支持** |
| Agent Skills | ✅ | ❌ | ❌ | **完全不支持** |

---

## 无 Gap 的特性

以下特性 Bedrock 完整支持。其中 Bedrock InvokeModel API 与 Anthropic API 格式基本等价（请求/响应结构相同，仅需添加 `anthropic_version` 字段和调整认证方式），无需做格式转换；Converse API 则需要做 Anthropic ↔ Bedrock 格式转换。

### Messages API 基础

Claude 的核心对话接口，支持多轮对话、system prompt、assistant prefill。所有与 Claude 的交互都通过此 API 进行。

- **Anthropic**: [https://docs.anthropic.com/en/api/messages](https://docs.anthropic.com/en/api/messages)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html)
- InvokeModel API 与 Anthropic API 格式基本等价，直接透传即可。Converse API 提供统一接口但格式不同，需做转换。

### Streaming (SSE)

服务端推送事件流，实现逐 token 输出。适用于需要实时展示生成过程的交互式应用（聊天、代码生成等）。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/streaming](https://docs.anthropic.com/en/build-with-claude/streaming)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModelWithResponseStream.html](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModelWithResponseStream.html) / ConverseStream
- InvokeModelWithResponseStream 返回的 SSE 事件格式与 Anthropic 一致。ConverseStream 使用 Bedrock 自有格式，需转换。

### Tool Use（函数调用）

让 Claude 调用外部工具/函数，如查询数据库、调用 API、执行计算等。是构建 Agent 的核心能力。

- **Anthropic**: [https://docs.anthropic.com/en/agents-and-tools/tool-use/overview](https://docs.anthropic.com/en/agents-and-tools/tool-use/overview)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages-tool-use.html](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages-tool-use.html)
- InvokeModel API 下工具定义格式与 Anthropic 一致。Converse API 下工具 schema 格式不同，需做转换。

### Extended Thinking

让 Claude 在回答前进行深度推理，输出 thinking block。适用于数学、逻辑推理、复杂代码等需要多步思考的任务。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/extended-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-extended-thinking.html)
- Converse 和 Invoke API 均支持 `thinking` 参数。

### Adaptive Thinking

Claude 动态决定是否思考及思考深度，无需手动设置 `budget_tokens`。适用于任务复杂度不均匀的场景（如 agentic workflow 中简单和复杂步骤交替出现）。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/adaptive-thinking](https://docs.anthropic.com/en/build-with-claude/adaptive-thinking)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html)
- `thinking: {type: "adaptive"}` — 无需 beta header。仅 Opus 4.6 / Sonnet 4.6 支持。自动启用 interleaved thinking。可配合 `output_config.effort`（`max`/`high`/`medium`/`low`）控制思考程度。

### Interleaved Thinking

在工具调用之间穿插思考过程。适用于多步工具调用的 Agent 场景，让 Claude 在每次工具返回后重新思考下一步。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/extended-thinking#interleaved-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking#interleaved-thinking)
- **Bedrock**: Beta header `interleaved-thinking-2025-05-14` 直接透传。
- 在手动 extended thinking 模式（`thinking.type: "enabled"`）下通过 beta header 启用。Adaptive thinking 模式下自动启用，无需此 header。

### Prompt Caching

缓存重复使用的 system prompt、工具定义等，避免重复计算 token。适用于多轮对话、长 system prompt、频繁调用相同工具集的场景，可显著降低延迟和成本。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/prompt-caching](https://docs.anthropic.com/en/build-with-claude/prompt-caching)
- **Bedrock**: InvokeModel API 下 `cache_control` 格式与 Anthropic 一致；Converse API 通过 `cachePoint` 机制支持，需做转换。TTL 支持 5m 和 1h。

### Vision（多模态）

让 Claude 理解和分析图像内容。适用于图表解读、OCR、UI 截图分析、图像描述等场景。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/vision](https://docs.anthropic.com/en/build-with-claude/vision)
- **Bedrock**: 支持 base64 编码图像输入（JPEG, PNG, GIF, WebP）。

### PDF Support

直接传入 PDF 文档让 Claude 阅读和分析。适用于文档摘要、合同审查、论文分析等场景，无需预处理提取文本。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/pdf-support](https://docs.anthropic.com/en/build-with-claude/pdf-support)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_DocumentUnderstanding_AnthropicClaude_section.html](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_DocumentUnderstanding_AnthropicClaude_section.html) — 支持 document content block。

### Citations

Claude 在回答中引用来源文档的具体位置。适用于需要溯源验证的场景（RAG、文档问答、研究报告）。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/citations](https://docs.anthropic.com/en/build-with-claude/citations)
- **Bedrock**: Converse API 支持。

### Structured Outputs

强制 Claude 输出符合指定 JSON Schema 的结构化数据。适用于数据提取、表单填充、API 响应生成等需要严格格式的场景。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/structured-outputs](https://docs.anthropic.com/en/build-with-claude/structured-outputs)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-structured-outputs.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-structured-outputs.html)

### Fine-grained Tool Streaming

流式传输工具调用参数，跳过 JSON 缓冲验证，降低工具调用的首 chunk 延迟。适用于需要快速展示工具调用权限提示的交互式应用（如 Claude Code）。

- **Anthropic**: [https://docs.anthropic.com/en/agents-and-tools/tool-use/fine-grained-tool-streaming](https://docs.anthropic.com/en/agents-and-tools/tool-use/fine-grained-tool-streaming)
- **Bedrock**: 全平台支持（GA，无需 beta header）
- 启用方式：在工具定义中设置 `"eager_input_streaming": true`。注意可能收到不完整的 JSON，需客户端处理。
- **实际影响**：Bedrock 默认缓冲整个 tool_use JSON 块，导致工具调用延迟 10-20 秒。启用后降至 1-3 秒。详见 [https://github.com/anthropics/claude-code/issues/26941](https://github.com/anthropics/claude-code/issues/26941)

### Compaction

自动压缩对话历史以适应上下文窗口。适用于长对话或 Agent 循环中上下文逐渐膨胀的场景，避免超出 context window 限制。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/compaction](https://docs.anthropic.com/en/build-with-claude/compaction)
- **Bedrock**: [https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-compaction.html](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-compaction.html)
- Beta header `compact-2026-01-12` 直接透传。

### Context Editing

编辑对话上下文中的特定消息，无需重新发送整个对话历史。适用于需要修正或更新历史消息的场景。

- **Anthropic**: [https://docs.anthropic.com/en/build-with-claude/context-editing](https://docs.anthropic.com/en/build-with-claude/context-editing)
- **Bedrock**: Beta header `context-management-2025-06-27` 直接透传。

---

## 有 Gap 的特性


### 1. Tool Search Tool

让 Claude 从大量工具（最多 10,000 个）中动态发现和加载所需工具，而非一次性加载所有工具定义。适用于 MCP 多服务器集成、大型工具库等工具数量超过 30-50 个导致选择准确率下降的场景。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `tool_search_tool_regex_20251119` / `tool_search_tool_bm25_20251119`。Server-side tool，Claude 动态发现和加载工具（最多 10,000 个），每次返回 3-5 个最相关工具。支持模型：Sonnet 4.0+, Opus 4.0+（不支持 Haiku） |
| **Bedrock** | **Converse API 不支持**。仅 InvokeModel API 支持，需传递 `tool-search-tool-2025-10-19` beta header |
| **Gap** | 使用 Converse API 的应用无法使用 Tool Search |

**Workaround Solution**：

- 检测到请求中包含 tool search 工具时，将 Anthropic beta header `advanced-tool-use-2025-11-20` 映射为 Bedrock 的 `tool-search-tool-2025-10-19`
- 自动从 Converse API 切换到 InvokeModel API
- 仅对支持的模型生效（配置在 `beta_header_supported_models` 中）

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/tool-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/tool-search-tool)
- Bedrock: [https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html)（通过 InvokeModel）
- Workaround 参考实现:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py) — `beta_header_mapping` / `beta_headers_requiring_invoke_model`
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/converters/anthropic_to_bedrock.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/converters/anthropic_to_bedrock.py) — `_map_beta_headers()` / `_supports_beta_header_mapping()`
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/bedrock_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/bedrock_service.py) — `invoke_model()` 方法，Claude 模型自动使用 InvokeModel API

---

### 2. Tool Input Examples (input_examples)

为工具定义提供示例输入，帮助 Claude 更好地理解工具的使用方式和参数格式。适用于工具参数复杂或模型经常传错参数的场景。

| 维度 | 说明 |
|------|------|
| **Anthropic** | 工具定义中的 `input_examples` 字段，为工具提供示例输入。Beta header: `advanced-tool-use-2025-11-20` |
| **Bedrock** | **Converse API 不支持**。仅 InvokeModel API 支持，需传递 `tool-examples-2025-10-29` beta header |
| **Gap** | 与 Tool Search 相同，Converse API 不可用 |

**Workaround Solution**：

- 同 Tool Search — 映射 `advanced-tool-use-2025-11-20` → `tool-examples-2025-10-29`
- 自动切换到 InvokeModel API

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/implement-tool-use#providing-tool-use-examples](https://docs.anthropic.com/en/agents-and-tools/tool-use/implement-tool-use#providing-tool-use-examples)
- Bedrock: 同上（InvokeModel API）
- Workaround 参考实现: 同 Tool Search（共用同一套 beta header 映射机制）

---

### 3. Web Search Tool

让 Claude 直接搜索互联网获取实时信息，自动引用来源。适用于需要最新数据的问答、事实核查、市场调研等场景。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `web_search_20250305`（基础版）/ `web_search_20260209`（动态过滤版）。Server-side tool，Anthropic 服务端执行搜索。$10/1,000 次搜索。支持 `max_uses`、`allowed_domains`、`blocked_domains`、`user_location`。动态过滤版 Claude 可编写代码过滤搜索结果 |
| **Bedrock** | **完全不支持**（Converse 和 Invoke API 均无此能力） |
| **Gap** | Bedrock 无原生 Web Search |

**Workaround Solution**：

代理端实现 agentic loop，拦截并执行搜索：

1. 代理拦截请求中的 `web_search_*` 工具定义，不传递给 Bedrock
2. 当 Bedrock 返回对 web_search 工具的调用（`server_tool_use`）时，代理拦截该调用
3. 代理端调用第三方搜索 API（Tavily / Brave Search）执行搜索
4. 将结果以 `web_search_tool_result` 格式注入响应
5. 将带有搜索结果的消息重新发送给 Bedrock 继续生成
6. 循环直到模型不再调用搜索（agentic loop）

动态过滤版（`web_search_20260209`）需额外配合 Docker sandbox 执行 Claude 生成的过滤代码。

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/web-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-search-tool)
- Bedrock: 无对应文档
- Workaround 参考实现:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py) — `WebSearchService` 类，实现 agentic loop、工具拦截、结果注入
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search/providers.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search/providers.py) — Tavily / Brave Search API 调用
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search/domain_filter.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search/domain_filter.py)
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/schemas/web_search.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/schemas/web_search.py)

---

### 4. Web Fetch Tool

让 Claude 抓取指定 URL 的完整页面内容（HTML 和 PDF）。适用于需要分析特定网页、阅读文档、提取结构化数据的场景。与 Web Search 不同，这里是抓取已知 URL 而非搜索关键词。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `web_fetch_20250910`（基础版）/ `web_fetch_20260209`（动态过滤版）。Server-side tool，抓取指定 URL 完整内容。无额外费用。支持 HTML 和 PDF |
| **Bedrock** | **完全不支持** |
| **Gap** | Bedrock 无原生 Web Fetch |

**Workaround Solution**：

与 Web Search 类似的 agentic loop 模式：

- 代理拦截 `web_fetch_*` 工具调用
- 使用 httpx 直接抓取 URL 内容（无需额外 API Key）
- 内置 HTML 转纯文本，PDF 以 base64 传递
- 动态过滤版（`web_fetch_20260209`）需 Docker sandbox

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/web-fetch-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-fetch-tool)
- Bedrock: 无对应文档
- Workaround 参考实现:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch_service.py) — `WebFetchService` 类
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch/providers.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch/providers.py) — httpx 直接抓取
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/schemas/web_fetch.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/schemas/web_fetch.py)

---

### 5. Code Execution Tool

让 Claude 在安全沙箱中执行 Bash 命令和文件操作。适用于数据分析、图表生成、复杂计算、文件处理等需要实际运行代码的场景。也是 Web Search/Fetch 动态过滤和 PTC 的基础依赖。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `code_execution_20250825`。Server-side tool，Claude 在安全沙箱中执行 Bash 命令和文件操作。容器规格：5GiB RAM, 5GiB 磁盘, 1 CPU, 无网络。Beta header: `code-execution-2025-08-25`。与 web_search/web_fetch 20260209 配合使用时免费 |
| **Bedrock** | **完全不支持** |
| **Gap** | Bedrock 无 Code Execution 容器环境 |

**Workaround Solution**：

代理端管理 Docker 容器，实现 agentic loop：

1. 代理识别 `code_execution_20250825` 工具定义
2. 实现 `bash_code_execution` 和 `text_editor_code_execution` 两个子工具
3. 将 Bedrock 响应中对 code execution 的调用拦截
4. 在本地 Docker 容器中执行命令/文件操作
5. 将结果注入消息后重新发送给 Bedrock
6. 循环直到模型不再调用 code execution

需实现容器生命周期管理（创建、复用、过期）。

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/code-execution-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/code-execution-tool)
- Bedrock: 无对应文档
- Workaround 参考实现:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py) — `StandaloneCodeExecutionService` 类，实现 agentic loop
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/standalone_sandbox.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/standalone_sandbox.py) — Docker 容器创建、执行、复用、清理

---

### 6. Programmatic Tool Calling (PTC)

让 Claude 编写 Python 代码在沙箱中批量调用客户端工具，减少模型往返次数。适用于需要循环调用多个工具、过滤大量数据、条件分支执行等复杂 Agent 工作流。

| 维度 | 说明 |
|------|------|
| **Anthropic** | 依赖 Code Execution Tool (`code_execution_20260120`)。Claude 编写 Python 代码在沙箱中调用客户端工具，减少模型往返。关键字段：`allowed_callers`、`caller`。支持模型：Opus 4.6/4.5, Sonnet 4.6/4.5 |
| **Bedrock** | **完全不支持** |
| **Gap** | Bedrock 无 Code Execution 环境，无法支持 PTC |

**Workaround Solution**：

代理层实现完整的 PTC 协议：

1. 识别请求中 `allowed_callers` 包含 `code_execution` 的工具定义
2. 将这些工具从发给 Bedrock 的请求中过滤掉（Bedrock 不认识 `allowed_callers`）
3. 当 Bedrock 返回 `tool_use` 且 `caller.type == "code_execution"` 时，代理拦截
4. 在 Docker sandbox 中执行 Claude 生成的 Python 代码
5. 当代码中调用了客户端工具时，暂停执行，将 `tool_use` 返回给客户端
6. 客户端返回 `tool_result` 后，注入回 sandbox 继续执行
7. 循环直到代码执行完毕，将最终结果作为 `code_execution_tool_result` 注入消息继续对话

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/programmatic-tool-calling](https://docs.anthropic.com/en/agents-and-tools/tool-use/programmatic-tool-calling)
- Bedrock: 无对应文档
- Workaround 参考实现:
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py) — `PTCService` 类，实现完整 PTC 协议
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/sandbox.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/sandbox.py) — Docker 容器管理、代码执行
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/schemas/ptc.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/schemas/ptc.py)
  - [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py) — `_filter_non_direct_tool_calls()` 函数

---

### 7. Files API

上传文件后通过 `file_id` 在多次请求中复用，避免每次请求重复传输大文件。适用于需要反复引用同一文档/图片的多轮对话，或配合 Code Execution 上传数据集进行分析。

| 维度 | 说明 |
|------|------|
| **Anthropic** | Beta header: `files-api-2025-04-14`。独立文件管理端点（上传/下载/列表/删除）。通过 `file_id` 在多次请求中复用。单文件最大 500MB，组织总存储 100GB |
| **Bedrock** | **完全不支持** |
| **Gap** | Bedrock 无 Files API，每次请求需内联传递文件内容 |

**Workaround Solution**：

在代理层实现文件存储服务：

- 使用 S3 作为后端存储，提供兼容的 `/v1/files` REST 端点（CRUD）
- 上传时将文件存入 S3，在 DynamoDB 中记录 `file_id → S3 key` 映射
- Messages 请求中遇到 `file_id` 引用时，从 S3 读取文件内容
- 按类型转换为对应的 content block（`document` / `image` / `container_upload`）内联注入请求体后发送给 Bedrock

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/build-with-claude/files](https://docs.anthropic.com/en/build-with-claude/files)
- Bedrock: 无对应文档
- Workaround 参考:
  - S3 文件存储 + DynamoDB 元数据索引方案，参考 AWS 官方 [https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)
  - Anthropic Files API 接口规范: [https://docs.anthropic.com/en/api/files-create](https://docs.anthropic.com/en/api/files-create)

---

### 8. Batch Processing

异步批量处理大量请求，享受 50% 折扣。适用于大规模数据标注、批量文档处理、评测跑分等不需要实时响应的场景。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `POST /v1/messages/batches`。异步批量处理，50% 折扣，最长 24 小时 |
| **Bedrock** | 有自己的 [https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html](https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html)，但接口完全不同 |
| **Gap** | 接口不兼容 |

**Workaround Solution**：

在代理层实现 Anthropic Batch API 接口（`POST /v1/messages/batches`），两种策略：

- **策略 A**：转换为 Bedrock Batch Inference Jobs
  - 通过 `CreateModelInvocationJob` API
  - 将批量请求写入 S3 JSONL 文件作为输入
  - 异步执行后从 S3 读取结果
- **策略 B**：排队逐个执行（适用于不支持 Batch Inference 的模型）
  - 使用 SQS 队列排队逐个调用 InvokeModel
  - 通过 DynamoDB 跟踪每个请求的状态
  - 客户端轮询 `GET /v1/messages/batches/{id}` 获取结果

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/build-with-claude/batch-processing](https://docs.anthropic.com/en/build-with-claude/batch-processing)
- Bedrock: [https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html](https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html)
- Workaround 参考:
  - Bedrock CreateModelInvocationJob API: [https://docs.aws.amazon.com/bedrock/latest/APIReference/API_CreateModelInvocationJob.html](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_CreateModelInvocationJob.html)
  - Anthropic Batch API 接口规范: [https://docs.anthropic.com/en/api/creating-message-batches](https://docs.anthropic.com/en/api/creating-message-batches)

---

### 9. Token Counting

在发送请求前预估 token 用量。适用于需要精确控制成本、预判是否超出 context window、或实现 token 预算管理的场景。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `POST /v1/messages/count_tokens`。发送前预估 token 用量 |
| **Bedrock** | **不支持**独立 token 计数端点 |
| **Gap** | 无法在发送前预估 token |

**Workaround Solution**：

在代理层实现 `POST /v1/messages/count_tokens` 端点：

- 使用 Anthropic 官方开源的 tokenizer 进行本地计算
- Claude 使用的 tokenizer 基于 `tiktoken`，Anthropic Python SDK 内置了 `client.count_tokens()` 方法可参考
- 也可使用 `anthropic-tokenizer` 包离线计算
- 注意：图片和 PDF 的 token 计算需按 Anthropic 的规则估算（如图片按分辨率计算）

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/build-with-claude/token-counting](https://docs.anthropic.com/en/build-with-claude/token-counting)
- Bedrock: 无对应文档
- Workaround 参考:
  - Anthropic Token Counting API 规范: [https://docs.anthropic.com/en/api/messages/count_tokens](https://docs.anthropic.com/en/api/messages/count_tokens)
  - Anthropic Python SDK tokenizer: [https://github.com/anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python)

---

### 10. MCP Connector

在 API 请求中直接连接远程 MCP 服务器，无需客户端实现 MCP 协议。适用于需要在服务端集成多个 MCP 工具源（如 GitHub、Slack、数据库等）的场景。

| 维度 | 说明 |
|------|------|
| **Anthropic** | Beta header: `mcp-client-2025-11-20`。在 API 请求中通过 `mcp_servers` 字段直接连接远程 MCP 服务器 |
| **Bedrock** | **不支持** |
| **Gap** | Bedrock 无法在推理时连接外部 MCP 服务器 |

**Workaround Solution**：

在代理层实现 MCP 客户端：

1. 解析请求中的 `mcp_servers` 字段
2. 使用 MCP SDK 连接指定的远程 MCP 服务器
3. 调用 `tools/list` 获取工具列表，转换为 Anthropic tool 定义注入请求的 `tools` 数组
4. 当模型返回对 MCP 工具的调用时，代理通过 MCP 协议调用对应服务器的 `tools/call`
5. 将结果作为 `tool_result` 注入消息继续对话

需处理 MCP 服务器的连接管理、认证、超时和错误重试。

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/mcp-connector](https://docs.anthropic.com/en/agents-and-tools/mcp-connector)
- Bedrock: 无对应文档
- Workaround 参考:
  - MCP 协议规范: [https://modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification)
  - MCP Python SDK: [https://github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
  - Anthropic Remote MCP Servers: [https://docs.anthropic.com/en/agents-and-tools/remote-mcp-servers](https://docs.anthropic.com/en/agents-and-tools/remote-mcp-servers)

---

### 11. Memory Tool

让 Claude 在对话中持久化记忆，跨会话记住用户偏好和上下文。适用于个性化助手、长期客户服务等需要跨对话保持状态的场景。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `memory_20250801`。Claude 可在对话中持久化记忆 |
| **Bedrock** | **不支持** |
| **Gap** | 无原生记忆持久化 |

**Workaround Solution**：

在代理层实现记忆存储服务：

- 使用 DynamoDB（或 Redis）作为后端，按 `user_id` / `organization_id` 分区存储记忆条目
- 拦截请求中的 `memory_20250801` 工具定义
- 当模型调用 memory tool 时（`add_memory` / `search_memory` / `delete_memory`），代理拦截 `server_tool_use` 调用
- 在本地执行记忆的 CRUD 操作，将结果以 `tool_result` 格式注入响应
- 搜索操作可使用 DynamoDB 的 GSI 或接入向量数据库（如 Amazon OpenSearch）实现语义检索

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/memory-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/memory-tool)
- Bedrock: 无对应文档
- Workaround 参考:
  - 类似的 agentic loop 拦截模式可参考本项目 Web Search 实现: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py)
  - Amazon DynamoDB: [https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)

---

### 12. Bash Tool / Text Editor Tool

让 Claude 直接执行 bash 命令、编辑文件。适用于自动化运维、代码编辑等需要 Claude 直接操作计算机环境的 Agent 场景（如 Claude Code）。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `bash_20250124`、`text_editor_20250124` / `text_editor_20250728`。Beta header: `computer-use-2025-01-24`。客户端工具——模型生成 `tool_use`，客户端负责执行 |
| **Bedrock** | **InvokeModel API 支持**（Converse API 不支持）。需传递 `computer-use-2025-01-24` beta header |
| **Gap** | Bedrock 上 text editor 的 tool name 必须为 `str_replace_based_edit_tool`（Anthropic 上为 `text_editor`），type 为 `text_editor_20250728`（Anthropic 上还支持 `text_editor_20250124`） |

**Workaround Solution**：

- 通过 InvokeModel API 直接传递工具定义，格式基本兼容
- 注意 Bedrock 上 text editor 的 name 差异：`str_replace_based_edit_tool`
- 模型返回 `tool_use` 后，客户端在本地环境执行命令/编辑文件，将 `tool_result` 返回继续对话

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/bash-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/bash-tool) / [https://docs.anthropic.com/en/agents-and-tools/tool-use/text-editor-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/text-editor-tool)
- Bedrock: 通过 InvokeModel API + `computer-use-2025-01-24` beta header 支持
- Workaround 参考:
  - Anthropic Computer Use 参考实现: [https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo)

---

### 13. Computer Use Tool

让 Claude 操作计算机界面（鼠标点击、键盘输入、截屏）。适用于 UI 自动化测试、RPA 等需要操作图形界面的场景。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `computer_20250124`。Beta header: `computer-use-2025-01-24`。需提供 `display_width_px`、`display_height_px` 等参数 |
| **Bedrock** | **完全不支持**。InvokeModel API 明确拒绝 `computer_20250124` tool type（即使 Opus 4.6 也不支持） |
| **Gap** | Bedrock 不支持 computer use tool type |

**Workaround Solution**：

- 将 `computer_20250124` 工具定义转换为普通的自定义 tool（`type: "custom"`），手动定义等价的 `input_schema`（包含 `action`、`coordinate` 等字段）
- 模型仍然可以生成类似的工具调用，客户端执行屏幕操作
- 缺点：失去 Anthropic 对 computer use 的专门优化和训练

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/tool-use/computer-use-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/computer-use-tool)
- Bedrock: 不支持
- Workaround 参考:
  - Anthropic Computer Use 参考实现: [https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo)

---

### 14. Agent Skills

模块化能力扩展包，包含指令、脚本和资源文件。适用于为 Claude 添加可复用的专业能力（如数据分析流程、特定领域的工作流模板）。

| 维度 | 说明 |
|------|------|
| **Anthropic** | 模块化能力扩展，包含指令、脚本和资源，依赖 Code Execution Tool |
| **Bedrock** | **不支持** |
| **Gap** | 依赖 Code Execution，Bedrock 无此基础设施 |

**Workaround Solution**：

需先解决 Code Execution Tool 的 gap（见第 5 项）。在此基础上：

1. 解析请求中的 skill 定义（包含指令、脚本、资源文件）
2. 将 skill 的指令注入 system prompt
3. 将 skill 的脚本和资源文件预加载到 Code Execution 容器中
4. 模型在执行过程中可通过 code execution 调用 skill 提供的脚本

Skills 本质上是对 Code Execution + System Prompt 的结构化封装。

**参考链接**：
- Anthropic: [https://docs.anthropic.com/en/agents-and-tools/agent-skills/overview](https://docs.anthropic.com/en/agents-and-tools/agent-skills/overview)
- Bedrock: 无对应文档
- Workaround 参考:
  - Anthropic Skills API 指南: [https://docs.anthropic.com/en/build-with-claude/skills-guide](https://docs.anthropic.com/en/build-with-claude/skills-guide)
  - 本项目 Code Execution 实现（Skills 的基础依赖）: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py)

---

## Beta Header 在 Bedrock 上的处理

Anthropic API 通过 `anthropic-beta` header 启用实验性功能（[https://docs.anthropic.com/en/api/beta-headers](https://docs.anthropic.com/en/api/beta-headers)）。在 Bedrock 上需分类处理：

### 直接透传（Bedrock 接受的 beta header）

以下 beta header 在 Bedrock InvokeModel API 上被接受（不会报 "invalid beta flag" 错误）：

| Beta Header | 功能 | 实际可用 |
|------------|------|:---:|
| `interleaved-thinking-2025-05-14` | Interleaved Thinking | ✅ 已验证 |
| `context-management-2025-06-27` | Context Editing | ✅ 已验证 |
| `compact-2026-01-12` | Compaction | ✅ 已验证 |
| `fine-grained-tool-streaming-2025-05-14` | Fine-grained Tool Streaming（已 GA，可用 `eager_input_streaming` 替代） | ✅ 已验证 |
| `tool-examples-2025-10-29` | Tool Input Examples | ✅ 已验证 |
| `tool-search-tool-2025-10-19` | Tool Search | ✅ 已验证 |
| `computer-use-2025-01-24` | Computer Use（bash + text editor） | ⚠️ bash/text_editor 可用，computer 不可用 |
| `computer-use-2024-10-22` | Computer Use（旧版） | ⚠️ 同上 |
| `mcp-client-2025-11-20` | MCP Connector | ⚠️ header 被接受，`mcp_servers` 字段可解析，但实际连接 MCP 服务器失败 |
| `token-counting-2024-11-01` | Token Counting | ⚠️ header 被接受，但 InvokeModel 不是 count_tokens 端点 |
| `pdfs-2024-09-25` | PDF Support（旧版 beta） | ✅ PDF 已 GA |
| `output-128k-2025-02-19` | 128k Output | ✅ 已 GA |
| `web-search-2025-03-05` | Web Search | ⚠️ header 被接受，但 Bedrock 无搜索后端 |

### 需要映射（Bedrock 用不同 header 名称）

| Anthropic Header | Bedrock Header | 功能 | 备注 |
|-----------------|---------------|------|------|
| `advanced-tool-use-2025-11-20` | `tool-examples-2025-10-29` | Tool Input Examples | 仅 Invoke API |
| `advanced-tool-use-2025-11-20` | `tool-search-tool-2025-10-19` | Tool Search | 仅 Invoke API |

> **重要**：这两个 Bedrock beta header 仅在 InvokeModel API 上可用，Converse API 不支持。使用时需自动切换 API。

参考实现: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py)

### Bedrock 明确拒绝的 beta header（报 "invalid beta flag"）

| Beta Header | 功能 |
|------------|------|
| `prompt-caching-scope-2026-01-05` | Prompt Caching Scope |
| `redact-thinking-2026-02-12` | Thinking 内容脱敏 |
| `files-api-2025-04-14` | Files API |
| `code-execution-2025-05-22` | Code Execution（旧版） |
| `code-execution-2025-08-25` | Code Execution |
| `max-tokens-3-5-sonnet-2024-07-15` | Max Tokens 3.5 Sonnet |
| `message-batches-2024-09-24` | Message Batches |
| `web-fetch-2025-09-10` | Web Fetch |
| `advanced-tool-use-2025-11-20` | Advanced Tool Use（Anthropic 侧的聚合 header） |

参考实现: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py)

---

## Claude Code / Agent SDK 使用 Bedrock 时的已知问题

当 Claude Code 或 Agent SDK 检测到直连 Bedrock 时（`CLAUDE_CODE_USE_BEDROCK=1`），会改变自身行为：

1. **丢弃 beta headers**：SDK 移除部分 beta header，导致 Extended Thinking、Adaptive Thinking 等功能行为与官方 API 不一致
2. **max_tokens 自动裁剪**：已知问题 [https://github.com/anthropics/claude-code/issues/8756](https://github.com/anthropics/claude-code/issues/8756)
3. **功能降级**：部分高级特性（如 PTC、Web Search）在直连 Bedrock 时不可用
4. **tool_use 权限提示延迟 10-20 秒**：Claude Code 未在工具定义中设置 `eager_input_streaming: true`，导致 Bedrock 缓冲整个 tool_use JSON 块后才返回给客户端。直连 Anthropic API 时权限提示约 1-3 秒出现，Bedrock 上需 10-20 秒。该特性已 GA，全平台支持，仅需在工具定义中添加 `"eager_input_streaming": true` 即可解决。详见 [https://github.com/anthropics/claude-code/issues/26941](https://github.com/anthropics/claude-code/issues/26941)

**Workaround**：通过代理伪装为 Anthropic 官方 API（设置 `CLAUDE_CODE_USE_BEDROCK=0` + 自定义 `ANTHROPIC_BASE_URL`），让 SDK 保持完整的 beta header 和行为。对于 `eager_input_streaming` 问题，代理层可在转发请求时自动为所有工具定义注入 `"eager_input_streaming": true`。

参考实现: [https://github.com/xiehust/anthropic_api_converter/blob/main/app/api/messages.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/api/messages.py) — 请求入口，处理模型 ID 映射和 beta header 转换
