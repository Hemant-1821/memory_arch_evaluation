"""Automatic phrasing guard (decision 2.12): Sonnet confirms the phrased question
means exactly what the code-written meaning says. Human review comes after."""
from generation.llm_client import call_llm, load_prompt

SCHEMA = {"type": "object",
          "properties": {"faithful": {"type": "boolean"}, "issue": {"type": "string"}},
          "required": ["faithful", "issue"], "additionalProperties": False}


def ambiguity_check(task: dict, question: str, attempt: int = 0) -> dict:
    r = call_llm("backbone", "ambiguity_check", "You review questions for exact meaning.",
                 load_prompt("ambiguity_checker").format(meaning=task["meaning"], question=question),
                 schema=SCHEMA, sample=attempt)["json"]
    return {"passed": r["faithful"], "issue": r["issue"]}


if __name__ == "__main__":
    task = {"meaning": "Which team is Kivo Ranet currently a member of?"}
    assert ambiguity_check(task, "Which team is Kivo Ranet on these days?")["passed"]
    assert not ambiguity_check(task, "Which project does Kivo Ranet lead?")["passed"]
    print("validation/ambiguity_check.py: OK")
