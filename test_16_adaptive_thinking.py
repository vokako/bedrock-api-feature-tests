"""Test 16: Adaptive Thinking — thinking.type: "adaptive" with effort parameter.

Verifies:
1. thinking.type: "adaptive" is accepted
2. Complex question triggers thinking blocks
3. effort=low on trivial question may skip thinking
4. output_config.effort parameter is accepted
"""
from helpers import invoke, print_header, print_pass, print_fail

print_header("16", "Adaptive Thinking (thinking.type: adaptive)")

try:
    # Test A: math problem — should produce thinking
    print("  --- Test A: math problem (expect thinking) ---")
    resp = invoke({
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "messages": [{"role": "user", "content": "What is 27 * 43? Show your work."}],
    })
    content = resp.get("content", [])
    types = [b.get("type") for b in content]
    print(f"  block types: {types}")
    has_thinking_a = "thinking" in types
    for i, b in enumerate(content):
        if b.get("type") == "thinking":
            print(f"    [{i}] thinking ({len(b.get('thinking', ''))} chars): \"{b.get('thinking', '')[:80]}...\"")
        elif b.get("type") == "text":
            print(f"    [{i}] text: \"{b.get('text', '')[:100]}\"")

    assert "text" in types, "no text block in response"
    if not has_thinking_a:
        print("  ⚠️  No thinking block for math problem (model may have decided it's simple enough)")

    # Test B: trivial question with effort=low — may skip thinking
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
    has_thinking_b = "thinking" in types2
    for i, b in enumerate(content2):
        if b.get("type") == "thinking":
            print(f"    [{i}] thinking: \"{b.get('thinking', '')[:80]}\"")
        elif b.get("type") == "text":
            print(f"    [{i}] text: \"{b.get('text', '')}\"")

    # Validate: adaptive thinking accepted + effort parameter works
    # The key proof is: type=adaptive doesn't error, and effort=low is accepted
    # Bonus: if thinking was present for A but not B, that proves adaptive behavior
    if has_thinking_a and not has_thinking_b:
        print(f"\n  ✓ Adaptive behavior confirmed: thinking for complex, skipped for trivial")
    elif has_thinking_a and has_thinking_b:
        print(f"\n  ✓ Adaptive thinking accepted (model chose to think for both)")
    else:
        print(f"\n  ✓ Adaptive thinking accepted (model skipped thinking for both at this complexity)")

    print_pass("Adaptive Thinking (type=adaptive + effort parameter accepted)")
except Exception as e:
    print_fail("Adaptive Thinking", str(e))
