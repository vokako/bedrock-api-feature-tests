"""Test 02: Streaming (SSE) — InvokeModelWithResponseStream."""
from helpers import invoke_stream, print_header, print_pass, print_fail

print_header("02", "Streaming (SSE)")

try:
    chunks = invoke_stream({
        "max_tokens": 128,
        "messages": [{"role": "user", "content": "Count from 1 to 5."}],
    })
    print(f"  Total events: {len(chunks)}")
    print(f"  Event types: {[c.get('type') for c in chunks]}")
    print()
    print("  --- Stream replay ---")
    for c in chunks:
        t = c.get("type")
        if t == "message_start":
            msg = c.get("message", {})
            print(f"  [message_start] model={msg.get('model')} id={msg.get('id')}")
        elif t == "content_block_start":
            cb = c.get("content_block", {})
            print(f"  [content_block_start] type={cb.get('type')}")
        elif t == "content_block_delta":
            d = c.get("delta", {})
            if d.get("type") == "text_delta":
                print(f"  [text_delta] \"{d.get('text', '')}\"")
        elif t == "message_delta":
            d = c.get("delta", {})
            print(f"  [message_delta] stop_reason={d.get('stop_reason')} usage={c.get('usage', {})}")
        elif t == "message_stop":
            print(f"  [message_stop]")

    types = [c.get("type") for c in chunks]
    assert "message_start" in types, "missing message_start"
    assert "content_block_delta" in types, "missing content_block_delta"
    print_pass("Streaming")
except Exception as e:
    print_fail("Streaming", str(e))
