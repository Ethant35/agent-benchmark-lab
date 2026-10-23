"""Contract tests for benchmark prompts and independent verifier expectations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from hypothesis import given, strategies as st

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus"


def task(task_id: str) -> dict:
    return yaml.safe_load((CORPUS / task_id / "task.yaml").read_text())


def test_order_filter_prompt_names_one_json_array_and_preserves_order() -> None:
    spec = task("feature-order-filter")
    prompt = spec["description"].casefold()
    assert spec["version"] == "1.1"
    assert "one json array" in prompt
    assert "input order" in prompt


def test_document_index_prompt_defines_every_generated_schema() -> None:
    spec = task("multistep-document-index")
    prompt = spec["description"].casefold()
    assert spec["version"] == "1.1"
    for detail in (
        "json array of objects",
        "file",
        "bytes",
        "lowercase word",
        "sorted array of relative file names",
        "sha256",
        "document_count",
    ):
        assert detail in prompt


def test_ledger_prompt_defines_outputs_without_changing_the_workload() -> None:
    spec = task("multistep-ledger")
    prompt = spec["description"].casefold()
    assert spec["version"] == "1.1"
    for detail in (
        "json array of objects",
        "account",
        "cents",
        "json array of objects",
        "total_cents",
        "sha256",
        "row_count",
        "first appearance",
    ):
        assert detail in prompt


def load_explanation_checker():
    """Load only the pure contract module; never execute the candidate program."""
    path = CORPUS / "navigation-config" / "verifier" / "contract.py"
    spec = __import__("importlib.util", fromlist=["spec_from_file_location"]).spec_from_file_location(
        "navigation_config_contract", path
    )
    module = __import__("importlib.util", fromlist=["module_from_spec"]).module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.explanation_describes_settings


@given(
    port_phrase=st.sampled_from(["port is 8123", "ports use 8123"]),
    retry_phrase=st.sampled_from(["retry limit is four", "retries stop after four"]),
    cache_phrase=st.sampled_from(
        [
            "caching is off",
            "the cache is disabled",
            "cached responses are not enabled",
            "the setting disables cached data",
        ]
    ),
    format_phrase=st.sampled_from(["supported formats are JSON and CSV", "formats include JSON and CSV"]),
    separator=st.sampled_from(["; ", ". ", " — ", "\n"]),
)
def test_navigation_explanation_accepts_equivalent_cache_wording(
    port_phrase: str,
    retry_phrase: str,
    cache_phrase: str,
    format_phrase: str,
    separator: str,
) -> None:
    accepts = load_explanation_checker()
    explanation = separator.join([port_phrase, retry_phrase, cache_phrase, format_phrase])
    assert accepts(explanation)


@given(missing=st.sampled_from(["port", "retry", "cache", "format"]))
def test_navigation_explanation_rejects_missing_a_fact(missing: str) -> None:
    accepts = load_explanation_checker()
    facts = {
        "port": "The port is 8123",
        "retry": "retry limit is four",
        "cache": "caching is off",
        "format": "supported formats are JSON and CSV",
    }
    explanation = ". ".join(value for key, value in facts.items() if key != missing)
    assert not accepts(explanation)


@given(value=st.sampled_from(["caching is off", "the cache is disabled", "cached responses are not enabled"]))
def test_navigation_config_passes_semantically_valid_explanations(value: str) -> None:
    # The observed v1.0 verifier rejected valid alternate cache wording.
    accepts = load_explanation_checker()
    assert accepts(f"Settings: port 8123, retry 4, {value}, supported formats JSON and CSV.")


def test_historical_live_evidence_remains_immutable() -> None:
    evidence = json.loads((ROOT / "evidence/full-deepseek-1017/summary.json").read_text())
    assert evidence["package_version"] == "1.0.1"
    assert len(evidence["trials"]) == 12
    assert [row["task_id"] for row in evidence["trials"] if row["status"] == "TIMEOUT"] == [
        "multistep-ledger"
    ]
