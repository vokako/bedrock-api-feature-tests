"""Test 10: Structured Outputs — JSON mode via forced tool use."""
import json
from helpers import invoke, print_header, print_pass, print_fail

print_header("10", "Structured Outputs (JSON via Tool Use)")

try:
    resp = invoke({
        "max_tokens": 256,
        "tool_choice": {"type": "tool", "name": "extract_info"},
        "tools": [{
            "name": "extract_info",
            "description": "Extract structured info from text",
            "input_schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                "required": ["name", "age"],
            },
        }],
        "messages": [{"role": "user", "content": "John is 30 years old."}],
    })
    tool_uses = [b for b in resp.get("content", []) if b.get("type") == "tool_use"]
    assert len(tool_uses) > 0, "no tool_use block"
    result = tool_uses[0]["input"]
    assert "name" in result and "age" in result, f"missing fields: {result}"
    print(f"  Extracted: {json.dumps(result)}")
    print_pass("Structured Outputs")
except Exception as e:
    print_fail("Structured Outputs", str(e))
