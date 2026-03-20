"""Test 20: CountTokens API — Bedrock native token counting."""
import json
from helpers import REGION, ANTHROPIC_VERSION, get_client, print_header, print_pass, print_fail

print_header("20", "CountTokens API")

client = get_client()

invoke_body = json.dumps({
    "anthropic_version": ANTHROPIC_VERSION,
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "What is the capital of France?"}],
})

converse_body = {
    "messages": [{"role": "user", "content": [{"text": "What is the capital of France?"}]}],
    "system": [{"text": "You are a helpful assistant."}],
}

MODELS = [
    ("Sonnet 4.6 in-region", "anthropic.claude-sonnet-4-6"),
    ("Sonnet 4.6 global", "global.anthropic.claude-sonnet-4-6"),
    ("Opus 4.6 in-region", "anthropic.claude-opus-4-6-v1"),
    ("Sonnet 4.5", "anthropic.claude-sonnet-4-5-20250929-v1:0"),
    ("Haiku 4.5", "anthropic.claude-haiku-4-5-20251001-v1:0"),
]

for label, model_id in MODELS:
    print(f"\n  --- {label} ({model_id}) ---")
    for fmt, inp in [
        ("InvokeModel", {"invokeModel": {"body": invoke_body}}),
        ("Converse", {"converse": converse_body}),
    ]:
        try:
            resp = client.count_tokens(modelId=model_id, input=inp)
            print(f"    {fmt}: inputTokens={resp['inputTokens']}")
            print_pass(f"{label} {fmt}")
        except Exception as e:
            err = str(e)
            if "doesn't support" in err:
                print(f"    {fmt}: not supported (global/cross-region ID)")
                print_pass(f"{label} {fmt} — expected rejection for non-in-region ID")
            else:
                print_fail(f"{label} {fmt}", err[:150])
