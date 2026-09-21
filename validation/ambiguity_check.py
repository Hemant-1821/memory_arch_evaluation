"""Ambiguity check (reference doc §3.1 validation table).
Threshold: 100% - one answer for low/medium tier tasks; checker-program
correctness for high tier tasks.
"""

def ambiguity_check(task: dict, entities: dict, triples: list[dict]) -> bool:
    """For low/medium tier: confirms exactly one entity/value satisfies
    task["reasoning_path"]. For high tier: confirms the constraint checker
    (generation.task_generator.check_staffing_candidate) itself is correct
    against task["ground_truth_answer"]. Returns True if unambiguous/correct."""
    raise NotImplementedError("requires LLM-phrased question text to check against")
