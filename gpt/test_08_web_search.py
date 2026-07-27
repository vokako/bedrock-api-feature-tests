"""Test 08: Web Search — OpenAI built-in server-side `web_search` hosted tool.

WORKS on Bedrock, but it is gated by an IAM permission that is easy to miss:
the calling principal needs **`bedrock-websearch:*`**.

Permission trap (verified 2026-07-27): without that permission the request still
returns HTTP 200 and the model still emits `web_search_call` items, but each one
has status="failed" and no citations — there is NO AccessDenied error. That
silent failure looks exactly like "Bedrock does not support web search".

Neither `AmazonBedrockLimitedAccess` (the policy attached to console-generated
Bedrock API key users) nor `AmazonBedrockFullAccess` includes it. Grant:

    {"Effect": "Allow", "Action": "bedrock-websearch:*", "Resource": "*"}

This test PASSES when a web_search_call completes; if all calls fail it reports
the permission as the likely cause.
"""
from helpers import create, print_header, print_pass, print_fail

print_header("08", "Web Search (server-side hosted tool)")


def statuses(resp):
    return [o.status for o in resp.output if getattr(o, "type", "") == "web_search_call"]


def citations(resp):
    out = []
    for o in resp.output:
        if getattr(o, "type", "") == "message":
            for c in o.content:
                out += [a for a in (getattr(c, "annotations", None) or [])]
    return out


try:
    all_status, cited = [], []
    for tool_type in ("web_search", "web_search_preview"):
        resp = create(
            tools=[{"type": tool_type}],
            tool_choice="required",
            input="What is the current stock price of NVDA (NVIDIA)? "
                  "Use web search and cite the source URL.",
        )
        st = statuses(resp)
        cites = citations(resp)
        all_status += st
        cited += cites
        print(f"  [{tool_type}] web_search_call statuses: {st}")
        print(f"  [{tool_type}] citations: {len(cites)}")
        print(f"  [{tool_type}] text: {resp.output_text.strip()[:160]!r}")

    if any(s == "completed" for s in all_status):
        print_pass("Web Search (search executed)")
    else:
        print_fail(
            "Web Search",
            f"every web_search_call returned status={set(all_status) or 'none'} with no "
            "citations. This is the silent-failure mode: the calling principal most "
            "likely lacks the `bedrock-websearch:*` IAM permission (see module docstring)",
        )
except Exception as e:
    print_fail("Web Search", str(e))
