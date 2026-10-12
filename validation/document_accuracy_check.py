"""Document accuracy (reference doc §3.1, per RAGEval): share of documents with no
invented claims. Computed from fidelity_check results - the same Sonnet pass
checks both (decision 2.20), so this costs nothing extra."""


def document_accuracy_check(results: list[dict]) -> float:
    checked = [r for r in results if r.get("verdicts") is not None and not r.get("missing_names")]
    return sum(not r["invented_claims"] for r in checked) / len(checked) if checked else 1.0


if __name__ == "__main__":
    rs = [{"verdicts": {}, "missing_names": [], "invented_claims": []},
          {"verdicts": {}, "missing_names": [], "invented_claims": ["X leads Y"]}]
    assert document_accuracy_check(rs) == 0.5
    assert document_accuracy_check([]) == 1.0
    print("validation/document_accuracy_check.py: OK")
