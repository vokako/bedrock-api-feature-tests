"""Test 15: Tool Input Examples — input_examples via InvokeModel."""
from helpers import invoke, print_header, print_pass, print_fail

print_header("15", "Tool Input Examples (input_examples)")

try:
    resp = invoke(
        body={
            "max_tokens": 256,
            "tools": [{
                "name": "get_weather",
                "description": "Get weather for a location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
                "input_examples": [
                    {"location": "Beijing", "unit": "celsius"},
                    {"location": "San Francisco, CA", "unit": "fahrenheit"},
                ],
            }],
            "messages": [{"role": "user", "content": "What's the weather in Tokyo?"}],
        },
        beta_headers=["tool-examples-2025-10-29"],
    )
    tool_uses = [b for b in resp.get("content", []) if b.get("type") == "tool_use"]
    assert len(tool_uses) > 0, "no tool_use block"
    print(f"  Tool called: {tool_uses[0]['name']}, input: {tool_uses[0]['input']}")
    print_pass("Tool Input Examples")
except Exception as e:
    print_fail("Tool Input Examples", str(e))
