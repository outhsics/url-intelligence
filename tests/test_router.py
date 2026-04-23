from url_intelligence.models import SourceType
from url_intelligence.router import detect_source_type
from url_intelligence.utils import parse_tweet_id, parse_youtube_video_id


def test_detect_source_type() -> None:
    assert detect_source_type("https://mp.weixin.qq.com/s/abc") == SourceType.WECHAT
    assert detect_source_type("https://x.com/openai/status/123") == SourceType.X
    assert detect_source_type("https://www.youtube.com/watch?v=abc") == SourceType.YOUTUBE
    assert detect_source_type("https://example.com/post") == SourceType.WEB


def test_parse_youtube_video_id() -> None:
    assert parse_youtube_video_id("https://www.youtube.com/watch?v=abc123") == "abc123"
    assert parse_youtube_video_id("https://youtu.be/abc123") == "abc123"
    assert parse_youtube_video_id("https://www.youtube.com/shorts/abc123") == "abc123"


def test_parse_tweet_id() -> None:
    assert parse_tweet_id("https://x.com/openai/status/1234567890") == "1234567890"
