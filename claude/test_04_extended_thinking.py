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
    print(f"  content blocks ({len(content)}):")
    for i, b in enumerate(content):
        btype = b.get("type")
        if btype == "thinking":
            thinking_text = b.get("thinking", "")
            print(f"    [{i}] thinking ({len(thinking_text)} chars):")
            for line in thinking_text.split("\n")[:5]:
                print(f"         {line}")
            if thinking_text.count("\n") > 5:
                print(f"         ... ({thinking_text.count(chr(10))} lines total)")
        elif btype == "text":
            print(f"    [{i}] text: \"{b.get('text', '')[:120]}\"")

    thinking_blocks = [b for b in content if b.get("type") == "thinking"]
    text_blocks = [b for b in content if b.get("type") == "text"]
    assert len(thinking_blocks) > 0, "no thinking block"
    assert len(text_blocks) > 0, "no text block"
    print_pass("Extended Thinking")
except Exception as e:
    print_fail("Extended Thinking", str(e))
