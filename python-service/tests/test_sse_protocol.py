import json

from app.streaming.protocol import segment_frames


def test_segment_frames_are_consistent():
    frames = segment_frames(1, "你好", "auto")

    assert len(frames) == 3
    assert frames[0].startswith("event: segment")
    assert frames[1].startswith("event: delta")
    assert frames[2].startswith("event: segment_end")

    payload = json.loads(frames[1].split("data: ", 1)[1])
    assert payload == {"content": "你好"}
    length = json.loads(frames[2].split("data: ", 1)[1])["length"]
    assert length == 2
