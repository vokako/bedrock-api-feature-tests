"""Test 09: Citations — document citations in response."""
from helpers import invoke, print_header, print_pass, print_fail
import json

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
    has_citation = False
    print(f"  content blocks ({len(content)}):")
    for i, b in enumerate(content):
        if b.get("type") == "text":
            print(f"    [{i}] text: \"{b.get('text', '')}\"")
            if b.get("citations"):
                has_citation = True
                for ci, c in enumerate(b["citations"]):
                    print(f"         citation[{ci}]: type={c.get('type')}, cited_text=\"{c.get('cited_text', '')[:60]}\"")
                    if c.get("document_title"):
                        print(f"                     document_title=\"{c['document_title']}\"")

    if has_citation:
        print_pass("Citations")
    else:
        print_fail("Citations", "no citation blocks found")
except Exception as e:
    print_fail("Citations", str(e))
