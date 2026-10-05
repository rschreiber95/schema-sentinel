"""Compare actual decoder observations, final fields, and the transport trace."""
import json
import os
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'generated/python'))
from v1.entity_pb2 import Entity

RUNTIMES = ['python', 'typescript', 'csharp']
CASES = [
    {'entity_id': 'roundtrip-001', 'name': 'Sensor A'},
    {'entity_id': '', 'name': ''},
    {'entity_id': 'entity-雪-🚀', 'name': 'Café / Δ / 🚀'},
    {'entity_id': 'entity-004', 'name': 'quotes " and newline\n and backslash \\'},
]


def validate_evidence(expected, received, observations, trace):
    # An unchanged returned payload alone cannot prove intermediate decoding.
    assert isinstance(observations, list), 'decoder observations must be a list'
    assert [item['runtime'] for item in observations] == RUNTIMES, 'missing or reordered decoder observations'
    for item in observations:
        assert item['fields'] == expected, f"{item['runtime']} decoded different stable fields: {item['fields']!r}"
    actual = {'entity_id': received.entity_id, 'name': received.name}
    assert actual == expected, f'final stable fields changed: {actual!r}'
    # The service trace is intentionally changing transport metadata, not an Entity field.
    assert trace == RUNTIMES, f'incorrect service trace: {trace!r}'


def main():
    for fields in CASES:
        sent = Entity(**fields)
        request = urllib.request.Request(
            os.environ.get('PYTHON_RELAY_URL', 'http://localhost:8000/relay'),
            data=sent.SerializeToString(), method='POST',
            headers={'Content-Type': 'application/x-protobuf'},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            assert response.headers.get_content_type() == 'application/x-protobuf', 'wrong content type'
            received = Entity.FromString(response.read())
            observations = json.loads(response.headers['X-Schema-Sentinel-Observations'])
            trace = json.loads(response.headers['X-Service-Trace'])
        validate_evidence(fields, received, observations, trace)
        print(json.dumps({'expected': fields, 'decoded': observations, 'service_trace': trace}, ensure_ascii=True))
    print(f'PASS: {len(CASES)} cases; all three decoders agree on stable fields; service trace verified separately')


if __name__ == '__main__':
    main()
