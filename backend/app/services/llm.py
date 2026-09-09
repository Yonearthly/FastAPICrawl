from openai import APIError, APITimeoutError, AsyncOpenAI

from app.core.config import settings


class LLMConfigurationError(RuntimeError):
    pass


class LLMServiceError(RuntimeError):
    pass


async def summarize_news(title: str, content: str) -> str:
    if not settings.openai_api_key:
        raise LLMConfigurationError("尚未配置 OPENAI_API_KEY")

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=2,
    )
    prompt = (
        "请为下面的新闻生成一段客观、准确的中文摘要。保留关键人物、地点、事件和结果，"
        "不要补充原文没有的信息，控制在120至180字。\n\n"
        f"标题：{title}\n正文：{content[:7000]}"
    )
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "你是严谨的中文新闻编辑。"},
                {"role": "user", "content": prompt},
            ],
        )
    except (APIError, APITimeoutError) as exc:
        raise LLMServiceError(f"模型服务调用失败：{exc}") from exc

    summary = (response.choices[0].message.content or "").strip()
    if not summary:
        raise LLMServiceError("模型返回了空摘要")
    return summary
