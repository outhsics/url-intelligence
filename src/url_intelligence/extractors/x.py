from __future__ import annotations

from bs4 import BeautifulSoup

from url_intelligence.config import settings
from url_intelligence.extractors.base import BaseExtractor
from url_intelligence.models import ExtractedContent, ImageAsset, SourceType
from url_intelligence.utils import fetch_json, fetch_text, parse_datetime_or_none, parse_tweet_id


class XExtractor(BaseExtractor):
    def extract(self, url: str) -> ExtractedContent:
        tweet_id = parse_tweet_id(url)
        if tweet_id:
            syndication_url = f"https://cdn.syndication.twimg.com/widgets/tweet?id={tweet_id}"
            try:
                payload = fetch_json(syndication_url, timeout=settings.request_timeout_seconds)
                photos = [
                    ImageAsset(url=photo["url"], alt="tweet image")
                    for photo in payload.get("photos", [])
                    if photo.get("url")
                ]
                author = None
                user = payload.get("user") or {}
                if user.get("name") and user.get("screen_name"):
                    author = f'{user["name"]} (@{user["screen_name"]})'
                return ExtractedContent(
                    url=url,
                    source_type=SourceType.X,
                    title=f"Post by {author}" if author else "X post",
                    author=author,
                    published_at=parse_datetime_or_none(payload.get("created_at")),
                    language=None,
                    markdown=(payload.get("text") or "").strip(),
                    images=photos,
                    metadata={
                        "tweet_id": tweet_id,
                        "likes": payload.get("favorite_count"),
                        "conversation_count": payload.get("conversation_count"),
                    },
                )
            except Exception:
                pass

        html = fetch_text(url, timeout=settings.request_timeout_seconds)
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else "X post"
        description = None
        node = soup.select_one('meta[property="og:description"]')
        if node:
            description = node.get("content")
        return ExtractedContent(
            url=url,
            source_type=SourceType.X,
            title=title,
            markdown=(description or "").strip(),
            metadata={"tweet_id": tweet_id},
        )
