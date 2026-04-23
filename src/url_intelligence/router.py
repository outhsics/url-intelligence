from __future__ import annotations

from urllib.parse import urlparse

from url_intelligence.models import SourceType


def detect_source_type(url: str) -> SourceType:
    host = urlparse(url).netloc.lower()

    if "mp.weixin.qq.com" in host:
        return SourceType.WECHAT
    if host.endswith("youtube.com") or host == "youtu.be" or host.endswith("youtube-nocookie.com"):
        return SourceType.YOUTUBE
    if host.endswith("x.com") or host.endswith("twitter.com") or host.endswith("t.co"):
        return SourceType.X
    return SourceType.WEB
