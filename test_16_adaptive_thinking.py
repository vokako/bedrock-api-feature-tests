"""Test 16: Adaptive Thinking — thinking.type: "adaptive" with effort parameter.

Adaptive thinking lets Claude dynamically determine when and how much to think.
No beta header required. Supported on Opus 4.6 and Sonnet 4.6 only.
Also automatically enables interleaved thinking.
"""
from helpers import invoke, print_header, print_pass, print_fail

print_header("16", "Adaptive Thinking (thinking.type: adaptive)")

try:
    # Test 1: basic adaptive thinking
    resp = invoke({
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "messages": [{"role": "user", "content": "What is 27 * 43? Show your work."}],
    })
    content = resp.get("content", [])
    types = [b.get("type") for b in content]
    print(f"  Basic — block types: {types}")
    has_thinking = "thinking" in types
    has_text = "text" in types
    assert has_text, "no text block"
    if has_thinking:
        print(f"  Thinking length: {len(content[0].get('thinking', ''))} chars")

    # Test 2: adaptive thinking with effort=low (may skip thinking for simple query)
    resp2 = invoke({
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "low"},
        "messages": [{"role": "user", "content": "What is 2+2?"}],
    })
    content2 = resp2.get("content", [])
    types2 = [b.get("type") for b in content2]
    print(f"  effort=low — block types: {types2}")

    print_pass("Adaptive Thinking (type=adaptive accepted, effort parameter works)")
except Exception as e:
    print_fail("Adaptive Thinking", str(e))
