from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from generated import testbed_pb2


PORT = int(os.environ.get("PORT", "8000"))
TYPESCRIPT_RELAY_URL = os.environ.get(
    "TYPESCRIPT_RELAY_URL", "http://localhost:8001/relay"
)


def forward_to_typescript(message: testbed_pb2.TestbedMessage) -> bytes:
    message.visited_services.append("python")
    request = urllib.request.Request(
        TYPESCRIPT_RELAY_URL,
        data=message.SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.read()


class TestbedHandler(BaseHTTPRequestHandler):
    server_version = "SchemaSentinelPython/0.1"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "runtime": "python"})
            return

        if self.path == "/demo":
            message = testbed_pb2.TestbedMessage(
                message_id="demo-001",
                payload="hello from Schema Sentinel",
            )
            try:
                response_bytes = forward_to_typescript(message)
                response = testbed_pb2.TestbedMessage.FromString(response_bytes)
            except (urllib.error.URLError, ValueError) as error:
                self._send_json(
                    HTTPStatus.BAD_GATEWAY,
                    {"error": "typescript relay failed", "detail": str(error)},
                )
                return

            self._send_json(
                HTTPStatus.OK,
                {
                    "message_id": response.message_id,
                    "payload": response.payload,
                    "visited_services": list(response.visited_services),
                },
            )
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path != "/relay":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            message = testbed_pb2.TestbedMessage.FromString(
                self.rfile.read(content_length)
            )
            response_bytes = forward_to_typescript(message)
        except (ValueError, urllib.error.URLError) as error:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "invalid or unrelayable protobuf message", "detail": str(error)},
            )
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/x-protobuf")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _send_json(self, status: HTTPStatus, body: dict[str, object]) -> None:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        print(f"python-service: {format % args}", flush=True)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), TestbedHandler)
    print(f"python-service listening on {PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
