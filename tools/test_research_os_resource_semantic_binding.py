import unittest

from tools.research_os_resource_parser import declared_identities
from tools.research_os_semantic_binding import resolve_semantic_binding


class SemanticBindingTests(unittest.TestCase):
    def test_filename_similarity_never_binds(self):
        texts = {
            'current/foo_contract.json': '{"contract_id":"REAL_FOO"}',
            'tests/test_foo_contract.py': 'assert True',
        }
        result = resolve_semantic_binding(
            target='current/foo_contract.json',
            relation='VERIFIED_BY',
            candidates=['tests/test_foo_contract.py'],
            texts=texts,
        )
        self.assertTrue(result.unresolved)
        self.assertFalse(result.targets)

    def test_explicit_identity_binds(self):
        texts = {
            'current/foo_contract.json': '{"contract_id":"REAL_FOO"}',
            'tools/foo.py': '{"contract_id":"REAL_FOO"}',
        }
        result = resolve_semantic_binding(
            target='current/foo_contract.json',
            relation='ENFORCED_BY',
            candidates=['tools/foo.py'],
            texts=texts,
        )
        self.assertEqual(result.tier, 'UNIQUE_SEMANTIC_IDENTITY')
        self.assertEqual(result.targets, ('tools/foo.py',))

    def test_explicit_reference_beats_semantic(self):
        texts = {
            'current/foo_contract.json': '{"contract_id":"REAL_FOO"}',
            'tools/explicit.py': 'current/foo_contract.json',
            'tools/semantic.py': '{"contract_id":"REAL_FOO"}',
        }
        result = resolve_semantic_binding(
            target='current/foo_contract.json',
            relation='ENFORCED_BY',
            candidates=['tools/explicit.py', 'tools/semantic.py'],
            texts=texts,
        )
        self.assertEqual(result.tier, 'EXPLICIT_CONTRACT_REFERENCE')
        self.assertEqual(result.targets, ('tools/explicit.py',))

    def test_single_relation_ambiguity_fails_closed(self):
        texts = {
            'current/foo_contract.json': '{"contract_id":"REAL_FOO"}',
            'tools/a.py': '{"contract_id":"REAL_FOO"}',
            'tools/b.py': '{"contract_id":"REAL_FOO"}',
        }
        result = resolve_semantic_binding(
            target='current/foo_contract.json',
            relation='ENFORCED_BY',
            candidates=['tools/a.py', 'tools/b.py'],
            texts=texts,
        )
        self.assertTrue(result.ambiguous)
        self.assertFalse(result.targets)

    def test_multi_relation_allows_multiple(self):
        texts = {
            'current/foo_contract.json': '{"contract_id":"REAL_FOO"}',
            'tests/a.py': '{"contract_id":"REAL_FOO"}',
            'tests/b.py': '{"contract_id":"REAL_FOO"}',
        }
        result = resolve_semantic_binding(
            target='current/foo_contract.json',
            relation='VERIFIED_BY',
            candidates=['tests/a.py', 'tests/b.py'],
            texts=texts,
        )
        self.assertEqual(
            result.targets,
            ('tests/a.py', 'tests/b.py'),
        )
        self.assertFalse(result.ambiguous)

    def test_parser_keeps_path_stem_out_of_explicit_identity(self):
        values = declared_identities(
            'tests/test_foo_contract.py',
            'assert True',
        )
        self.assertIn('test_foo_contract', values)


if __name__ == '__main__':
    unittest.main()
