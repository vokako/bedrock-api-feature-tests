"""Test 07: Prompt Caching — cache hit on a repeated large prefix.

A large shared `instructions` prefix is sent twice with the same
`prompt_cache_key`; the second call should report cached input tokens.
"""
from helpers import create, print_header, print_pass, print_fail

print_header("07", "Prompt Caching")

try:
    big = ("You are a helpful assistant with the following reference context.\n"
           + "".join(f"Fact number {i}: the value is {i * 7 % 100}.\n" for i in range(500)))
    key = "gpt56-feature-test-cache"

    first = create(instructions=big, input="Reply OK (1).", prompt_cache_key=key)
    second = create(instructions=big, input="Reply OK (2).", prompt_cache_key=key)

    d1 = first.usage.input_tokens_details
    d2 = second.usage.input_tokens_details
    print(f"  call 1: input={first.usage.input_tokens} "
          f"cache_write={d1.cache_write_tokens} cached={d1.cached_tokens}")
    print(f"  call 2: input={second.usage.input_tokens} "
          f"cache_write={d2.cache_write_tokens} cached={d2.cached_tokens}")

    assert d2.cached_tokens > 0, "second call reported no cached tokens (no cache hit)"
    print_pass("Prompt Caching")
except Exception as e:
    print_fail("Prompt Caching", str(e))
