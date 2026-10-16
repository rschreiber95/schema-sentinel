"""Entity example and HTTP relay using the canonical generated bindings."""
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from google.protobuf.message import DecodeError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "generated/python"))
OBSERVATIONS = "X-Schema-Sentinel-Observations"
TRACE = "X-Service-Trace"


def process_entity(raw_bytes: bytes, version: str):
    if version not in ("v1", "v2"):
        raise ValueError(f"Unsupported schema version: {version}")
    entity = importlib.import_module(f"{version}.entity_pb2").Entity.FromString(raw_bytes)
    fields = {"entity_id": entity.entity_id}
    if version == "v1":
        fields["name"] = entity.name
    print(json.dumps({"runtime": "python", "version": version, "fields": fields}, ensure_ascii=True), flush=True)
    return entity, fields


class Relay(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_error(404)
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok","runtime":"python"}')

    def do_POST(self):
        if self.path != "/relay":
            self.send_error(404)
            return
        try:
            entity, fields = process_entity(self.rfile.read(int(self.headers.get("Content-Length", "0"))), "v1")
            observation = {"runtime": "python", "fields": fields}
            request = urllib.request.Request(
                os.environ.get("TYPESCRIPT_RELAY_URL", "http://localhost:8001/relay"),
                data=entity.SerializeToString(), method="POST",
                headers={"Content-Type": "application/x-protobuf", TRACE: json.dumps(["python"])},
            )
            with urllib.request.urlopen(request, timeout=5) as downstream:
                body = downstream.read()
                observations = [observation] + json.loads(downstream.headers[OBSERVATIONS])
                trace = downstream.headers[TRACE]
            self.send_response(200)
            self.send_header("Content-Type", "application/x-protobuf")
            self.send_header("Content-Length", str(len(body)))
            self.send_header(OBSERVATIONS, json.dumps(observations, ensure_ascii=True))
            self.send_header(TRACE, trace)
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, DecodeError) as error:
            self.send_error(400, str(error))
        except (OSError, KeyError) as error:
            self.send_error(502, str(error))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--version", choices=["v1", "v2"], default="v1")
    args = parser.parse_args()
    if args.serve:
        ThreadingHTTPServer((os.environ.get("HOST", "0.0.0.0"), int(os.environ.get("PORT", "8000"))), Relay).serve_forever()
    else:
        module = importlib.import_module(f"{args.version}.entity_pb2")
        entity = module.Entity(entity_id="py_101")
        if args.version == "v1":
            entity.name = "Sensor A"
        process_entity(entity.SerializeToString(), args.version)
