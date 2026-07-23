"""Test 02: Streaming — Responses API server-sent events."""
from helpers import get_client, MODEL_ID, print_header, print_pass, print_fail

print_header("02", "Streaming (Responses API SSE)")

try:
    stream = get_client().responses.create(
        model=MODEL_ID,
        input="Count from 1 to 5.",
        stream=True,
    )
    events = []
    text = ""
    for ev in stream:
        events.append(ev.type)
        if ev.type == "response.output_text.delta":
            text += ev.delta

    print(f"  Total events: {len(events)}")
    print(f"  Distinct event types: {sorted(set(events))}")
    print(f"  Reconstructed text: \"{text.strip()}\"")

    assert "response.created" in events, "missing response.created"
    assert "response.output_text.delta" in events, "missing text deltas"
    assert "response.completed" in events, "missing response.completed"
    assert len(text) > 0, "no streamed text"
    print_pass("Streaming")
except Exception as e:
    print_fail("Streaming", str(e))
