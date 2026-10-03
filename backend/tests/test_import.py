import json,subprocess,sys
import pytest
from app.importing.youtube import canonical_youtube,import_youtube
from app.importing.media import probe_media
from app.errors import ProcessingError
from app.config import Config

@pytest.mark.parametrize('url',['https://example.com/watch?v=C842vFY5kRo','https://youtube.com.evil.test/watch?v=C842vFY5kRo','https://youtube.com/playlist?list=123'])
def test_nonvideo_and_non_youtube_urls_rejected(url):
    with pytest.raises(ProcessingError):canonical_youtube(url)

def test_youtube_url_is_canonicalized_without_tracking():
    assert canonical_youtube('https://youtu.be/C842vFY5kRo?t=40')==('C842vFY5kRo','https://www.youtube.com/watch?v=C842vFY5kRo')

def test_video_without_audio_is_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:subprocess.CompletedProcess(a[0],0,json.dumps({'format':{'format_name':'mov,mp4','duration':'5'},'streams':[{'codec_type':'video'}]}),''))
    with pytest.raises(ProcessingError,match='audio'):probe_media(tmp_path/'test.mp4','lesson',Config(ffprobe_path=sys.executable))

def test_missing_captions_have_explicit_fallback(monkeypatch):
    import yt_dlp
    monkeypatch.setattr(yt_dlp.YoutubeDL,'extract_info',lambda *a,**k:{'id':'C842vFY5kRo','title':'Test video','duration':600,'chapters':[],'subtitles':{},'automatic_captions':{}})
    source,segments=import_youtube('https://youtu.be/C842vFY5kRo','lesson')
    assert source.youtube_id=='C842vFY5kRo'
    assert segments is None
