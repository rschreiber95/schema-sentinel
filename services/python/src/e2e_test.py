from __future__ import annotations

import json
import os
import sys
import urllib.request

from generated import testbed_pb2


PYTHON_RELAY_URL = os.environ.get(
    "PYTHON_RELAY_URL", "http://localhost:8000/relay"
)


def message_as_dict(message: testbed_pb2.TestbedMessage) -> dict[str, object]:
    return {
        "message_id": message.message_id,
        "payload": message.payload,
        "visited_services": list(message.visited_services),
    }


def main() -> int:
    sent = testbed_pb2.TestbedMessage(
        message_id="roundtrip-001",
        payload="schema changes should not change this payload",
    )
    request = urllib.request.Request(
        PYTHON_RELAY_URL,
        data=sent.SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        if response.headers.get_content_type() != "application/x-protobuf":
            print("FAIL: relay returned the wrong content type", file=sys.stderr)
            return 1
        received = testbed_pb2.TestbedMessage.FromString(response.read())

    expected = {
        "message_id": sent.message_id,
        "payload": sent.payload,
        "visited_services": ["python", "typescript"],
    }
    actual = message_as_dict(received)

    if actual != expected:
        print("FAIL: message changed during the round trip", file=sys.stderr)
        print(json.dumps({"expected": expected, "actual": actual}, indent=2))
        return 1

    print("PASS: protobuf message survived both runtimes")
    print(json.dumps(actual, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
