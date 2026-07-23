"""Test 05: Structured Outputs — strict JSON schema via text.format."""
from helpers import create, print_header, print_pass, print_fail
import json

print_header("05", "Structured Outputs (json_schema)")

try:
    resp = create(
        input="Give me a person named Alice aged 30.",
        text={"format": {
            "type": "json_schema",
            "name": "person",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                "required": ["name", "age"],
                "additionalProperties": False,
            },
        }},
    )
    print(f"  raw output_text: {resp.output_text}")
    parsed = json.loads(resp.output_text)
    print(f"  parsed: {parsed}")

    assert set(parsed.keys()) == {"name", "age"}, f"unexpected keys: {parsed.keys()}"
    assert isinstance(parsed["age"], int), "age not an integer"
    print_pass("Structured Outputs")
except Exception as e:
    print_fail("Structured Outputs", str(e))
