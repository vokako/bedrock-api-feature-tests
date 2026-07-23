"""Test 10: Structured Outputs — forced tool use + output_config.format (json_schema).

Verifies:
1. Forced tool use returns structured JSON via tool_use block
2. output_config.format with json_schema returns schema-compliant JSON in text content

Note: output_config.format is supported on Claude 4.6 models via InvokeModel.
      Claude Opus 4.7 does not yet support output_config.format on Bedrock.
"""
import json
from helpers import invoke, print_header, print_pass, print_fail

print_header("10", "Structured Outputs")

# --- Test 1: Forced tool use ---
print("\n  [1] JSON via forced tool use")
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
    print(f"      Extracted: {json.dumps(result)}")
    print_pass("Forced tool use")
except Exception as e:
    print_fail("Forced tool use", str(e))

# --- Test 2: output_config.format with json_schema ---
print("\n  [2] JSON via output_config.format (json_schema)")
try:
    resp = invoke({
        "max_tokens": 256,
        "messages": [{"role": "user", "content": "John is 30 years old and lives in Tokyo."}],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                        "city": {"type": "string"},
                    },
                    "required": ["name", "age", "city"],
                    "additionalProperties": False,
                },
            }
        },
    })
    text = resp["content"][0]["text"]
    parsed = json.loads(text)
    assert "name" in parsed and "age" in parsed and "city" in parsed, f"missing fields: {parsed}"
    print(f"      Extracted: {text}")
    print_pass("output_config.format (json_schema)")
except Exception as e:
    err = str(e)
    if "Extra inputs are not permitted" in err:
        print(f"      ⚠️  output_config.format not supported on this model")
        print_fail("output_config.format (json_schema)", "not supported on current model")
    else:
        print_fail("output_config.format (json_schema)", err)
