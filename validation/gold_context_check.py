"""Gold-context ceiling check (reference doc §3.1 validation table).
Threshold: backbone must pass when given the correct facts directly - works
with closed_book_check to distinguish "needs memory" from "solvable at all".
"""

def gold_context_check(task: dict, backbone_client) -> bool:
    """Runs the backbone once with task["reasoning_path"]'s facts injected
    directly into context (no retrieval) and checks it produces
    task["ground_truth_answer"]. Returns True if it passes."""
    raise NotImplementedError("requires backbone LLM access")
