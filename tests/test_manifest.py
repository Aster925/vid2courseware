from core.manifest import fingerprint


def test_fingerprint_matches_identical_head_tail_content(tmp_path):
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    payload = b"head-bytes" + (b"x" * 128) + b"tail-bytes"
    first.write_bytes(payload)
    second.write_bytes(payload)

    assert fingerprint(first, first.stat().st_size) == fingerprint(second, second.stat().st_size)


def test_fingerprint_uses_tail_content_for_same_sized_files(tmp_path, monkeypatch):
    monkeypatch.setattr("core.manifest.HEAD_TAIL", 8)
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    first.write_bytes(b"samehead" + b"a" * 16 + b"tail-one")
    second.write_bytes(b"samehead" + b"a" * 16 + b"tail-two")

    assert first.stat().st_size == second.stat().st_size
    assert fingerprint(first, first.stat().st_size) != fingerprint(second, second.stat().st_size)
