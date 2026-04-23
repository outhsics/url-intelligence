from __future__ import annotations

from url_intelligence.analyzer import AIAnalyzer
from url_intelligence.cache import FileCache
from url_intelligence.config import settings
from url_intelligence.extractors.web import WebExtractor
from url_intelligence.extractors.wechat import WeChatExtractor
from url_intelligence.extractors.x import XExtractor
from url_intelligence.extractors.youtube import YouTubeExtractor
from url_intelligence.models import ExtractedContent, PipelineResult, SourceType
from url_intelligence.router import detect_source_type


class URLIntelligenceService:
    def __init__(self) -> None:
        self.cache = FileCache(settings.cache_dir, settings.cache_ttl_seconds)
        self.extractors = {
            SourceType.WEB: WebExtractor(),
            SourceType.WECHAT: WeChatExtractor(),
            SourceType.X: XExtractor(),
            SourceType.YOUTUBE: YouTubeExtractor(),
        }

    def extract(self, url: str) -> ExtractedContent:
        cache_key = f"extract:{url}"
        cached = self.cache.get(cache_key)
        if cached:
            return ExtractedContent.model_validate(cached)

        source_type = detect_source_type(url)
        extractor = self.extractors[source_type]
        content = extractor.extract(url)
        self.cache.set(cache_key, content.model_dump(mode="json"))
        return content

    def extract_and_analyze(self, url: str) -> PipelineResult:
        content = self.extract(url)
        analysis = AIAnalyzer().analyze(content)
        return PipelineResult(content=content, analysis=analysis)
