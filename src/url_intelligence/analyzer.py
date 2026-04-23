from __future__ import annotations

import json

from anthropic import Anthropic
from openai import OpenAI

from url_intelligence.config import settings
from url_intelligence.models import AnalysisOutput, ExtractedContent


SYSTEM_PROMPT = """你要分析已经被标准化的 URL 内容，并返回结构化结果。
所有自然语言字段统一使用简体中文输出。
专有名词、作品名、品牌名、地名、人名可以保留原文。
所有结论只能基于提供的内容，不要补充外部事实。
如果信息缺失，在对应字段里简短说明。"""

JSON_PROMPT = """请分析抽取后的 URL 内容，并且只返回 JSON。
JSON 必须且只能包含以下键：
- summary: string
- key_points: string[]
- entities: string[]
- risks: string[]
- sentiment: string
- suggested_questions: string[]

要求：
- 不要使用 markdown 代码块包裹 JSON
- 不要添加额外字段
- `summary`、`key_points`、`risks`、`suggested_questions` 必须用中文
- `sentiment` 使用中文短词，例如“正面”“中性”“负面”
- `entities` 优先保留实体原名，必要时可加中文说明
- 所有内容都必须严格基于提供的正文和字幕"""


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


def _extract_anthropic_text(message) -> str:
    texts: list[str] = []
    for block in getattr(message, "content", []) or []:
        if getattr(block, "type", None) == "text" and getattr(block, "text", None):
            texts.append(block.text)
    if texts:
        return "\n".join(texts)
    raise ValueError("Could not extract text output from anthropic response")


class AIAnalyzer:
    def __init__(self) -> None:
        self.provider = settings.ai_provider.strip().lower()
        self.base_url = (settings.openai_base_url or "").lower()
        self.client = None
        self.anthropic_client = None

        if self._use_anthropic():
            auth_token = settings.anthropic_auth_token
            api_key = settings.anthropic_api_key
            if not auth_token and not api_key:
                raise ValueError(
                    "ANTHROPIC_AUTH_TOKEN or ANTHROPIC_API_KEY is required for anthropic analysis"
                )
            client_kwargs = {}
            if auth_token:
                client_kwargs["auth_token"] = auth_token
            if api_key:
                client_kwargs["api_key"] = api_key
            if settings.anthropic_base_url:
                client_kwargs["base_url"] = settings.anthropic_base_url
            self.anthropic_client = Anthropic(**client_kwargs)
            return

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
        if self._use_anthropic():
            return self._analyze_with_anthropic(user_payload)
        if self._use_glm_compat():
            return self._analyze_with_chat_completions(user_payload)

        response = self.client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "请分析这份抽取后的 URL 内容，并返回中文的摘要、关键点、实体、风险提示、情绪判断和后续追问。\n\n"
                        f"{user_payload}"
                    ),
                },
            ],
            text_format=AnalysisOutput,
        )
        return _extract_parsed_output(response)

    def _use_glm_compat(self) -> bool:
        return self.provider == "glm" or "bigmodel.cn" in self.base_url

    def _use_anthropic(self) -> bool:
        return self.provider == "anthropic"

    def _analyze_with_chat_completions(self, user_payload: dict[str, object]) -> AnalysisOutput:
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": JSON_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "请分析这份抽取后的 URL 内容，并按要求返回中文 JSON。\n\n"
                        f"{json.dumps(user_payload, ensure_ascii=False)}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        raw = _extract_text_output(response)
        return AnalysisOutput.model_validate(json.loads(raw))

    def _analyze_with_anthropic(self, user_payload: dict[str, object]) -> AnalysisOutput:
        response = self.anthropic_client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1200,
            system=f"{SYSTEM_PROMPT}\n\n{JSON_PROMPT}",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "请分析这份抽取后的 URL 内容，并按要求返回中文 JSON。\n\n"
                        f"{json.dumps(user_payload, ensure_ascii=False)}"
                    ),
                }
            ],
        )
        raw = _extract_anthropic_text(response)
        return AnalysisOutput.model_validate(json.loads(raw))
