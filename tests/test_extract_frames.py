from pathlib import Path

from PIL import Image

from core.extract_frames import ahash, hamming


def _half_image(path: Path, *, inverted: bool = False) -> None:
    img = Image.new("L", (64, 64), color=0 if not inverted else 255)
    pixels = img.load()
    for x in range(32, 64):
        for y in range(64):
            pixels[x, y] = 255 if not inverted else 0
    img.save(path)


def test_average_hash_changes_for_synthetic_frame_shift(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    _half_image(first)
    _half_image(second, inverted=True)

    first_hash = ahash(first, crop=[0.0, 0.0, 1.0, 1.0], n=8)
    second_hash = ahash(second, crop=[0.0, 0.0, 1.0, 1.0], n=8)

    assert hamming(first_hash, first_hash) == 0
    assert hamming(first_hash, second_hash) == 64
