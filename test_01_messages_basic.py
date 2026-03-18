"""Test 01: Messages API Basic — non-streaming request via InvokeModel."""
from helpers import invoke, print_header, print_pass, print_fail
import json

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
    print(f"  model: {resp.get('model')}")
    print(f"  stop_reason: {resp.get('stop_reason')}")
    print(f"  usage: {json.dumps(resp.get('usage', {}))}")
    print(f"  response: \"{text}\"")
    print_pass("Messages API basic request")
except Exception as e:
    print_fail("Messages API basic", str(e))
