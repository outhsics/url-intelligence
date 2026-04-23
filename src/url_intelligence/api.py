from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from url_intelligence.analyzer import AIAnalyzer
from url_intelligence.models import ExtractRequest, PipelineResult
from url_intelligence.service import URLIntelligenceService
from pathlib import Path

app = FastAPI(title="URL Intelligence", version="0.1.0")
service = URLIntelligenceService()
web_dir = Path(__file__).with_name("web")

app.mount("/static", StaticFiles(directory=web_dir), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(web_dir / "index.html")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract")
def extract_url(request: ExtractRequest):
    try:
        return {"ok": True, "content": service.extract(str(request.url))}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/analyze")
def analyze_content(request: ExtractRequest):
    try:
        content = service.extract(str(request.url))
        analysis = AIAnalyzer().analyze(content)
        return {"ok": True, "analysis": analysis}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/extract-and-analyze", response_model=PipelineResult)
def extract_and_analyze(request: ExtractRequest) -> PipelineResult:
    try:
        return service.extract_and_analyze(str(request.url))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
