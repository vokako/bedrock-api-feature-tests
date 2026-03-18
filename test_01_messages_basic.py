"""Test 01: Messages API Basic — non-streaming request via InvokeModel."""
from helpers import invoke, print_header, print_pass, print_fail

print_header("01", "Messages API Basic (InvokeModel)")

try:
    resp = invoke({
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "Say hello in one word."}],
    })
    assert resp.get("type") == "message", f"unexpected type: {resp.get('type')}"
    assert resp.get("role") == "assistant"
    text = resp["content"][0].get("text", "")
    assert len(text) > 0, "empty response text"
    print(f"  Response: {text[:80]}")
    print_pass("Messages API basic request")
except Exception as e:
    print_fail("Messages API basic", str(e))
