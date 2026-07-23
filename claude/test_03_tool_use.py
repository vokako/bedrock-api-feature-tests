"""Test 03: Tool Use — function calling via InvokeModel."""
from helpers import invoke, print_header, print_pass, print_fail
import json

print_header("03", "Tool Use (Function Calling)")

try:
    resp = invoke({
        "max_tokens": 256,
        "tools": [{
            "name": "get_weather",
            "description": "Get weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        }],
        "messages": [{"role": "user", "content": "What's the weather in Tokyo?"}],
    })
    print(f"  stop_reason: {resp.get('stop_reason')}")
    print(f"  content blocks ({len(resp.get('content', []))}):")
    for i, b in enumerate(resp.get("content", [])):
        btype = b.get("type")
        if btype == "text":
            print(f"    [{i}] text: \"{b.get('text', '')[:100]}\"")
        elif btype == "tool_use":
            print(f"    [{i}] tool_use: name={b['name']}, id={b['id']}")
            print(f"         input: {json.dumps(b['input'])}")

    tool_uses = [b for b in resp.get("content", []) if b.get("type") == "tool_use"]
    assert len(tool_uses) > 0, "no tool_use block in response"
    assert tool_uses[0]["name"] == "get_weather"
    print_pass("Tool Use")
except Exception as e:
    print_fail("Tool Use", str(e))
