"""Shared helpers for GPT-5.6 (OpenAI) Responses API feature tests on Amazon Bedrock.

Access path is the `bedrock-mantle` endpoint using the OpenAI SDK:
    OPENAI_BASE_URL = https://bedrock-mantle.<region>.api.aws/openai/v1
    OPENAI_API_KEY  = <Bedrock API key>   (read from AWS_BEARER_TOKEN_BEDROCK)

Note: GPT-5.6 uses the `openai/v1` path, which differs from the plain `v1`
path used by other models (e.g. gpt-oss) on the same endpoint.
"""
import os
from openai import OpenAI

REGION = "us-east-1"
# Three GPT-5.6 tiers (launched 2026-07-13). All share the 272K context window.
TERRA = "openai.gpt-5.6-terra"  # balanced, everyday production (default)
SOL = "openai.gpt-5.6-sol"      # most capable, frontier reasoning
LUNA = "openai.gpt-5.6-luna"    # fast & affordable
MODEL_ID = TERRA


def base_url(region: str = REGION) -> str:
    return f"https://bedrock-mantle.{region}.api.aws/openai/v1"


def _api_key() -> str:
    key = os.environ.get("AWS_BEARER_TOKEN_BEDROCK") or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "No Bedrock API key found. Set AWS_BEARER_TOKEN_BEDROCK (or OPENAI_API_KEY) "
            "to a Bedrock long-term API key."
        )
    return key


def get_client(region: str = REGION) -> OpenAI:
    return OpenAI(base_url=base_url(region), api_key=_api_key())


def create(model: str = MODEL_ID, region: str = REGION, **kwargs):
    """Thin wrapper around client.responses.create."""
    return get_client(region).responses.create(model=model, **kwargs)


def output_types(resp) -> list[str]:
    return [getattr(o, "type", "?") for o in resp.output]


def print_pass(name: str):
    print(f"  ✅ PASS: {name}")


def print_fail(name: str, reason: str):
    print(f"  ❌ FAIL: {name} — {reason}")


def print_header(num: str, title: str):
    print(f"\n{'='*60}")
    print(f"  Test {num}: {title}")
    print(f"{'='*60}")
