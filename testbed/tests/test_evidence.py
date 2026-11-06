import copy
import unittest
from e2e_test import Entity, RUNTIMES, validate_evidence


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fields = {'entity_id': '001', 'name': 'Sensor A'}
        self.message = Entity(**self.fields)
        self.observations = [{'runtime': runtime, 'fields': dict(self.fields)} for runtime in RUNTIMES]

    def test_matching_decoders(self):
        validate_evidence(self.fields, self.message, self.observations, RUNTIMES)

    def test_intermediate_misdecode_fails_even_when_final_payload_matches(self):
        observations = copy.deepcopy(self.observations)
        observations[1]['fields']['name'] = 'wrong'
        with self.assertRaisesRegex(AssertionError, 'typescript decoded'):
            validate_evidence(self.fields, self.message, observations, RUNTIMES)

    def test_missing_runtime_fails(self):
        with self.assertRaisesRegex(AssertionError, 'missing or reordered'):
            validate_evidence(self.fields, self.message, self.observations[:-1], RUNTIMES)

    def test_final_payload_change_fails(self):
        with self.assertRaisesRegex(AssertionError, 'final stable fields'):
            validate_evidence(self.fields, Entity(entity_id='wrong', name='Sensor A'), self.observations, RUNTIMES)

    def test_trace_fails_separately(self):
        with self.assertRaisesRegex(AssertionError, 'incorrect service trace'):
            validate_evidence(self.fields, self.message, self.observations, ['python', 'typescript'])


if __name__ == '__main__':
    unittest.main()
