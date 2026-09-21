"""Verbalisation coverage check (reference doc §3.1 validation table).
Threshold: 100% - every required fact must be findable in the generated documents.
"""

def fidelity_check(task: dict, documents: list[str]) -> float:
    """Checks every fact along task["reasoning_path"] appears in at least
    one of `documents`. Returns the fraction found (must equal 1.0 to pass)."""
    raise NotImplementedError("requires the generated document corpus (LLM verbalisation step)")
