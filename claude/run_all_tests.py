#!/usr/bin/env python3
"""Run all Bedrock InvokeModel API feature tests sequentially."""
import subprocess
import sys
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
tests = sorted(f for f in os.listdir(SCRIPT_DIR) if f.startswith("test_") and f.endswith(".py"))

print(f"Running {len(tests)} feature tests against Bedrock InvokeModel API...")
print(f"Model: global.anthropic.claude-sonnet-4-6 | Region: us-east-1\n")

results = []
for t in tests:
    path = os.path.join(SCRIPT_DIR, t)
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True,
            cwd=SCRIPT_DIR,
            timeout=120,
        )
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        output = f"  ❌ FAIL: {t} — timeout (120s)"
    elapsed = time.time() - start
    passed = "✅ PASS" in output
    results.append((t, passed, elapsed))
    print(output.strip())
    print(f"  ⏱  {elapsed:.1f}s\n")

print("\n" + "=" * 60)
print("  SUMMARY")
print("=" * 60)
pass_count = sum(1 for _, p, _ in results if p)
fail_count = len(results) - pass_count
for name, passed, elapsed in results:
    status = "✅" if passed else "❌"
    print(f"  {status} {name} ({elapsed:.1f}s)")
print(f"\n  Total: {pass_count} passed, {fail_count} failed out of {len(results)}")
sys.exit(0 if fail_count == 0 else 1)
