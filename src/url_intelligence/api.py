from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from url_intelligence.analyzer import AIAnalyzer
from url_intelligence.models import ExtractRequest, PipelineResult
from url_intelligence.service import URLIntelligenceService

app = FastAPI(title="URL Intelligence", version="0.1.0")
service = URLIntelligenceService()
web_dir = Path(__file__).with_name("web")


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path == "/" or request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheMiddleware)
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
