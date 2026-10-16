"""Health endpoint for the synthetic Sentinel reference API."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
import json
from typing import Any

from api.demo import ALLOWED_ORIGINS, SCENARIOS


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/api/health":
            self._send_json(404, {"error": "not_found"})
            return
        self._send_json(
            200,
            {
                "ok": True,
                "service": "sentinel-reference-demo-api",
                "mode": "synthetic-demo-only",
                "scenarios": sorted(SCENARIOS),
            },
        )

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin")
        if origin not in ALLOWED_ORIGINS:
            self._send_json(403, {"error": "origin_not_allowed"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return
