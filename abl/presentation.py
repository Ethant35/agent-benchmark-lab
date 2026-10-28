"""Additive, identity-aware result summaries for the read-only API."""
from __future__ import annotations

import hashlib
import json


def task_context(store, trial):
    """Return current contract text only when saved run identity proves it applies."""
    unavailable = {"status": "unavailable", "reason": "Historical task identity could not be verified."}
    try:
        from .engine import manifest_hash
        from .models import load_tasks, tree_hash

        manifest = store.manifest(trial.get("run_id"))
        if not manifest or not trial.get("corpus_hash"):
            return unavailable
        if manifest_hash(manifest) != trial["corpus_hash"]:
            return unavailable
        entry = next((item for item in manifest.get("tasks", [])
                      if item.get("id") == trial.get("task_id")), None)
        if not entry or entry.get("version") != trial.get("task_version"):
            return unavailable
        task_pair = load_tasks().get(trial.get("task_id"))
        if not task_pair:
            return unavailable
        task, folder = task_pair
        if (task.version != entry.get("version")
                or tree_hash(folder) != entry.get("sha256")
                or trial.get("task_artifact_id") != entry.get("sha256")):
            return unavailable
        return {
            "status": "verified",
            "description": task.description,
            "expected_artifacts": task.expected_artifacts,
            "verifier": task.verifier,
        }
    except (KeyError, TypeError, ValueError, OSError):
        return unavailable


def _cost(attempts):
    exact = [a.get("cost_usd") for a in attempts]
    known_values = [value for value in exact if value is not None]
    partial_values = [attempt.get("known_cost_subtotal_usd") for attempt in attempts
                      if attempt.get("cost_usd") is None
                      and attempt.get("known_cost_subtotal_usd") is not None]
    known = sum(known_values) + sum(partial_values)
    total = sum(exact) if attempts and all(value is not None for value in exact) else None
    return total, known if known_values or partial_values else None


def schedule_summary(store, run_id=None, provider=None, model=None, task_id=None, *, snapshot=None):
    """Summarize one matching run without changing attempt-level benchmark metrics."""
    run, manifest, attempts = (snapshot if snapshot is not None else
                               store.schedule_snapshot(run_id, provider, model, task_id))
    if not run:
        return None
    unknown_schedule = {
        "run_id": run["id"], "run_status": run["status"], "tasks": None,
        "passed": 0, "failed": 0, "recovered": 0, "pending": 0,
        "unknown": 1, "incomplete": 0, "cost_usd": None,
        "known_cost_subtotal_usd": None,
    }
    if not isinstance(manifest, dict) or not isinstance(manifest.get("tasks"), list):
        return unknown_schedule
    try:
        repeats = int(run["config"].get("repeats", 1))
        manifest_tasks = manifest["tasks"]
        task_ids = [item["id"] for item in manifest_tasks]
        if repeats < 1 or not task_ids:
            raise ValueError("invalid schedule")
        # Engine enumerates chosen * repeats: the task list repeats in the same order.
        expected = task_ids * repeats
    except (KeyError, TypeError, ValueError):
        return unknown_schedule

    from .engine import manifest_hash
    manifest_digest = manifest_hash(manifest)
    config_digest = hashlib.sha256(json.dumps(run["config"], sort_keys=True).encode()).hexdigest()
    task_versions = {item["id"]: item.get("version") for item in manifest_tasks}
    if task_id:
        selected_slots = [(slot, expected_task) for slot, expected_task in enumerate(expected)
                          if expected_task == task_id]
    else:
        selected_slots = list(enumerate(expected))

    attempts_by_slot = {}
    unknown = 0
    for attempt in attempts:
        slot = attempt.get("slot")
        if not isinstance(slot, int) or slot < 0 or slot >= len(expected):
            unknown += 1
            continue
        attempts_by_slot.setdefault(slot, []).append(attempt)

    passed = failed = recovered = pending = incomplete = 0
    all_attempts = []
    for slot, expected_task in selected_slots:
        slot_attempts = attempts_by_slot.get(slot, [])
        if not slot_attempts:
            pending += 1
            continue
        all_attempts.extend(slot_attempts)
        latest = slot_attempts[-1]
        # A status only counts toward a scheduled result when all saved identities
        # still agree with the immutable run manifest and saved configuration.
        if (latest.get("task_id") != expected_task
                or latest.get("task_version") != task_versions[expected_task]
                or latest.get("corpus_hash") != manifest_digest
                or latest.get("config_hash") != config_digest):
            unknown += 1
            continue
        if latest.get("status") == "PASS":
            passed += 1
            if any(attempt.get("status") in {"INTERRUPTED", "CANCELLED"}
                   and attempt.get("task_id") == expected_task
                   and attempt.get("task_version") == task_versions[expected_task]
                   and attempt.get("corpus_hash") == manifest_digest
                   and attempt.get("config_hash") == config_digest
                   for attempt in slot_attempts[:-1]):
                recovered += 1
        elif latest.get("status") in {"FAIL", "TIMEOUT", "ERROR", "UNSUPPORTED", "BLOCKED_EXTERNAL"}:
            failed += 1
        else:
            incomplete += 1
    total_cost, known_cost = _cost(all_attempts)
    if run["status"] == "RUNNING" or pending or incomplete or unknown:
        total_cost = None
    return {
        "run_id": run["id"], "run_status": run["status"], "tasks": len(selected_slots),
        "passed": passed, "failed": failed, "recovered": recovered,
        "pending": pending, "unknown": unknown, "incomplete": incomplete,
        "cost_usd": total_cost, "known_cost_subtotal_usd": known_cost,
    }
