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
CASE_NAMES = ['Standard text', 'Empty strings', 'Unicode', 'Escaped text']
RUNTIME_NAMES = {'python': 'Python', 'typescript': 'TypeScript', 'csharp': 'C#'}


def format_fields(fields):
    return ', '.join(f'{field}={json.dumps(value, ensure_ascii=False)}' for field, value in fields.items())


def print_encoded(label, payload):
    print(f'  {label} ({len(payload)} bytes, hex):')
    if not payload:
        print('    (empty)')
    for offset in range(0, len(payload), 16):
        print('    ' + payload[offset:offset + 16].hex(' '))


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
    # Keep piped output usable on terminals with limited character support.
    sys.stdout.reconfigure(errors='backslashreplace')
    print('\nRound-trip tests')
    print('Route: Python -> TypeScript -> C#\n')
    for index, (name, fields) in enumerate(zip(CASE_NAMES, CASES, strict=True), start=1):
        sent = Entity(**fields)
        sent_bytes = sent.SerializeToString()
        request = urllib.request.Request(
            os.environ.get('PYTHON_RELAY_URL', 'http://localhost:8000/relay'),
            data=sent_bytes, method='POST',
            headers={'Content-Type': 'application/x-protobuf'},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            assert response.headers.get_content_type() == 'application/x-protobuf', 'wrong content type'
            returned_bytes = response.read()
            received = Entity.FromString(returned_bytes)
            observations = json.loads(response.headers['X-Schema-Sentinel-Observations'])
            trace = json.loads(response.headers['X-Service-Trace'])
        validate_evidence(fields, received, observations, trace)
        print(f'[PASS] {index}/{len(CASES)} - {name}')
        print(f'  Input: {format_fields(fields)}')
        print_encoded('Encoded request', sent_bytes)
        print('  Decoded by each service:')
        for observation in observations:
            runtime = RUNTIME_NAMES[observation['runtime']]
            print(f'    {runtime} [PASS]: {format_fields(observation["fields"])}')
        print_encoded('Encoded response', returned_bytes)
        print(f'  Decoded response [PASS]: {format_fields({"entity_id": received.entity_id, "name": received.name})}')
        print('  Service order [PASS]: ' + ' -> '.join(RUNTIME_NAMES[runtime] for runtime in trace) + '\n')
    print(f'PASS: {len(CASES)}/{len(CASES)} round-trip cases passed.')


if __name__ == '__main__':
    main()
