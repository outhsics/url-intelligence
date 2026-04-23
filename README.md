# URL Intelligence

`URL Intelligence` is a local-first MVP that turns a URL into LLM-friendly structured content and then asks an AI model to analyze it.

The design follows the same broad split used by tools like Mercury and Folo:

- ingestion and normalization
- a stable item schema
- AI on top of normalized content

This project is intentionally smaller. It targets a practical workflow:

1. paste a `YouTube`, `微信公众号`, `X/Twitter`, or normal web URL
2. extract clean text, metadata, and transcripts when available
3. send the normalized payload to an AI model
4. receive a structured analysis result

## What Works

- `YouTube`
  - transcript via `youtube-transcript-api`
  - metadata via `yt-dlp`
- `微信公众号`
  - direct article HTML parsing
  - extracts title, author, publish time, body markdown, and images
- `X/Twitter`
  - public syndication endpoint first
  - HTML fallback second
- generic web pages
  - readability-based article extraction
  - markdown conversion

## Project Structure

```text
url-intelligence/
  src/url_intelligence/
    extractors/
    analyzer.py
    api.py
    cli.py
    config.py
    models.py
    router.py
    service.py
  tests/
```

## Requirements

- Python `3.11+`
- `uv` recommended
- `OPENAI_API_KEY` for AI analysis
- `yt-dlp` installed locally for richer YouTube metadata

## Quick Start

```bash
cd /Users/terre/Documents/Codex/2026-04-22-ai-url-url-llm-markdown-json/url-intelligence
uv venv
source .venv/bin/activate
uv pip install -e '.[dev]'
cp .env.example .env
```

Set at least:

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-5.4-mini
```

For `GLM`, switch to the official OpenAI-compatible endpoint documented by Zhipu:

```bash
AI_PROVIDER=glm
OPENAI_API_KEY=your_glm_key
OPENAI_MODEL=glm-5
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

This project will then route analysis through `chat.completions.create(...)` with JSON output, which is the compatibility path shown in Zhipu's official docs.

Run the API:

```bash
uvicorn url_intelligence.api:app --reload
```

Run the CLI:

```bash
url-intel extract-and-analyze "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## API

### `POST /extract`

```json
{
  "url": "https://mp.weixin.qq.com/s/..."
}
```

### `POST /extract-and-analyze`

```json
{
  "url": "https://x.com/user/status/1234567890"
}
```

## Output Schema

The extractor always normalizes to one content shape:

```json
{
  "url": "https://...",
  "source_type": "web",
  "title": "Title",
  "author": "Author",
  "published_at": "2026-04-22T10:00:00+08:00",
  "language": "zh",
  "markdown": "Main body as markdown",
  "transcript": "Video transcript if available",
  "images": [
    {"url": "https://...", "alt": "cover"}
  ],
  "metadata": {}
}
```

## Notes

- This is an MVP, not a full feed reader.
- `X/Twitter` extraction remains best-effort because public access rules can change.
- For WeChat history sync, subscriptions, and authenticated feeds, you would add a separate ingestion job later.
- OpenAI uses the `Responses API` path in this project; GLM uses the OpenAI-compatible `chat.completions` path.
