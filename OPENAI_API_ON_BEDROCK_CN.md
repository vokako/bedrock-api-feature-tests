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
- [五、Web Search —— 可用，但被 IAM 权限门禁](#五web-search--可用但被一个-iam-权限门禁)
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
| **Web Search（托管工具）** | ✅¹ | [`test_08`](gpt/test_08_web_search.py) | ¹需 `bedrock-websearch:*` 权限；缺权限会**静默失败**（见[第五节](#五web-search--可用但被一个-iam-权限门禁)） |
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

## 五、Web Search —— 可用，但被一个 IAM 权限门禁

**结论：GPT-5.6 在 Bedrock 上的 hosted `web_search` 是可用的。它被 `bedrock-websearch:*` 这个 IAM 权限门禁；缺少该权限时工具会*静默失败*，极易误判为"不支持"。**

### 需要的权限

```json
{"Effect": "Allow", "Action": "bedrock-websearch:*", "Resource": "*"}
```

**`AmazonBedrockLimitedAccess`**（控制台生成 API key 时默认挂的策略）和 **`AmazonBedrockFullAccess`** 都**不含**它。`bedrock-websearch` 是一个独立的服务命名空间——不被 `bedrock:*` 或 `bedrock-mantle:*` 覆盖，也不在 botocore 的服务列表里。

Bedrock API key 本质是一个名为 `BedrockAPIKey-<后缀>` 的专用 IAM 用户的长期凭证，所以把权限加到该用户上：

```bash
aws iam put-user-policy \
  --user-name BedrockAPIKey-<后缀> \
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

然后用 [`check_gpt56_web_search.py`](check_gpt56_web_search.py) 或 `gpt/test_08` 验证。权限到位后 OpenAI 整套测试 **9/9** 全通过；缺权限时 `test_08` 是唯一失败项。

2026-07-27 实测（`openai.gpt-5.6-terra` @ `us-east-1`，同一个 API key，只改 IAM 策略）：

| 主体权限 | `web_search_call` 结果 |
|---|---|
| `AmazonBedrockLimitedAccess`（API key 默认） | `failed`，0 引用 ❌ |
| `AmazonBedrockFullAccess` | `failed` ❌ |
| `BedrockAgentCoreFullAccess` / `bedrock-agentcore:*` | `failed` ❌ |
| `bedrock:*` + `bedrock-mantle:*` | `failed` ❌ |
| **+ `bedrock-websearch:*`** | **`completed`，返回真实引用 ✅** |
| `AdministratorAccess`（`Action:"*"`） | `completed` ✅ |

补上权限后模型返回真实数据，例如 *"NVDA is currently $206.84 USD per share"*，引用 `investor.nvidia.com`。

### 静默失败这个坑

缺少 `bedrock-websearch:*` 时，API 返回 **HTTP 200**，模型也会规划真实查询并产出 `web_search_call`（含 `search` 与 `open_page` 两种动作）——但每个 `status` 都是 `"failed"`，没有引用，模型还会说"web search 暂时不可用"。**全程没有 `AccessDenied`**，响应里没有任何迹象指向权限问题。

### 补充说明

- **鉴权机制本身无关**：Bedrock API key（bearer）与 SigV4 行为完全一致，起作用的是背后身份的权限。API key 解码后是一个专用 IAM 用户（`BedrockAPIKey-<后缀>`），默认挂 `AmazonBedrockLimitedAccess`——这就是 bearer 路径看起来"坏掉"的原因。
- OpenAI 的[兼容性指南](https://developers.openai.com/api/docs/guides/amazon-bedrock)把 Bedrock 上的 "Hosted web search" 标为 Not available（截至 2026-07-13 上线）。**该表已过时／未考虑权限因素**——实测可用。
- `bedrock-websearch` 下的确切动作名未公开，实用做法就是 `bedrock-websearch:*`。（`Search`、`InvokeWebSearch`、`WebSearch`、`OpenPage`、`Retrieve`、`Query`、`Fetch`、`GetPage`、`Browse`、`PerformSearch` 均已逐个测试，都不是。）
- 其他托管工具（`file_search`、`image_generation`、`code_interpreter`、`computer_use_preview`、`shell`、`server_url` 形式的远程 MCP）是真的不支持——它们在 schema 校验层就 **400 硬拒**，与权限无关。见[第六节](#六对照-openai-官方表的能力复核)。
- **Claude 在 Bedrock 上完全无法使用 web search**——Anthropic 的 `web_search_20250305` 工具类型在 `bedrock-runtime` 和 `bedrock-mantle` 上都被校验层拒绝，权限给满也一样。见 [Anthropic 指南](ANTHROPIC_API_ON_BEDROCK_CN.md)。

---

## 六、对照 OpenAI 官方表的能力复核

对照 OpenAI [OpenAI models in Amazon Bedrock](https://developers.openai.com/api/docs/guides/amazon-bedrock) 特性表（截至 2026-07-13 上线）里的每一项，直接对 `us-east-1` 的 `openai.gpt-5.6-terra` 实测。除 hosted web search 外所有官方结论均吻合（web search 补上 `bedrock-websearch:*` 后可用，见第五节），汇总在 [`test_09`](gpt/test_09_capability_matrix.py)。

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
| Hosted web search | Not available | 给了 `bedrock-websearch:*` 就**可用**；否则静默 `failed` | ❌ 官方表已过时 |
| Hosted file search | Not available | **400** tool type not supported | ✅ |
| Image generation tool | Not available | **400** tool type not supported | ✅ |
| Code interpreter | Not available | **400** tool type not supported | ✅ |
| Computer use | Not available | **400** tool type not supported | ✅ |
| Shell tool | Not available | **400** tool type not supported | ✅ |
| 远程 MCP 服务器（`server_url`） | Not available | **400** "use a connector ARN instead" | ✅ |

### 表格没写出的两个细节

1. **web search 在 OpenAI 表里被标错了，而且失败方式是个陷阱。** `web_search` / `web_search_preview` 在校验层被接受，并且**确实能用**——前提是调用方持有 `bedrock-websearch:*`。缺该权限时它们在执行阶段失败（`status="failed"`）且**不报 AccessDenied**，看起来与"不支持"一模一样。其余托管工具（`file_search`、`image_generation`、`code_interpreter`、`computer_use_preview`、`shell`）是推理前就 **400 硬拒**——那些才是真不支持，且与权限无关。

2. **API 会自己报出支持的工具类型白名单。** 400 报错原文：*"Supported tool types are: `function`, `mcp`, `custom`, `namespace`, `tool_search`."* 注意 `web_search` **不在**这个列表里（与"不可用"一致），却被接受而非拒绝，前后不一致。`namespace` 则是 OpenAI 表里压根没提的一个受支持类型。

### 端点 / API / 区域事实

| 项目 | 状态 | 说明 |
|------|:---:|------|
| `bedrock-runtime` 端点 | ❌ | GPT-5.6 仅 `bedrock-mantle` |
| `Invoke` / `Converse` / `Chat Completions` API | ❌ | 仅 `Responses` |
| Geo / Global 跨区推理 | ❌ | 仅 in-region |
| 音频/语音/视频输入，Embedding/图片/语音/视频输出 | ❌ | 仅文本+图片输入、文本输出 |
| `openai.gpt-5.6-sol` 在 `us-west-2` | ❌（实测） | 2026-07-23 返回 404，与模型卡片不符 |
