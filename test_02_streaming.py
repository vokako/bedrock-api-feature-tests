"""Test 02: Streaming (SSE) — InvokeModelWithResponseStream."""
from helpers import invoke_stream, print_header, print_pass, print_fail

print_header("02", "Streaming (SSE)")

try:
    chunks = invoke_stream({
        "max_tokens": 128,
        "messages": [{"role": "user", "content": "Count from 1 to 5."}],
    })
    types = [c.get("type") for c in chunks]
    assert "message_start" in types, "missing message_start"
    assert "content_block_delta" in types, "missing content_block_delta"
    text_parts = [
        c["delta"]["text"] for c in chunks
        if c.get("type") == "content_block_delta" and c.get("delta", {}).get("type") == "text_delta"
    ]
    full_text = "".join(text_parts)
    print(f"  Streamed text: {full_text[:100]}")
    print(f"  Total chunks: {len(chunks)}")
    print_pass("Streaming")
except Exception as e:
    print_fail("Streaming", str(e))
