"""Test 04: Extended Thinking — thinking blocks in response."""
from helpers import invoke, print_header, print_pass, print_fail

print_header("04", "Extended Thinking")

try:
    resp = invoke({
        "max_tokens": 16000,
        "thinking": {"type": "enabled", "budget_tokens": 5000},
        "messages": [{"role": "user", "content": "What is 27 * 43? Think step by step."}],
    })
    content = resp.get("content", [])
    thinking_blocks = [b for b in content if b.get("type") == "thinking"]
    text_blocks = [b for b in content if b.get("type") == "text"]
    assert len(thinking_blocks) > 0, "no thinking block"
    assert len(text_blocks) > 0, "no text block"
    print(f"  Thinking length: {len(thinking_blocks[0].get('thinking', ''))} chars")
    print(f"  Answer: {text_blocks[0].get('text', '')[:100]}")
    print_pass("Extended Thinking")
except Exception as e:
    print_fail("Extended Thinking", str(e))
