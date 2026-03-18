"""Probe all known Anthropic beta headers and tool types on Bedrock InvokeModel."""
import boto3
import json

REGION = "us-east-1"
MODEL_ID = "global.anthropic.claude-sonnet-4-6"
VERSION = "bedrock-2023-05-31"

client = boto3.client("bedrock-runtime", region_name=REGION)


def try_invoke(label, body):
    try:
        resp = client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            body=json.dumps(body),
        )
        r = json.loads(resp["body"].read())
        types = [b.get("type") for b in r.get("content", [])]
        print(f"  ✅ {label} — content types: {types}")
        return True
    except Exception as e:
        err = str(e)
        # Extract just the key error message
        if "ValidationException" in err:
            msg = err.split("ValidationException) when calling the InvokeModel operation: ")[-1][:150]
        else:
            msg = err[:150]
        print(f"  ❌ {label} — {msg}")
        return False


print("=" * 70)
print("  PART 1: Computer Use tool types + beta headers")
print("=" * 70)

# All known computer-use related beta headers
cu_betas = [
    "computer-use-2025-01-24",
    "computer-use-2024-10-22",
]

# All known computer use tool type versions
cu_tool_types = [
    "computer_20250124",
    "computer_20241022",
]

for beta in cu_betas:
    for tool_type in cu_tool_types:
        body = {
            "anthropic_version": VERSION,
            "anthropic_beta": [beta],
            "max_tokens": 256,
            "tools": [{
                "type": tool_type,
                "name": "computer",
                "display_width_px": 1024,
                "display_height_px": 768,
                "display_number": 1,
            }],
            "messages": [{"role": "user", "content": "Click center of screen."}],
        }
        try_invoke(f"beta={beta}, tool={tool_type}", body)

print()
print("=" * 70)
print("  PART 2: Bash tool type versions")
print("=" * 70)

bash_types = ["bash_20250124", "bash_20241022"]
for beta in cu_betas:
    for tool_type in bash_types:
        body = {
            "anthropic_version": VERSION,
            "anthropic_beta": [beta],
            "max_tokens": 256,
            "tools": [{"type": tool_type, "name": "bash"}],
            "messages": [{"role": "user", "content": "Run echo hello"}],
        }
        try_invoke(f"beta={beta}, tool={tool_type}", body)

print()
print("=" * 70)
print("  PART 3: Text editor tool type versions")
print("=" * 70)

te_combos = [
    ("text_editor_20250728", "str_replace_based_edit_tool"),
    ("text_editor_20250124", "str_replace_editor"),
    ("text_editor_20250124", "str_replace_based_edit_tool"),
    ("text_editor_20250124", "text_editor"),
    ("text_editor_20241022", "str_replace_editor"),
]
for beta in cu_betas:
    for tool_type, name in te_combos:
        body = {
            "anthropic_version": VERSION,
            "anthropic_beta": [beta],
            "max_tokens": 256,
            "tools": [{"type": tool_type, "name": name}],
            "messages": [{"role": "user", "content": "Create file test.txt with hello"}],
        }
        try_invoke(f"beta={beta}, tool={tool_type}, name={name}", body)

print()
print("=" * 70)
print("  PART 4: Other Anthropic beta headers (acceptance test)")
print("=" * 70)

other_betas = [
    ("interleaved-thinking-2025-05-14", "Interleaved Thinking"),
    ("compact-2026-01-12", "Compaction"),
    ("context-management-2025-06-27", "Context Editing"),
    ("fine-grained-tool-streaming-2025-05-14", "Fine-grained Tool Streaming (legacy beta)"),
    ("prompt-caching-scope-2026-01-05", "Prompt Caching Scope"),
    ("redact-thinking-2026-02-12", "Redact Thinking"),
    ("files-api-2025-04-14", "Files API"),
    ("mcp-client-2025-11-20", "MCP Connector"),
    ("code-execution-2025-05-22", "Code Execution (legacy)"),
    ("code-execution-2025-08-25", "Code Execution"),
    ("max-tokens-3-5-sonnet-2024-07-15", "Max Tokens 3.5 Sonnet"),
    ("token-counting-2024-11-01", "Token Counting"),
    ("message-batches-2024-09-24", "Message Batches"),
    ("pdfs-2024-09-25", "PDFs (legacy)"),
    ("output-128k-2025-02-19", "Output 128k"),
    ("web-search-2025-03-05", "Web Search"),
    ("web-fetch-2025-09-10", "Web Fetch"),
    ("tool-examples-2025-10-29", "Tool Examples"),
    ("tool-search-tool-2025-10-19", "Tool Search"),
    ("advanced-tool-use-2025-11-20", "Advanced Tool Use"),
]

for beta, label in other_betas:
    body = {
        "anthropic_version": VERSION,
        "anthropic_beta": [beta],
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "Say hi."}],
    }
    try_invoke(f"{label} ({beta})", body)
