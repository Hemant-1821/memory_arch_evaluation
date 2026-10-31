"""Closed-book leakage check (decision 2.15): the backbone (Sol) answers the bare question 3
times with no documents; the task is kept only if all 3 answers are wrong."""
from validation.grading import answer_question, grade


def closed_book_check(task, entities, triples, samples=3) -> dict:
    answers = [answer_question(task["question"], None, "closed_book", i) for i in range(samples)]
    correct = [grade(task, a["answer"], entities, triples) for a in answers]
    return {"passed": not any(correct), "correct": correct, "answers": answers}
