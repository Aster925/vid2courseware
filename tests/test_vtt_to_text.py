from recipes.youtube_subs.vtt_to_text import vtt_to_text


def test_vtt_to_text_strips_timing_tags_and_consecutive_duplicates(tmp_path):
    vtt = tmp_path / "lesson.en.vtt"
    vtt.write_text(
        "\n".join(
            [
                "WEBVTT",
                "Kind: captions",
                "Language: en",
                "",
                "1",
                "00:00:00.000 --> 00:00:01.000",
                "<00:00:00.200><c>Hello</c> class",
                "<00:00:00.200><c>Hello</c> class",
                "",
                "2",
                "00:00:01.000 --> 00:00:02.000",
                "Next topic",
            ]
        ),
        encoding="utf-8",
    )

    assert vtt_to_text(vtt) == "Hello class Next topic"
