"""Test 01: Responses API Basic — non-streaming request via bedrock-mantle."""
from helpers import create, print_header, print_pass, print_fail
import json

print_header("01", "Responses API Basic (bedrock-mantle)")

try:
    resp = create(input="Say hello in one word.")
    assert resp.status == "completed", f"unexpected status: {resp.status}"
    text = resp.output_text
    assert len(text) > 0, "empty response text"
    print(f"  model: {resp.model}")
    print(f"  status: {resp.status}")
    print(f"  usage: {json.dumps(resp.usage.model_dump(), default=str)}")
    print(f"  response: \"{text}\"")
    print_pass("Responses API basic request")
except Exception as e:
    print_fail("Responses API basic", str(e))
