# Claude Fable 5 在 Amazon Bedrock 上的使用说明

> 面向第一次接触 Fable 5 的人。读完即可调用。最后更新：2026-06-10

## 一、Fable 5 是什么

Anthropic 于 2026-06-09 在 Bedrock 上线的前沿模型，是**第一个公开可用的 Mythos 级模型**。擅长长时间自主运行的知识工作和编程任务，能跨阶段规划、委派子任务、自我验证。

- **上下文窗口**：1M tokens
- **最大输出**：128K tokens
- **思考**：adaptive thinking 强制常开，不能关闭，只能调 effort 等级
- **知识截止**：2026 年 1 月

## 二、最重要的前提：必须开启 data sharing

Fable 5 是 **"covered model"**，AWS 强制要求：使用前必须把账号（或 project）的**数据保留模式**设为 `provider_data_share`，否则调用会被直接拒绝。

### 这意味着什么

- 你发给 Fable 5 的 **prompt 和模型的输出，会被分享给 Anthropic 并保留最多 30 天**，用于滥用检测和可能的人工审查。
- 这是 Fable 5 / Mythos 5 这类模型的**硬性安全要求**，无法绕过。
- 如果开了 cross-region inference，保留的数据会存在目标 region。

### 不用担心的地方（容易误解的点）

把账号设成 `provider_data_share` **不代表你所有模型的数据都开始共享**。账号设置只是定义你"允许"的上限，每个模型有自己的 `allowed_modes`：

| 模型 | 行为 |
|------|------|
| **Fable 5 / Mythos 5** | 真正共享数据给 Anthropic，保留 30 天 |
| **其他模型**（Sonnet 4.6、Opus 4.7 等） | 不受影响，仍按各自默认模式，**不会**开始共享 |

### 数据保留模式一览

| 模式 | 含义 |
|------|------|
| `inherit` | 不表态，向上一级（account → 模型默认）继承。新账号默认值 |
| `default` | AWS 可为安全目的保留，但**不**给模型提供商 |
| `provider_data_share` | 允许保留并**共享给模型提供商**。Fable 5 需要它 |
| `none` | 零数据保留（ZDR）。需向 AWS account team 单独申请 |

## 三、如何开启（一次性操作）

### 前提：IAM 权限

执行账号的 IAM 身份需要 `bedrock:PutAccountDataRetention` 权限：

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:GetAccountDataRetention",
    "bedrock:PutAccountDataRetention"
  ],
  "Resource": "*"
}
```

> 如果走 Messages API（`bedrock-mantle` endpoint），对应 action 是 `bedrock-mantle:PutAccountDataRetention`，建议两个都加。

> ⚠️ 注意：如果环境里设了 `AWS_BEARER_TOKEN_BEDROCK`，boto3 会用那个 API key 而不是 IAM 凭证。要走 IAM，先 unset 这个环境变量，或确保该 API key 用户也有上述权限。

### 方式 A：账号级开启（整个账号可用 Fable 5）

```python
import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")

# 开启
bedrock.put_account_data_retention(mode="provider_data_share")

# 确认
print(bedrock.get_account_data_retention())   # {'mode': 'provider_data_share', ...}
```

需要 boto3 / botocore 较新版本（botocore ≥ 1.43，含 `PutAccountDataRetention` 操作）。

### 方式 B：project 级开启（影响范围最小，推荐隔离场景）

只想让某个 project 里的 Fable 5 流量被共享、其他流量（含 Opus 4.7/4.8）保持**零留存**时，用 project 级隔离。**仅 mantle 端点支持**（runtime/InvokeModel 没有 project 概念）。

> 原理：account 与 project 是两套**独立**配置（且各自又分 control-plane / mantle 两份）。effective mode 解析顺序为 `project → account → model default`（取第一个非 `inherit` 的值）。把 account 设成 `none`、只在某个 project 设 `provider_data_share`，就能做到"默认零留存，仅该 project 共享"。

下面是完整三步（命令用 `x-api-key` 或 SigV4 均可），每步附 2026-06-10 实测输出。

**第 1 步：确认 / 设置 account（mantle）数据保留为 `none`**

`none` = 默认任何模型都零留存，作为隔离的安全基线。

```bash
# 查当前 account 保留模式
curl https://bedrock-mantle.us-east-1.api.aws/v1/data_retention \
  -H "x-api-key: $BEDROCK_API_KEY"
# => {"mode": "inherit", "updated_at": ...}

# 设为 none（零留存基线）
curl -X PUT https://bedrock-mantle.us-east-1.api.aws/v1/data_retention \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "mode": "none" }'
# => {"mode": "none", "updated_at": ...}

# 再次确认
curl https://bedrock-mantle.us-east-1.api.aws/v1/data_retention \
  -H "x-api-key: $BEDROCK_API_KEY"
# => {"mode": "none", "updated_at": ...}
```

**第 2 步：创建 project 并开启 project 级 `provider_data_share`**

```bash
# 列出现有 project（账号自带一个 default，不可修改）
curl -s https://bedrock-mantle.us-east-1.api.aws/v1/organization/projects \
  -H "x-api-key: $BEDROCK_API_KEY"
# => {"data": [{"id": "default", "name": "default", "data_retention": {"mode": "inherit"}, ...}]}

# 创建新 project，自动提取返回的 project id
export PROJECT_ID=$(curl -s -X POST https://bedrock-mantle.us-east-1.api.aws/v1/organization/projects \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "name": "fable5-isolated" }' | jq -r '.id')
echo "created: $PROJECT_ID"
# => created: proj_xxxxxxxxxxxx

# 给该 project 设 provider_data_share
curl -s -X POST "https://bedrock-mantle.us-east-1.api.aws/v1/organization/projects/$PROJECT_ID" \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "data_retention": { "mode": "provider_data_share" } }'
# => {"id": "proj_xxx", "data_retention": {"mode": "provider_data_share"}, ...}

# 确认 project 配置
curl -s "https://bedrock-mantle.us-east-1.api.aws/v1/organization/projects/$PROJECT_ID" \
  -H "x-api-key: $BEDROCK_API_KEY"
# => {"id": "proj_xxx", "data_retention": {"mode": "provider_data_share"}, ...}

# （可选）查 Fable 5 在该 project 下的生效 retention
curl -s https://bedrock-mantle.us-east-1.api.aws/v1/models/anthropic.claude-fable-5 \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "openai-project: $PROJECT_ID"
# => {"status": "available", "data_retention": {"mode": "provider_data_share", "source": "project", ...}}
```

**第 3 步：测试 Fable 5 —— 加 header vs 不加 header**

请求绑定 project 用 `anthropic-workspace-id` header（Messages API 格式）。

```bash
# 不加 header：落到 account=none，Fable 5 被拒
curl -s -X POST https://bedrock-mantle.us-east-1.api.aws/anthropic/v1/messages \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"anthropic.claude-fable-5","max_tokens":16,"messages":[{"role":"user","content":"Say hi"}]}'
# => {"error": {"message": "data retention mode 'none' is not available for this model"}}

# 加 header：落到 project=provider_data_share，Fable 5 可用
curl -s -X POST https://bedrock-mantle.us-east-1.api.aws/anthropic/v1/messages \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-workspace-id: $PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{"model":"anthropic.claude-fable-5","max_tokens":16,"messages":[{"role":"user","content":"Say hi"}]}'
# => {"content": [{"type": "text", "text": "Hello there, friend!"}], "stop_reason": "end_turn", ...}
```

实测结果：

| 请求 | 生效 scope | 结果 |
|------|-----------|------|
| **不加** `anthropic-workspace-id` | account = `none` | ❌ 400 `data retention mode 'none' is not available for this model` |
| **加** `anthropic-workspace-id=$PROJECT_ID` | project = `provider_data_share` | ✅ `Hello there, friend!` |

这就证明了隔离生效：**account 零留存，只有显式绑定到该 project 的请求才会被记录共享**。其他模型（Opus 4.7/4.8 等）在不带 header 时走 account=`none`，不被留存。

**在 Claude Code 中使用该 project**

编辑 `~/.claude/settings.json`，在 `env` 中加入以下配置（Claude Code ≥ v2.1.94），将 `$PROJECT_ID` 替换为上面创建的实际值：

```json
{
  "env": {
    "CLAUDE_CODE_USE_MANTLE": "1",
    "AWS_REGION": "us-east-1",
    "ANTHROPIC_MODEL": "anthropic.claude-fable-5",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "anthropic.claude-haiku-4-5",
    "ANTHROPIC_CUSTOM_HEADERS": "anthropic-workspace-id: <上面 $PROJECT_ID 的值>"
  }
}
```

或者一行命令自动写入（基于上面已 export 的 `$PROJECT_ID`）：

```bash
# 用 jq 自动把 project id 写进 settings.json
SETTINGS=~/.claude/settings.json
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
jq --arg pid "$PROJECT_ID" '.env += {
  "CLAUDE_CODE_USE_MANTLE": "1",
  "AWS_REGION": "us-east-1",
  "ANTHROPIC_MODEL": "anthropic.claude-fable-5",
  "ANTHROPIC_DEFAULT_HAIKU_MODEL": "anthropic.claude-haiku-4-5",
  "ANTHROPIC_CUSTOM_HEADERS": ("anthropic-workspace-id: " + $pid)
}' "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
echo "wrote $SETTINGS with project=$PROJECT_ID"
```

重启 Claude Code 后 `/status` 显示 `Amazon Bedrock (Mantle)` 即生效。所有请求自动带上该 project 的 workspace header，走 `provider_data_share`。

> project header 因 API 格式而异：Messages 格式（`/anthropic/v1/messages`）用 `anthropic-workspace-id`；OpenAI 兼容格式（`/v1/...`，如 `/v1/models`）用 `openai-project`。

### 怎么改回去

把对应 scope（account 或 project）再设成 `inherit` / `default` / `none` 即可。但**已经发送的流量无法撤回**。

## 四、如何调用


Fable 5 有两条调用路径，**数据保留的配置 scope 不同**：

| 路径 | 端点 | 数据保留 scope | project 隔离 |
|------|------|---------------|:---:|
| 方式一：InvokeModel | `bedrock-runtime` | 仅 account 级 | ❌ |
| 方式二：Messages API | `bedrock-mantle` | account + **project** | ✅ |

### Model ID

| 类型 | ID |
|------|----|
| 基础 ID（不能直接 on-demand 调用） | `anthropic.claude-fable-5` |
| **Global cross-region（推荐）** | `global.anthropic.claude-fable-5` |
| US geo | `us.anthropic.claude-fable-5`（需账号在该 geo 启用） |

### 方式一：InvokeModel（account 级 data share）

```python
import json, boto3

runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

resp = runtime.invoke_model(
    modelId="global.anthropic.claude-fable-5",
    contentType="application/json",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "What is 17 + 25?"}],
    }),
)
data = json.loads(resp["body"].read())

# 正确解析：遍历所有 content block，不要只取 content[0]
for block in data["content"]:
    if block["type"] == "text":
        print(block["text"])
    elif block["type"] == "thinking":
        print("[thinking]", block.get("thinking", ""))

print("stop_reason:", data["stop_reason"])
```

> 走 runtime 时，account（control-plane）的数据保留必须是 `provider_data_share`（方式 A）。runtime 没有 project，无法只隔离 Fable 5。

### 方式二：Messages API + project（可隔离 data share，推荐）

用官方 `AnthropicBedrockMantle` SDK（`pip install -U "anthropic[bedrock]"`），通过 `anthropic-workspace-id` header 把请求绑定到开了 `provider_data_share` 的 project：

```python
import os
# 若环境里有 AWS_BEARER_TOKEN_BEDROCK 且其 API key 未绑定该 project，
# pop 掉走 IAM 凭证；或确保该 API key 属于目标 project
os.environ.pop("AWS_BEARER_TOKEN_BEDROCK", None)

from anthropic import AnthropicBedrockMantle

client = AnthropicBedrockMantle(aws_region="us-east-1")

msg = client.messages.create(
    model="anthropic.claude-fable-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What is 17 + 25?"}],
    # 关键：绑定到开了 provider_data_share 的 project
    extra_headers={"anthropic-workspace-id": "proj_xxxxxxxxxxxx"},
)

for block in msg.content:
    if block.type == "text":
        print(block.text)
    elif block.type == "thinking":
        print("[thinking]", block.thinking)
print("stop_reason:", msg.stop_reason)
```

> **project header 因 API 格式而异**：Anthropic Messages 格式（`/anthropic/v1/messages`）用 `anthropic-workspace-id`；OpenAI 兼容格式（`/v1/...`，如 `/v1/models`）用 `openai-project`。用错会报 `The openai-project header is not supported for this API format. Use anthropic-workspace-id instead.`
>
> 不带 project header 的请求会落到 default project（`inherit`→`default`），Fable 5 会返回 `data retention mode 'default' is not available for this model`。

## 五、特性兼容性（2026-06-10 实测）

实测于 `global.anthropic.claude-fable-5`，对应自动化脚本 `test_22_fable5.py`：

| 特性 | 支持 | 备注 |
|------|:---:|------|
| Basic Messages | ✅ | |
| Streaming (SSE) | ✅ | |
| Tool Use | ✅ | `stop_reason=tool_use` |
| Adaptive Thinking | ✅ | 强制常开 |
| effort=xhigh | ✅ | |
| Prompt Caching | ✅ | cache 指标真实命中（非 0） |
| Vision（图片输入） | ✅ | 最高 2576px / 3.75MP |
| Citations | ✅ | |
| **Structured Outputs (`output_config.format`)** | ❌ | 报 400，改用 forced tool use |
| 采样参数限制 | ✅ | `temperature`/`top_p`/`top_k` 受限 |
| Refusal 机制 | ✅ | `stop_reason=refusal` + `stop_details` |

## 六、踩坑提醒

### 1. 一定要处理 `stop_reason: "refusal"`

Fable 5 内置 cybersecurity / biology 等领域的拦截分类器，**拒答率明显高于以往模型**。被拦时返回的是 **HTTP 200**（不是报错），但：

- `stop_reason` 为 `"refusal"`
- 带一个 `stop_details` 对象说明拦截类别

生产代码要把 refusal 当作**主要响应路径**处理，而不是异常。

- Prompt 阶段就被拦（推理还没开始）→ **不计费**
- 推理中途被拦 → 已生成的 token **计费**

### 2. text 可能为空

adaptive thinking 常开，响应里可能出现 thinking block 而可见 text 为空。**务必遍历所有 content block**，并处理 text 为空的情况，别假设 `content[0]` 就是答案。

### 3. 采样参数受限

- `temperature`：必须为 `1.0` 或不设
- `top_p`：必须 `≥ 0.99` 且 `< 1.0`，或不设
- `top_k`：不支持

设了不符合的值会报 400。

### 4. Structured Outputs 不支持 `output_config.format`

和 Opus 4.7 一样，Fable 5 **不支持** `output_config.format`（json_schema），传了会报 400 `output_config.format: Extra inputs are not permitted`。

要做结构化 JSON 输出，请改用 **forced tool use**（`tool_choice` 指定一个工具 + `input_schema` 定义结构），模型会把结构化结果放在 `tool_use` block 的 `input` 里。

### 5. Region 可用性

`us-east-1` 支持 In-Region / Geo / Global 三种；多数其他 region 只支持 Global。用 `global.` 前缀最省事。

## 七、相关文档

- [模型卡片](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-fable-5.html)
- [数据保留](https://docs.aws.amazon.com/bedrock/latest/userguide/data-retention.html)
- [滥用检测](https://docs.aws.amazon.com/bedrock/latest/userguide/abuse-detection.html)
