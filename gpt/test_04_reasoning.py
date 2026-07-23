"""Test 04: Reasoning — reasoning effort control via Responses API."""
from helpers import create, output_types, print_header, print_pass, print_fail

print_header("04", "Reasoning (effort control)")

try:
    resp = create(
        reasoning={"effort": "low"},
        input="What is 17 * 23? Think step by step, then give the number.",
    )
    types = output_types(resp)
    print(f"  output types: {types}")
    print(f"  reasoning_tokens: {resp.usage.output_tokens_details.reasoning_tokens}")
    print(f"  answer: \"{resp.output_text.strip()}\"")

    assert "reasoning" in types, "no reasoning item in output"
    assert "391" in resp.output_text, "wrong/absent answer (17*23=391)"
    print_pass("Reasoning")
except Exception as e:
    print_fail("Reasoning", str(e))
