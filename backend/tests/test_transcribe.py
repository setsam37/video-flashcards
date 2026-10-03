from app.importing.transcribe import merge_chunks,transcribe_media
from app.models import TranscriptSegment,SourceDescriptor

def test_chunk_timestamp_offsets_are_preserved():
    chunks=[(0,[TranscriptSegment(id='x',start=0,end=2,text='First')]),(600,[TranscriptSegment(id='x',start=3,end=4,text='Second')])]
    result=merge_chunks(chunks)
    assert result[1].start==603
    assert result[1].end==604
    assert result[0].id != result[1].id

def test_retry_reuses_completed_audio_chunks(tmp_path,monkeypatch):
    from app.importing import transcribe
    def extract(source,start,duration,path):path.write_bytes(b'audio')
    monkeypatch.setattr(transcribe,'extract_audio_chunk',extract)
    class Provider:
        calls=0
        def transcribe(self,path):
            self.calls+=1
            return [TranscriptSegment(id='local',start=0,end=2,text='Taught material')]
    provider=Provider();source=SourceDescriptor(lecture_id='lesson',title='Test',duration=60,source_kind='upload',media_path=str(tmp_path/'video.mp4'))
    first=transcribe_media(source,provider,tmp_path/'chunks')
    second=transcribe_media(source,provider,tmp_path/'chunks')
    assert second==first
    assert provider.calls==1
