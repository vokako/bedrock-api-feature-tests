"""Test 07: Vision — image input via base64."""
from helpers import invoke, print_header, print_pass, print_fail

print_header("07", "Vision (Multimodal Image)")

# 1x1 red PNG
RED_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

try:
    resp = invoke({
        "max_tokens": 128,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": RED_PNG_B64}},
                {"type": "text", "text": "What color is this image? Reply in one word."},
            ],
        }],
    })
    text = resp["content"][0].get("text", "")
    print(f"  Response: {text[:80]}")
    assert len(text) > 0, "empty response"
    print_pass("Vision")
except Exception as e:
    print_fail("Vision", str(e))
