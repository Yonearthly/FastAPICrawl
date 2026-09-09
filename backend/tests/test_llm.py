import asyncio
from types import SimpleNamespace

from app.services import llm


def test_summary_request_uses_model_default_temperature(monkeypatch):
    captured = {}

    class FakeCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            message = SimpleNamespace(content="这是一段测试摘要。")
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(llm.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(llm, "AsyncOpenAI", FakeClient)

    result = asyncio.run(llm.summarize_news("标题", "新闻正文"))

    assert result == "这是一段测试摘要。"
    assert "temperature" not in captured
