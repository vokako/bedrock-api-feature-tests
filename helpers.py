"""Shared helpers for Bedrock InvokeModel API feature tests."""
import boto3
import json
import time

REGION = "us-east-1"
MODEL_ID = "global.anthropic.claude-sonnet-4-6"
ANTHROPIC_VERSION = "bedrock-2023-05-31"


def get_client():
    return boto3.client("bedrock-runtime", region_name=REGION)


def invoke(body: dict, beta_headers: list[str] | None = None) -> dict:
    client = get_client()
    if "anthropic_version" not in body:
        body["anthropic_version"] = ANTHROPIC_VERSION
    if beta_headers:
        body["anthropic_beta"] = beta_headers
    resp = client.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        body=json.dumps(body),
    )
    return json.loads(resp["body"].read())


def invoke_stream(body: dict, beta_headers: list[str] | None = None):
    client = get_client()
    if "anthropic_version" not in body:
        body["anthropic_version"] = ANTHROPIC_VERSION
    if beta_headers:
        body["anthropic_beta"] = beta_headers
    resp = client.invoke_model_with_response_stream(
        modelId=MODEL_ID,
        contentType="application/json",
        body=json.dumps(body),
    )
    chunks = []
    for event in resp["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        chunks.append(chunk)
    return chunks


def print_pass(name: str):
    print(f"  ✅ PASS: {name}")


def print_fail(name: str, reason: str):
    print(f"  ❌ FAIL: {name} — {reason}")


def print_header(num: str, title: str):
    print(f"\n{'='*60}")
    print(f"  Test {num}: {title}")
    print(f"{'='*60}")
