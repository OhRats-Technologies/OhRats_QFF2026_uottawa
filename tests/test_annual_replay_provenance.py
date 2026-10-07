import unittest
from wildfire_lab.annual_replay_provenance import check_replay_code


class ReplayProvenanceTests(unittest.TestCase):
    def test_unrelated_manifest_change_is_disclosed_for_collection(self):
        frozen = {'scientific.py': 'same', 'uv.lock': 'old', 'pyproject.toml': 'old'}
        current = dict(frozen, **{'uv.lock': 'new', 'pyproject.toml': 'new'})
        result = check_replay_code(current, frozen)
        self.assertTrue(result['scientific_code_matches'])
        self.assertEqual(result['dependency_manifests_changed'], ['pyproject.toml', 'uv.lock'])

    def test_changed_or_missing_scientific_code_still_blocks_replay(self):
        frozen = {'scientific.py': 'same', 'uv.lock': 'old'}
        for current in [{'scientific.py': 'changed', 'uv.lock': 'old'}, {'uv.lock': 'old'}]:
            with self.assertRaisesRegex(ValueError, 'scientific code changed'):
                check_replay_code(current, frozen)


if __name__ == '__main__':
    unittest.main()
