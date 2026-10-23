"""Downloaded-wheel first and returning use journey; no provider requests. Author: Ethan."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen
import yaml


def cli(executable: Path, args: list[str], *, timeout: int = 180, input_text: str | None = None,
        expected: tuple[int, ...] = (0,)):
    result = subprocess.run(
        [str(executable), *args], text=True, input=input_text,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
        env={k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")},
    )
    if result.returncode not in expected:
        raise AssertionError(f"abl {' '.join(args)} exited {result.returncode}:\n{result.stdout}")
    return result.stdout


def records(root: Path) -> list[dict]:
    with sqlite3.connect(root / "results.sqlite3") as db:
        return [json.loads(row[0]) for row in db.execute("SELECT data FROM trials ORDER BY rowid")]


def run_rows(root: Path) -> list[dict]:
    with sqlite3.connect(root / "results.sqlite3") as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM runs ORDER BY created_at")]


def http_json(url: str):
    with urlopen(url, timeout=3) as response:
        assert response.status == 200
        return json.loads(response.read())


def wait_for_dashboard(process: subprocess.Popen, base: str):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"Dashboard exited early with {process.returncode}")
        try:
            return http_json(base + "/api/trials/page?limit=10&offset=0")
        except (URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(.1)
    raise AssertionError("Dashboard did not become ready on loopback")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", required=True, type=Path, help="abl executable from the downloaded-wheel environment")
    parser.add_argument("--root", required=True, type=Path, help="new, empty result directory")
    args = parser.parse_args()
    executable = args.cli.resolve()
    root = args.root.resolve()
    if not executable.is_file():
        raise SystemExit(f"CLI executable does not exist: {executable}")
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"Use a fresh, empty result directory: {root}")
    root.mkdir(parents=True, exist_ok=True)
    evidence = {
        "author": "Ethan",
        "journey": "free-first local CLI and dashboard",
        "provider_calls": 0,
        "reference_cost_usd": 0,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "milestones": {},
    }

    def save_evidence():
        (root / "usability-journey.json").write_text(json.dumps(evidence, indent=2) + "\n")

    save_evidence()

    # Do not inherit provider credentials: every run in this harness is local reference mode.
    print("Check installed package and container prerequisite", flush=True)
    cli(executable, ["check"])

    # Open the dashboard against a new result root to verify a real empty state.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    dashboard = subprocess.Popen(
        [str(executable), "dashboard", "--root", str(root), "--port", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")},
    )
    base = f"http://127.0.0.1:{port}"
    try:
        empty = wait_for_dashboard(dashboard, base)
        assert empty["total"] == 0 and empty["items"] == [], empty
        overview = http_json(base + "/api/overview")
        assert overview["summary"]["trials"] == 0, overview
        evidence["milestones"]["empty_workspace"] = {"status": "PASS", "api_trial_total": 0}
        save_evidence()
        print("PASS: fresh workspace reports zero saved runs", flush=True)
    finally:
        dashboard.terminate()
        dashboard.wait(timeout=10)

    # The default guided path is one deterministic, free reference task.
    print("Run the one-task reference journey", flush=True)
    first_output = cli(executable, ["start", "--root", str(root)], input_text="y\n", timeout=240)
    assert "bugfix-rounding" in first_output and "PASS" in first_output, first_output
    assert any(word in first_output.lower() for word in ("progress", "running", "tool", "verifier")), first_output
    first_trials = records(root)
    first_runs = run_rows(root)
    reference = [t for t in first_trials if t["task_id"] == "bugfix-rounding"]
    assert len(reference) == 1 and reference[0]["status"] == "PASS", reference
    assert reference[0]["provider"] == "none" and reference[0]["runner"] == "reference", reference[0]
    assert reference[0]["cost_usd"] == 0, reference[0].get("cost_usd")
    assert len(first_runs) == 1 and first_runs[0]["status"] == "COMPLETED", first_runs
    rid = first_runs[0]["id"]
    assert rid in first_output, (rid, first_output)
    evidence["milestones"]["free_reference"] = {
        "status": "PASS", "run_id": rid, "trial_id": reference[0]["id"],
        "provider": reference[0]["provider"], "runner": reference[0]["runner"],
        "trial_status": reference[0]["status"], "cost_usd": reference[0]["cost_usd"],
        "progress_output_present": True,
    }
    save_evidence()
    cli(executable, ["runs", "--root", str(root)])
    cli(executable, ["inspect", rid, "--root", str(root)])
    print(f"PASS: free reference trial {reference[0]['id']} verified at $0", flush=True)

    # Revisit through the API and confirm that records and an empty filtered view differ.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    dashboard = subprocess.Popen(
        [str(executable), "dashboard", "--root", str(root), "--port", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")},
    )
    base = f"http://127.0.0.1:{port}"
    try:
        page = wait_for_dashboard(dashboard, base)
        assert page["total"] == 1 and len(page["items"]) == 1, page
        no_match = http_json(base + "/api/trials/page?limit=10&offset=0&task_id=not-a-task")
        assert no_match["total"] == 0, no_match
        summary = http_json(base + "/api/overview")
        assert summary["summary"]["trials"] == 1, summary
        evidence["milestones"]["returning_dashboard"] = {
            "status": "PASS", "saved_trial_total": page["total"],
            "filtered_trial_total": no_match["total"],
        }
        save_evidence()
        print("PASS: returning dashboard lists the saved trial and reports zero filter matches separately", flush=True)
    finally:
        dashboard.terminate()
        dashboard.wait(timeout=10)

    # Backup and restore into a new destination, then compare public JSON exports byte-for-byte.
    backup = root.parent / (root.name + "-backup")
    restored = root.parent / (root.name + "-restored")
    if backup.exists() or restored.exists():
        raise SystemExit("Backup and restore destinations must not already exist")
    cli(executable, ["backup", str(backup), "--root", str(root)])
    cli(executable, ["restore", str(backup), "--root", str(restored)])
    before = root.parent / (root.name + "-before.json")
    after = root.parent / (root.name + "-after.json")
    cli(executable, ["export", str(before), "--root", str(root)])
    cli(executable, ["export", str(after), "--root", str(restored)])
    assert before.read_bytes() == after.read_bytes()
    evidence["milestones"]["backup_restore"] = {
        "status": "PASS", "trial_count_preserved": len(first_trials), "export_bytes_equal": True,
    }
    save_evidence()
    print("PASS: backup/restore preserves the JSON trial export exactly", flush=True)

    # A private reference-only timeout is used to check process interruption and resume.
    # The canonical corpus task files remain installed and are never modified.
    recovery = root / "recovery-reference.yaml"
    recovery.write_text(yaml.safe_dump({
        "runner": "reference", "provider": "none", "model": "deterministic-reference",
        "tasks": ["bugfix-rounding"], "repeats": 1,
        "runtime_seconds": 5, "reference_mode": "timeout",
    }, sort_keys=False))
    recovery.chmod(0o600)
    print("Start the controlled reference-only cancellation case", flush=True)
    with tempfile.TemporaryFile(mode="w+t") as log:
        process = subprocess.Popen(
            [str(executable), "start", "--root", str(root), "--config", str(recovery)],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, text=True,
            env={k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")},
        )
        deadline = time.monotonic() + 40
        run_id = None
        trial_id = None
        while time.monotonic() < deadline:
            current = run_rows(root)
            active = [r for r in current if r.get("status") == "RUNNING"]
            active_trials = [t for t in records(root) if t.get("status") == "RUNNING"]
            if active and active_trials:
                run_id = active[-1]["id"]
                trial_id = active_trials[-1]["id"]
                break
            if process.poll() is not None:
                log.seek(0)
                raise AssertionError("Recovery run exited before entering RUNNING:\n" + log.read())
            time.sleep(.05)
        if run_id is None:
            process.terminate()
            raise AssertionError("Recovery run did not enter RUNNING")
        # Wait until the isolated task container exists, so the signal exercises
        # cleanup during execution rather than racing run initialization.
        container_name = "abl-" + trial_id
        container_deadline = time.monotonic() + 4
        while time.monotonic() < container_deadline:
            listing = subprocess.run(["podman", "ps", "-a", "--format", "{{.Names}}"],
                                     capture_output=True, text=True, timeout=10)
            if listing.returncode == 0 and container_name in listing.stdout.splitlines():
                break
            trial_state = next((t for t in records(root) if t["id"] == trial_id), None)
            if trial_state is None or trial_state["status"] != "RUNNING":
                log.seek(0)
                raise AssertionError(f"Timed out before cancellation could reach a live container:\n{log.read()}")
            time.sleep(.05)
        else:
            process.terminate()
            raise AssertionError(f"Timed task container did not appear: {container_name}")
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=30)
        log.flush(); log.seek(0); output = log.read()
        assert "bugfix-rounding" in output, output
    interrupted = next(r for r in run_rows(root) if r["id"] == run_id)
    interrupted_trials = [t for t in records(root) if t["run_id"] == run_id]
    assert interrupted["status"] == "INTERRUPTED", interrupted
    assert len(interrupted_trials) == 1 and interrupted_trials[0]["status"] == "INTERRUPTED", interrupted_trials
    assert not interrupted_trials[0]["cleanup_errors"], interrupted_trials[0]
    artifacts = Path(interrupted_trials[0]["artifact_dir"])
    assert not list(artifacts.rglob("*.partial")), list(artifacts.rglob("*.partial"))
    evidence["milestones"]["sigterm_recovery"] = {
        "status": "PASS", "run_id": run_id,
        "interrupted_trial_status": interrupted_trials[0]["status"],
        "cleanup_errors": interrupted_trials[0]["cleanup_errors"],
        "partial_archives": 0,
    }
    save_evidence()
    print(f"PASS: SIGTERM left a clean interrupted run {run_id}", flush=True)

    resumed = cli(executable, ["start", "--root", str(root), "--resume", run_id],
                  input_text="y\n", timeout=90, expected=(0, 1))
    final_run = next(r for r in run_rows(root) if r["id"] == run_id)
    final_trials = [t for t in records(root) if t["run_id"] == run_id]
    assert final_run["status"] == "COMPLETED", final_run
    assert len(final_trials) == 2 and final_trials[0]["status"] == "INTERRUPTED" and final_trials[1]["status"] == "TIMEOUT", final_trials
    assert not final_trials[-1]["cleanup_errors"], final_trials[-1]
    assert "TIMEOUT" in resumed, resumed

    # Confirm the runtime no longer owns resources for any trial in this recovery run.
    names = subprocess.run(["podman", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=30)
    volumes = subprocess.run(["podman", "volume", "ls", "--format", "{{.Name}}"], capture_output=True, text=True, timeout=30)
    assert names.returncode == 0 and volumes.returncode == 0, (names.stderr, volumes.stderr)
    for trial in final_trials:
        environment = trial.get("environment_id") or ""
        assert environment not in names.stdout and environment not in volumes.stdout, environment
    evidence["milestones"]["resume_and_cleanup"] = {
        "status": "PASS", "run_id": run_id,
        "trial_statuses": [t["status"] for t in final_trials],
        "cleanup_errors": [t["cleanup_errors"] for t in final_trials],
        "owned_containers_or_volumes": 0,
    }
    evidence["status"] = "PASS"
    save_evidence()
    print(f"PASS: resumed reference timeout completed and cleaned resources ({len(final_trials)} attempts)", flush=True)
    print("USABILITY E2E PASS: no provider configuration, credential, or model request was used", flush=True)


if __name__ == "__main__":
    main()
