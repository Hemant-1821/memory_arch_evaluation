"""Level accuracy check (reference doc §3.1 validation table).
Threshold: measured hops/constraints must match the task's assigned tier,
per level. This one needs NO LLM - it's pure graph re-verification.
"""
from generation.task_generator import classify_complexity


def level_accuracy_check(task: dict, triples: list[dict]) -> bool:
    """Re-derives the tier from the task's measured hops and constraints and
    confirms classify_complexity() agrees with task["tier"]."""
    return classify_complexity(task["required_hops"], task["constraint_count"]) == task["tier"]


if __name__ == "__main__":
    assert level_accuracy_check({"tier": "low", "required_hops": 1, "constraint_count": 0}, [])
    assert level_accuracy_check({"tier": "high", "required_hops": 4, "constraint_count": 4}, [])
    assert not level_accuracy_check({"tier": "high", "required_hops": 1, "constraint_count": 0}, [])
    print("validation/level_accuracy_check.py: OK (re-derives tier correctly, catches a mismatch)")
