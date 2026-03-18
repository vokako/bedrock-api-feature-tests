"""Test 18: Text Editor Tool — text_editor_20250728 via InvokeModel.

Text editor tool is a client-side tool: model generates tool_use, client executes.
Bedrock InvokeModel accepts the tool definition and returns tool_use blocks.
Note: Bedrock requires name='str_replace_based_edit_tool' (not 'text_editor').
Beta header: computer-use-2025-01-24
"""
from helpers import invoke, print_header, print_pass, print_fail
import json

print_header("18", "Text Editor Tool (text_editor_20250728)")

try:
    resp = invoke(
        body={
            "max_tokens": 1024,
            "tools": [
                {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"},
            ],
            "messages": [{"role": "user", "content": "Create a file called test.txt with content 'hello world'."}],
        },
        beta_headers=["computer-use-2025-01-24"],
    )
    content = resp.get("content", [])
    print(f"  stop_reason: {resp.get('stop_reason')}")
    for i, b in enumerate(content):
        btype = b.get("type")
        if btype == "tool_use":
            print(f"  [{i}] tool_use: name={b['name']}, input={json.dumps(b['input'])[:150]}")
        elif btype == "text":
            print(f"  [{i}] text: \"{b.get('text', '')[:80]}\"")

    tool_uses = [b for b in content if b.get("type") == "tool_use"]
    assert len(tool_uses) > 0, "no tool_use block"
    assert tool_uses[0]["name"] == "str_replace_based_edit_tool"
    print_pass("Text Editor Tool")
except Exception as e:
    print_fail("Text Editor Tool", str(e))
