<div align="center">

# OpenAI API on Amazon Bedrock

**OpenAI GPT-5.6 各特性在 Amazon Bedrock 上的支持情况**

[English Version](OPENAI_API_ON_BEDROCK_EN.md)

</div>

---

本文档逐一梳理 OpenAI Responses API 的各特性在 Amazon Bedrock 上 GPT-5.6 三档模型（Terra / Sol / Luna）的支持状态，并说明访问方式与行为要点。它是 [ANTHROPIC_API_ON_BEDROCK_CN.md](ANTHROPIC_API_ON_BEDROCK_CN.md) 的 OpenAI 对应版本。

> 📌 **验证方式**：基于 Bedrock 的 `bedrock-mantle` 端点（OpenAI Responses API），用 `openai` Python SDK 实测。所有标注 ✅ 的特性均有对应测试脚本（`gpt/test_01`–`gpt/test_08`）。
> 📅 **验证时间**：2026-07-23，模型 `openai.gpt-5.6-terra`，区域 `us-east-1`（web search 另在 Sol / `us-east-1` / `us-east-2` 交叉验证）。

## 目录

- [一、模型现状与三档模型](#一模型现状与三档模型)
- [二、访问方式与鉴权](#二访问方式与鉴权)
- [三、特性总览表](#三特性总览表)
- [四、已支持特性（详解）](#四已支持特性详解)
- [五、Web Search —— 不可用](#五web-search--不可用)
- [六、对照 OpenAI 官方表的能力复核](#六对照-openai-官方表的能力复核)

---

## 一、模型现状与三档模型

GPT-5.6 于 **2026-07-13** 上线 Bedrock，分三档。三档共享 **272K token 上下文窗口**，输入支持 **文本 + 图片**，输出为 **文本**，访问方式完全一致（只有 model ID 不同）。

| 档位 | Model ID | 定位（模型卡片） |
|------|----------|------------------|
| **Sol** | `openai.gpt-5.6-sol` | 最强 —— 前沿推理、SOTA agentic（编码、网络安全、科研） |
| **Terra** | `openai.gpt-5.6-terra` | 均衡型，日常生产；性能优于 GPT-5.5 且成本更低（本项目默认） |
| **Luna** | `openai.gpt-5.6-luna` | 快速廉价 —— 分类、摘要、路由、实时场景 |

**模型卡片列出的特性支持**（三档相同）：Server-side tool calling ✅ · Projects ✅ · Prompt caching ✅。

**区域可用性**（模型卡片列出 `us-east-1`、`us-east-2`、`us-west-2`，仅 in-region，无 Geo/Global 跨区推理）。
> ⚠️ **实测偏差（2026-07-23）**：`openai.gpt-5.6-sol` 在 `us-west-2` 返回 `404 model does not exist`，而在 `us-east-1` / `us-east-2` 正常。us-west-2 的上线似乎滞后于模型卡片描述。Terra 在 `us-east-1` 验证通过。

服务档位：仅 **Standard**（不提供 Priority / Flex / Reserved）。

---

## 二、访问方式与鉴权

与 Anthropic 模型（走 `bedrock-runtime` 的 InvokeModel / Messages）不同，GPT-5.6 **只能通过 `bedrock-mantle` 端点、用 OpenAI Responses API 访问**。

- **Base URL**：`https://bedrock-mantle.<region>.api.aws/openai/v1`
  > ⚠️ GPT-5.6 用的是 **`openai/v1`** 路径，和同一端点上其他模型（如 `gpt-oss-120b`）用的 **`v1`** 路径不同。对 GPT-5.6 用 `/v1` 会 404。
- **鉴权**：用 **Bedrock API key**（bearer token）作为 `OPENAI_API_KEY`。文档也支持用 AWS SigV4 凭证发原始 HTTP 请求，但 OpenAI SDK 这条路必须用 API key。本项目从环境变量 `AWS_BEARER_TOKEN_BEDROCK` 读取该 key。
- **API**：仅 `Responses`。`Chat Completions`、`Invoke`、`Converse` **均不支持**。

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

测试用的共享客户端见 [`gpt/helpers.py`](gpt/helpers.py)。

---

## 三、特性总览表

| 特性 | 状态 | 测试 | 说明 |
|------|:---:|------|------|
| 基础调用（非流式） | ✅ | [`test_01`](gpt/test_01_basic.py) | `responses.create`，`status="completed"` |
| 流式（SSE） | ✅ | [`test_02`](gpt/test_02_streaming.py) | `response.output_text.delta` 事件 |
| 客户端工具调用（function calling） | ✅ | [`test_03`](gpt/test_03_tool_use.py) | `type:"function"`，返回 `function_call` |
| 推理（effort 控制） | ✅ | [`test_04`](gpt/test_04_reasoning.py) | `reasoning={"effort": ...}`，产出 `reasoning` 项 |
| 结构化输出（JSON schema） | ✅ | [`test_05`](gpt/test_05_structured_outputs.py) | `text.format.type="json_schema"`，`strict=True` |
| 视觉（图片输入） | ✅ | [`test_06`](gpt/test_06_vision.py) | `input_image` data URL |
| Prompt Caching | ✅ | [`test_07`](gpt/test_07_prompt_caching.py) | `prompt_cache_key`，重复调用命中缓存 |
| 文件输入（PDF） | ✅ | [`test_09`](gpt/test_09_capability_matrix.py) | `input_file` data URL，正确提取文字 |
| 会话状态 | ✅ | [`test_09`](gpt/test_09_capability_matrix.py) | `previous_response_id` 能回忆上一轮 |
| 推理 effort `max` | ✅ | [`test_09`](gpt/test_09_capability_matrix.py) | `reasoning={"effort":"max"}` 被接受 |
| 客户端 `tool_search` | ✅ | [`test_09`](gpt/test_09_capability_matrix.py) | 工具类型被接受 |
| **Web Search（托管工具）** | ❌ | [`test_08`](gpt/test_08_web_search.py) | 被接受，但每次 `web_search_call` 都 `status="failed"` |
| 其他托管工具（file_search / image_generation / code_interpreter / computer_use / shell） | ❌ | [`test_09`](gpt/test_09_capability_matrix.py) | 直接 **400** "tool type not supported" |
| 远程 MCP（`server_url`）/ 非 Standard 服务档位 | ❌ | [`test_09`](gpt/test_09_capability_matrix.py) | **400**；须用 connector ARN / 仅 on-demand |
| 服务端自定义工具 —— Lambda / AgentCore Gateway（`mcp` + connector ARN） | ➖ | — | 文档称支持；此处未测（需部署 Lambda/Gateway） |

图例：✅ 可用 · ❌ 不可用 · ➖ 此处未测。完整的对照 OpenAI 官方表的复核见[第六节](#六对照-openai-官方表的能力复核)。

---

## 四、已支持特性（详解）

### 基础调用
`client.responses.create(model=..., input=...)` 返回 `status="completed"` 与 `output_text`。用量在 `usage.input_tokens` / `output_tokens`，并带 `input_tokens_details.{cache_write_tokens,cached_tokens}` 和 `output_tokens_details.reasoning_tokens`。

### 流式
传 `stream=True` 得到 OpenAI Responses 的 SSE 事件。实测顺序包含 `response.created` → `response.in_progress` → `response.output_item.added` → `response.content_part.added` → `response.output_text.delta`（多次）→ `response.output_text.done` → `response.content_part.done` → `response.output_item.done` → `response.completed`。拼接 `response.output_text.delta` 的 `.delta` 字段即得全文。

### 客户端工具调用（function calling）
工具用 Responses 的结构 `{"type":"function","name":...,"description":...,"parameters":{...}}`（注意 `name`/`parameters` 是顶层字段，不嵌套在 `function` 键下）。模型决定调用时，输出里出现 `function_call` 项，带 `.name` 和 JSON 字符串 `.arguments`。

### 推理
`reasoning={"effort": "low"|"medium"|"high"}` 控制思考预算。输出里先有 `reasoning` 项再有 `message`，`usage.output_tokens_details.reasoning_tokens` 被填充。（17 × 23 → "391" 已验证。）

### 结构化输出
传 `text={"format": {"type":"json_schema","name":...,"strict":True,"schema":{...}}}`。`output_text` 是符合 schema 的 JSON 字符串。已用 `{name, age}` schema 验证，返回可解析的合法 JSON。

### 视觉（图片输入）
在多模态内容里传 `{"type":"input_image","image_url":"data:image/png;base64,..."}` 配合 `input_text`。用本地生成的纯红 PNG，模型正确识别为 "Red"。（仅支持图片输入；不支持图片*输出*。）

### Prompt Caching
用 `instructions` 发一段较大的共享前缀两次，带同一个 `prompt_cache_key`。实测：第一次 `cache_write_tokens=5524, cached_tokens=0`；第二、三次 `cache_write_tokens=0, cached_tokens=5524` —— 可复现的缓存命中。缓存以公共前缀为键；带上 `prompt_cache_key` 能让命中更稳定。

---

## 五、Web Search —— 不可用

**结论：OpenAI 内置的 `web_search` 托管工具会被 API 接受，模型也会主动尝试调用，但搜索从不真正执行 —— 每次 `web_search_call` 都返回 `status="failed"`。**

实测情况（Terra @ us-east-1；另测 Sol @ us-east-1 和 us-east-2）：

- 带 `tools=[{"type":"web_search"}]`（以及 `web_search_preview`）的请求被接受 —— **不报校验错误**。
- 模型会规划真实查询词并在输出里产出 `web_search_call` 项（例如 `NVDA stock price NVIDIA current quote Nasdaq`）。
- 每个 `web_search_call` 的 `status` 都是 `"failed"`。随后模型拒绝回答时效性问题，称 "web search is temporarily unavailable"，通常只给一个手动链接。
- 换两种工具名、换两档模型、换两个区域，结果一致 —— 不是偶发抖动。

**这一点由 OpenAI 官方文档坐实 —— 是设计上"不可用"，不是 bug、也不是请求写法问题。** OpenAI 的 [OpenAI models in Amazon Bedrock](https://developers.openai.com/api/docs/guides/amazon-bedrock) 指南（功能可用性截至 **2026-07-13**，即上线当天）列明 **Hosted web search → Not available**（在 Amazon Bedrock 上不可用），同列的还有 hosted file search、computer use、shell、image-generation tool、remote MCP servers。文档原文：

> *"Hosted tools run through OpenAI-operated service infrastructure and are unavailable on Amazon Bedrock."*

也就是说：工具类型能通过 API 校验（OpenAI 兼容层），模型也会规划搜索，但回到 OpenAI 搜索基础设施的执行链路在 Bedrock 上根本不存在 —— 所以恒为 `failed`。

**为什么模型卡片仍写 "Server-side tool calling ✅"：** 那指的是 Bedrock 自家的服务端工具编排（通过 `mcp` 工具类型注册的自定义 **Lambda** / **AgentCore Gateway** 工具，以及 gpt-oss 模型上内置的 `notes`/`tasks` 工具），**并不等于** OpenAI 的托管 `web_search` 工具在 `bedrock-mantle` 上接通了。AWS 的服务端工具文档从未列出 `web_search`。

**在 Bedrock 上同样标记为 "Not available" 的其他托管工具**（据 OpenAI 指南）：hosted file search、computer use、shell、image-generation tool、remote MCP servers、programmatic tool calling、multi-agent、pro mode。**可用的**：function calling、客户端 `tool_search`、自定义（Lambda/Gateway）工具、结构化输出、图片输入、流式、prompt caching、reasoning effort。

**一句话：** 目前 GPT-5.6 在 Bedrock 上没有可用的 web search。若需联网结果，请自行做检索再作为上下文喂入，或通过 Lambda/AgentCore Gateway 注册自定义搜索工具。`test_08` 每次运行都会重新检查，一旦 AWS 接通后端就会自动变 ✅。

---

## 六、对照 OpenAI 官方表的能力复核

对照 OpenAI [OpenAI models in Amazon Bedrock](https://developers.openai.com/api/docs/guides/amazon-bedrock) 特性表（截至 2026-07-13 上线）里的每一项，直接对 `us-east-1` 的 `openai.gpt-5.6-terra` 实测。所有官方结论均吻合，汇总在 [`test_09`](gpt/test_09_capability_matrix.py)。

| OpenAI 文档能力 | 文档 → Bedrock | 实测行为 | 吻合 |
|-----------------|:---:|---------|:---:|
| 文本生成 | Available | 正常 | ✅ |
| 图片输入 | Available | 正确识别红色 PNG | ✅ |
| 文件输入 | Available（支持的类型） | 从 PDF 提取出数字 | ✅ |
| 结构化输出 | Available | 合法 JSON | ✅ |
| Function calling | Available | 返回 `function_call` | ✅ |
| 流式 | Available | `output_text.delta` 事件 | ✅ |
| 推理 effort（含 `max`） | Available | `effort="max"` → 答案正确 | ✅ |
| 会话状态 / 持久化推理 | Available | `previous_response_id` 回忆上一轮 | ✅ |
| Prompt caching | Implicit + explicit | 命中缓存已复现 | ✅ |
| 客户端 `tool_search` | Available | 工具类型被接受 | ✅ |
| 自定义工具（Lambda / AgentCore connector） | Available | `mcp`+connector ARN 是唯一被接受的 MCP 形式 | ✅（未完整跑通） |
| 音频输入 / WebSocket / Pro mode / Multi-agent / Programmatic tool calling | Not available | 未测（无干净探针） | ➖ |
| 服务档位 | 仅 on-demand | `service_tier="flex"` → **400** | ✅ |
| Hosted web search | Not available | 被接受，`web_search_call` → **failed** | ✅ |
| Hosted file search | Not available | **400** tool type not supported | ✅ |
| Image generation tool | Not available | **400** tool type not supported | ✅ |
| Code interpreter | Not available | **400** tool type not supported | ✅ |
| Computer use | Not available | **400** tool type not supported | ✅ |
| Shell tool | Not available | **400** tool type not supported | ✅ |
| 远程 MCP 服务器（`server_url`） | Not available | **400** "use a connector ARN instead" | ✅ |

### 表格没写出的两个细节

1. **"不可用"分两种。** `web_search` / `web_search_preview` 是*校验层接受*、模型也主动调用，只在*执行时*失败（`status="failed"`）。其余所有托管工具（`file_search`、`image_generation`、`code_interpreter`、`computer_use_preview`、`shell`）是*推理前就 400 硬拒*。web search 是唯一的"半接通"特例。

2. **API 会自己报出支持的工具类型白名单。** 400 报错原文：*"Supported tool types are: `function`, `mcp`, `custom`, `namespace`, `tool_search`."* 注意 `web_search` **不在**这个列表里（与"不可用"一致），却被接受而非拒绝，前后不一致。`namespace` 则是 OpenAI 表里压根没提的一个受支持类型。

### 端点 / API / 区域事实

| 项目 | 状态 | 说明 |
|------|:---:|------|
| `bedrock-runtime` 端点 | ❌ | GPT-5.6 仅 `bedrock-mantle` |
| `Invoke` / `Converse` / `Chat Completions` API | ❌ | 仅 `Responses` |
| Geo / Global 跨区推理 | ❌ | 仅 in-region |
| 音频/语音/视频输入，Embedding/图片/语音/视频输出 | ❌ | 仅文本+图片输入、文本输出 |
| `openai.gpt-5.6-sol` 在 `us-west-2` | ❌（实测） | 2026-07-23 返回 404，与模型卡片不符 |
