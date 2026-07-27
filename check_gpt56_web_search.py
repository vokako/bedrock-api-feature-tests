#!/usr/bin/env python3
"""GPT-5.6 hosted web_search on Amazon Bedrock — minimal repro, OpenAI SDK.

    pip install openai
    export AWS_BEARER_TOKEN_BEDROCK="<Bedrock API key>"
    python3 check_gpt56_web_search.py

It WORKS, but requires the IAM permission `bedrock-websearch:*` on the calling
identity. Without it you get HTTP 200, `web_search_call.status == "failed"` and
no citations — there is NO AccessDenied error, so it just looks unsupported.
Note that a Bedrock API key is a dedicated IAM user carrying
AmazonBedrockLimitedAccess, which does NOT include that permission (neither does
AmazonBedrockFullAccess). Grant:

    {"Effect": "Allow", "Action": "bedrock-websearch:*", "Resource": "*"}
"""
import os
from openai import OpenAI

REGION = "us-east-1"
MODEL = "openai.gpt-5.6-terra"          # or openai.gpt-5.6-sol / -luna

# NOTE: GPT-5.6 is on the `openai/v1` path, not the plain `v1` path
# that other models (e.g. gpt-oss) use on the same endpoint.
client = OpenAI(
    base_url=f"https://bedrock-mantle.{REGION}.api.aws/openai/v1",
    api_key=os.environ["AWS_BEARER_TOKEN_BEDROCK"],
)

resp = client.responses.create(
    model=MODEL,
    tools=[{"type": "web_search"}],
    tool_choice="required",
    input="What is the current stock price of NVDA? Use web search and cite the source URL.",
)

print(f"{MODEL} @ {REGION}\n")
worked = False
for item in resp.output:
    if item.type == "web_search_call":
        action = item.action
        query = getattr(action, "query", None) or getattr(action, "url", None)
        print(f"web_search_call: status={item.status}  {action.type}={query!r}")
        worked |= item.status == "completed"
    elif item.type == "message":
        for part in item.content:
            print(f"\nannotations (citations): {part.annotations}")
            print(f"text: {part.text.strip()}")

if not worked:
    print("\n>>> Every web_search_call failed and no citations came back.")
    print(">>> Most likely cause: the caller lacks `bedrock-websearch:*` (see docstring).")
