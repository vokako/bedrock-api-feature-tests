"""Test 11: Fine-grained Tool Streaming — eager_input_streaming."""
from helpers import invoke_stream, print_header, print_pass, print_fail

print_header("11", "Fine-grained Tool Streaming (eager_input_streaming)")

try:
    chunks = invoke_stream({
        "max_tokens": 512,
        "tools": [{
            "name": "make_file",
            "description": "Write text to a file",
            "eager_input_streaming": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "lines_of_text": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["filename", "lines_of_text"],
            },
        }],
        "messages": [{"role": "user", "content": "Write a 4-line poem and save it to poem.txt using make_file."}],
    })
    input_deltas = [
        c for c in chunks
        if c.get("type") == "content_block_delta" and c.get("delta", {}).get("type") == "input_json_delta"
    ]
    assert len(input_deltas) > 0, "no input_json_delta chunks"
    partial = "".join(d["delta"]["partial_json"] for d in input_deltas)
    print(f"  input_json_delta chunks: {len(input_deltas)}")
    print(f"  Partial JSON (first 120): {partial[:120]}")
    print_pass("eager_input_streaming")
except Exception as e:
    print_fail("eager_input_streaming", str(e))
