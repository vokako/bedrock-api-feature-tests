"""Test 14: Tool Search — tool_search_tool_regex via InvokeModel."""
from helpers import invoke, print_header, print_pass, print_fail

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
    types = [b.get("type") for b in content]
    print(f"  Content block types: {types}")
    has_search = "server_tool_use" in types or "tool_search_tool_result" in types or "tool_use" in types
    if has_search:
        print_pass("Tool Search")
    else:
        print_fail("Tool Search", f"unexpected types: {types}")
except Exception as e:
    print_fail("Tool Search", str(e))
