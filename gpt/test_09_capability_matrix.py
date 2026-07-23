"""Test 09: Capability Matrix — double-check OpenAI's Bedrock compatibility table.

Verifies, in one place, the boundary between what the bedrock-mantle Responses API
accepts vs rejects for GPT-5.6, against OpenAI's "OpenAI models in Amazon Bedrock"
feature table (as of the 2026-07-13 launch).

Key findings encoded here:
  - Unsupported hosted tools (file_search, image_generation, code_interpreter,
    computer_use_preview, shell) are HARD-REJECTED with 400.
  - `web_search` is the odd one out: ACCEPTED at validation, but its
    web_search_call executes with status="failed" (see test_08).
  - Supported tool types reported by the API: function, mcp, custom, namespace,
    tool_search.
  - service_tier other than on-demand -> 400 (on-demand only on Bedrock).
  - Available capabilities: reasoning effort=max, conversation state
    (previous_response_id), file input.
"""
from helpers import get_client, MODEL_ID, print_header, print_pass, print_fail
from openai import BadRequestError
import base64

print_header("09", "Capability Matrix (double-check vs OpenAI compat table)")

client = get_client()
UNSUPPORTED_HOSTED = ["file_search", "image_generation", "code_interpreter",
                      "computer_use_preview", "shell"]


def create(**kw):
    return client.responses.create(model=MODEL_ID, **kw)


def expect_400(fn) -> str:
    try:
        fn()
        return ""  # no error = unexpected
    except BadRequestError as e:
        return str(e)


try:
    results = []

    # 1. Unsupported hosted tools must 400.
    for t in UNSUPPORTED_HOSTED:
        tool = {"type": t}
        if t == "file_search":
            tool["vector_store_ids"] = ["vs_dummy"]
        if t == "code_interpreter":
            tool["container"] = {"type": "auto"}
        if t == "computer_use_preview":
            tool.update(display_width=1024, display_height=768, environment="linux")
        err = expect_400(lambda tool=tool: create(tools=[tool], input="help"))
        ok = "is not supported" in err
        print(f"  hosted '{t}': {'400 rejected ✓' if ok else 'NOT rejected ✗'}")
        results.append(ok)

    # 2. remote MCP via server_url must 400 (only connector ARN allowed).
    err = expect_400(lambda: create(
        tools=[{"type": "mcp", "server_label": "d", "server_url": "https://example.com/mcp",
                "require_approval": "never"}], input="help"))
    ok = "connector ARN" in err or "server_url" in err
    print(f"  remote MCP server_url: {'400 rejected ✓' if ok else 'NOT rejected ✗'}")
    results.append(ok)

    # 3. web_search is accepted (no 400) but soft-fails — the documented odd case.
    r = create(tools=[{"type": "web_search"}], tool_choice="required",
               input="current NVDA price? cite url")
    ws = [o.status for o in r.output if getattr(o, "type", "") == "web_search_call"]
    ok = len(ws) > 0 and all(s == "failed" for s in ws)
    print(f"  web_search: accepted, statuses={ws} {'(soft-fail as documented) ✓' if ok else '✗'}")
    results.append(ok)

    # 4. tool_search accepted.
    r = create(tools=[{"type": "tool_search"}], input="hello")
    print("  tool_search: accepted ✓")
    results.append(True)

    # 5. service_tier=flex must 400 (on-demand only).
    err = expect_400(lambda: create(input="hi", service_tier="flex"))
    ok = "service_tier" in err
    print(f"  service_tier=flex: {'400 rejected ✓' if ok else 'NOT rejected ✗'}")
    results.append(ok)

    # 6. reasoning effort=max works.
    r = create(reasoning={"effort": "max"}, input="What is 12*13? number only.")
    ok = "156" in r.output_text
    print(f"  reasoning effort=max: {'works ✓' if ok else 'FAILED ✗'} ({r.output_text.strip()[:20]!r})")
    results.append(ok)

    # 7. conversation state via previous_response_id works.
    r1 = create(input="Remember the number 42. Reply OK.")
    r2 = create(input="What number did I ask you to remember?", previous_response_id=r1.id)
    ok = "42" in r2.output_text
    print(f"  conversation state: {'works ✓' if ok else 'FAILED ✗'} ({r2.output_text.strip()[:30]!r})")
    results.append(ok)

    # 8. file input (PDF) works.
    pdf = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
           b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
           b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R"
           b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
           b"4 0 obj<</Length 44>>stream\nBT /F1 18 Tf 20 100 Td (Hello PDF 7788) Tj ET\nendstream endobj\n"
           b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF")
    b64 = base64.b64encode(pdf).decode()
    r = create(input=[{"role": "user", "content": [
        {"type": "input_text", "text": "What number appears in this PDF?"},
        {"type": "input_file", "filename": "t.pdf", "file_data": f"data:application/pdf;base64,{b64}"}]}])
    ok = "7788" in r.output_text
    print(f"  file input (PDF): {'works ✓' if ok else 'FAILED ✗'} ({r.output_text.strip()[:30]!r})")
    results.append(ok)

    assert all(results), f"{results.count(False)} capability checks did not match expectations"
    print_pass("Capability Matrix matches OpenAI compat table")
except Exception as e:
    print_fail("Capability Matrix", str(e))
