import unittest

from wildfire_lab.discovery_replay import replay
from wildfire_lab.evolution_policy import next_action, score


def root(ap=.2):
    return {'id': 'root', 'parent': None,
            'candidate': 'standard_logistic', 'ap': ap}


def rollout(panel, policy, budget=3):
    tree = [root(panel['standard_logistic']['ap'])]
    while (action := next_action(tree, policy, budget)) is not None:
        tree.append(dict(id=f'node-{len(tree)}', ap=panel[action['candidate']]['ap'],
                         **action))
    return tree


class EvolutionPolicyTests(unittest.TestCase):
    def test_baseline_matches_historical_trace_and_reward(self):
        for robust, standard in ((.1, .15), (.3, .25), (.1, .3), (.2, .2)):
            with self.subTest(robust=robust, standard=standard):
                panel = {name: {'ap': ap, 'seconds': 0} for name, ap in (
                    ('standard_logistic', .2), ('robust_tanh/rbf', robust),
                    ('standard_tanh/rbf', standard), ('robust_tanh/qiskit_ZZ', .4))}
                old = replay(panel, 'classical_gate')
                tree = rollout(panel, 'classical_gate')
                self.assertEqual([n['candidate'] for n in tree[1:]], old['trace'])
                self.assertEqual(score(tree), old['best_ap'] - .005 * old['evaluations'])

    def test_v1_stops_after_first_probe_at_or_below_penalty(self):
        for root_ap, robust_ap in ((.2, .1), (.2, .2), (.2, .203), (0, .005)):
            with self.subTest(root_ap=root_ap, robust_ap=robust_ap):
                tree = [root(root_ap), {'id': 'rbf', 'parent': 'root',
                         'candidate': 'robust_tanh/rbf', 'ap': robust_ap}]
                self.assertIsNone(next_action(tree, 'evolved_v1'))

    def test_v1_uses_revealed_nodes_to_continue_then_stop(self):
        class RevealedNode(dict):
            def __getitem__(self, key):
                if key not in ('id', 'candidate', 'ap'):
                    raise AssertionError('Policy accessed evaluator metadata')
                return super().__getitem__(key)

        tree = [RevealedNode(root())]
        self.assertEqual(next_action(tree, 'evolved_v1'),
                         {'parent': 'root', 'candidate': 'robust_tanh/rbf'})
        tree.append(RevealedNode(id='rbf', candidate='robust_tanh/rbf', ap=.3))
        self.assertEqual(next_action(tree, 'evolved_v1'),
                         {'parent': 'rbf', 'candidate': 'standard_tanh/rbf'})
        tree.append(RevealedNode(id='standard', candidate='standard_tanh/rbf', ap=.4))
        self.assertIsNone(next_action(tree, 'evolved_v1'))
        self.assertEqual(score(tree), .39)

    def test_budgets_and_live_leaf_parents(self):
        panel = {name: {'ap': .3, 'seconds': 0} for name in (
            'robust_tanh/rbf', 'standard_tanh/rbf', 'robust_tanh/qiskit_ZZ')}
        panel['standard_logistic'] = {'ap': .2, 'seconds': 0}
        for policy in ('classical_gate', 'evolved_v1'):
            for budget in (1, 2, 3):
                with self.subTest(policy=policy, budget=budget):
                    tree = rollout(panel, policy, budget)
                    expected = budget if policy == 'classical_gate' else min(budget, 2)
                    self.assertEqual(len(tree) - 1, expected)
                    self.assertIsNone(next_action(tree, policy, budget))
                    for parent, child in zip(tree, tree[1:]):
                        self.assertEqual(child['parent'], parent['id'])
                    self.assertEqual(len({n['candidate'] for n in tree}), len(tree))


if __name__ == '__main__':
    unittest.main()
