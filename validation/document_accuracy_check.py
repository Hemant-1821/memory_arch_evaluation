"""Document accuracy check (reference doc §3.1 validation table).
Threshold: per RAGEval - sampled documents checked for invented content and completeness.
"""

def document_accuracy_check(documents: list[str], entities: dict, sample_size: int = 20) -> float:
    """Samples `sample_size` documents and checks every fact stated in them
    traces back to a real triple/entity (no invented content) and that no
    required fact was dropped. Returns the pass rate (per RAGEval methodology)."""
    raise NotImplementedError("requires the generated document corpus (LLM verbalisation step)")
