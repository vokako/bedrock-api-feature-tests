"""Test 12: Compaction — compact beta header.

Verifies:
1. compact-2026-01-12 beta header is accepted by Bedrock (no "invalid beta flag" error)
2. Response is valid with the beta header present

Note: Actual compaction behavior (auto-compressing long conversations) requires
a conversation exceeding the context window, which is impractical in a unit test.
This test verifies the beta header is accepted and the feature is available.
"""
from helpers import invoke, print_header, print_pass, print_fail

print_header("12", "Compaction (compact beta header)")

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
    print(f"  stop_reason: {resp.get('stop_reason')}")
    assert len(text) > 0, "empty response"
    print_pass("Compaction (beta header accepted, response valid)")
except Exception as e:
    if "invalid beta flag" in str(e).lower():
        print_fail("Compaction", f"beta header rejected: {e}")
    else:
        print_fail("Compaction", str(e))
