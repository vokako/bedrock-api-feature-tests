"""Test 06: Vision — image input (multimodal) via Responses API.

Uses a locally-generated solid-red PNG so the test needs no network fetch
beyond the Bedrock endpoint itself.
"""
from helpers import create, print_header, print_pass, print_fail
import base64, struct, zlib

print_header("06", "Vision (Image Input)")


def solid_png(w: int, h: int, rgb: tuple[int, int, int]) -> bytes:
    def chunk(typ: bytes, data: bytes) -> bytes:
        body = typ + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


try:
    b64 = base64.b64encode(solid_png(64, 64, (220, 20, 20))).decode()
    resp = create(input=[{"role": "user", "content": [
        {"type": "input_text", "text": "What is the dominant color of this image? Answer with one word."},
        {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"},
    ]}])
    text = resp.output_text.strip()
    print(f"  response: \"{text}\"")

    assert "red" in text.lower(), f"model did not identify red: {text!r}"
    print_pass("Vision (Image Input)")
except Exception as e:
    print_fail("Vision (Image Input)", str(e))
