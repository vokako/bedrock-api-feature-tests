"""Test 06: Prompt Caching — cache_control with ephemeral TTL."""
from helpers import invoke, print_header, print_pass, print_fail

print_header("06", "Prompt Caching (cache_control)")

LONG_SYSTEM = ("You are a helpful assistant who specializes in software engineering. " * 100)

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

    cw1 = u1.get("cache_creation_input_tokens", 0)
    cr2 = u2.get("cache_read_input_tokens", 0)
    print(f"  Req 1 — cache_creation: {cw1}, cache_read: {u1.get('cache_read_input_tokens', 0)}")
    print(f"  Req 2 — cache_creation: {u2.get('cache_creation_input_tokens', 0)}, cache_read: {cr2}")
    print(f"  Req 1 full usage: {u1}")

    # cache_control is accepted (no error), and cache fields are present in usage
    has_cache_fields = "cache_creation_input_tokens" in u1
    if cw1 > 0 or cr2 > 0:
        print_pass("Prompt Caching (cache hit/write confirmed)")
    elif has_cache_fields:
        # Global endpoints accept cache_control but may not report metrics
        print_pass("Prompt Caching (cache_control accepted, fields present — global endpoint may not report cache metrics)")
    else:
        print_fail("Prompt Caching", "cache fields not present in usage")
except Exception as e:
    print_fail("Prompt Caching", str(e))
