"""Test 05: Interleaved Thinking — thinking between tool calls via beta header."""
from helpers import invoke, print_header, print_pass, print_fail
import json

print_header("05", "Interleaved Thinking (interleaved-thinking beta)")

try:
    resp = invoke(
        body={
            "max_tokens": 16000,
            "thinking": {"type": "enabled", "budget_tokens": 5000},
            "tools": [{
                "name": "get_price",
                "description": "Get stock price for a given symbol",
                "input_schema": {
                    "type": "object",
                    "properties": {"symbol": {"type": "string"}},
                    "required": ["symbol"],
                },
            }],
            "messages": [{"role": "user", "content": "Get the price of AAPL and tell me if it's a good buy."}],
        },
        beta_headers=["interleaved-thinking-2025-05-14"],
    )
    content = resp.get("content", [])
    types = [b.get("type") for b in content]
    print(f"  stop_reason: {resp.get('stop_reason')}")
    print(f"  content block types: {types}")
    print()
    for i, b in enumerate(content):
        btype = b.get("type")
        if btype == "thinking":
            print(f"    [{i}] thinking: \"{b.get('thinking', '')[:80]}...\"")
        elif btype == "text":
            print(f"    [{i}] text: \"{b.get('text', '')[:80]}\"")
        elif btype == "tool_use":
            print(f"    [{i}] tool_use: name={b['name']}, input={json.dumps(b['input'])}")

    assert "thinking" in types, "no thinking block"
    assert "tool_use" in types, "no tool_use block"
    print_pass("Interleaved Thinking")
except Exception as e:
    print_fail("Interleaved Thinking", str(e))
