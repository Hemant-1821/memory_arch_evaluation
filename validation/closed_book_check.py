"""Closed-book leakage check (reference doc §3.1 validation table).
Threshold: backbone answers at-or-near chance with no memory access, 3 samples.
"""

def closed_book_check(task: dict, backbone_client, samples: int = 3) -> bool:
    """Runs the backbone `samples` times with no memory/tool access on
    task["question"] and checks its accuracy is at-or-near chance.
    Returns True (passes) if the task is safe to include - i.e. the backbone
    could NOT already answer it from parametric knowledge alone."""
    raise NotImplementedError("requires backbone LLM access")
