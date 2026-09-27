"""Objective scoring (decision 2.13): the backbone returns {answer, explanation};
only `answer` is scored, after name normalisation. Lists compare as sets; the
high tier is scored by the staffing checker. `explanation` is kept for human
review (decision 2.14)."""
from generation.episode_splitter import current_state
from generation.facts import normalise_name
from generation.llm_client import call_llm, load_prompt
from generation.task_generator import check_staffing_candidate

SCHEMA = {"type": "object",
          "properties": {"answer": {"type": "array", "items": {"type": "string"}},
                         "explanation": {"type": "string"}},
          "required": ["answer", "explanation"], "additionalProperties": False}


def answer_question(question, facts, step, sample) -> dict:
    context = ("Known facts:\n" + "\n".join(f"- {f}" for f in facts)) if facts else \
        "You have no documents or notes about this organisation."
    return call_llm("backbone", step, "You answer questions about an organisation.",
                    load_prompt("answer").format(context=context, question=question),
                    schema=SCHEMA, sample=sample)["json"]


def grade(task, answer_names, entities, triples) -> bool:
    given = {normalise_name(n) for n in answer_names if n.strip()}
    if task["tier"] != "high":
        return given == {normalise_name(n) for n in task["ground_truth_answer"]}
    people = {normalise_name(a["display_name"]): e for e, a in entities.items() if a["entity_type"] == "Person"}
    if not given or not given <= set(people):
        return False
    live = current_state(triples, task["as_of_episode"])
    return check_staffing_candidate([people[n] for n in given], task["project"], entities, live)


if __name__ == "__main__":
    task = {"tier": "medium", "ground_truth_answer": ["Kivo Ranet", "Salo Dimet"]}
    assert grade(task, ["salo dimet", "Dr. Kivo Ranet"], {}, [])
    assert not grade(task, ["Kivo Ranet"], {}, [])
    assert not grade({"tier": "low", "ground_truth_answer": ["Photonic Sensing Group"]}, [""], {}, [])
    print("validation/grading.py: OK")
