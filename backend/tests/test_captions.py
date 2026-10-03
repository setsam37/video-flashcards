import pytest
from app.importing.captions import parse_captions
from app.errors import ProcessingError

def test_rolling_captions_preserve_words_once():
    result=parse_captions('WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nA load balancer\n\n00:00:02.000 --> 00:00:05.000\nA load balancer distributes requests.\n','vtt')
    assert ' '.join(s.text for s in result)=='A load balancer distributes requests.'
    assert result[0].start == 1
    assert result[-1].end == 5

def test_genuine_later_repetition_is_kept():
    result=parse_captions('1\n00:00:01,000 --> 00:00:02,000\nRecall this.\n\n2\n00:00:10,000 --> 00:00:11,000\nRecall this.\n','srt')
    assert len(result)==2

def test_invalid_transcript_does_not_look_successful():
    with pytest.raises(ProcessingError):parse_captions('no timestamped content','srt')
