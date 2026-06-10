# Fable 5 Project 级隔离开启指南

> Account 零留存（`none`），仅指定 project 的 Fable 5 流量共享给 Anthropic（`provider_data_share`）。
>
> 仅 mantle 端点支持（runtime/InvokeModel 没有 project 概念）。

## 前提：IAM 权限

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DataRetentionControlPlane",
      "Effect": "Allow",
      "Action": [
        "bedrock:GetAccountDataRetention",
        "bedrock:PutAccountDataRetention"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DataRetentionMantle",
      "Effect": "Allow",
      "Action": [
        "bedrock-mantle:GetAccountDataRetention",
        "bedrock-mantle:PutAccountDataRetention",
        "bedrock-mantle:ListProjects",
        "bedrock-mantle:CreateProject",
        "bedrock-mantle:GetProject",
        "bedrock-mantle:UpdateProject",
        "bedrock-mantle:ListModels",
        "bedrock-mantle:GetModel"
      ],
      "Resource": "*"
    }
  ]
}
```

## 第 1 步：设置 account 数据保留为 `none`

```bash
# 查当前
curl -s https://bedrock-mantle.us-east-1.api.aws/v1/data_retention \
  -H "x-api-key: $BEDROCK_API_KEY"
# => {"mode": "inherit", "updated_at": ...}

# 设为 none（零留存基线）
curl -s -X PUT https://bedrock-mantle.us-east-1.api.aws/v1/data_retention \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "mode": "none" }'
# => {"mode": "none", "updated_at": ...}

# 确认
curl -s https://bedrock-mantle.us-east-1.api.aws/v1/data_retention \
  -H "x-api-key: $BEDROCK_API_KEY"
# => {"mode": "none", "updated_at": ...}
```

## 第 2 步：创建 project 并开启 `provider_data_share`

```bash
# 查已有同名 project，有则复用，无则创建
export PROJECT_ID=$(curl -s https://bedrock-mantle.us-east-1.api.aws/v1/organization/projects \
  -H "x-api-key: $BEDROCK_API_KEY" | jq -r '.data[] | select(.name=="fable5-isolated") | .id')

if [ -z "$PROJECT_ID" ]; then
  export PROJECT_ID=$(curl -s -X POST https://bedrock-mantle.us-east-1.api.aws/v1/organization/projects \
    -H "x-api-key: $BEDROCK_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{ "name": "fable5-isolated" }' | jq -r '.id')
  echo "created: $PROJECT_ID"
else
  echo "reusing existing: $PROJECT_ID"
fi

# 设 provider_data_share
curl -s -X POST "https://bedrock-mantle.us-east-1.api.aws/v1/organization/projects/$PROJECT_ID" \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "data_retention": { "mode": "provider_data_share" } }'
# => {"id": "proj_xxx", "data_retention": {"mode": "provider_data_share"}, ...}

# 确认
curl -s "https://bedrock-mantle.us-east-1.api.aws/v1/organization/projects/$PROJECT_ID" \
  -H "x-api-key: $BEDROCK_API_KEY"
# => {"id": "proj_xxx", "data_retention": {"mode": "provider_data_share"}, ...}
```

## 第 3 步：测试 Fable 5

```bash
# 不加 header → account=none → 被拒
curl -s -X POST https://bedrock-mantle.us-east-1.api.aws/anthropic/v1/messages \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"anthropic.claude-fable-5","max_tokens":16,"messages":[{"role":"user","content":"Say hi"}]}'
# => {"error": {"message": "data retention mode 'none' is not available for this model"}}

# 加 header → project=provider_data_share → 成功
curl -s -X POST https://bedrock-mantle.us-east-1.api.aws/anthropic/v1/messages \
  -H "x-api-key: $BEDROCK_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-workspace-id: $PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{"model":"anthropic.claude-fable-5","max_tokens":16,"messages":[{"role":"user","content":"Say hi"}]}'
# => {"content": [{"type": "text", "text": "Hello there, friend!"}], "stop_reason": "end_turn", ...}
```

| 请求 | 结果 |
|------|------|
| 不加 `anthropic-workspace-id` | ❌ 400 |
| 加 `anthropic-workspace-id: $PROJECT_ID` | ✅ 成功 |

## 在 Claude Code 中使用

编辑 `~/.claude/settings.json`，`env` 中加入（将 `<PROJECT_ID>` 替换为上面的实际值）：

```json
{
  "env": {
    "CLAUDE_CODE_USE_MANTLE": "1",
    "AWS_REGION": "us-east-1",
    "ANTHROPIC_MODEL": "anthropic.claude-fable-5",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "anthropic.claude-haiku-4-5",
    "ANTHROPIC_CUSTOM_HEADERS": "anthropic-workspace-id: <PROJECT_ID>"
  }
}
```

重启 Claude Code，`/status` 显示 `Amazon Bedrock (Mantle)` 即生效。
