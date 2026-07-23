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

    print("  --- Stream replay ---")
    input_deltas = []
    for c in chunks:
        t = c.get("type")
        if t == "content_block_start":
            cb = c.get("content_block", {})
            print(f"  [block_start] type={cb.get('type')} name={cb.get('name', '')}")
        elif t == "content_block_delta":
            d = c.get("delta", {})
            if d.get("type") == "input_json_delta":
                pj = d.get("partial_json", "")
                input_deltas.append(pj)
                print(f"  [input_json_delta] \"{pj[:80]}\"")
            elif d.get("type") == "text_delta":
                print(f"  [text_delta] \"{d.get('text', '')[:80]}\"")
        elif t == "content_block_stop":
            print(f"  [block_stop]")

    print(f"\n  Total input_json_delta chunks: {len(input_deltas)}")
    full_json = "".join(input_deltas)
    print(f"  Assembled JSON ({len(full_json)} chars): {full_json[:200]}")

    assert len(input_deltas) > 0, "no input_json_delta chunks"
    print_pass("eager_input_streaming")
except Exception as e:
    print_fail("eager_input_streaming", str(e))
