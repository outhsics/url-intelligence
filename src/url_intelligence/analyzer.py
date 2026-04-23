from __future__ import annotations

import json

from openai import OpenAI

from url_intelligence.config import settings
from url_intelligence.models import AnalysisOutput, ExtractedContent


SYSTEM_PROMPT = """You analyze normalized URL content for a user.
Return a concise but useful structured result.
Base all claims only on the provided content.
If information is missing, say so briefly in the relevant fields."""

JSON_PROMPT = """Analyze the extracted URL content and return JSON only.
The JSON must contain exactly these keys:
- summary: string
- key_points: string[]
- entities: string[]
- risks: string[]
- sentiment: string
- suggested_questions: string[]

Do not wrap the JSON in markdown fences.
Do not add extra keys.
Keep the response grounded only in the supplied content."""


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


def _extract_text_output(response) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return text

    choices = getattr(response, "choices", None) or []
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content
    raise ValueError("Could not extract text output from model response")


class AIAnalyzer:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for AI analysis")
        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        self.client = OpenAI(**client_kwargs)
        self.provider = settings.ai_provider.strip().lower()
        self.base_url = (settings.openai_base_url or "").lower()

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
        if self._use_glm_compat():
            return self._analyze_with_chat_completions(user_payload)

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

    def _use_glm_compat(self) -> bool:
        return self.provider == "glm" or "bigmodel.cn" in self.base_url

    def _analyze_with_chat_completions(self, user_payload: dict[str, object]) -> AnalysisOutput:
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": JSON_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Analyze this extracted URL content and return the required JSON.\n\n"
                        f"{json.dumps(user_payload, ensure_ascii=False)}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        raw = _extract_text_output(response)
        return AnalysisOutput.model_validate(json.loads(raw))
