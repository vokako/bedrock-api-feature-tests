"""Test 25: Cross-model feature matrix (incl. Claude Opus 5).

Exercises the documented feature set against every modern Claude model on
`bedrock-runtime` and prints a matrix. This is the script behind the table in
ANTHROPIC_API_ON_BEDROCK_*.md §1.

Legend:
  Y   accepted & the feature was observed working
  y   accepted, but the feature was not exercised this run
      (adaptive thinking may legitimately choose not to think)
  .   rejected by the API (400 ValidationException) — i.e. unsupported
  E   other error

Methodology notes (each of these was a bug in an earlier version of this test):
  - the image must be a *valid* PNG or every model 400s on `vision`
  - `tool_search` tool `name` must equal the canonical tool name
  - a mid-conversation `role:system` message must precede an assistant message
    or end the array, otherwise even supporting models reject it
  - "no thinking block" is NOT the same as "thinking rejected"
  - `eager_input_streaming` goes INSIDE the tool definition, not at body top level

PASSES when every model answers a basic invocation and no unexpected (E) errors
occur; the matrix itself is the artifact to read.
"""
import json

import boto3

from helpers import ANTHROPIC_VERSION, REGION, print_fail, print_header, print_pass

rt = boto3.client("bedrock-runtime", region_name=REGION)

# valid 1x1 red PNG
RED = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+h"
       "HgAHggJ/PchI7wAAAABJRU5ErkJggg==")

MODELS = [
    ("Opus5", "global.anthropic.claude-opus-5"),
    ("Son5", "global.anthropic.claude-sonnet-5"),
    ("Fable5", "global.anthropic.claude-fable-5"),
    ("Opus4.8", "global.anthropic.claude-opus-4-8"),
    ("Opus4.7", "global.anthropic.claude-opus-4-7"),
    ("Opus4.6", "global.anthropic.claude-opus-4-6-v1"),
    ("Son4.6", "global.anthropic.claude-sonnet-4-6"),
    ("Haiku4.5", "global.anthropic.claude-haiku-4-5-20251001-v1:0"),
]

print_header("25", "Cross-model feature matrix (incl. Opus 5)")

rejections = {}
unexpected = []


def call(model, body):
    resp = rt.invoke_model(modelId=model, contentType="application/json",
                           body=json.dumps({"anthropic_version": ANTHROPIC_VERSION, **body}))
    return json.loads(resp["body"].read())


def row(name, body_fn, verify=None):
    cells = []
    for label, mid in MODELS:
        try:
            out = call(mid, body_fn(mid))
            cells.append("Y" if (verify is None or verify(out)) else "y")
        except Exception as e:
            msg = str(e)
            if "ValidationException" in msg:
                cells.append(".")
                rejections.setdefault(name, {})[label] = \
                    msg.split("InvokeModel operation: ")[-1][:100]
            else:
                cells.append("E")
                unexpected.append(f"{name}/{label}: {msg[:120]}")
    print(f"  {name:32s} " + " ".join(f"{c:^8s}" for c in cells))
    return cells


print("\n  " + " " * 32 + " ".join(f"{l:^8s}" for l, _ in MODELS))
print("  " + "-" * (32 + 9 * len(MODELS)))

basic = row("basic invocation",
            lambda m: {"max_tokens": 16,
                       "messages": [{"role": "user", "content": "hi"}]},
            lambda o: bool(o["content"]))

row("adaptive thinking",
    lambda m: {"max_tokens": 6000, "thinking": {"type": "adaptive"},
               "output_config": {"effort": "high"},
               "messages": [{"role": "user",
                             "content": "Prove sqrt(2) is irrational, step by step."}]},
    lambda o: any(b.get("type") == "thinking" for b in o["content"]))

row("legacy thinking (budget_tokens)",
    lambda m: {"max_tokens": 3000,
               "thinking": {"type": "enabled", "budget_tokens": 2000},
               "messages": [{"role": "user", "content": "What is 23*47? think."}]},
    lambda o: any(b.get("type") == "thinking" for b in o["content"]))

row("sampling temperature",
    lambda m: {"max_tokens": 16, "temperature": 0.5,
               "messages": [{"role": "user", "content": "hi"}]})

row("structured out (output_config)",
    lambda m: {"max_tokens": 256,
               "messages": [{"role": "user", "content": "John is 30, lives in Tokyo."}],
               "output_config": {"format": {"type": "json_schema", "schema": {
                   "type": "object",
                   "properties": {"name": {"type": "string"},
                                  "age": {"type": "integer"},
                                  "city": {"type": "string"}},
                   "required": ["name", "age", "city"],
                   "additionalProperties": False}}}},
    lambda o: "John" in "".join(b.get("text", "") for b in o["content"]))

row("mid-conv system (at array end)",
    lambda m: {"max_tokens": 48, "messages": [
        {"role": "user", "content": "say hello"},
        {"role": "system", "content": "Reply only in uppercase."}]},
    lambda o: bool(o["content"]))

row("assistant prefill",
    lambda m: {"max_tokens": 24, "messages": [
        {"role": "user", "content": "Name a color."},
        {"role": "assistant", "content": "The color is"}]})

row("vision (image input)",
    lambda m: {"max_tokens": 48, "messages": [{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                     "data": RED}},
        {"type": "text", "text": "What color? one word."}]}]},
    lambda o: bool("".join(b.get("text", "") for b in o["content"])))

row("tool use (function calling)",
    lambda m: {"max_tokens": 256,
               "tools": [{"name": "get_weather", "description": "weather",
                          "input_schema": {"type": "object",
                                           "properties": {"city": {"type": "string"}},
                                           "required": ["city"]}}],
               "messages": [{"role": "user", "content": "weather in Tokyo?"}]},
    lambda o: any(b.get("type") == "tool_use" for b in o["content"]))

row("citations (documents)",
    lambda m: {"max_tokens": 300, "messages": [{"role": "user", "content": [
        {"type": "document",
         "source": {"type": "text", "media_type": "text/plain",
                    "data": "The sky is blue due to Rayleigh scattering."},
         "citations": {"enabled": True}},
        {"type": "text", "text": "Why is the sky blue?"}]}]},
    lambda o: any(b.get("citations") for b in o["content"] if b.get("type") == "text"))

row("prompt caching",
    lambda m: {"max_tokens": 16,
               "system": [{"type": "text", "text": "Helpful. " + ("filler word " * 500),
                           "cache_control": {"type": "ephemeral"}}],
               "messages": [{"role": "user", "content": "hi"}]},
    lambda o: o.get("usage", {}).get("cache_creation_input_tokens", 0) > 0)

row("bash tool",
    lambda m: {"max_tokens": 256, "tools": [{"type": "bash_20250124", "name": "bash"}],
               "messages": [{"role": "user", "content": "list files in /tmp"}]})

row("text_editor tool",
    lambda m: {"max_tokens": 256,
               "tools": [{"type": "text_editor_20250728",
                          "name": "str_replace_based_edit_tool"}],
               "messages": [{"role": "user", "content": "view /tmp/x"}]})

row("memory tool",
    lambda m: {"max_tokens": 256,
               "tools": [{"type": "memory_20250818", "name": "memory"}],
               "messages": [{"role": "user", "content": "remember x=1"}]})

row("tool_search (regex)",
    lambda m: {"max_tokens": 1024, "tools": [
        {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},
        {"name": "get_weather", "description": "Get weather for a location",
         "input_schema": {"type": "object",
                          "properties": {"location": {"type": "string"}},
                          "required": ["location"]},
         "defer_loading": True}],
        "messages": [{"role": "user", "content": "weather in Paris?"}]},
    lambda o: any(b.get("type") == "server_tool_use" for b in o["content"]))

row("web_search (native)",
    lambda m: {"max_tokens": 512,
               "tools": [{"type": "web_search_20250305", "name": "web_search"}],
               "messages": [{"role": "user", "content": "NVDA price?"}]})

print("\n  Y=works  y=accepted but not exercised  .=rejected(400)  E=other error")

print("\n  representative rejection messages:")
for feature, per_model in rejections.items():
    grouped = {}
    for label, msg in per_model.items():
        grouped.setdefault(msg, []).append(label)
    for msg, labels in grouped.items():
        print(f"    {feature} [{','.join(labels)}]: {msg}")

try:
    assert all(c == "Y" for c in basic), "some model failed basic invocation"
    assert not unexpected, f"unexpected errors: {unexpected[:3]}"
    print()
    print_pass("Cross-model matrix collected (see table above)")
except Exception as e:
    print()
    print_fail("Cross-model matrix", str(e))
