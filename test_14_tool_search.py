"""Test 14: Tool Search — tool_search_tool_regex via InvokeModel."""
from helpers import invoke, print_header, print_pass, print_fail
import json

print_header("14", "Tool Search (tool_search_tool_regex)")

try:
    resp = invoke(
        body={
            "max_tokens": 1024,
            "tools": [
                {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},
                {
                    "name": "get_weather",
                    "description": "Get weather for a location",
                    "input_schema": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"],
                    },
                    "defer_loading": True,
                },
                {
                    "name": "search_files",
                    "description": "Search through files in the workspace",
                    "input_schema": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                    "defer_loading": True,
                },
            ],
            "messages": [{"role": "user", "content": "What is the weather in San Francisco?"}],
        },
        beta_headers=["tool-search-tool-2025-10-19"],
    )
    content = resp.get("content", [])
    print(f"  stop_reason: {resp.get('stop_reason')}")
    print(f"  content blocks ({len(content)}):")
    for i, b in enumerate(content):
        btype = b.get("type")
        if btype == "text":
            print(f"    [{i}] text: \"{b.get('text', '')[:80]}\"")
        elif btype == "server_tool_use":
            print(f"    [{i}] server_tool_use: name={b.get('name')}, input={json.dumps(b.get('input', {}))}")
        elif btype == "tool_search_tool_result":
            refs = b.get("content", {}).get("tool_references", [])
            ref_names = [r.get("tool_name") for r in refs]
            print(f"    [{i}] tool_search_tool_result: found tools={ref_names}")
        elif btype == "tool_use":
            print(f"    [{i}] tool_use: name={b['name']}, input={json.dumps(b['input'])}")

    types = [b.get("type") for b in content]
    has_search = "server_tool_use" in types or "tool_search_tool_result" in types or "tool_use" in types
    if has_search:
        print_pass("Tool Search")
    else:
        print_fail("Tool Search", f"unexpected types: {types}")
except Exception as e:
    print_fail("Tool Search", str(e))
