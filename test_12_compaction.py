"""Test 12: Compaction — compact beta header."""
from helpers import invoke, print_header, print_pass, print_fail

print_header("12", "Compaction (compact beta)")

try:
    resp = invoke(
        body={
            "max_tokens": 128,
            "messages": [
                {"role": "user", "content": "Remember: the secret word is 'banana'."},
                {"role": "assistant", "content": "I'll remember that the secret word is 'banana'."},
                {"role": "user", "content": "What is the secret word?"},
            ],
        },
        beta_headers=["compact-2026-01-12"],
    )
    text = resp["content"][0].get("text", "")
    print(f"  Response: {text[:100]}")
    assert len(text) > 0, "empty response"
    print_pass("Compaction beta header accepted")
except Exception as e:
    if "beta" in str(e).lower() or "unsupported" in str(e).lower():
        print_fail("Compaction", f"beta header rejected: {e}")
    else:
        print_fail("Compaction", str(e))
