import os,pytest
from app.providers.openai_provider import OpenAIProvider,SupportOutput

@pytest.mark.skipif(os.environ.get('RUN_LIVE_TESTS')!='1',reason='Real API calls are opt-in: set RUN_LIVE_TESTS=1; consumes provider credits.')
def test_real_structured_provider_connection():
    assert OpenAIProvider()._parse('Return supported=true.',{'purpose':'connection verification'},SupportOutput).supported
