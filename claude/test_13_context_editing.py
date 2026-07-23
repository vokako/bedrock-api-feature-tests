"""Test 13: Context Editing — context-management beta header.

Verifies:
1. context-management-2025-06-27 beta header is accepted by Bedrock
2. Response is valid with the beta header present

Note: Actual context editing (modifying specific messages in history) requires
multi-turn conversations with message IDs. This test verifies the beta header
is accepted and the feature is available.
"""
from helpers import invoke, print_header, print_pass, print_fail

print_header("13", "Context Editing (context-management beta header)")

try:
    resp = invoke(
        body={
            "max_tokens": 128,
            "messages": [{"role": "user", "content": "Hello, how are you?"}],
        },
        beta_headers=["context-management-2025-06-27"],
    )
    text = resp["content"][0].get("text", "")
    print(f"  Response: {text[:100]}")
    print(f"  stop_reason: {resp.get('stop_reason')}")
    assert len(text) > 0, "empty response"
    print_pass("Context Editing (beta header accepted, response valid)")
except Exception as e:
    if "invalid beta flag" in str(e).lower():
        print_fail("Context Editing", f"beta header rejected: {e}")
    else:
        print_fail("Context Editing", str(e))
