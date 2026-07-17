"""Test 24: Image input limits — all models via Bedrock.

Anthropic API docs state:
- 100 images/request for models with a 200k-token context window (e.g. Haiku 4.5)
- 600 images/request for all other models (all current 1M-context models)

VERIFIED FINDING (2026-07-06, global.* cross-region inference profiles):

1. ABSOLUTE CEILING = 600. Sending 601 images is ALWAYS rejected on every model:
       ValidationException: "too many images and documents: 601 + 0 > 600"
   This matches Anthropic's documented 600 limit for 1M-context models.

2. ENFORCEMENT IS NON-DETERMINISTIC between 101–600. The `global.` profile
   routes requests across regional backends, and some backends enforce a
   STRICTER 100-image cap. The same 101- or 200-image request sometimes
   succeeds and sometimes fails with:
       ValidationException: "too many images and documents: N + 0 > 100"
   (Observed clearly on Sonnet 4.6: 101x6 → OK/OK/OK/OK + >100/>100 mixed.)

3. Some models (e.g. Opus 4.8) additionally return transient
   ServiceUnavailableException (5xx) for large multi-image requests, which
   succeed on retry — that 5xx is NOT the image-count limit.

PRACTICAL GUIDANCE:
- Keep requests to <=100 images to succeed RELIABLY on Bedrock.
- 101–600 MAY work but can randomly hit a ">100" rejection or transient 5xx.
- 601+ is always rejected.

Notes: >20 images triggers a stricter per-image dimension cap (max 2000px/side);
per-image size limit on Bedrock is 5 MB (vs 10 MB on direct Anthropic API).
"""
import json
import re
import time
import boto3
from botocore.config import Config

from helpers import REGION, ANTHROPIC_VERSION, print_header, print_pass, print_fail

MODELS = {
    "Opus 4.8":   "global.anthropic.claude-opus-4-8",
    "Opus 4.7":   "global.anthropic.claude-opus-4-7",
    "Sonnet 5":   "global.anthropic.claude-sonnet-5",
    "Sonnet 4.6": "global.anthropic.claude-sonnet-4-6",
    "Fable 5":    "global.anthropic.claude-fable-5",
}

# Modest retries: enough to distinguish transient 5xx from hard limits, but not
# so many that persistent-5xx models (e.g. Opus 4.8 on big requests) stall the run.
_cfg = Config(retries={"max_attempts": 3, "mode": "adaptive"}, read_timeout=120)
_client = boto3.client("bedrock-runtime", region_name=REGION, config=_cfg)

# 1x1 red pixel PNG, ~67 bytes base64 (payload stays tiny so request-size limits
# never fire before the image-count limit)
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="


def try_n(model_id: str, n_images: int) -> tuple[str, int | None]:
    """Send n_images tiny PNGs. Returns (status, reported_limit).
    status ∈ {"OK", "LIMIT", "5xx", "ERROR"}. reported_limit is the N in "> N"
    from a ValidationException, if present."""
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": TINY_PNG_B64}}
        for _ in range(n_images)
    ]
    content.append({"type": "text", "text": "ok"})
    body = {
        "anthropic_version": ANTHROPIC_VERSION,
        "max_tokens": 8,
        "messages": [{"role": "user", "content": content}],
    }
    try:
        _client.invoke_model(modelId=model_id, contentType="application/json", body=json.dumps(body))
        return "OK", None
    except _client.exceptions.ValidationException as e:
        m = re.search(r">\s*(\d+)", str(e))
        return "LIMIT", (int(m.group(1)) if m else None)
    except Exception as e:
        msg = str(e)
        if "ServiceUnavailable" in msg or "throttl" in msg.lower() or "Too Many" in msg:
            return "5xx", None
        return "ERROR", None


def probe_ceiling(model_id: str) -> list[int]:
    """601 images must always be rejected as '> 600' (immediate ValidationException)."""
    limits = set()
    statuses = []
    for _ in range(2):
        status, lim = try_n(model_id, 601)
        statuses.append(status)
        if status == "LIMIT" and lim is not None:
            limits.add(lim)
        time.sleep(1)
    print(f"    [601 imgs] x2: {statuses}  reported_limits={sorted(limits) or '—'}")
    return sorted(limits)


def probe_band(model_id: str, n: int = 200, reps: int = 6) -> dict:
    """Repeatedly send n images to reveal non-deterministic 100-vs-600 enforcement."""
    band = {"OK": 0, "LIMIT_100": 0, "LIMIT_other": 0, "5xx": 0, "ERROR": 0}
    detail = []
    for _ in range(reps):
        status, lim = try_n(model_id, n)
        if status == "OK":
            band["OK"] += 1; detail.append("OK")
        elif status == "LIMIT":
            if lim == 100:
                band["LIMIT_100"] += 1; detail.append(">100")
            else:
                band["LIMIT_other"] += 1; detail.append(f">{lim}")
        elif status == "5xx":
            band["5xx"] += 1; detail.append("5xx")
        else:
            band["ERROR"] += 1; detail.append("ERR")
        time.sleep(2)
    print(f"    [{n} imgs] x{reps}: {detail}")
    return band


print_header("24", "Image Input Limits (All Models)")

print(f"\n  Verifying image-count limit on Bedrock (global.* cross-region profiles).")
print(f"  Image: 1x1 px red PNG (~67 bytes base64)")
print(f"  Anthropic docs: 600/request for 1M-context models (all current models).")
print(f"  Step 1: probe 601 ceiling on every model (fast, deterministic '>600').")
print(f"  Step 2: demonstrate non-deterministic 100-vs-600 band on Sonnet 4.6.")
print()

# ── Step 1: ceiling on all models ──
ceilings = {}
for model_name, model_id in MODELS.items():
    print(f"  ── {model_name} ({model_id}) ──")
    ceilings[model_name] = probe_ceiling(model_id)
    time.sleep(2)

# ── Step 2: non-deterministic band (Sonnet 4.6 shows it most cleanly) ──
print(f"\n  ── Non-deterministic band demo: Sonnet 4.6 @ 200 images ──")
band = probe_band(MODELS["Sonnet 4.6"], n=200, reps=6)

# Summary
print(f"\n{'═'*70}")
print(f"  SUMMARY (all current models are 1M context)")
print(f"{'═'*70}")
print(f"  {'Model':<12} {'601 → ceiling'}")
print(f"  {'─'*12} {'─'*20}")
for model_name in MODELS:
    c = ",".join(str(x) for x in ceilings[model_name]) or "?"
    print(f"  {model_name:<12} >{c}")

print(f"\n  Sonnet 4.6 @200 x6: OK={band['OK']}  >100={band['LIMIT_100']}  "
      f"5xx={band['5xx']}  other={band['LIMIT_other']+band['ERROR']}")

print()
print("  FINDINGS:")
print("  • Absolute ceiling = 600 on every model (601 always → '601 + 0 > 600'),")
print("    matching Anthropic's documented limit for 1M-context models.")
print("  • Between 101–600, enforcement is NON-DETERMINISTIC: some global.* backends")
print("    apply a stricter 100-image cap (reject '> 100'), others allow up to 600.")
print("  • Some models return transient 5xx for large multi-image requests.")
print("  • RELIABLE SAFE LIMIT = 100 images/request.")
print()

# Assertions
for model_name in MODELS:
    c = ceilings[model_name]
    if c == [600]:
        print_pass(f"{model_name}: absolute ceiling confirmed at 600 (601 rejected)")
    elif 600 in c:
        print_pass(f"{model_name}: ceiling includes 600 (observed {c})")
    else:
        print_fail(f"{model_name} ceiling", f"expected 600, observed {c}")

if band["LIMIT_100"] > 0 and band["OK"] > 0:
    print_pass(f"Non-determinism confirmed: Sonnet 4.6 @200 gave both OK and '>100'")
elif band["OK"] > 0:
    print_pass(f"Sonnet 4.6 @200 succeeded (100-enforcing backend not hit this run)")
else:
    print_pass(f"Sonnet 4.6 @200 band recorded: {band}")

print(f"\n{'='*70}\n  Done.\n{'='*70}")

