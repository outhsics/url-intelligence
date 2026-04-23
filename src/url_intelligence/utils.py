from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def fetch_text(url: str, timeout: float) -> str:
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=DEFAULT_HEADERS) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def fetch_json(url: str, timeout: float) -> dict[str, Any]:
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=DEFAULT_HEADERS) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def clean_html_to_markdown(html: str) -> str:
    return html_to_markdown(html, heading_style="ATX", bullets="-").strip()


def text_from_soup(soup: BeautifulSoup, selector: str) -> str | None:
    node = soup.select_one(selector)
    if not node:
        return None
    return node.get_text(" ", strip=True) or None


def attr_from_soup(soup: BeautifulSoup, selector: str, attr: str) -> str | None:
    node = soup.select_one(selector)
    if not node:
        return None
    value = node.get(attr)
    return str(value).strip() if value else None


def parse_iso_or_none(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    try:
        return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_datetime_or_none(value: str | None) -> datetime | None:
    parsed = parse_iso_or_none(value)
    if parsed:
        return parsed
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None


def parse_unix_or_none(value: str | None) -> datetime | None:
    if not value or not value.isdigit():
        return None
    return datetime.fromtimestamp(int(value), tz=UTC)


def regex_group(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.S)
    return match.group(1).strip() if match else None


def parse_youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return parsed.path.lstrip("/") or None
    if "youtube.com" in parsed.netloc:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/"):
            parts = [part for part in parsed.path.split("/") if part]
            return parts[1] if len(parts) >= 2 else None
    return None


def parse_tweet_id(url: str) -> str | None:
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else None


def run_yt_dlp_json(url: str) -> dict[str, Any] | None:
    try:
        completed = subprocess.run(
            ["yt-dlp", "--dump-single-json", "--no-warnings", url],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None
