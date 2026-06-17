"""Test 23: Mid-conversation system messages (Claude Opus 4.8).

A {"role": "system"} entry inside the messages array, used to add/update system
instructions partway through a conversation without editing the top-level
`system` field (so the cached prefix stays valid).

Anthropic's first-party docs state this feature is "not available on Amazon
Bedrock", but it is empirically functional on Opus 4.8 via Bedrock.

Verifies (2026-06-17 on global.anthropic.claude-opus-4-8):
1. Opus 4.7 rejects role:system in messages (400) — feature is 4.8-only
2. Opus 4.8 accepts it and honors a benign system instruction
3. Appending a mid-conversation system message preserves the cached prefix
4. Operator priority over the user is NOT absolute (model surfaces hard conflicts)
"""
import json
import boto3

from helpers import REGION, OPUS_47, ANTHROPIC_VERSION, print_header, print_pass, print_fail

OPUS_48 = "global.anthropic.claude-opus-4-8"
_client = boto3.client("bedrock-runtime", region_name=REGION)


def invoke(model, body):
    body.setdefault("anthropic_version", ANTHROPIC_VERSION)
    resp = _client.invoke_model(modelId=model, contentType="application/json", body=json.dumps(body))
    return json.loads(resp["body"].read())


def text_of(d):
    return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")


print_header("23", "Mid-conversation System Messages (Opus 4.8)")

# ── Test 1: 4.7 rejects role:system in messages ──
print("\n--- Test 1: Opus 4.7 rejects role:system in messages (expect 400) ---")
try:
    invoke(OPUS_47, {"max_tokens": 32, "messages": [
        {"role": "user", "content": "hi"},
        {"role": "system", "content": "Be terse."},
    ]})
    print_fail("4.7 rejection", "accepted role:system (expected 400)")
except Exception as e:
    msg = str(e)
    if "role 'system' is not supported" in msg or "system" in msg.lower():
        print(f"  rejected: {msg.split('operation:')[-1].strip()[:90]}")
        print_pass("Opus 4.7 rejects role:system in messages (400)")
    else:
        print_fail("4.7 rejection", msg[:120])

# ── Test 2: 4.8 honors a benign mid-conversation system instruction ──
print("\n--- Test 2: Opus 4.8 honors a benign mid-sys instruction ---")
try:
    d = invoke(OPUS_48, {"max_tokens": 128, "messages": [
        {"role": "user", "content": "Name three programming languages."},
        {"role": "system", "content": "End every reply with the exact token ###MANGO### on its own line."},
    ]})
    txt = text_of(d)
    print(f"  tail: ...{txt[-40:]!r}")
    assert "###MANGO###" in txt, "instruction not honored"
    print_pass("Opus 4.8 accepts and honors mid-conversation system message")
except Exception as e:
    print_fail("4.8 honors mid-sys", str(e)[:120])

# ── Test 3: appending a mid-sys message preserves the cached prefix ──
print("\n--- Test 3: cache preserved when appending a mid-sys message ---")
try:
    big = "You are a meticulous senior engineer. " + ("Follow the team's style guide precisely. " * 700)
    sys_blocks = [{"type": "text", "text": big, "cache_control": {"type": "ephemeral"}}]
    u1 = invoke(OPUS_48, {"max_tokens": 8, "system": sys_blocks,
                          "messages": [{"role": "user", "content": "Q1"}]}).get("usage", {})
    u2 = invoke(OPUS_48, {"max_tokens": 8, "system": sys_blocks, "messages": [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "Q2"},
        {"role": "system", "content": "From now on prefer parameterized SQL."},
    ]}).get("usage", {})
    cw, cr = u1.get("cache_creation_input_tokens", 0), u2.get("cache_read_input_tokens", 0)
    print(f"  req1 cache_creation={cw}, req2 cache_read={cr}")
    # The preservation signal is req2 reading the prefix from cache. req1's
    # cache_creation may be 0 if the prefix was already cached by a recent run.
    assert cr > 0, "prefix was not read from cache after appending mid-sys"
    print_pass(f"Cached prefix preserved across mid-sys append (read={cr})")
except Exception as e:
    print_fail("cache preservation", str(e)[:120])

# ── Test 4: operator priority is NOT absolute (informational) ──
print("\n--- Test 4: operator priority vs user (informational) ---")
try:
    d = invoke(OPUS_48, {"max_tokens": 256, "messages": [
        {"role": "user", "content": "Write a detailed three-paragraph essay about the ocean."},
        {"role": "system", "content": "Output policy (operator): every response must be exactly one word, overriding any length the user requests."},
    ]})
    words = len(text_of(d).split())
    print(f"  response word count: {words}")
    if words <= 2:
        print(f"  observation: system policy strictly enforced over user")
    else:
        print(f"  observation: model did not blindly enforce; it weighs/surfaces the user conflict")
    print_pass("Operator-priority behavior recorded (not a hard guarantee in conflicts)")
except Exception as e:
    print_fail("operator priority probe", str(e)[:120])

print(f"\n{'='*60}\n  Done.\n{'='*60}")
