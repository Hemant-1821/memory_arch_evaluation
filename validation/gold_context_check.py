"""Gold-context ceiling check (decision 2.19): the backbone (Sol) gets the question plus the
needed facts as plain code-written statements, 3 times; the task is kept if at
least 2 answers are correct."""
from generation.facts import fact_to_statement
from validation.grading import answer_question, grade


def gold_context_check(task, entities, triples, samples=3) -> dict:
    by_id = {t["fact_id"]: t for t in triples}
    facts = [fact_to_statement(by_id[f], entities) for f in task["reasoning_path"]]
    answers = [answer_question(task["question"], facts, "gold_context", i) for i in range(samples)]
    correct = [grade(task, a["answer"], entities, triples) for a in answers]
    return {"passed": sum(correct) >= 2, "correct": correct, "answers": answers}
