from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class SourceType(StrEnum):
    WEB = "web"
    WECHAT = "wechat"
    X = "x"
    YOUTUBE = "youtube"


class ImageAsset(BaseModel):
    url: str
    alt: str | None = None


class ExtractedContent(BaseModel):
    url: str
    source_type: SourceType
    title: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    markdown: str = ""
    transcript: str | None = None
    images: list[ImageAsset] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisOutput(BaseModel):
    summary: str
    key_points: list[str]
    entities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    suggested_questions: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    content: ExtractedContent
    analysis: AnalysisOutput | None = None


class ExtractRequest(BaseModel):
    url: HttpUrl

