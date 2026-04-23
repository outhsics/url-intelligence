from __future__ import annotations

import argparse
import json

from url_intelligence.analyzer import AIAnalyzer
from url_intelligence.service import URLIntelligenceService


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and analyze URLs for AI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("url")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("url")

    combo_parser = subparsers.add_parser("extract-and-analyze")
    combo_parser.add_argument("url")

    args = parser.parse_args()
    service = URLIntelligenceService()

    if args.command == "extract":
        content = service.extract(args.url)
        print(json.dumps(content.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    if args.command == "analyze":
        content = service.extract(args.url)
        analysis = AIAnalyzer().analyze(content)
        print(json.dumps(analysis.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    result = service.extract_and_analyze(args.url)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
