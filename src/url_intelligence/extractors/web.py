from __future__ import annotations

from bs4 import BeautifulSoup

from url_intelligence.config import settings
from url_intelligence.extractors.base import BaseExtractor
from url_intelligence.models import ExtractedContent, ImageAsset, SourceType
from url_intelligence.utils import (
    attr_from_soup,
    clean_html_to_markdown,
    fetch_text,
    parse_iso_or_none,
    text_from_soup,
)


class WebExtractor(BaseExtractor):
    def extract(self, url: str) -> ExtractedContent:
        html = fetch_text(url, timeout=settings.request_timeout_seconds)
        soup = BeautifulSoup(html, "html.parser")
        article_node = self._pick_article_node(soup)
        article_html = str(article_node)
        title = (
            attr_from_soup(soup, 'meta[property="og:title"]', "content")
            or text_from_soup(soup, "title")
            or text_from_soup(article_node, "h1")
        )

        images = []
        for image in article_node.select("img[src]"):
            images.append(ImageAsset(url=image["src"], alt=image.get("alt")))

        return ExtractedContent(
            url=url,
            source_type=SourceType.WEB,
            title=title,
            author=(
                attr_from_soup(soup, 'meta[name="author"]', "content")
                or attr_from_soup(soup, 'meta[property="article:author"]', "content")
            ),
            published_at=(
                parse_iso_or_none(attr_from_soup(soup, "time[datetime]", "datetime"))
                or parse_iso_or_none(attr_from_soup(soup, 'meta[property="article:published_time"]', "content"))
            ),
            language=soup.html.get("lang") if soup.html else None,
            markdown=clean_html_to_markdown(article_html),
            images=images,
            metadata={
                "source_title": title,
                "description": attr_from_soup(soup, 'meta[name="description"]', "content"),
            },
        )

    def _pick_article_node(self, soup: BeautifulSoup) -> BeautifulSoup:
        for selector in ("article", "main", "[role=main]", ".article", ".post", ".entry-content"):
            node = soup.select_one(selector)
            if node:
                return node
        return soup.body or soup
