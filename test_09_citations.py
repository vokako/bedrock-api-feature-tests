"""Test 09: Citations — document citations in response."""
from helpers import invoke, print_header, print_pass, print_fail

print_header("09", "Citations")

try:
    resp = invoke({
        "max_tokens": 256,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "text", "media_type": "text/plain", "data": "The capital of France is Paris. The Eiffel Tower is 330 meters tall."},
                    "title": "France Facts",
                    "citations": {"enabled": True},
                },
                {"type": "text", "text": "How tall is the Eiffel Tower? Cite the source."},
            ],
        }],
    })
    content = resp.get("content", [])
    has_citation = any(b.get("citations") for b in content if b.get("type") == "text")
    for b in content:
        if b.get("type") == "text":
            print(f"  Text: {b.get('text', '')[:80]}")
            if b.get("citations"):
                print(f"  Citation found: {b['citations'][0].get('type', '')}")
    if has_citation:
        print_pass("Citations")
    else:
        print_fail("Citations", "no citation blocks found")
except Exception as e:
    print_fail("Citations", str(e))
