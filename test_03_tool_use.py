"""Test 03: Tool Use — function calling via InvokeModel."""
from helpers import invoke, print_header, print_pass, print_fail

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
    tool_uses = [b for b in resp.get("content", []) if b.get("type") == "tool_use"]
    assert len(tool_uses) > 0, "no tool_use block in response"
    tu = tool_uses[0]
    assert tu["name"] == "get_weather"
    assert "location" in tu.get("input", {})
    print(f"  Tool called: {tu['name']}, input: {tu['input']}")
    print_pass("Tool Use")
except Exception as e:
    print_fail("Tool Use", str(e))
