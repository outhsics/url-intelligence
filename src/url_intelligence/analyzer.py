from __future__ import annotations

from openai import OpenAI

from url_intelligence.config import settings
from url_intelligence.models import AnalysisOutput, ExtractedContent


SYSTEM_PROMPT = """You analyze normalized URL content for a user.
Return a concise but useful structured result.
Base all claims only on the provided content.
If information is missing, say so briefly in the relevant fields."""


def _extract_parsed_output(response) -> AnalysisOutput:
    for output in response.output:
        if output.type != "message":
            continue
        for item in output.content:
            if item.type == "refusal":
                raise ValueError(f"Model refused the analysis request: {item.refusal}")
            if getattr(item, "parsed", None):
                return item.parsed
    raise ValueError("Could not parse model output into AnalysisOutput")


class AIAnalyzer:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for AI analysis")
        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        self.client = OpenAI(**client_kwargs)

    def analyze(self, content: ExtractedContent) -> AnalysisOutput:
        user_payload = {
            "url": content.url,
            "source_type": content.source_type.value,
            "title": content.title,
            "author": content.author,
            "published_at": content.published_at.isoformat() if content.published_at else None,
            "language": content.language,
            "markdown": content.markdown,
            "transcript": content.transcript,
            "metadata": content.metadata,
        }
        response = self.client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Analyze this extracted URL content. Provide a summary, key points, entities, "
                        "possible risks or caveats, sentiment, and good follow-up questions.\n\n"
                        f"{user_payload}"
                    ),
                },
            ],
            text_format=AnalysisOutput,
        )
        return _extract_parsed_output(response)
