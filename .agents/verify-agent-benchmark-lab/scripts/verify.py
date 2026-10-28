#!/usr/bin/env python3
"""Drive an installed candidate through existing free local checks. Author: Ethan."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    evidence = args.evidence.resolve()
    if evidence.exists():
        parser.error('Use a new evidence directory; previous evidence is never overwritten.')
    evidence.mkdir(parents=True, mode=0o700)
    cli = args.cli.resolve()
    env = {key: value for key, value in os.environ.items() if not key.endswith('_API_KEY')}
    report = {'author': 'Ethan', 'provider_calls': 0, 'api_cost_usd': 0,
              'distribution': 'local candidate wheel', 'new_mac_setup': 'not exercised',
              'checks': [], 'status': 'RUNNING'}
    server = None

    def save():
        (evidence / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')

    def run(name, argv, cwd=repo, timeout=300):
        with (evidence / f'{name}.log').open('w') as log:
            process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except BaseException:
                import signal
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                raise
        report['checks'].append({'name': name, 'exit_code': code})
        save()
        if code:
            raise RuntimeError(f'{name} failed; see {evidence / (name + ".log")}')
        print(f'PASS: {name}', flush=True)

    def get(base, route):
        with urlopen(base + route, timeout=5) as response:
            return json.loads(response.read())

    save()
    try:
        run('doctor', [str(cli), 'check'])
        run('journey', [sys.executable, str(repo / 'tests/usability_e2e.py'),
                       '--cli', str(cli), '--root', str(evidence / 'state'),
                       '--recovery-mode', 'success'])
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        with (evidence / 'dashboard.log').open('w') as log:
            server = subprocess.Popen([str(cli), 'dashboard', '--root', str(evidence / 'state'),
                                       '--port', str(port)], cwd=evidence, env=env,
                                      stdout=log, stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 20
            while True:
                if server.poll() is not None:
                    raise RuntimeError('Dashboard exited before ready')
                try:
                    workspace = get(base, '/api/workspace')
                    rows = get(base, '/api/trials')
                    if not workspace.get('workspace_id') or len(rows) != 3:
                        raise AssertionError('Candidate did not serve the expected result store')
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(.1)
            journey = json.loads((evidence / 'state/usability-journey.json').read_text())
            recovered_run = journey['milestones']['resume_and_cleanup']['run_id']
            overview = get(base, '/api/overview?run_id=' + recovered_run)
            schedule = overview['schedule']
            assert schedule['tasks'] == schedule['passed'] == schedule['recovered'] == 1, schedule
            assert overview['summary']['trials'] == 2 and overview['summary']['completion_rate'] == .5
            assert overview['summary']['total_spend_usd'] == 0
            latest = next(row for row in rows if row['run_id'] == recovered_run and row['status'] == 'PASS')
            detail = get(base, '/api/trials/' + latest['id'])
            assert detail['task_context']['status'] == 'verified', detail['task_context']
            assert detail['task_context']['expected_artifacts'] and detail['verifier']['exit_code'] == 0
            assert all(row['runner'] == 'reference' and row['provider'] == 'none' and row['cost_usd'] == 0 for row in rows)
            (evidence / 'recovered-overview.json').write_text(json.dumps(overview, indent=2) + '\n')
            (evidence / 'recovered-detail.json').write_text(json.dumps(detail, indent=2) + '\n')
            env['ABL_BASE_URL'] = base
            try:
                run('browser', ['npm', 'run', 'test:e2e'], cwd=repo / 'dashboard', timeout=300)
            finally:
                screenshots = repo / 'dashboard/test-results'
                if screenshots.exists():
                    shutil.copytree(screenshots, evidence / 'browser-artifacts')
        report['status'] = 'PASS'
    except BaseException as error:
        report['status'] = 'FAIL'
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
            report['dashboard_stopped'] = True
            with socket.socket() as probe:
                probe.settimeout(1)
                report['dashboard_port_closed'] = probe.connect_ex(('127.0.0.1', port)) != 0
        report['evidence_hashes'] = {str(path.relative_to(evidence)): hashlib.sha256(path.read_bytes()).hexdigest()
                                     for path in evidence.glob('*.json') if path.name != 'verification.json'}
        save()
    assert (evidence / 'journey.log').exists() and (evidence / 'recovered-overview.json').exists()
    print(f'Verified. Evidence retained at {evidence}', flush=True)


if __name__ == '__main__':
    main()
