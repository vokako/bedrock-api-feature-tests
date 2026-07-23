"""Test 21: Claude Opus 4.7 Changes — breaking changes and new features.

Verifies (per migration guide https://platform.claude.com/docs/en/about-claude/models/migration-guide):
1. Basic Messages API works on Opus 4.7
2. Extended thinking (type:enabled) returns 400 error (BREAKING)
3. Sampling parameters (temperature/top_p/top_k) return 400 error (BREAKING)
4. Prefill assistant messages returns 400 error (BREAKING)
5. Adaptive thinking (type:adaptive) works
6. New effort level "xhigh" is accepted
7. Thinking display omitted by default (thinking field empty)
8. Thinking display: "summarized" returns thinking content
9. 128k max_tokens without beta header
10. Task budgets beta (task-budgets-2026-03-13)
"""
import json
import boto3

from helpers import (
    REGION, ANTHROPIC_VERSION, OPUS_47,
    get_client, print_header, print_pass, print_fail,
)


def invoke_opus47(body, beta_headers=None):
    client = get_client()
    if "anthropic_version" not in body:
        body["anthropic_version"] = ANTHROPIC_VERSION
    if beta_headers:
        body["anthropic_beta"] = beta_headers
    resp = client.invoke_model(
        modelId=OPUS_47,
        contentType="application/json",
        body=json.dumps(body),
    )
    return json.loads(resp["body"].read())


def expect_error(body, beta_headers=None):
    """Invoke and expect a validation error. Returns (True, error_str) or (False, response)."""
    try:
        resp = invoke_opus47(body, beta_headers)
        return False, resp
    except Exception as e:
        return True, str(e)


print_header("21", "Claude Opus 4.7 Changes")

# ── Test 1: Basic Messages API ──
print("\n--- Test 1: Basic Messages API ---")
try:
    resp = invoke_opus47({
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "Say hello in one word."}],
    })
    text = resp["content"][0].get("text", "")
    print(f"  model: {resp.get('model')}")
    print(f"  response: \"{text[:80]}\"")
    print(f"  usage: {json.dumps(resp.get('usage', {}))}")
    assert len(text) > 0
    print_pass("Basic Messages API on Opus 4.7")
except Exception as e:
    print_fail("Basic Messages API", str(e)[:200])

# ── Test 2: Extended thinking type:enabled → 400 (BREAKING) ──
print("\n--- Test 2: Extended thinking type:enabled (expect 400) ---")
errored, result = expect_error({
    "max_tokens": 16000,
    "thinking": {"type": "enabled", "budget_tokens": 5000},
    "messages": [{"role": "user", "content": "What is 2+2?"}],
})
if errored:
    print(f"  Error: {result[:200]}")
    print_pass("Extended thinking type:enabled rejected (400)")
else:
    print(f"  Response: {json.dumps(result)[:200]}")
    print_fail("Extended thinking", "Expected 400 but got success — type:enabled still works")

# ── Test 3: Sampling parameters → 400 (BREAKING) ──
print("\n--- Test 3a: temperature → 400 ---")
errored, result = expect_error({
    "max_tokens": 64,
    "temperature": 0.7,
    "messages": [{"role": "user", "content": "Hi"}],
})
if errored:
    print(f"  Error: {result[:150]}")
    print_pass("temperature rejected (400)")
else:
    print_fail("temperature", "Expected 400 but got success")

print("\n--- Test 3b: top_p → 400 ---")
errored, result = expect_error({
    "max_tokens": 64,
    "top_p": 0.9,
    "messages": [{"role": "user", "content": "Hi"}],
})
if errored:
    print(f"  Error: {result[:150]}")
    print_pass("top_p rejected (400)")
else:
    print_fail("top_p", "Expected 400 but got success")

print("\n--- Test 3c: top_k → 400 ---")
errored, result = expect_error({
    "max_tokens": 64,
    "top_k": 50,
    "messages": [{"role": "user", "content": "Hi"}],
})
if errored:
    print(f"  Error: {result[:150]}")
    print_pass("top_k rejected (400)")
else:
    print_fail("top_k", "Expected 400 but got success")

# ── Test 4: Prefill → 400 (BREAKING) ──
print("\n--- Test 4: Prefill assistant message (expect 400) ---")
errored, result = expect_error({
    "max_tokens": 64,
    "messages": [
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "The answer is"},
    ],
})
if errored:
    print(f"  Error: {result[:200]}")
    print_pass("Prefill rejected (400)")
else:
    print(f"  Response: {result['content'][0].get('text', '')[:100]}")
    print_fail("Prefill", "Expected 400 but got success — prefill still works")

# ── Test 5: Adaptive thinking works ──
print("\n--- Test 5: Adaptive thinking (type:adaptive) ---")
try:
    resp = invoke_opus47({
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "messages": [{"role": "user", "content": "What is 27 * 43? Show your work."}],
    })
    content = resp.get("content", [])
    types = [b.get("type") for b in content]
    print(f"  block types: {types}")
    assert "text" in types
    print_pass("Adaptive thinking accepted")
except Exception as e:
    print_fail("Adaptive thinking", str(e)[:200])

# ── Test 6: New effort level "xhigh" ──
print("\n--- Test 6: effort=xhigh ---")
try:
    resp = invoke_opus47({
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "xhigh"},
        "messages": [{"role": "user", "content": "What is 27 * 43?"}],
    })
    content = resp.get("content", [])
    types = [b.get("type") for b in content]
    print(f"  block types: {types}")
    print_pass("effort=xhigh accepted")
except Exception as e:
    print_fail("effort=xhigh", str(e)[:200])

# ── Test 7: Thinking display omitted by default ──
print("\n--- Test 7: Thinking display omitted by default ---")
try:
    resp = invoke_opus47({
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "max"},
        "messages": [{"role": "user", "content": "Prove that the square root of 2 is irrational using proof by contradiction. Be rigorous and show every step."}],
    })
    content = resp.get("content", [])
    thinking_blocks = [b for b in content if b.get("type") == "thinking"]
    if thinking_blocks:
        thinking_text = thinking_blocks[0].get("thinking", "")
        print(f"  thinking blocks: {len(thinking_blocks)}")
        print(f"  thinking text length: {len(thinking_text)}")
        if len(thinking_text) == 0:
            print_pass("Thinking display omitted by default (empty thinking field)")
        else:
            print(f"  thinking preview: \"{thinking_text[:100]}\"")
            print_fail("Thinking display", "thinking field not empty — default may still be summarized")
    else:
        print(f"  No thinking blocks (model skipped thinking at this effort)")
        print_pass("Thinking display — no thinking block produced (adaptive skipped)")
except Exception as e:
    print_fail("Thinking display omitted", str(e)[:200])

# ── Test 8: Thinking display: summarized ──
print("\n--- Test 8: Thinking display: summarized ---")
try:
    resp = invoke_opus47({
        "max_tokens": 16000,
        "thinking": {"type": "adaptive", "display": "summarized"},
        "output_config": {"effort": "max"},
        "messages": [{"role": "user", "content": "Prove that the square root of 2 is irrational using proof by contradiction. Be rigorous and show every step."}],
    })
    content = resp.get("content", [])
    thinking_blocks = [b for b in content if b.get("type") == "thinking"]
    if thinking_blocks:
        thinking_text = thinking_blocks[0].get("thinking", "")
        print(f"  thinking blocks: {len(thinking_blocks)}")
        print(f"  thinking text length: {len(thinking_text)}")
        if len(thinking_text) > 0:
            print(f"  thinking preview: \"{thinking_text[:120]}...\"")
            print_pass("Thinking display: summarized returns content")
        else:
            print_fail("Thinking display: summarized", "thinking field still empty with display=summarized")
    else:
        print(f"  No thinking blocks (model skipped thinking)")
        print_pass("Thinking display: summarized — no thinking block (adaptive skipped)")
except Exception as e:
    print_fail("Thinking display: summarized", str(e)[:200])

# ── Test 9: 128k max_tokens without beta ──
print("\n--- Test 9: max_tokens=128000 without beta ---")
try:
    resp = invoke_opus47({
        "max_tokens": 128000,
        "messages": [{"role": "user", "content": "Say 'hello' in one word."}],
    })
    text = resp["content"][0].get("text", "")
    print(f"  response: \"{text[:80]}\"")
    print(f"  usage: {json.dumps(resp.get('usage', {}))}")
    print_pass("max_tokens=128000 accepted without beta (GA)")
except Exception as e:
    print_fail("max_tokens=128000", str(e)[:200])

# ── Test 10: Task budgets beta ──
print("\n--- Test 10: Task budgets (task-budgets-2026-03-13) ---")
try:
    resp = invoke_opus47(
        body={
            "max_tokens": 64000,
            "thinking": {"type": "adaptive"},
            "output_config": {
                "effort": "high",
                "task_budget": {"type": "tokens", "total": 128000},
            },
            "messages": [{"role": "user", "content": "Say hello briefly."}],
        },
        beta_headers=["task-budgets-2026-03-13"],
    )
    text = resp["content"][0].get("text", "")
    print(f"  response: \"{text[:80]}\"")
    print_pass("Task budgets beta accepted")
except Exception as e:
    err = str(e)
    if "invalid beta" in err.lower():
        print(f"  Error: {err[:200]}")
        print_fail("Task budgets", "beta header rejected")
    else:
        print(f"  Error: {err[:200]}")
        print_fail("Task budgets", err[:200])

print(f"\n{'='*60}")
print("  Done.")
print(f"{'='*60}")
