"""The experiment agent (reference doc 3.2): one purpose-built ReAct loop, identical
in every condition - only the tool list changes (decision 4.3). Vector gets
search_memory, graph gets the four traversal tools, hybrid gets all five and
chooses per step (agentic hybrid, not HybridRAG's fixed fusion). The harness binds
as_of_episode and k; the model never sees or sets them."""
import json
import time

from generation.facts import contains_name, display_name, period_label
from generation.llm_client import call_azure, load_prompt
from validation.grading import grade

MAX_STEPS = 10  # decision 4.4: hitting the limit counts as a failure


def _tool(tool_name, description, **props):
    return {"type": "function", "name": tool_name, "description": description, "strict": True,
            "parameters": {"type": "object", "properties": props, "required": list(props),
                           "additionalProperties": False}}


STR = {"type": "string"}
VECTOR_TOOLS = [_tool("search_memory", "Find passages in the organisation's documents that are similar to a query.",
                      query=STR)]
GRAPH_TOOLS = [
    _tool("find_entity", "Find entities (people, teams, projects, ...) whose name contains the given text.", name=STR),
    _tool("get_neighbours", "List every current relation of the named entity, in both directions.", name=STR),
    _tool("follow_relation", "List the entities linked to the named entity by one relation "
          "(e.g. leads, member_of, has_skill, status). Direction 'out' follows name -> target, 'in' finds sources.",
          name=STR, relation=STR, direction={"type": "string", "enum": ["out", "in"]}),
    _tool("filter_by_attribute", "List entities of a type linked by a relation to a value, "
          "e.g. Project / status / active, or Person / has_skill / Signal Processing.",
          entity_type=STR, relation=STR, value=STR),
]
FINAL = _tool("final_answer", "Give your final answer and end the task.",
              answer={"type": "array", "items": STR}, explanation=STR)
TOOLS = {"vector": VECTOR_TOOLS, "graph": GRAPH_TOOLS, "hybrid": VECTOR_TOOLS + GRAPH_TOOLS}


def _call_tool(name, args, vector, graph, as_of):
    if name == "search_memory":
        return [{"period": period_label(h["episode"]), "text": h["text"]}
                for h in vector.search_memory(args["query"], as_of)]
    if name == "find_entity":
        return graph.find_entity(args["name"])
    if name == "get_neighbours":
        return graph.get_neighbours(args["name"], as_of)
    if name == "follow_relation":
        return graph.follow_relation(args["name"], args["relation"], as_of, args["direction"])
    return graph.filter_by_attribute(args["entity_type"], args["relation"], args["value"], as_of)


def recall(task, tool_outputs, entities, triples) -> float:
    """Share of the task's required facts whose subject AND object names appear together
    in one tool output - the same rule for every condition (decision 4.5)."""
    by_id = {t["fact_id"]: t for t in triples}
    facts = [by_id[f] for f in task["reasoning_path"]]
    found = sum(any(contains_name(out, display_name(f["subject"], entities)) and
                    contains_name(out, display_name(f["object"], entities)) for out in tool_outputs)
                for f in facts)
    return round(found / len(facts), 4) if facts else 0.0


def run_task(task, condition, vector, graph, entities, triples, seed, model=None) -> dict:
    tools = TOOLS[condition] + [FINAL]
    items = [{"role": "system", "content": load_prompt("agent")}, {"role": "user", "content": task["question"]}]
    run = {"task_id": task["task_id"], "tier": task["tier"], "condition": condition, "seed": seed,
           "answer": None, "explanation": None, "correct": False, "steps": 0, "hit_step_limit": False,
           "input_tokens": 0, "cached_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
           "model_latency_s": 0.0, "tool_latency_s": 0.0, "tools_per_step": [], "error": None}
    outputs = []
    for step in range(MAX_STEPS):
        r = call_azure("experiment_agent", items, tools=tools, sample=seed, model=model)
        run["steps"] = step + 1
        for k in ("input_tokens", "cached_tokens", "output_tokens", "cost_usd"):
            run[k] += r[k]
        run["model_latency_s"] += r["latency_s"]
        items += r["output"]  # incl. encrypted reasoning, so the next turn continues the same thought
        calls = [o for o in r["output"] if o["type"] == "function_call"]
        run["tools_per_step"].append([c["name"] for c in calls])
        if final := next((c for c in calls if c["name"] == "final_answer"), None):
            args = json.loads(final["arguments"])
            run["answer"], run["explanation"] = args["answer"], args["explanation"]
            break
        if not calls:
            items.append({"role": "user", "content": "Call final_answer to give your answer."})
        for c in calls:
            start = time.perf_counter()
            out = json.dumps(_call_tool(c["name"], json.loads(c["arguments"]), vector, graph, task["as_of_episode"]))
            run["tool_latency_s"] += time.perf_counter() - start
            outputs.append(out)
            items.append({"type": "function_call_output", "call_id": c["call_id"], "output": out})
    else:
        run["hit_step_limit"] = True
    run["correct"] = run["answer"] is not None and grade(task, run["answer"], entities, triples)
    run["recall"] = recall(task, outputs, entities, triples)
    run["latency_s"] = round(run["model_latency_s"] + run["tool_latency_s"], 3)
    run["cost_usd"] = round(run["cost_usd"], 6)
    return run


if __name__ == "__main__":
    assert [t["name"] for t in TOOLS["hybrid"]] == ["search_memory"] + [t["name"] for t in GRAPH_TOOLS]
    entities = {"P1": {"display_name": "Kivo Ranet"}, "L1": {"display_name": "Hedto"}, "L2": {"display_name": "Tapdiho"}}
    triples = [{"fact_id": "f1", "subject": "P1", "predicate": "based_in", "object": "L1"},
               {"fact_id": "f2", "subject": "P1", "predicate": "based_in", "object": "L2"}]
    task = {"reasoning_path": ["f1", "f2"]}
    assert recall(task, ['[{"subject": "Kivo Ranet", "object": "Hedto"}]'], entities, triples) == 0.5
    assert recall(task, ['["Kivo Ranet"]', '["Hedto"]'], entities, triples) == 0.0, "names must co-occur in one output"
    print("agent/react.py: OK")
