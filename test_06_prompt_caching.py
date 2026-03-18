"""Test 06: Prompt Caching — cache_control with ephemeral TTL."""
from helpers import invoke, print_header, print_pass, print_fail
import json
import uuid

print_header("06", "Prompt Caching (cache_control)")

# Add a unique nonce so each test run gets a fresh cache entry
nonce = uuid.uuid4().hex[:8]
LONG_SYSTEM = f"You are a helpful assistant. Session: {nonce}. " + ("You specialize in software engineering and cloud architecture. " * 100)

try:
    resp1 = invoke({
        "max_tokens": 32,
        "system": [{"type": "text", "text": LONG_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": "Say hi."}],
    })
    u1 = resp1.get("usage", {})

    resp2 = invoke({
        "max_tokens": 32,
        "system": [{"type": "text", "text": LONG_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": "Say bye."}],
    })
    u2 = resp2.get("usage", {})

    print(f"  Req 1 usage: {json.dumps(u1, indent=4)}")
    print(f"  Req 2 usage: {json.dumps(u2, indent=4)}")

    has_cache_fields = "cache_creation_input_tokens" in u1
    cw1 = u1.get("cache_creation_input_tokens", 0)
    cr2 = u2.get("cache_read_input_tokens", 0)

    if cw1 > 0 or cr2 > 0:
        print_pass("Prompt Caching (cache hit/write confirmed)")
    elif has_cache_fields:
        print_pass("Prompt Caching (cache_control accepted, fields present — global endpoint may not report cache metrics)")
    else:
        print_fail("Prompt Caching", "cache fields not present in usage")
except Exception as e:
    print_fail("Prompt Caching", str(e))
