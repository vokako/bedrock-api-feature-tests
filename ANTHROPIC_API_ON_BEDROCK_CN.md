<div align="center">

# Anthropic API on Amazon Bedrock

**Anthropic API 各特性在 Amazon Bedrock 上的支持情况**

[English Version](ANTHROPIC_API_ON_BEDROCK_EN.md)

</div>

---

本文档逐一梳理 Anthropic Messages API 的每个特性在 Amazon Bedrock 上的原生支持状态，并说明各模型之间的行为差异。对于 Bedrock 尚未内置的 Anthropic 特有特性，给出通过代理层或应用层自行实现的方案。

> 📌 **验证方式**：基于 Bedrock InvokeModel（runtime）与 Messages API（mantle）实测。所有标注 ✅ 的特性均有对应测试脚本（`claude/test_01`–`claude/test_25`）。
> 📅 **最近一次全模型复核**：2026-07-27，新增 **Claude Opus 5** 并对 Opus 5 / Sonnet 5 / Fable 5 / Opus 4.8 / 4.7 / 4.6 / Sonnet 4.6 / Haiku 4.5 全量重跑矩阵（[`claude/test_25`](claude/test_25_cross_model_matrix.py)）。上一次全量复核 2026-07-03；图片限制 2026-07-06。

## 目录

- [一、模型现状与跨模型差异](#一模型现状与跨模型差异)
- [二、特性总览表](#二特性总览表)
- [三、Bedrock 原生支持的特性](#三bedrock-原生支持的特性)
- [四、需要代理层适配的特性](#四需要代理层适配的特性)
- [五、Beta Header 在 Bedrock 上的处理](#五beta-header-在-bedrock-上的处理)
- [六、Claude Code / Agent SDK 使用 Bedrock 的注意事项](#六claude-code--agent-sdk-使用-bedrock-的注意事项)
- [七、Opus 4.8 新特性在 Bedrock 上的状态](#七opus-48-新特性在-bedrock-上的状态)

---

## 一、模型现状与跨模型差异

### 当前 Bedrock 上的 Anthropic 现代模型

| 模型 | Invoke（runtime）model ID | 说明 |
|------|--------------------------|------|
| Claude Opus 5 | `global.anthropic.claude-opus-5` | 2026-07-24 发布。**1M 上下文 / 128k 输出**，知识截止 2026-05。官方 In-Region ID 为 N/A，必须用 `global.`/`us.`。行为属新一代。 |
| Claude Sonnet 5 | `global.anthropic.claude-sonnet-5` | 2026-06-30 发布，最强 agentic Sonnet，1M 上下文 / 128k 输出 |
| Claude Fable 5 | `global.anthropic.claude-fable-5` | Mythos 级，强制 `provider_data_share` 数据保留（见 [FABLE5_PROJECT_SETUP.md](FABLE5_PROJECT_SETUP.md)） |
| Claude Opus 4.8 | `global.anthropic.claude-opus-4-8` | drop-in 替换 4.7 |
| Claude Opus 4.7 | `global.anthropic.claude-opus-4-7` | |
| Claude Opus 4.6 | `global.anthropic.claude-opus-4-6-v1` | |
| Claude Sonnet 4.6 | `global.anthropic.claude-sonnet-4-6` | |
| Claude Haiku 4.5 | `global.anthropic.claude-haiku-4-5-20251001-v1:0` | |

### 跨模型行为矩阵

全部经 `bedrock-runtime` 实测。Opus 5 列与全量复核为 2026-07-27，上一次为 2026-07-03。可用 [`claude/test_25`](claude/test_25_cross_model_matrix.py) 复现。

**关键结论：模型明显分成"新一代"（Opus 5 / Sonnet 5 / Fable 5 / Opus 4.8 / 4.7）与"4.6 一代"（Opus 4.6 / Sonnet 4.6 / Haiku 4.5）两种行为。**

| 特性 | Opus 5 | Sonnet 5 | Fable 5 | Opus 4.8 | Opus 4.7 | Opus 4.6 | Sonnet 4.6 | Haiku 4.5 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 基础调用 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Adaptive Thinking（`type:"adaptive"`+`effort`） | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ 不支持 `effort` |
| 旧版 Thinking（`type:"enabled"`+`budget_tokens`） | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ✅ | ✅ | ✅ |
| 采样参数 `temperature`/`top_p`/`top_k` | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ✅ | ✅ | ✅ |
| Structured Outputs（`output_config.format`） | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 | ✅ | ✅ | ✅ |
| Mid-conversation System Messages（`role:system`） | ✅ | ✅ | ✅ | ✅ | ❌ 400 | ❌ 400 | ❌ 400 | ❌ 400 |
| Assistant Prefill | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 最小可缓存长度（模型卡片官方值） | **512** | 1,024 | 4,096 | 4,096 | 4,096 | 1,024 | 4,096 |

数值取自各模型的 AWS 模型卡片 "Min tokens per cache checkpoint"（权威来源）。规律：**Opus 5 为 512（目前最低），Fable 5 与 Sonnet 4.6 为 1,024，其余（Sonnet 5、Opus 4.6/4.7/4.8、Haiku 4.5）均为 4,096**。Opus 5 的 512 门槛已实测确认：466 token 前缀 `cache_creation_input_tokens=0`，608 token 前缀为 608。低于该长度即使设 `cache_control` 也不会缓存。

### 所有 Claude 模型都不支持 web search（2026-07-27 实测）

Anthropic 原生的 `web_search_20250305` 服务端工具在 Bedrock 上**于校验层被拒**，实测覆盖全部模型（Opus 5 / Sonnet 5 / Fable 5 / Opus 4.8 / 4.7 / 4.6 / Sonnet 4.6 / Haiku 4.5）与**两条**访问路径：

- `bedrock-runtime` InvokeModel —— 新一代报 `tool type 'web_search_20250305' is not supported for this model`；4.6 一代报 `Input tag 'web_search_20250305' ... does not match any of the expected tags`，该报错还列出了完整白名单：`bash_20250124`、`custom`、`memory_20250818`、`text_editor_20250124/20250429/20250728`、`tool_search_tool_bm25(_20251119)`、`tool_search_tool_regex(_20251119)`。
- `bedrock-mantle` 的 `/anthropic/v1/messages`（Opus 5 / Opus 4.8 / Sonnet 5）—— 同样返回 `not supported for this model`。

这是 **schema 层拒绝，与权限无关**：用 `AdministratorAccess`、并已授予 `bedrock-websearch:*` 时依然失败。这与 GPT-5.6 形成对比——后者补上 `bedrock-websearch:*` 后 hosted web search 确实可用，见 [OpenAI 指南](OPENAI_API_ON_BEDROCK_CN.md#五web-search--可用但被一个-iam-权限门禁)。要让 Claude 在 Bedrock 上获得联网信息，只能自行检索后作为上下文传入。

### Opus 5 要点（2026-07-27 实测）

- **Model ID**：runtime 必须用 `global.anthropic.claude-opus-5`（或 `us.`）；裸 in-region 的 `anthropic.claude-opus-5` 会 `ValidationException`（模型卡片标注 In-Region 为 N/A）。`bedrock-mantle` 上则用 in-region 形式 `anthropic.claude-opus-5`，路径 `/anthropic/v1/messages`，且**必须带 `anthropic_version`**。
- **可用**：adaptive thinking、思考与工具交替、流式、视觉、PDF 输入、工具调用、citations、prompt caching、bash / text_editor / memory 工具、`tool_search`、对话中 system 消息、`eager_input_streaming`（须写在**工具定义内部**）、context editing + compaction + `input_examples`（各需对应 beta header），1M 上下文 beta header 被接受。
- **被拒**：旧版 `thinking.type:"enabled"`、`temperature`（`deprecated for this model`）、`output_config.format`、assistant prefill、`web_search_20250305`。
- **CountTokens 分端点**：`bedrock-runtime` 上 Opus 5 / Sonnet 5 / Opus 4.8 **不支持**（`The provided model doesn't support counting tokens.`，在 admin 凭证下确认，非权限问题），与模型卡片一致；但 **`bedrock-mantle` 上可用**——`POST /anthropic/v1/messages/count_tokens` 带 `anthropic_version`，Opus 5 返回 `{"input_tokens": 11}`。runtime 上 Sonnet 4.6 支持，需用 **in-region** ID 且被计数的 body 里要有 `max_tokens`。
- **Prompt caching 最小 512 token**（模型卡片），为 Bedrock 上 Claude 的最低值；最多 4 个检查点，TTL 5 分钟/1 小时，可用于 `system`/`messages`/`tools`。
- **adaptive thinking 默认开启**；据模型卡片可关闭，但关闭后 effort 上限为 `high`。
- **Computer use** 在 Opus 5 上为工具类型 `computer_20251124`，beta header `computer-use-2025-11-24`。
- **API**：支持 `Invoke`、`Converse`、`Messages`；不支持 `Responses` 与 `Chat Completions`。服务档位仅 Standard 与 Batch。
- **未上 mantle**：`anthropic.claude-sonnet-4-6` 与 `anthropic.claude-opus-4-6-v1` 在 mantle 上 404；Opus 5 / Opus 4.8 / Sonnet 5 可用。

### 关键差异要点

- **Thinking 一直可用，只是换了 API。** 新一代移除了旧版 `thinking.type:"enabled"` + `budget_tokens`（传了报 400），统一改用 **adaptive thinking**（`thinking.type:"adaptive"` + `output_config.effort`）。实测思考正常工作（Sonnet 5 / Opus 4.7 在难题上产出数千 thinking tokens）。adaptive 会自适应决定是否思考，简单问题可能不产 thinking block——这是设计如此，不是故障。迁移：把 `{"type":"enabled","budget_tokens":N}` 换成 `{"type":"adaptive"}` + `output_config:{"effort":"high"}`。
- **采样参数在新一代被移除**：`temperature`/`top_p`/`top_k` 传非默认值一律 400。改用 prompt 引导行为。
- **Structured Outputs 出现"代际反转"**：`output_config.format` 在 **4.6 一代（含 Haiku 4.5）可用**，但在**新一代全部 400**。做结构化输出须按模型分流——4.6 一代用 `output_config.format`，新一代改用 **forced tool use**（`tool_choice` 指定工具 + `input_schema`）。
- **Mid-conversation system messages**：仅 **Opus 4.8 / Fable 5 / Sonnet 5** 接受并遵守 `messages` 内的 `role:system`（见[第七节](#七opus-48-新特性在-bedrock-上的状态)）。
- **Prompt cache 最小长度按模型不同**：**Fable 5 与 Sonnet 4.6 为 1,024**；**Sonnet 5、Opus 4.6/4.7/4.8、Haiku 4.5 均为 4,096**（取自各模型卡片官方 "Min tokens per cache checkpoint"）。低于门槛即使设 `cache_control` 也不缓存（`cache_creation_input_tokens=0`）。注意新一代 tokenizer 更"膨胀"，同样文本 token 数比 4.6 一代高约 1.4–1.7×。
- **Assistant Prefill**：Claude 4.6 起（含新一代）不再支持对话最后一条为 assistant 的预填充，发送返回 400 `This model does not support assistant message prefill`。仅 Haiku 4.5 仍支持。替代：用 [Structured Outputs](#structured-outputs) 或 system prompt 控制格式。

### Opus 4.7 在 Bedrock 上的适配缺口（汇总）

Opus 4.7 有多个特性 Bedrock 侧尚未适配（beta header 被接受但带真实参数会报错）。**Opus 4.8 已修复其中大部分**，如需这些特性建议用 4.8 或 4.6：

| 特性 | Opus 4.7 表现 |
|------|--------------|
| Computer Use（bash/text_editor） | `tool type ... is not supported for this model` |
| Context Editing（message ID） | `messages.0.id: Extra inputs are not permitted` |
| Tool Search | `tool_search ... not supported for this model` |
| Fine-grained Tool Streaming（`eager_input_streaming`） | ~~曾报 `Extra inputs are not permitted`~~ 2026-07-17 复测已可用 |
| CountTokens | 仅 global 部署、无 in-region ID，不可用 |
| Mid-conversation system messages | `role 'system' is not supported`（4.8 已支持） |

### Fable 5 / Sonnet 5 备注

- **Fable 5**：曾于 2026-06 从 Bedrock 短暂下线（runtime 5xx / mantle 404），后 "back on Amazon Bedrock with stronger guardrails" 重新上线，2026-07-03 复测 runtime + mantle 均恢复正常。是 Mythos 级模型，**必须开启 `provider_data_share` 数据保留**才能调用（账号级或 project 级），详见 [FABLE5_PROJECT_SETUP.md](FABLE5_PROJECT_SETUP.md) 与 [test_22](claude/test_22_fable5.py)。
- **Sonnet 5**（2026-06-30）：最强 agentic Sonnet，1M 上下文 / 128k 输出，特性与 Sonnet 4.6 相同（除 Priority Tier），在 Bedrock 上行为归入"新一代"。

---

## 二、特性总览表

| 特性 | Anthropic API | Bedrock Converse | Bedrock Invoke | 实现差异 | 验证 |
|------|:---:|:---:|:---:|:---:|:---:|
| Messages API 基础 | ✅ | ✅ | ✅ | 无 | [test_01](claude/test_01_messages_basic.py) |
| Streaming (SSE) | ✅ | ✅ | ✅ | 无 | [test_02](claude/test_02_streaming.py) |
| Tool Use | ✅ | ✅ | ✅ | 无 | [test_03](claude/test_03_tool_use.py) |
| Extended Thinking（旧版，仅 4.6 一代） | ✅ | ✅ | ✅ | 新一代已移除 | [test_04](claude/test_04_extended_thinking.py) |
| Adaptive Thinking | ✅ | ✅ | ✅ | Haiku 4.5 无 effort | [test_16](claude/test_16_adaptive_thinking.py) |
| Interleaved Thinking | ✅ | ✅ | ✅ | 无 | [test_05](claude/test_05_interleaved_thinking.py) |
| Prompt Caching | ✅ | ✅ | ✅ | 最小长度按模型不同 | [test_06](claude/test_06_prompt_caching.py) |
| Vision | ✅ | ✅ | ✅ | 天花板 600 张/请求；101–600 非确定性（部分后端限 100），可靠安全值 100 | [test_07](claude/test_07_vision.py) [test_24](claude/test_24_image_limits.py) |
| PDF Support | ✅ | ✅ | ✅ | 无 | [test_08](claude/test_08_pdf_support.py) |
| Citations | ✅ | ✅ | ✅ | 无 | [test_09](claude/test_09_citations.py) |
| Structured Outputs (`output_config.format`) | ✅ | ✅ | ✅ | **仅 4.6 一代**；新一代 400 | [test_10](claude/test_10_structured_outputs.py) |
| Fine-grained Tool Streaming | ✅ | ✅ | ✅ | 4.6 系列 + 新一代（Opus 4.7/4.8、Fable 5，2026-07-17 复测）均支持 | [test_11](claude/test_11_eager_input_streaming.py) |
| Compaction | ✅ | ✅ | ✅ | 无 | [test_12](claude/test_12_compaction.py) |
| Context Editing | ✅ | ✅ | ✅ | Opus 4.7 不可用 | [test_13](claude/test_13_context_editing.py) |
| Tool Search | ✅ | ❌ | ✅ | 仅 Invoke API；Opus 4.7 不可用 | [test_14](claude/test_14_tool_search.py) |
| Tool Input Examples | ✅ | ❌ | ✅ | 仅 Invoke API | [test_15](claude/test_15_tool_input_examples.py) |
| Bash Tool | ✅ | ✅ | ✅ | Opus 4.7 不可用 | [test_17](claude/test_17_bash_tool.py) |
| Text Editor Tool | ✅ | ✅ | ✅ | name 映射；Opus 4.7 不可用 | [test_18](claude/test_18_text_editor_tool.py) |
| Claude 4.7 变更验证 | — | — | ✅ | breaking changes | [test_21](claude/test_21_claude47_changes.py) |
| Claude Fable 5 兼容性 | ✅ | — | ✅ | 需 `provider_data_share` | [test_22](claude/test_22_fable5.py) |
| Mid-conversation System Messages | ✅ | ❓ | ✅ | 仅新一代 4.8/Fable5/Sonnet5；文档称不支持但实测可用 | [test_23](claude/test_23_mid_conversation_system.py) |
| Token Counting | ✅ | ❌ | ❌ | Bedrock 原生 CountTokens API（仅 in-region ID） | [test_20](claude/test_20_count_tokens.py) |
| Web Search Tool | ✅ | ❌ | ❌ | 需自行实现 | — |
| Web Fetch Tool | ✅ | ❌ | ❌ | 需自行实现 | — |
| Code Execution Tool | ✅ | ❌ | ❌ | 需自行实现 | — |
| Programmatic Tool Calling | ✅ | ❌ | ❌ | 需自行实现 | — |
| Files API | ✅ | ❌ | ❌ | 需自行实现 | — |
| Batch Processing | ✅ | ❌ | ❌ | Bedrock 有独立接口 | — |
| MCP Connector | ✅ | ❌ | ❌ | 需自行实现 | — |
| Memory Tool | ✅ | ❌ | ❌ | 需自行实现 | — |
| Computer Use Tool | ✅ | ❌ | ❌ | 需自行实现 | — |
| Agent Skills | ✅ | ❌ | ❌ | 需自行实现 | — |
| Dynamic Workflows | ✅ | ❌ | ❌ | Claude Code 客户端特性，非 API | — |
| Fast Mode (`speed:"fast"`) | ✅ | ❌ | ❌ | 仅 Claude API | — |

---

## 三、Bedrock 原生支持的特性

以下特性 Bedrock 完整支持。InvokeModel API 与 Anthropic Messages API 格式基本等价（请求/响应结构相同，仅需添加 `anthropic_version` 字段和调整认证方式），无需格式转换；Converse API 则需要 Anthropic ↔ Bedrock 格式转换。

> 📌 模型间的 breaking changes（Thinking / 采样参数 / prefill / Structured Outputs 等）统一见[第一节的跨模型矩阵](#跨模型行为矩阵)，本节不再逐条重复。

### Messages API 基础

Claude 的核心对话接口，支持多轮对话、system prompt。所有与 Claude 的交互都通过此 API 进行。

- **Anthropic**: [messages](https://docs.anthropic.com/en/api/messages)
- **Bedrock**: [model-parameters-anthropic-claude-messages](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html)
- InvokeModel API 与 Anthropic API 格式基本等价，直接透传即可；Converse API 需做转换。

### Streaming (SSE)

服务端推送事件流，逐 token 输出。适用于聊天、代码生成等交互式场景。

- **Anthropic**: [streaming](https://docs.anthropic.com/en/build-with-claude/streaming)
- **Bedrock**: `InvokeModelWithResponseStream` 的 SSE 事件格式与 Anthropic 一致；ConverseStream 使用 Bedrock 自有格式需转换。

### Tool Use（函数调用）

让 Claude 调用外部工具/函数，是构建 Agent 的核心能力。

- **Anthropic**: [tool-use/overview](https://docs.anthropic.com/en/agents-and-tools/tool-use/overview)
- **Bedrock**: InvokeModel 下工具定义格式与 Anthropic 一致；Converse 下 schema 格式不同需转换。
- **结构化输出**：新一代模型（Sonnet 5/Fable 5/Opus 4.8/4.7）不支持 `output_config.format`，用 **forced tool use**（`tool_choice` 强制某工具 + `input_schema` 定义结构）替代。

### Adaptive Thinking（推荐）

Claude 动态决定是否思考及思考深度，无需手动设 `budget_tokens`。**新一代模型唯一的 thinking 方式。**

- **Anthropic**: [adaptive-thinking](https://docs.anthropic.com/en/build-with-claude/adaptive-thinking)
- **Bedrock**: [claude-messages-adaptive-thinking](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html)
- `thinking: {type: "adaptive"}` — 无需 beta header，自动启用 interleaved thinking，配合 `output_config.effort`（`low`/`medium`/`high`/`xhigh`/`max`）控制思考程度。
- 新一代默认关闭 thinking（不设 `thinking` 字段时不思考），需显式 `thinking:{type:"adaptive"}`；thinking 内容默认隐藏（`display:"omitted"`），设 `display:"summarized"` 才返回可见 thinking 文本。
- **Haiku 4.5** 不接受 `output_config.effort` 字段（其余正常）。

### Extended Thinking（旧版，仅 4.6 一代）

`thinking: {type: "enabled", budget_tokens: N}` 手动设定思考预算。**仅 Opus 4.6 / Sonnet 4.6 / Haiku 4.5 可用**，新一代已移除（返回 400），须迁移到 Adaptive Thinking。

- **Anthropic**: [extended-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking)

### Interleaved Thinking

在工具调用之间穿插思考。Adaptive thinking 模式下自动启用；手动 extended thinking 模式下通过 `interleaved-thinking-2025-05-14` beta header 启用（Opus 4.6 已 deprecated，Sonnet 4.6 仍支持）。

- **Anthropic**: [extended-thinking#interleaved-thinking](https://docs.anthropic.com/en/build-with-claude/extended-thinking#interleaved-thinking)

### Prompt Caching

缓存重复使用的 system prompt、工具定义等。**最小可缓存长度按模型不同**（见[第一节矩阵](#跨模型行为矩阵)）。

- **Anthropic**: [prompt-caching](https://docs.anthropic.com/en/build-with-claude/prompt-caching)
- **Bedrock**: InvokeModel 下 `cache_control` 格式与 Anthropic 一致；Converse 通过 `cachePoint` 支持。TTL 支持 5m 和 1h。

> ⚠️ **Bedrock 不支持顶层 Automatic Caching**：Anthropic 的顶层 `cache_control`（自动选最后一个可缓存 block）在 Bedrock 上报 `cache_control: Extra inputs are not permitted`，官方标注 "coming later"。Bedrock 目前仅支持 **explicit cache breakpoints**（在单个 content block 上设 `cache_control`）。

**Automatic Caching 的 Workaround**：代理层收到顶层 `cache_control` 时转换为显式断点——移除顶层字段，在最后一个可缓存 block（`system`/`messages`/`tools` 的最后一个）上加 `cache_control:{"type":"ephemeral"}`（InvokeModel）或追加 `cachePoint:{"type":"default"}`（Converse）。Converse API 还支持 **Simplified Cache Management**：在静态内容末尾放一个 `cachePoint`，系统自动回溯约 20 个 block 匹配最长前缀。

```jsonc
// Converse API
"messages": [{"role":"user","content":[
    {"text":"长静态内容..."},
    {"cachePoint":{"type":"default"}}
]}]

// InvokeModel API
"messages": [{"role":"user","content":[
    {"type":"text","text":"长静态内容...","cache_control":{"type":"ephemeral"}}
]}]
```

### Vision（多模态）

理解和分析图像。适用于图表解读、OCR、UI 截图分析等。

- **Anthropic**: [vision](https://docs.anthropic.com/en/build-with-claude/vision)
- **Bedrock**: 支持 base64 图像输入（JPEG/PNG/GIF/WebP）。

> ⚠️ **图片数量限制（在 Bedrock 上表现复杂，非确定性）**：
>
> Anthropic API 文档规定：200k 上下文模型限 100 张/请求，1M 上下文模型限 600 张/请求。当前 Bedrock 上所有主流模型均为 1M 上下文（Opus 4.8/4.7、Sonnet 5/4.6、Fable 5），只有 Haiku 4.5 等旧模型是 200k。
>
> 实测（2026-07-06，通过 `global.*` 跨区域推理配置）发现三层行为：
>
> 1. **绝对天花板 = 600**。所有模型发送 601 张必被拒：`ValidationException: too many images and documents: 601 + 0 > 600`。与 Anthropic 文档一致。
> 2. **101–600 之间：执行非确定性**。`global.*` 会把请求路由到不同区域后端，**部分后端执行更严格的 100 张上限**，同一个 200 张请求有时成功、有时被拒 `too many images and documents: 200 + 0 > 100`。实测 Sonnet 4.6 @200 张 ×6 次：成功 4 次、`>100` 拒绝 2 次。
> 3. **部分模型（如 Opus 4.8）对大批量多图请求返回瞬时 `ServiceUnavailableException`（5xx）**，重试可成功——这不是图片数量限制，只是服务端瞬时繁忙。
>
> | 模型 | 上下文 | Anthropic API 限制 | Bedrock 绝对天花板 | Bedrock 可靠安全上限 |
> |------|--------|-------------------|-------------------|---------------------|
> | Opus 4.8 | 1M | 600 | 600 | **100** |
> | Opus 4.7 | 1M | 600 | 600 | **100** |
> | Sonnet 5 | 1M | 600 | 600 | **100** |
> | Sonnet 4.6 | 1M | 600 | 600 | **100** |
> | Fable 5 | 1M | 600 | 600 | **100** |
>
> **实践建议：控制在 ≤100 张可在 Bedrock 上可靠成功**；101–600 张可能成功，但会随机遇到 `>100` 拒绝或瞬时 5xx；601+ 必被拒。
>
> 另外，超过 20 张图片时每张图片有更严格的尺寸限制（单边不超 2000px），否则报 `invalid_request_error`。单张图片大小限 **5 MB**（Anthropic API 为 10 MB）。
>
> 验证：[test_24](claude/test_24_image_limits.py)（2026-07-06 实测）

### PDF Support

直接传入 PDF 让 Claude 阅读分析。

- **Anthropic**: [pdf-support](https://docs.anthropic.com/en/build-with-claude/pdf-support)
- **Bedrock**: 支持 document content block。

### Citations

Claude 在回答中引用来源文档的具体位置，适用于 RAG、文档问答。

- **Anthropic**: [citations](https://docs.anthropic.com/en/build-with-claude/citations)
- **Bedrock**: InvokeModel（document block 上设 `citations:{enabled:true}`）和 Converse 均支持。

### Structured Outputs

强制输出符合 JSON Schema 的结构化数据。

- **Anthropic**: [structured-outputs](https://docs.anthropic.com/en/build-with-claude/structured-outputs)
- **Bedrock**: [claude-messages-structured-outputs](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-structured-outputs.html)

> ⚠️ **两个要点**：
> 1. 旧参数 `output_format` 在 Bedrock 上**全平台不可用**（所有模型 400，提示改用 `output_config.format`）。新语法：`"output_config":{"format":{"type":"json_schema","schema":{..., "additionalProperties":false}}}`，所有 `object` 必须显式 `"additionalProperties":false`。
> 2. **`output_config.format` 仅 4.6 一代可用**（Opus 4.6 / Sonnet 4.6 / Haiku 4.5）；**新一代（Sonnet 5 / Fable 5 / Opus 4.8 / 4.7）全部返回 400**，须改用 forced tool use（`strict:true` 工具，4.6 一代已验证支持）。

### Fine-grained Tool Streaming

流式传输工具调用参数，降低工具调用首 chunk 延迟（Bedrock 默认缓冲整块 tool_use JSON，导致 10-20s 延迟，启用后降至 1-3s）。

- **Anthropic**: [fine-grained-tool-streaming](https://docs.anthropic.com/en/agents-and-tools/tool-use/fine-grained-tool-streaming)
- **Bedrock**: 全平台 GA，无需 beta header。在工具定义中设 `"eager_input_streaming": true`。
- **模型兼容性**：4.6 系列及新一代（Opus 4.7 / Opus 4.8 / Fable 5）均支持（2026-07-17 实测三者流式 tool_use 输入正常；Opus 4.7 早期不支持，现已修复）。Sonnet 4.5 及更早会 400（`Extra inputs are not permitted`），且 Sonnet 4.5 本身已默认细粒度流式返回，无需该字段。代理层应按模型版本决定是否注入。

### Compaction

自动压缩对话历史以适应上下文窗口。

- **Anthropic**: [compaction](https://docs.anthropic.com/en/build-with-claude/compaction)
- **Bedrock**: beta header `compact-2026-01-12` 直接透传。

### Context Editing

编辑上下文中的特定消息，无需重发整个历史。

- **Anthropic**: [context-editing](https://docs.anthropic.com/en/build-with-claude/context-editing)
- **Bedrock**: beta header `context-management-2025-06-27` 直接透传。**Opus 4.7 不可用**（message ID 字段报 400）。

### Bash Tool / Text Editor Tool

让 Claude 直接执行 bash 命令、编辑文件（客户端工具，模型生成 `tool_use`，客户端执行）。

- **Anthropic**: [bash-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/bash-tool) / [text-editor-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/text-editor-tool)
- **Bedrock**: InvokeModel 和 Converse 均支持，需 `computer-use-2025-01-24` beta header。
- **name 差异**：Bedrock 上 text editor 的 name 必须为 `str_replace_based_edit_tool`，type 为 `text_editor_20250728`。
- **Opus 4.7 不可用**：`bash_20250124` / `text_editor_20250728` 均报 `not supported for this model`（Opus 4.6 正常）。

---

## 四、需要代理层适配的特性

以下特性 Bedrock 无原生支持，需通过代理层（如 [anthropic_api_converter](https://github.com/xiehust/anthropic_api_converter)）实现。

### 1. Tool Search Tool

从大量工具（最多 10,000 个）中动态发现和加载所需工具。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `tool_search_tool_regex_20251119` / `tool_search_tool_bm25_20251119`，server-side，每次返回 3-5 个最相关工具（Sonnet 4.0+/Opus 4.0+，不支持 Haiku） |
| **Bedrock** | Converse 不支持；仅 InvokeModel 支持，需 `tool-search-tool-2025-10-19` beta header。**Opus 4.7 不可用**（`not supported for this model`） |

**方案**：检测 tool search 工具时，映射 Anthropic `advanced-tool-use-2025-11-20` → Bedrock `tool-search-tool-2025-10-19`，并自动从 Converse 切换到 InvokeModel API。

- Anthropic: [tool-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/tool-search-tool)
- 参考实现: [config.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py) / [anthropic_to_bedrock.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/converters/anthropic_to_bedrock.py) / [bedrock_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/bedrock_service.py)

### 2. Tool Input Examples (`input_examples`)

为工具提供示例输入，帮助模型理解参数格式。

| 维度 | 说明 |
|------|------|
| **Anthropic** | 工具定义中的 `input_examples` 字段，beta header `advanced-tool-use-2025-11-20` |
| **Bedrock** | Converse 不支持；仅 InvokeModel，需 `tool-examples-2025-10-29` beta header |

**方案**：同 Tool Search，映射 `advanced-tool-use-2025-11-20` → `tool-examples-2025-10-29`，切换到 InvokeModel。

- Anthropic: [providing-tool-use-examples](https://docs.anthropic.com/en/agents-and-tools/tool-use/implement-tool-use#providing-tool-use-examples)

### 3. Web Search Tool

让 Claude 搜索互联网获取实时信息。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `web_search_20250305` / `web_search_20260209`（动态过滤版），server-side，$10/1,000 次 |
| **Bedrock** | 不支持（header 被接受但无搜索后端） |

**方案**：代理端实现 agentic loop——拦截 `web_search_*` 工具调用，调用第三方搜索 API（Tavily/Brave）执行，以 `web_search_tool_result` 注入响应后重新发给 Bedrock，循环至模型不再搜索。动态过滤版需 Docker sandbox 执行 Claude 生成的过滤代码。

- Anthropic: [web-search-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-search-tool)
- 参考实现: [web_search_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search_service.py) / [providers.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_search/providers.py)

### 4. Web Fetch Tool

抓取指定 URL 的完整页面内容（HTML/PDF）。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `web_fetch_20250910` / `web_fetch_20260209`，server-side，无额外费用 |
| **Bedrock** | 需自行实现 |

**方案**：类似 Web Search 的 agentic loop——拦截 `web_fetch_*` 调用，用 httpx 抓取 URL，HTML 转纯文本、PDF 以 base64 传递。

- Anthropic: [web-fetch-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/web-fetch-tool)
- 参考实现: [web_fetch_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/web_fetch_service.py)

### 5. Code Execution Tool

让 Claude 在安全沙箱中执行 Bash 命令和文件操作（也是 Web Search/Fetch 动态过滤和 PTC 的基础依赖）。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `code_execution_20250825`，server-side，容器 5GiB RAM / 1 CPU / 无网络，beta header `code-execution-2025-08-25` |
| **Bedrock** | 需自行实现 |

**方案**：代理端管理 Docker 容器，实现 agentic loop——拦截 code execution 调用，在本地容器执行命令/文件操作，结果注入消息后重发。需处理容器生命周期（创建、复用、过期）。

- Anthropic: [code-execution-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/code-execution-tool)
- 参考实现: [standalone_code_execution_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/standalone_code_execution_service.py) / [standalone_sandbox.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/standalone_sandbox.py)

### 6. Programmatic Tool Calling (PTC)

让 Claude 编写 Python 代码在沙箱中批量调用客户端工具，减少模型往返。

| 维度 | 说明 |
|------|------|
| **Anthropic** | 依赖 Code Execution (`code_execution_20260120`)，关键字段 `allowed_callers`/`caller`（Opus 4.6/4.5, Sonnet 4.6/4.5） |
| **Bedrock** | 需自行实现 |

**方案**：代理层实现完整 PTC 协议——过滤 `allowed_callers` 含 `code_execution` 的工具、在 sandbox 执行 Claude 生成的 Python 代码、代码调用客户端工具时暂停并把 `tool_use` 返回客户端、拿到 `tool_result` 后注入 sandbox 继续，最终以 `code_execution_tool_result` 注入消息。

- Anthropic: [programmatic-tool-calling](https://docs.anthropic.com/en/agents-and-tools/tool-use/programmatic-tool-calling)
- 参考实现: [ptc_service.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc_service.py) / [sandbox.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/services/ptc/sandbox.py)

### 7. Files API

上传文件后通过 `file_id` 在多次请求中复用。

| 维度 | 说明 |
|------|------|
| **Anthropic** | beta header `files-api-2025-04-14`，独立文件端点，单文件最大 500MB |
| **Bedrock** | 需自行实现 |

**方案**：代理层用 S3 存储 + DynamoDB 记录 `file_id → S3 key`，实现 `/v1/files` REST 端点；请求遇 `file_id` 时从 S3 读取内容，按类型转为 `document`/`image`/`container_upload` block 内联注入。

- Anthropic: [files](https://docs.anthropic.com/en/build-with-claude/files)

### 8. Batch Processing

异步批量处理，享 50% 折扣。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `POST /v1/messages/batches`，50% 折扣，最长 24h |
| **Bedrock** | 有独立的 [Batch Inference](https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html)，接口完全不同 |

**方案**：代理层实现 Anthropic Batch API 接口，转换为 Bedrock `CreateModelInvocationJob`（S3 JSONL 输入/输出），或用 SQS 队列 + DynamoDB 状态跟踪逐个执行。

- Anthropic: [batch-processing](https://docs.anthropic.com/en/build-with-claude/batch-processing)

### 9. Token Counting

发送前预估 token 用量。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `POST /v1/messages/count_tokens` |
| **Bedrock** | **原生支持** [CountTokens API](https://docs.aws.amazon.com/bedrock/latest/userguide/count-tokens.html)，免费，支持 InvokeModel/Converse 格式 |

> ⚠️ **限制**：CountTokens **仅支持 in-region model ID**（如 `anthropic.claude-sonnet-4-6`），用 `us.`/`global.` 前缀会报 `The provided model doesn't support counting tokens`——代理层需剥离前缀。**Opus 4.7 不支持**（仅 global 部署、无 in-region ID）。已验证支持：Claude 3.5 Haiku、Sonnet 4、Sonnet 4.5、Haiku 4.5、Sonnet 4.6、Opus 4.6。见 [test_20](claude/test_20_count_tokens.py)。

**方案**：代理层实现 `/v1/messages/count_tokens`，转换为 Bedrock CountTokens 格式并用 in-region model ID 调用；不支持的模型回退到本地 tokenizer。

- Anthropic: [token-counting](https://docs.anthropic.com/en/build-with-claude/token-counting)

### 10. MCP Connector

在 API 请求中直接连接远程 MCP 服务器。

| 维度 | 说明 |
|------|------|
| **Anthropic** | beta header `mcp-client-2025-11-20`，通过 `mcp_servers` 字段连接 |
| **Bedrock** | 不支持（header/字段被解析但连接时报错） |

**方案**：代理层实现 MCP 客户端——解析 `mcp_servers`，用 MCP SDK 连接、`tools/list` 转为 tool 定义注入 `tools`，模型调用时通过 MCP `tools/call` 执行并以 `tool_result` 注入。

- Anthropic: [mcp-connector](https://docs.anthropic.com/en/agents-and-tools/mcp-connector)

### 11. Memory Tool

让 Claude 跨会话持久化记忆。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `memory_20250801` |
| **Bedrock** | 需自行实现 |

**方案**：代理层用 DynamoDB/Redis 按 `user_id`/`organization_id` 分区存储记忆，拦截 memory tool 调用执行 CRUD，搜索可接入向量库（OpenSearch）做语义检索。

- Anthropic: [memory-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/memory-tool)

### 12. Computer Use Tool

让 Claude 操作计算机界面（鼠标/键盘/截屏）。

| 维度 | 说明 |
|------|------|
| **Anthropic** | `computer_20250124`，beta header `computer-use-2025-01-24` |
| **Bedrock** | **完全不支持**（InvokeModel 明确拒绝 `computer_20250124`，即使 Opus 4.6） |

**方案**：将 `computer_20250124` 转为普通自定义 tool（`type:"custom"`），手动定义等价 `input_schema`；客户端执行屏幕操作。缺点：失去 Anthropic 对 computer use 的专门优化。

- Anthropic: [computer-use-tool](https://docs.anthropic.com/en/agents-and-tools/tool-use/computer-use-tool)

### 13. Agent Skills

模块化能力扩展包（指令 + 脚本 + 资源），依赖 Code Execution。

| 维度 | 说明 |
|------|------|
| **Anthropic** | 依赖 Code Execution Tool |
| **Bedrock** | 需自行实现 |

**方案**：先解决 Code Execution gap（第 5 项），再将 skill 指令注入 system prompt、脚本/资源预加载到容器，模型通过 code execution 调用。

- Anthropic: [agent-skills/overview](https://docs.anthropic.com/en/agents-and-tools/agent-skills/overview)

---

## 五、Beta Header 在 Bedrock 上的处理

Anthropic API 通过 `anthropic-beta` header 启用实验性功能。在 Bedrock 上分三类处理。

### 直接透传（Bedrock InvokeModel 接受）

| Beta Header | 功能 | 备注 |
|------------|------|------|
| `interleaved-thinking-2025-05-14` | Interleaved Thinking | Opus 4.6 已 deprecated，Sonnet 4.6 仍支持 |
| `context-management-2025-06-27` | Context Editing | Opus 4.7 不可用 |
| `compact-2026-01-12` | Compaction | |
| `computer-use-2025-01-24` / `-11-24` | Computer Use（bash+text editor 可用，computer 不可用） | Opus 4.7 不可用 |
| `context-1m-2025-08-07` | 1M Context Window | |
| `structured-outputs-2025-11-13` | Structured Outputs | 仅 4.6 一代 |
| `token-efficient-tools-2025-02-19` | Token Efficient Tools | Claude 4+ 已内置，无实际效果 |
| `effort-2025-11-24` | Effort Parameter（已 GA） | Haiku 4.5 不支持 |
| `tool-examples-2025-10-29` | Tool Input Examples | 仅 Invoke API |
| `tool-search-tool-2025-10-19` | Tool Search | 仅 Invoke API；Opus 4.7 不可用 |
| `fine-grained-tool-streaming-2025-05-14` | Fine-grained Tool Streaming（已 GA） | Opus 4.7 不可用 |
| `task-budgets-2026-03-13` | Task Budgets（Opus 4.7+） | |
| `pdfs-2024-09-25` | PDF Support（已 GA） | |
| `output-128k-2025-02-19` | 128k Output（已 GA） | |
| `token-counting-2024-11-01` | Token Counting | ❌ 功能不可用（用原生 CountTokens API） |
| `mcp-client-2025-11-20` | MCP Connector | ❌ 功能不可用 |
| `web-search-2025-03-05` | Web Search | ❌ 工具类型在所有模型、两个端点上均于校验层被拒（见[第一节](#所有-claude-模型都不支持-web-search2026-07-27-实测)） |

### 需要映射（Bedrock 用不同 header 名，仅 InvokeModel）

| Anthropic Header | Bedrock Header | 功能 |
|-----------------|---------------|------|
| `advanced-tool-use-2025-11-20` | `tool-examples-2025-10-29` | Tool Input Examples |
| `advanced-tool-use-2025-11-20` | `tool-search-tool-2025-10-19` | Tool Search |

### Bedrock 明确拒绝（报 "invalid beta flag"）

`advanced-tool-use-2025-11-20`（聚合 header，需拆分）、`prompt-caching-scope-2026-01-05`、`redact-thinking-2026-02-12`、`files-api-2025-04-14`、`code-execution-2025-05-22` / `-08-25`、`max-tokens-3-5-sonnet-2024-07-15`、`message-batches-2024-09-24`、`web-fetch-2025-09-10`、`fast-mode-2026-02-01`、`skills-2025-10-02`。

参考实现: [config.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/core/config.py)

---

## 六、Claude Code / Agent SDK 使用 Bedrock 的注意事项

当 Claude Code / Agent SDK 检测到直连 Bedrock（`CLAUDE_CODE_USE_BEDROCK=1`）时，会改变行为：

1. **发送不兼容的 beta headers**（如 `advanced-tool-use-2025-11-20`、`prompt-caching-scope-2026-01-05`），导致 "invalid beta flag"。LiteLLM 曾为此发 incident report。见 [issue #11672](https://github.com/anthropics/claude-code/issues/11672)、[LiteLLM incident](https://docs.litellm.ai/blog/claude-code-beta-headers-incident)。
2. **max_tokens 自动裁剪**：[issue #8756](https://github.com/anthropics/claude-code/issues/8756)。
3. **Task tool / 子 Agent 模型 ID 错误**：使用硬编码 Anthropic 模型 ID（缺 `us` 前缀），导致 "model identifier is invalid"。[issue #21235](https://github.com/anthropics/claude-code/issues/21235)。
4. **tool_use 权限提示延迟 10-20s**：未设 `eager_input_streaming:true`。[issue #26941](https://github.com/anthropics/claude-code/issues/26941)。
5. **功能降级**：PTC、Web Search、Code Execution 等直连 Bedrock 时不可用。

**Workaround**：通过代理伪装为 Anthropic 官方 API（`CLAUDE_CODE_USE_BEDROCK=0` + 自定义 `ANTHROPIC_BASE_URL`），代理层负责过滤/映射 beta header、映射模型 ID、注入 `eager_input_streaming:true`。参考: [messages.py](https://github.com/xiehust/anthropic_api_converter/blob/main/app/api/messages.py)。

> 💡 使用 Mantle 端点（Claude in Amazon Bedrock）时，Claude Code 用 `CLAUDE_CODE_USE_MANTLE=1`，模型 ID 用 `anthropic.` 前缀（无 `global.`/`us.`）。Fable 5 的 project 隔离配置见 [FABLE5_PROJECT_SETUP.md](FABLE5_PROJECT_SETUP.md)。

---

## 七、Opus 4.8 新特性在 Bedrock 上的状态

Opus 4.8（及 Sonnet 5 / Fable 5）随附几个新卖点，在 Bedrock 上支持情况各异：

| 特性 | Bedrock 可用性 |
|------|:---:|
| Mid-conversation System Messages | ✅ 可用（4.8/Fable5/Sonnet5） |
| effort=`xhigh` | ✅ 可用 |
| Dynamic Workflows | ⚠️ Claude Code 客户端特性，非 API |
| Fast Mode (`speed:"fast"`) | ❌ 不支持 |
| Lower Prompt Cache Min (1024) | ❌ Opus 4.7/4.8/Sonnet5 仍 4096；仅 Fable 5 / Sonnet 4.6 为 1024 |

### Mid-conversation System Messages — ✅ 实测可用

在 `messages` 数组里插入 `{"role":"system"}` 条目，用于长会话中途追加 system 指令而**不改动顶层 `system` 字段**，从而保留前缀 prompt cache。无需 beta header。

- **可用范围**：**Opus 4.8 / Fable 5 / Sonnet 5** 接受并遵守；Opus 4.7 报 `role 'system' is not supported`；4.6 一代报 `Unexpected role "system"`。
- **官方文档 vs 实测**：Anthropic 文档称 "not available on Amazon Bedrock"，但实测上述三个模型（InvokeModel + mantle）均可用。
- **放置规则**：`role:system` 条目须紧跟 `user` 轮（或以 server tool use 结尾的 `assistant` 轮），且为数组最后一项或紧接一个 `assistant` 轮；不能位于 `tool_use` 与其 `tool_result` 之间。

**实测结论**（见 [test_23](claude/test_23_mid_conversation_system.py)）：

1. 接受且**遵守**中性 system 指令（"每条回复末尾加 `###MANGO###`" → 照做）。
2. **Cache 保留**：已缓存前缀（≥4096 token）后追加 mid-sys 条目，下次请求 `cache_read_input_tokens=9117`，前缀缓存未失效 ✅。
3. **Operator 优先级非绝对**：与用户请求硬冲突时（system "只回一个词" vs 用户 "写三段"），模型指出冲突并倾向用户；中性、不与用户对立的指令才稳定生效。

> ⚠️ 判定该特性是否可用，须用**中性指令**。对抗性措辞（"忽略用户问题"）会触发模型抵抗，造成"不生效"的误判。
>
> Anthropic: [mid-conversation-system-messages](https://docs.anthropic.com/en/build-with-claude/mid-conversation-system-messages)（该页称 Bedrock 不支持，与本仓库实测不符）

### Dynamic Workflows — ⚠️ Claude Code 客户端特性，非 API

Anthropic 宣传 Dynamic Workflows "支持 Anthropic API / Bedrock / Vertex / Foundry"，**易被误解为 Bedrock API 新增能力**。实际上：

> "支持 Bedrock" = **Claude Code 客户端接 Bedrock 后端时能用**，**不是** Bedrock 的 InvokeModel/Messages API 多了 dynamic-workflow 字段。

编排逻辑全在 Claude Code 客户端：Claude 写一段 JS 编排脚本 → 客户端内的 workflow runtime 执行 → 拉起 N 个 subagent，每个 subagent 只是发**普通 InvokeModel 调用**到 Bedrock。Bedrock 对 "Dynamic Workflows" 无感知。

- **如何用**：Claude Code（CLI/Desktop/IDE，≥ v2.1.154），`ultracode` 关键词 / `/effort ultracode` / `/workflows` 触发。
- **程序化**：只能走 Claude Code 的 `claude -p`（headless）或 Agent SDK。
- **Bedrock 限制**：内置 `/deep-research` 依赖 WebSearch（Bedrock 后端不可用），联网类 workflow 跑不全；纯代码类可正常跑。
- 文档: [introducing-dynamic-workflows](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code)

### Fast Mode — ❌ Bedrock 不支持

顶层设 `speed:"fast"`（+ beta header `fast-mode-2026-02-01`），输出速度最高 2.5×，溢价计费（Opus 4.8: $10/$50 per MTok）。

- **Anthropic**：research preview，支持 Opus 4.8/4.7/4.6，需 account manager 申请。
- **Bedrock**：**不支持**。实测传 `speed:"fast"`（带/不带 beta header）均返回 400 `speed: Extra inputs are not permitted`。官方文档亦明确 "not available on... Amazon Bedrock"。
- 文档: [fast-mode](https://platform.claude.com/docs/en/build-with-claude/fast-mode)

### Lower Prompt Cache Min — ❌ Opus 4.7/4.8/Sonnet 5 仍为 4096

Anthropic 宣布 Opus 4.8 将最小可缓存长度从 4,096 降到 1,024。但**该改动在 Bedrock 上未对 Opus 4.7/4.8 生效**。

各模型卡片官方 "Min tokens per cache checkpoint"（权威值）：

| 模型 | 最小可缓存长度 |
|------|:---:|
| Fable 5 | 1,024 |
| Sonnet 4.6 | 1,024 |
| Sonnet 5 | 4,096 |
| Opus 4.6 / 4.7 / 4.8 | 4,096 |
| Haiku 4.5 | 4,096 |

即：**只有 Fable 5 和 Sonnet 4.6 是 1,024，其余均为 4,096**。Opus 4.8 的 InvokeModel 实测边界扫描也印证为 4096（4018 tokens 不缓存 / 4135 tokens 缓存）。设计缓存时按模型区分，低于门槛不会缓存。

> ⚠️ 注意：在 `global.` cross-region 端点上用 `cache_creation_input_tokens` 反推最小长度会出现噪声/非单调结果，不可靠——请以各模型卡片的官方值为准。
