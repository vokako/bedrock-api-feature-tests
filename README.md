# Bedrock InvokeModel API Feature Tests

Verify Anthropic API features on AWS Bedrock using InvokeModel / InvokeModelWithResponseStream API.

## Prerequisites

- Python 3.12+
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- Access to `global.anthropic.claude-sonnet-4-6` in `us-east-1`

## Setup

```bash
uv sync
```

## Run all tests

```bash
uv run python run_all_tests.py
```

## Run a single test

```bash
uv run python test_01_messages_basic.py
```

## Test List

| # | Test | Feature | Beta Header |
|---|------|---------|-------------|
| 01 | `test_01_messages_basic.py` | Messages API Basic | — |
| 02 | `test_02_streaming.py` | Streaming (SSE) | — |
| 03 | `test_03_tool_use.py` | Tool Use (Function Calling) | — |
| 04 | `test_04_extended_thinking.py` | Extended Thinking | — |
| 05 | `test_05_interleaved_thinking.py` | Interleaved Thinking | `interleaved-thinking-2025-05-14` |
| 06 | `test_06_prompt_caching.py` | Prompt Caching | — |
| 07 | `test_07_vision.py` | Vision (Multimodal Image) | — |
| 08 | `test_08_pdf_support.py` | PDF Support | — |
| 09 | `test_09_citations.py` | Citations | — |
| 10 | `test_10_structured_outputs.py` | Structured Outputs | — |
| 11 | `test_11_eager_input_streaming.py` | Fine-grained Tool Streaming | — (`eager_input_streaming` field) |
| 12 | `test_12_compaction.py` | Compaction | `compact-2026-01-12` |
| 13 | `test_13_context_editing.py` | Context Editing | `context-management-2025-06-27` |
| 14 | `test_14_tool_search.py` | Tool Search | `tool-search-tool-2025-10-19` |
| 15 | `test_15_tool_input_examples.py` | Tool Input Examples | `tool-examples-2025-10-29` |
| 16 | `test_16_adaptive_thinking.py` | Adaptive Thinking | — (`thinking.type: "adaptive"` + `effort`) |

## Configuration

Edit `helpers.py` to change:
- `REGION` — AWS region (default: `us-east-1`)
- `MODEL_ID` — Bedrock model ID (default: `global.anthropic.claude-sonnet-4-6`)
