"""Test 08: Web Search — OpenAI built-in server-side `web_search` hosted tool.

The GPT-5.6 model cards list "Server-side tool calling" as supported. This test
checks whether the OpenAI built-in `web_search` hosted tool actually executes on
the bedrock-mantle endpoint.

Observed (2026-07-23, us-east-1/us-east-2, Terra & Sol): the API ACCEPTS the tool
and the model plans + emits `web_search_call` items, but each call comes back with
status "failed" ("web search service unavailable"). So the search never runs and
no results/citations are returned.

This matches OpenAI's official compatibility guide (feature availability as of the
2026-07-13 launch), which lists "Hosted web search" as **Not available** on Amazon
Bedrock: "Hosted tools run through OpenAI-operated service infrastructure and are
unavailable on Amazon Bedrock." So the FAIL below is EXPECTED, not a regression.
See https://developers.openai.com/api/docs/guides/amazon-bedrock

The test PASSES only if a web_search_call completes; it FAILS while the backend
search is non-functional, so it will flip to green automatically if AWS enables it.
"""
from helpers import create, print_header, print_pass, print_fail

print_header("08", "Web Search (server-side hosted tool)")


def _statuses(resp):
    return [o.status for o in resp.output if getattr(o, "type", "") == "web_search_call"]


try:
    accepted = False
    statuses = []
    for tool_type in ("web_search", "web_search_preview"):
        resp = create(
            tools=[{"type": tool_type}],
            tool_choice="required",
            input="What is the current stock price of NVDA (NVIDIA)? "
                  "Use web search and cite the source URL.",
        )
        accepted = True  # no validation error -> tool type is accepted
        st = _statuses(resp)
        statuses += st
        print(f"  [{tool_type}] output types: {[o.type for o in resp.output]}")
        print(f"  [{tool_type}] web_search_call statuses: {st}")
        print(f"  [{tool_type}] text: {resp.output_text.strip()[:200]!r}")

    completed = [s for s in statuses if s == "completed"]
    if completed:
        print_pass("Web Search (search executed)")
    else:
        assert accepted, "web_search tool type was not accepted by the API"
        print_fail(
            "Web Search",
            "tool accepted and model invoked it, but every web_search_call returned "
            f"status={set(statuses) or 'none'} — server-side search is not functional "
            "on bedrock-mantle",
        )
except Exception as e:
    print_fail("Web Search", str(e))
