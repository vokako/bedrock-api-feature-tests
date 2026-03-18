"""Test 05: Interleaved Thinking — thinking between tool calls via beta header.

This tests the interleaved-thinking-2025-05-14 beta header, which enables
thinking blocks between tool calls in manual extended thinking mode.
"""
from helpers import invoke, print_header, print_pass, print_fail

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
    print(f"  Content block types: {types}")
    assert "thinking" in types, "no thinking block"
    assert "tool_use" in types, "no tool_use block"
    print_pass("Interleaved Thinking")
except Exception as e:
    print_fail("Interleaved Thinking", str(e))
