"""Offline collection provenance; training/evaluation execution guards stay strict."""
MANIFESTS = {'uv.lock', 'pyproject.toml'}


def check_replay_code(current, frozen):
    scientific = lambda pins: {path: value for path, value in pins.items() if path not in MANIFESTS}
    if scientific(current) != scientific(frozen):
        raise ValueError('Frozen annual scientific code changed')
    return dict(scientific_code_matches=True,
                dependency_manifests_changed=sorted(path for path in MANIFESTS
                    if current.get(path) != frozen.get(path)),
                interpretation='Saved arithmetic replay, not training or an environment reproduction.')
