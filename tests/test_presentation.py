"""Additive run and task context summaries preserve attempt history."""
import json

from fastapi.testclient import TestClient

from abl.api import create_app
from abl.engine import manifest_hash
from abl.models import load_tasks, tree_hash
from abl.presentation import schedule_summary, task_context
from abl.store import Store, aggregate, export_data


def manifest_for(task_ids=("bugfix-rounding",)):
    tasks = load_tasks()
    return {"schema_version": 1, "image_id": "sha256:image",
            "tasks": [{"id": tasks[task_id][0].id,
                       "version": tasks[task_id][0].version,
                       "sha256": tree_hash(tasks[task_id][1])}
                      for task_id in task_ids]}


def trial(run_id, slot, status, **overrides):
    version = load_tasks()["bugfix-rounding"][0].version
    return {"id": f"{len(overrides):02x}{slot:030x}", "run_id": run_id,
            "slot": slot, "task_id": "bugfix-rounding", "task_version": version,
            "category": "bug_fix", "status": status, "runner": "reference", "provider": "none",
            "model": "deterministic-reference", "config_hash": "cfg",
            "corpus_hash": None, "task_artifact_id": None, "cost_usd": 0,
            "known_cost_subtotal_usd": None, "cost_source": "no_provider_requests",
            "wall_seconds": 0, "ttft_seconds": None, "input_tokens": None,
            "output_tokens": None, "cached_input_tokens": None, "tool_calls": 0,
            "failed_tool_calls": 0, "retry_count": 0, "timed_out": False,
            "verifier": {"exit_code": 0}, **overrides}


def setup_store(tmp_path, *, repeats=1, task_ids=("bugfix-rounding",), with_manifest=True, status="COMPLETED"):
    store = Store(tmp_path)
    rid = "a" * 32
    manifest = manifest_for(task_ids) if with_manifest else None
    store.create_run(rid, {"repeats": repeats}, manifest=manifest)
    store.state(rid, status)
    return store, rid, manifest


def save(store, record):
    run = store.run(record["run_id"])
    if run:
        record["config_hash"] = __import__("hashlib").sha256(
            json.dumps(run["config"], sort_keys=True).encode()).hexdigest()
        manifest = store.manifest(record["run_id"])
        if manifest and record.get("corpus_hash") is None:
            record["corpus_hash"] = manifest_hash(manifest)
        if manifest and record.get("task_artifact_id") is None:
            entry = next(item for item in manifest["tasks"] if item["id"] == record["task_id"])
            record["task_artifact_id"] = entry["sha256"]
    store.save(record)


def test_recovered_pass_is_one_scheduled_success_with_two_retained_attempts(tmp_path):
    store, rid, manifest = setup_store(tmp_path)
    old = trial(rid, 0, "INTERRUPTED", cost_usd=None,
                known_cost_subtotal_usd=.02, corpus_hash=manifest_hash(manifest),
                task_artifact_id=manifest["tasks"][0]["sha256"])
    new = trial(rid, 0, "PASS", cost_usd=.01,
                corpus_hash=manifest_hash(manifest),
                task_artifact_id=manifest["tasks"][0]["sha256"])
    save(store, old)
    save(store, new)

    schedule = schedule_summary(store, rid)
    attempts = store.trials(run_id=rid)
    report = aggregate(attempts)
    assert schedule == {"run_id": rid, "run_status": "COMPLETED", "tasks": 1,
                        "passed": 1, "failed": 0, "recovered": 1, "pending": 0,
                        "unknown": 0, "incomplete": 0, "cost_usd": None,
                        "known_cost_subtotal_usd": .03}
    assert report["trials"] == 2 and report["successes"] == 1
    assert report["completion_rate"] == .5 and report["total_spend_usd"] is None
    assert len(attempts) == 2 and [r["status"] for r in attempts] == ["INTERRUPTED", "PASS"]
    assert json.loads(export_data(attempts, "json")) == attempts
    exact_only, known_only = __import__("abl.presentation", fromlist=["_cost"])._cost([
        {"cost_usd": .1, "known_cost_subtotal_usd": .8}])
    assert (exact_only, known_only) == (.1, .1)


def test_schedule_preserves_pending_slots_and_active_attempts(tmp_path):
    store, rid, _ = setup_store(tmp_path, repeats=2, status="RUNNING")
    active = trial(rid, 0, "RUNNING")
    save(store, active)
    schedule = schedule_summary(store, rid)
    assert schedule["tasks"] == 2
    assert schedule["pending"] == 1 and schedule["incomplete"] == 1
    assert schedule["passed"] == schedule["failed"] == schedule["recovered"] == 0


def test_missing_manifest_is_reported_as_unknown_schedule(tmp_path):
    store, rid, _ = setup_store(tmp_path, with_manifest=False)
    result = schedule_summary(store, rid)
    assert result["tasks"] is None and result["unknown"] == 1


def test_task_text_requires_exact_saved_corpus_identity(tmp_path):
    store, rid, manifest = setup_store(tmp_path)
    valid = trial(rid, 0, "PASS", corpus_hash=manifest_hash(manifest),
                  task_artifact_id=manifest["tasks"][0]["sha256"])
    assert task_context(store, valid)["status"] == "verified"
    assert task_context(store, valid)["expected_artifacts"]
    assert task_context(store, valid)["verifier"] == ["python", "/verifier/check.py"]

    mismatched = valid | {"corpus_hash": "0" * 64}
    assert task_context(store, mismatched) == {
        "status": "unavailable",
        "reason": "Historical task identity could not be verified."}
    wrong_task_hash = valid | {"task_artifact_id": "0" * 64}
    assert task_context(store, wrong_task_hash)["status"] == "unavailable"


def test_legacy_detail_and_additive_overview_are_backward_compatible(tmp_path):
    store = Store(tmp_path)
    rid = "b" * 32
    record = trial(rid, 0, "PASS")
    store.save(record)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        detail = client.get(f"/api/trials/{record['id']}").json()
        assert detail["task_context"]["status"] == "unavailable"
        assert detail["verifier"] == record["verifier"]
        overview = client.get("/api/overview").json()
        assert overview["schedule"] is None
        assert overview["summary"]["trials"] == 1


def test_schedule_task_filter_keeps_manifest_slot_indices(tmp_path):
    store, rid, manifest = setup_store(tmp_path, task_ids=("bugfix-rounding", "navigation-config"))
    for slot, task_id in enumerate(("bugfix-rounding", "navigation-config")):
        entry = next(item for item in manifest["tasks"] if item["id"] == task_id)
        save(store, trial(rid, slot, "PASS", task_id=task_id,
                          task_version=entry["version"],
                          corpus_hash=manifest_hash(manifest),
                          task_artifact_id=entry["sha256"]))
    filtered = schedule_summary(store, rid, task_id="navigation-config")
    assert filtered["tasks"] == 1 and filtered["passed"] == 1
    assert filtered["unknown"] == 0 and filtered["pending"] == 0


def test_schedule_rejects_changed_attempt_identities_and_counts_out_of_range(tmp_path):
    store, rid, manifest = setup_store(tmp_path)
    valid = trial(rid, 0, "PASS", corpus_hash=manifest_hash(manifest),
                  task_artifact_id=manifest["tasks"][0]["sha256"])
    save(store, valid)
    assert schedule_summary(store, rid)["passed"] == 1

    store.save(valid | {"id": "c" * 32, "slot": 0, "status": "PASS",
                        "config_hash": "changed"})
    # The latest row for slot zero has a changed config identity.
    result = schedule_summary(store, rid)
    assert result["passed"] == 0 and result["unknown"] == 1

    store.save(valid | {"id": "d" * 32, "slot": 7, "status": "PASS"})
    assert schedule_summary(store, rid)["unknown"] == 2


def test_schedule_marks_corpus_and_version_mismatches_unknown(tmp_path):
    store, rid, manifest = setup_store(tmp_path)
    base = trial(rid, 0, "PASS", corpus_hash=manifest_hash(manifest),
                 task_artifact_id=manifest["tasks"][0]["sha256"])
    save(store, base)
    store.save(base | {"id": "e" * 32, "slot": 0, "status": "PASS",
                       "corpus_hash": "wrong"})
    assert schedule_summary(store, rid)["unknown"] == 1
    store.save(base | {"id": "f" * 32, "slot": 0, "status": "PASS",
                       "task_version": "other"})
    assert schedule_summary(store, rid)["unknown"] == 1


def test_duplicate_manifest_tasks_keep_each_scheduled_position(tmp_path):
    store, rid, manifest = setup_store(tmp_path, repeats=2,
                                      task_ids=("bugfix-rounding", "bugfix-rounding"))
    result = schedule_summary(store, rid)
    assert result["tasks"] == 4 and result["pending"] == 4


def test_schedule_cost_stays_unknown_until_all_outcomes_are_final(tmp_path):
    store, rid, manifest = setup_store(tmp_path, repeats=2, status="RUNNING")
    valid = trial(rid, 0, "PASS", corpus_hash=manifest_hash(manifest),
                  task_artifact_id=manifest["tasks"][0]["sha256"], cost_usd=.1,
                  known_cost_subtotal_usd=.8)
    save(store, valid)
    schedule = schedule_summary(store, rid)
    assert schedule["passed"] == 1 and schedule["pending"] == 1
    assert schedule["cost_usd"] is None
    assert schedule["known_cost_subtotal_usd"] == .1


def test_schedule_unknown_attempt_cost_is_reported_through_api(tmp_path):
    store, rid, manifest = setup_store(tmp_path)
    unknown = trial(rid, 0, "PASS", corpus_hash=manifest_hash(manifest),
                    task_artifact_id=manifest["tasks"][0]["sha256"],
                    cost_usd=None, known_cost_subtotal_usd=None)
    save(store, unknown)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        overview = client.get(f"/api/overview?run_id={rid}").json()
    assert overview["schedule"]["cost_usd"] is None
    assert overview["schedule"]["known_cost_subtotal_usd"] is None
    assert overview["summary"]["total_spend_usd"] is None
    assert overview["summary"]["known_spend_usd"] is None


def test_mismatched_interrupted_attempt_does_not_claim_recovery(tmp_path):
    store, rid, manifest = setup_store(tmp_path)
    interrupted = trial(rid, 0, "INTERRUPTED", corpus_hash="different")
    passed = trial(rid, 0, "PASS", corpus_hash=manifest_hash(manifest),
                   task_artifact_id=manifest["tasks"][0]["sha256"])
    save(store, interrupted)
    save(store, passed)
    result = schedule_summary(store, rid)
    assert result["passed"] == 1 and result["recovered"] == 0


def test_overview_summary_and_schedule_share_one_read_snapshot(tmp_path, monkeypatch):
    store, rid, manifest = setup_store(tmp_path)
    record = trial(rid, 0, "PASS", corpus_hash=manifest_hash(manifest),
                   task_artifact_id=manifest["tasks"][0]["sha256"])
    original = Store.schedule_snapshot
    inserted = False

    def insert_then_snapshot(instance, *args, **kwargs):
        nonlocal inserted
        if instance.root == tmp_path.resolve() and kwargs.get("db") is not None and not inserted:
            inserted = True
            save(store, record)
        return original(instance, *args, **kwargs)

    monkeypatch.setattr(Store, "schedule_snapshot", insert_then_snapshot)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        first = client.get(f"/api/overview?run_id={rid}").json()
        second = client.get(f"/api/overview?run_id={rid}").json()

    assert first["summary"]["trials"] == 0
    assert first["schedule"]["pending"] == 1 and first["schedule"]["passed"] == 0
    assert second["summary"]["trials"] == 1
    assert second["schedule"]["pending"] == 0 and second["schedule"]["passed"] == 1
