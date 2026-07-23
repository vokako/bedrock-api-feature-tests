"""Test 17: Bash Tool — bash_20250124 via InvokeModel.

Bash tool is a client-side tool: model generates tool_use, client executes.
Bedrock InvokeModel accepts the tool definition and returns tool_use blocks.
Beta header: computer-use-2025-01-24
"""
from helpers import invoke, print_header, print_pass, print_fail
import json

print_header("17", "Bash Tool (bash_20250124)")

try:
    resp = invoke(
        body={
            "max_tokens": 1024,
            "tools": [
                {"type": "bash_20250124", "name": "bash"},
            ],
            "messages": [{"role": "user", "content": "Run 'echo hello' in bash."}],
        },
        beta_headers=["computer-use-2025-01-24"],
    )
    content = resp.get("content", [])
    print(f"  stop_reason: {resp.get('stop_reason')}")
    for i, b in enumerate(content):
        btype = b.get("type")
        if btype == "tool_use":
            print(f"  [{i}] tool_use: name={b['name']}, input={json.dumps(b['input'])}")
        elif btype == "text":
            print(f"  [{i}] text: \"{b.get('text', '')[:80]}\"")

    tool_uses = [b for b in content if b.get("type") == "tool_use"]
    assert len(tool_uses) > 0, "no tool_use block"
    assert tool_uses[0]["name"] == "bash"
    print_pass("Bash Tool")
except Exception as e:
    print_fail("Bash Tool", str(e))
