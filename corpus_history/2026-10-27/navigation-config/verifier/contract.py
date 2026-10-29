"""Pure explanation contract shared by verifier and local contract tests."""

import re


_REQUIRED_CONCEPTS = (
    re.compile(r"\bports?\b"),
    re.compile(r"\bretr(?:y|ies|ied)\b"),
    re.compile(r"\bcach(?:e|es|ed|ing|ability|able)\b"),
    re.compile(r"\bformats?\b"),
)


def explanation_describes_settings(explanation: str) -> bool:
    """Require all four requested topics without prescribing one synonym."""
    folded = explanation.casefold()
    return all(pattern.search(folded) for pattern in _REQUIRED_CONCEPTS)
