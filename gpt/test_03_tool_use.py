"""Test 03: Client-side Tool Use — function calling via Responses API."""
from helpers import create, output_types, print_header, print_pass, print_fail

print_header("03", "Client-side Tool Use (Function Calling)")

try:
    resp = create(
        tools=[{
            "type": "function",
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        }],
        input="What's the weather in Tokyo?",
    )
    print(f"  output types: {output_types(resp)}")
    calls = [o for o in resp.output if o.type == "function_call"]
    for c in calls:
        print(f"    function_call: name={c.name} arguments={c.arguments}")

    assert len(calls) > 0, "no function_call in output"
    assert calls[0].name == "get_weather"
    print_pass("Client-side Tool Use")
except Exception as e:
    print_fail("Client-side Tool Use", str(e))
