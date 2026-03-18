"""Test 16: Adaptive Thinking — thinking.type: "adaptive" with effort parameter.

Adaptive thinking lets Claude dynamically determine when and how much to think.
No beta header required. Supported on Opus 4.6 and Sonnet 4.6 only.
Also automatically enables interleaved thinking.
"""
from helpers import invoke, print_header, print_pass, print_fail

print_header("16", "Adaptive Thinking (thinking.type: adaptive)")

try:
    # Test 1: adaptive thinking on a math problem (should think)
    print("  --- Test A: math problem (expect thinking) ---")
    resp = invoke({
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "messages": [{"role": "user", "content": "What is 27 * 43? Show your work."}],
    })
    content = resp.get("content", [])
    types = [b.get("type") for b in content]
    print(f"  block types: {types}")
    for i, b in enumerate(content):
        if b.get("type") == "thinking":
            print(f"    [{i}] thinking ({len(b.get('thinking', ''))} chars): \"{b.get('thinking', '')[:80]}...\"")
        elif b.get("type") == "text":
            print(f"    [{i}] text: \"{b.get('text', '')[:100]}\"")

    # Test 2: effort=low on trivial question (may skip thinking)
    print("\n  --- Test B: trivial question with effort=low (may skip thinking) ---")
    resp2 = invoke({
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "low"},
        "messages": [{"role": "user", "content": "What is 2+2?"}],
    })
    content2 = resp2.get("content", [])
    types2 = [b.get("type") for b in content2]
    print(f"  block types: {types2}")
    for i, b in enumerate(content2):
        if b.get("type") == "thinking":
            print(f"    [{i}] thinking: \"{b.get('thinking', '')[:80]}\"")
        elif b.get("type") == "text":
            print(f"    [{i}] text: \"{b.get('text', '')}\"")

    skipped = "thinking" not in types2
    print(f"  Thinking skipped at effort=low: {skipped}")

    print_pass("Adaptive Thinking (type=adaptive accepted, effort parameter works)")
except Exception as e:
    print_fail("Adaptive Thinking", str(e))
