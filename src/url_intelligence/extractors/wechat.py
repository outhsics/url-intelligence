from __future__ import annotations

from bs4 import BeautifulSoup

from url_intelligence.config import settings
from url_intelligence.extractors.base import BaseExtractor
from url_intelligence.models import ExtractedContent, ImageAsset, SourceType
from url_intelligence.utils import (
    clean_html_to_markdown,
    fetch_text,
    parse_unix_or_none,
    regex_group,
    text_from_soup,
)


class WeChatExtractor(BaseExtractor):
    def extract(self, url: str) -> ExtractedContent:
        html = fetch_text(url, timeout=settings.request_timeout_seconds)
        soup = BeautifulSoup(html, "html.parser")
        content_node = soup.select_one("#js_content")
        body_html = str(content_node or "")

        images = []
        if content_node:
            for image in content_node.select("img"):
                image_url = image.get("data-src") or image.get("src")
                if image_url:
                    images.append(ImageAsset(url=image_url, alt=image.get("data-alt") or image.get("alt")))

        title = (
            text_from_soup(soup, "#activity-name")
            or regex_group(r"var\s+msg_title\s*=\s*'(.*?)';", html)
            or regex_group(r'window\.__INITIAL_STATE__.*?"title":"(.*?)"', html)
        )
        author = (
            text_from_soup(soup, "#js_name")
            or regex_group(r"var\s+nickname\s*=\s*htmlDecode\(\"(.*?)\"\);", html)
        )

        publish_time = parse_unix_or_none(regex_group(r"var\s+publish_time\s*=\s*\"?(\d+)\"?;", html))

        return ExtractedContent(
            url=url,
            source_type=SourceType.WECHAT,
            title=title,
            author=author,
            published_at=publish_time,
            language="zh",
            markdown=clean_html_to_markdown(body_html),
            images=images,
            metadata={
                "biz": regex_group(r"var\s+biz\s*=\s*\"(.*?)\";", html),
                "wechat_article": True,
            },
        )
