"""Test 13: Context Editing — context-management beta header."""
from helpers import invoke, print_header, print_pass, print_fail

print_header("13", "Context Editing (context-management beta)")

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
    assert len(text) > 0, "empty response"
    print_pass("Context Editing beta header accepted")
except Exception as e:
    if "beta" in str(e).lower() or "unsupported" in str(e).lower():
        print_fail("Context Editing", f"beta header rejected: {e}")
    else:
        print_fail("Context Editing", str(e))
