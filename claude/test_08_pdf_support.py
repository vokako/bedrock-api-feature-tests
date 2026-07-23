"""Test 08: PDF Support — document content block."""
import base64
from helpers import invoke, print_header, print_pass, print_fail

print_header("08", "PDF Support (Document Block)")

MINIMAL_PDF = b"""%PDF-1.0
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj
4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
5 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Hello PDF) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000340 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
434
%%EOF"""

try:
    resp = invoke({
        "max_tokens": 128,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": base64.b64encode(MINIMAL_PDF).decode()}},
                {"type": "text", "text": "What text is in this PDF? Reply briefly."},
            ],
        }],
    })
    text = resp["content"][0].get("text", "")
    print(f"  Response: {text[:100]}")
    assert len(text) > 0, "empty response"
    print_pass("PDF Support")
except Exception as e:
    print_fail("PDF Support", str(e))
