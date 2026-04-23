from __future__ import annotations

from datetime import UTC, datetime

from youtube_transcript_api import YouTubeTranscriptApi

from url_intelligence.extractors.base import BaseExtractor
from url_intelligence.models import ExtractedContent, ImageAsset, SourceType
from url_intelligence.utils import parse_youtube_video_id, run_yt_dlp_json


class YouTubeExtractor(BaseExtractor):
    def extract(self, url: str) -> ExtractedContent:
        video_id = parse_youtube_video_id(url)
        if not video_id:
            raise ValueError(f"Could not determine YouTube video id from URL: {url}")

        transcript = self._load_transcript(video_id)
        metadata = run_yt_dlp_json(url) or {}
        images = []
        thumbnail = metadata.get("thumbnail")
        if thumbnail:
            images.append(ImageAsset(url=thumbnail, alt="video thumbnail"))

        description = metadata.get("description") or ""
        markdown_parts = []
        if description.strip():
            markdown_parts.append("## Description\n\n" + description.strip())
        if transcript:
            markdown_parts.append("## Transcript\n\n" + transcript)

        return ExtractedContent(
            url=url,
            source_type=SourceType.YOUTUBE,
            title=metadata.get("title") or f"YouTube video {video_id}",
            author=metadata.get("uploader") or metadata.get("channel"),
            published_at=self._published_at(metadata),
            language=metadata.get("language"),
            markdown="\n\n".join(markdown_parts).strip(),
            transcript=transcript,
            images=images,
            metadata={
                "video_id": video_id,
                "channel_id": metadata.get("channel_id"),
                "duration": metadata.get("duration"),
                "view_count": metadata.get("view_count"),
            },
        )

    def _load_transcript(self, video_id: str) -> str | None:
        try:
            segments = YouTubeTranscriptApi().fetch(video_id)
        except Exception:
            return None
        lines = [segment.text.strip() for segment in segments if segment.text.strip()]
        return "\n".join(lines) if lines else None

    def _published_at(self, metadata: dict[str, object]) -> datetime | None:
        timestamp = metadata.get("timestamp")
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp, tz=UTC)
        upload_date = metadata.get("upload_date")
        if isinstance(upload_date, str) and len(upload_date) == 8 and upload_date.isdigit():
            return datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=UTC)
        return None
