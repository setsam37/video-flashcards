import pytest
from app.storage import Repository
from app.models import SourceDescriptor

@pytest.fixture
def repo(tmp_path):
    repository = Repository(tmp_path / 'study.sqlite')
    repository.save_source(SourceDescriptor(lecture_id='lesson',title='Synthetic test lesson',duration=600,source_kind='upload',media_path='/private/lesson.mp4'))
    return repository
