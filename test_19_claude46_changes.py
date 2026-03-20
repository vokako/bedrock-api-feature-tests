"""Test 19: Claude 4.6 Changes — verify new deprecations and breaking changes."""
import json
import boto3

from helpers import (
    REGION, ANTHROPIC_VERSION,
    get_client, invoke, print_header, print_pass, print_fail,
)

MODEL_SONNET_46 = "global.anthropic.claude-sonnet-4-6"
MODEL_OPUS_46 = "global.anthropic.claude-opus-4-6-v1"


def invoke_model(model_id, body, beta_headers=None):
    client = get_client()
    if "anthropic_version" not in body:
        body["anthropic_version"] = ANTHROPIC_VERSION
    if beta_headers:
        body["anthropic_beta"] = beta_headers
    resp = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        body=json.dumps(body),
    )
    return json.loads(resp["body"].read())


print_header("19", "Claude 4.6 Changes Verification")

# ── Test 1: Opus 4.6 Prefill → should return error ──
print("\n--- Test 1: Opus 4.6 Prefill (expect 400 error) ---")
try:
    resp = invoke_model(MODEL_OPUS_46, {
        "max_tokens": 64,
        "messages": [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "The answer is"},
        ],
    })
    # If we get here, prefill still works
    text = resp["content"][0].get("text", "")
    print(f"  Response: \"{text[:100]}\"")
    print_fail("Opus 4.6 Prefill", "Expected 400 error but got success — prefill still works on Bedrock")
except boto3.client("bedrock-runtime").exceptions.ValidationException as e:
    print(f"  Error: {e}")
    print_pass("Opus 4.6 Prefill rejected (400 error as expected)")
except Exception as e:
    err = str(e)
    if "400" in err or "validation" in err.lower() or "prefill" in err.lower():
        print(f"  Error: {err[:200]}")
        print_pass("Opus 4.6 Prefill rejected")
    else:
        print(f"  Error: {err[:200]}")
        print_fail("Opus 4.6 Prefill", f"Unexpected error: {err[:200]}")

# ── Test 2: Sonnet 4.6 Prefill → should still work ──
print("\n--- Test 2: Sonnet 4.6 Prefill (expect success) ---")
try:
    resp = invoke_model(MODEL_SONNET_46, {
        "max_tokens": 64,
        "messages": [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "The answer is"},
        ],
    })
    text = resp["content"][0].get("text", "")
    print(f"  Response: \"{text[:100]}\"")
    print_pass("Sonnet 4.6 Prefill works")
except Exception as e:
    print_fail("Sonnet 4.6 Prefill", str(e)[:200])

# ── Test 3: output_config.format (new structured output syntax) ──
print("\n--- Test 3: output_config.format (new syntax, correct format) ---")
try:
    resp = invoke_model(MODEL_SONNET_46, {
        "max_tokens": 256,
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name", "age"],
                    "additionalProperties": False,
                },
            }
        },
        "messages": [{"role": "user", "content": "John is 30 years old. Extract his info."}],
    })
    text = resp["content"][0].get("text", "")
    parsed = json.loads(text)
    print(f"  Parsed: {json.dumps(parsed)}")
    print_pass("output_config.format works")
except Exception as e:
    print(f"  Error: {str(e)[:300]}")
    print_fail("output_config.format", str(e)[:200])

# ── Test 4: old output_format syntax ──
print("\n--- Test 4: output_format (old deprecated syntax) ---")
try:
    resp = invoke_model(MODEL_SONNET_46, {
        "max_tokens": 256,
        "output_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "person",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name", "age"],
                },
            },
        },
        "messages": [{"role": "user", "content": "Jane is 25 years old. Extract her info."}],
    })
    text = resp["content"][0].get("text", "")
    parsed = json.loads(text)
    print(f"  Parsed: {json.dumps(parsed)}")
    print_pass("output_format (deprecated) still works")
except Exception as e:
    print(f"  Error: {str(e)[:300]}")
    print_fail("output_format (deprecated)", str(e)[:200])

# ── Test 5: thinking type:enabled still functional on Sonnet 4.6 (deprecated but works) ──
print("\n--- Test 5: thinking type:enabled on Sonnet 4.6 (deprecated but functional) ---")
try:
    resp = invoke_model(MODEL_SONNET_46, {
        "max_tokens": 8000,
        "thinking": {"type": "enabled", "budget_tokens": 2000},
        "messages": [{"role": "user", "content": "What is 15 * 17?"}],
    })
    thinking = [b for b in resp.get("content", []) if b.get("type") == "thinking"]
    text = [b for b in resp.get("content", []) if b.get("type") == "text"]
    print(f"  thinking blocks: {len(thinking)}, text blocks: {len(text)}")
    if thinking:
        print(f"  thinking preview: \"{thinking[0].get('thinking', '')[:100]}\"")
    if text:
        print(f"  text: \"{text[0].get('text', '')[:100]}\"")
    assert len(thinking) > 0 and len(text) > 0
    print_pass("thinking type:enabled still works (deprecated but functional)")
except Exception as e:
    print_fail("thinking type:enabled", str(e)[:200])

# ── Test 6: Sonnet 4.6 max_tokens > 64k with output-128k beta ──
print("\n--- Test 6: Sonnet 4.6 max_tokens=65536 with output-128k-2025-02-19 beta ---")
try:
    resp = invoke_model(MODEL_SONNET_46, {
        "max_tokens": 65536,
        "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
    }, beta_headers=["output-128k-2025-02-19"])
    text = resp["content"][0].get("text", "")
    print(f"  Response: \"{text[:100]}\"")
    print(f"  usage: {json.dumps(resp.get('usage', {}))}")
    print_pass("Sonnet 4.6 accepts max_tokens=65536 with 128k beta")
except Exception as e:
    print_fail("Sonnet 4.6 128k beta", str(e)[:200])

# ── Test 7: Sonnet 4.6 max_tokens > 64k WITHOUT beta ──
print("\n--- Test 7: Sonnet 4.6 max_tokens=65536 WITHOUT 128k beta ---")
try:
    resp = invoke_model(MODEL_SONNET_46, {
        "max_tokens": 65536,
        "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
    })
    text = resp["content"][0].get("text", "")
    print(f"  Response: \"{text[:100]}\"")
    print_pass("Sonnet 4.6 accepts max_tokens=65536 without beta (GA)")
except Exception as e:
    err = str(e)
    if "max_tokens" in err.lower() or "64" in err:
        print(f"  Error: {err[:200]}")
        print_pass("Sonnet 4.6 rejects max_tokens>64k without beta (as expected)")
    else:
        print_fail("Sonnet 4.6 64k limit", f"Unexpected error: {err[:200]}")

# ── Test 8: Opus 4.6 max_tokens=128000 without beta ──
print("\n--- Test 8: Opus 4.6 max_tokens=128000 without beta ---")
try:
    resp = invoke_model(MODEL_OPUS_46, {
        "max_tokens": 128000,
        "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
    })
    text = resp["content"][0].get("text", "")
    print(f"  Response: \"{text[:100]}\"")
    print(f"  usage: {json.dumps(resp.get('usage', {}))}")
    print_pass("Opus 4.6 accepts max_tokens=128000 without beta (GA)")
except Exception as e:
    print_fail("Opus 4.6 128k", str(e)[:200])

# ── Test 9: fast-mode-2026-02-01 beta header ──
print("\n--- Test 9: fast-mode-2026-02-01 beta header ---")
try:
    resp = invoke_model(MODEL_OPUS_46, {
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "Say hello."}],
    }, beta_headers=["fast-mode-2026-02-01"])
    text = resp["content"][0].get("text", "")
    print(f"  Response: \"{text[:100]}\"")
    print_pass("fast-mode beta header accepted")
except Exception as e:
    err = str(e)
    if "invalid" in err.lower() and "beta" in err.lower():
        print(f"  Error: {err[:200]}")
        print_pass("fast-mode beta header rejected (as expected)")
    else:
        print_fail("fast-mode beta", f"Unexpected error: {err[:200]}")

print(f"\n{'='*60}")
print("  Done.")
print(f"{'='*60}")
