from __future__ import annotations

import json
import time
from hashlib import sha256
from pathlib import Path
from typing import Any


class FileCache:
    def __init__(self, root: Path, ttl_seconds: int) -> None:
        self.root = root
        self.ttl_seconds = ttl_seconds
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        digest = sha256(key.encode("utf-8")).hexdigest()
        return self.root / f"{digest}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path_for(key)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - payload["stored_at"] > self.ttl_seconds:
            path.unlink(missing_ok=True)
            return None
        return payload["value"]

    def set(self, key: str, value: dict[str, Any]) -> None:
        path = self._path_for(key)
        payload = {"stored_at": time.time(), "value": value}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
