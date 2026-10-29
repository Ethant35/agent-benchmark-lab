"""Read-only matched task comparisons. Never infer a model cause from a status."""
from collections import Counter, defaultdict
import hashlib
import json
import statistics

from .presentation import _cost
from .store import TERMINAL

SETTINGS = (
    'runner', 'provider', 'model', 'supports_tools', 'streaming', 'stream_usage',
    'temperature', 'reasoning_effort', 'max_requests', 'max_output_tokens',
    'max_tool_steps', 'runtime_seconds', 'token_budget', 'spend_limit_usd',
    'input_price_per_million', 'output_price_per_million', 'repeats', 'tasks',
    'runtime', 'image', 'reference_mode',
)


def outcome_kind(trial):
    status, reason = trial.get('status'), trial.get('failure_category')
    if status == 'PASS':
        return 'passed'
    if reason in {'isolation_error', 'runner_error', 'verification_error', 'cleanup_error', 'artifact_limit', 'output_limit'}:
        return 'harness_or_execution_error'
    if reason == 'provider_error':
        return 'provider_error'
    if status == 'TIMEOUT' or reason in {'step_limit', 'budget_limit', 'runtime_limit'}:
        return 'configured_limit'
    if status in {'INTERRUPTED', 'CANCELLED'}:
        return 'interrupted_or_cancelled'
    if status in {'UNSUPPORTED', 'BLOCKED_EXTERNAL'}:
        return 'blocked_or_unsupported'
    if reason == 'verification_failed':
        return 'verifier_rejected_cause_unresolved'
    return 'unresolved'


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _identity(trial, run, manifest):
    """Check saved identities, without substituting today's installed contract."""
    if not run or not isinstance(manifest, dict):
        return None
    config = run['config']
    if not isinstance(config, dict):
        return None
    if _digest(config) != trial.get('config_hash') or _digest(manifest) != trial.get('corpus_hash'):
        return None
    entries = manifest.get('tasks')
    slot, repeats = trial.get('slot'), config.get('repeats', 1)
    if (not isinstance(entries, list) or not entries or type(slot) is not int
            or type(repeats) is not int or not 0 <= slot < len(entries) * repeats):
        return None
    entry = entries[slot % len(entries)]
    if not isinstance(entry, dict):
        return None
    for key in ('runner', 'provider', 'model'):
        if not config.get(key) or trial.get(key) != config[key]:
            return None
    if (entry.get('id') != trial.get('task_id')
            or entry.get('version') != trial.get('task_version')
            or entry.get('sha256') != trial.get('task_artifact_id')
            or manifest.get('image_id') != trial.get('image_id')):
        return None
    key = tuple(trial.get(field) for field in (
        'task_id', 'task_version', 'task_artifact_id', 'fixture_hash', 'image_id', 'runner'))
    return key if all(isinstance(v, str) and v for v in key) else None


def _side(rows, runs):
    total, known = _cost(rows)
    times = [r['wall_seconds'] for r in rows if r.get('wall_seconds') is not None]
    evidence = [{key: row.get(key) for key in (
        'id', 'run_id', 'slot', 'status', 'failure_category', 'wall_seconds',
        'cost_usd', 'cost_source', 'known_cost_subtotal_usd', 'verifier_exit_code')}
        | {'outcome_kind': outcome_kind(row)} for row in rows[:100]]
    active = any(runs[r['run_id']]['status'] in {'RUNNING', 'CANCELLING'} for r in rows)
    return {
        'attempts': len(rows), 'passes': sum(r['status'] == 'PASS' for r in rows),
        'outcomes': dict(Counter(outcome_kind(r) for r in rows)),
        'median_wall_seconds': statistics.median(times) if times else None,
        'measured_wall_attempts': len(times),
        'cost_usd': total, 'known_cost_subtotal_usd': known,
        'cost_sources': dict(Counter(r.get('cost_source') or 'unavailable' for r in rows)),
        'active_run': active, 'evidence': evidence, 'evidence_sampled': len(rows) > 100,
    }


def matched_comparison(rows, runs, manifests, left, right, limit=200):
    """All attempts contribute; never select only successful or latest retries."""
    if left == right:
        raise ValueError('Choose two different configurations')
    grouped = {left: defaultdict(list), right: defaultdict(list)}
    excluded = {left: Counter(), right: Counter()}
    configs = {}
    for trial in rows:
        side = trial.get('config_hash')
        if side not in grouped:
            continue
        if trial.get('status') not in TERMINAL:
            excluded[side]['nonterminal'] += 1
            continue
        run = runs.get(trial.get('run_id'))
        identity = _identity(trial, run, manifests.get(trial.get('run_id')))
        if identity is None:
            excluded[side]['unverified_identity'] += 1
            continue
        configs[side] = run['config']
        grouped[side][identity].append(trial)
    shared = sorted(set(grouped[left]) & set(grouped[right]))
    for side in (left, right):
        excluded[side]['no_equivalent_task'] = sum(len(attempts) for key, attempts in grouped[side].items() if key not in shared)
    differences = []
    if left in configs and right in configs:
        for field in sorted(set(configs[left]) | set(configs[right])):
            a, b = configs[left].get(field), configs[right].get(field)
            if a != b:
                differences.append({'setting': field, 'left': a if field in SETTINGS else '[withheld]',
                                    'right': b if field in SETTINGS else '[withheld]'})
    matches = []
    for identity in shared[:limit]:
        a, b = _side(grouped[left][identity], runs), _side(grouped[right][identity], runs)
        comparable_cost = (a['cost_usd'] is not None and b['cost_usd'] is not None
                           and a['cost_sources'] == b['cost_sources'])
        matches.append(dict(zip(('task_id', 'task_version', 'task_artifact_id', 'fixture_hash', 'image_id', 'runner'), identity)) | {
            'left': a, 'right': b,
            'pass_rate_delta': b['passes'] / b['attempts'] - a['passes'] / a['attempts'],
            'cost_delta_usd': b['cost_usd'] - a['cost_usd'] if comparable_cost else None,
            'wall_delta_seconds': (b['median_wall_seconds'] - a['median_wall_seconds']
                if a['median_wall_seconds'] is not None and b['median_wall_seconds'] is not None else None),
        })
    return {
        'left_config': left, 'right_config': right, 'differences': differences,
        'matches': matches, 'matched_tasks': len(shared), 'display_limited': len(shared) > limit,
        'excluded': {'left': dict(excluded[left]), 'right': dict(excluded[right])},
        'uncertainty': 'Observational attempts, not independent paired trials. Small samples and retries do not establish a causal advantage. Harness version and provider routing are not matched. Verifier rejection does not establish model fault.',
        'basis': 'Same saved task version, task bytes, fixture, image and runner; verified against saved manifests and configurations. Costs cover retained terminal attempts only.',
    }
