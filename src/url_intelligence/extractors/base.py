from __future__ import annotations

from abc import ABC, abstractmethod

from url_intelligence.models import ExtractedContent


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, url: str) -> ExtractedContent:
        raise NotImplementedError
