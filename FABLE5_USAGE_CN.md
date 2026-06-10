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

### 方式 B：仅 project 级开启（影响范围更小，推荐）

如果只想在某个 project 里用 Fable 5，可以只在该 project 开启，不动整个账号：

```bash
curl https://bedrock-mantle.us-east-1.api.aws/v1/organization/projects/proj_abc123 \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "data_retention": { "mode": "provider_data_share" } }'
```

### 怎么改回去

再调一次 API 改成 `inherit` / `default` / `none` 即可。但**已经发送的流量无法撤回**。

## 四、如何调用

### Model ID

| 类型 | ID |
|------|----|
| 基础 ID（不能直接 on-demand 调用） | `anthropic.claude-fable-5` |
| **Global cross-region（推荐）** | `global.anthropic.claude-fable-5` |
| US geo | `us.anthropic.claude-fable-5`（需账号在该 geo 启用） |

### 示例代码（InvokeModel）

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
