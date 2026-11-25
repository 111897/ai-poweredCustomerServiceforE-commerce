from app.segmenter.splitter import Segmenter


def test_segments_never_exceed_limit():
    text = "第一句话。" * 10
    segmenter = Segmenter(20)
    output: list[str] = []
    for char in text:
        output.extend(segmenter.feed(char))
    output.extend(segmenter.flush())

    assert output
    assert all(len(segment) <= 20 for segment in output)
    assert "".join(output) == text


def test_newline_splits_early():
    segmenter = Segmenter(200)
    assert segmenter.feed("第一行\n第二行") == ["第一行"]
    assert segmenter.flush() == ["第二行"]


def test_flush_empty_buffer():
    assert Segmenter(200).flush() == []
