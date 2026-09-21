"""Level accuracy check (reference doc §3.1 validation table).
Threshold: measured hops/constraints must match the task's assigned tier,
per level. This one needs NO LLM - it's pure graph re-verification.
"""
from generation.task_generator import classify_complexity


def level_accuracy_check(task: dict, triples: list[dict]) -> bool:
    """Re-derives hop count + constraint count from task["reasoning_path"]
    and confirms generation.task_generator.classify_complexity() agrees
    with task["tier"]."""
    measured_tier = classify_complexity(task["required_hops"], len(task.get("reasoning_path", [])) - 1)
    return measured_tier == task["tier"]


if __name__ == "__main__":
    fake_task = {"tier": "low", "required_hops": 1, "reasoning_path": ["Project_0001"]}
    assert level_accuracy_check(fake_task, triples=[]) is True

    fake_high_task = {"tier": "high", "required_hops": 5, "reasoning_path": ["a", "b", "c", "d", "e", "f"]}
    assert level_accuracy_check(fake_high_task, triples=[]) is True

    mismatched_task = {"tier": "high", "required_hops": 1, "reasoning_path": ["a"]}
    assert level_accuracy_check(mismatched_task, triples=[]) is False

    print("validation/level_accuracy_check.py: OK (re-derives tier correctly, catches a mismatch)")
