"""Task generation: hop counts, constraint counting, low/medium/high
classification, a staffing constraint-checker, and code that builds every task
with its correct answer computed from the ground-truth graph (decision 2.11).
The LLM only phrases questions.
"""
import random
from collections import Counter, defaultdict
from itertools import combinations

import networkx as nx

from generation.episode_splitter import current_state
from generation.facts import display_name
from generation.llm_client import call_llm, load_prompt
from generation.seeding import derive_seed


def _build_graph(triples: list[dict]) -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    for t in triples:
        obj = t["object"]
        if isinstance(obj, str) and "_" in obj and obj.split("_")[-1].isdigit():
            g.add_edge(t["subject"], obj, predicate=t["predicate"])
    return g


def compute_hops(triples: list[dict], source_id: str, target_id: str) -> int | None:
    g = _build_graph(triples)
    if source_id not in g or target_id not in g:
        return None
    try:
        return nx.shortest_path_length(g.to_undirected(), source_id, target_id)
    except nx.NetworkXNoPath:
        return None


def classify_complexity(hops: int, constraint_count: int) -> str:
    """Reference doc §3.1: "the generator finds the shortest reasoning path
    by graph traversal; the level follows from path length + number of
    constraints" (Table 1: low=1 hop/0 constraints, medium=2-3 hops with
    grouping/filtering, high=4+ hops with constraints and a stopping decision).
    """
    if hops <= 1 and constraint_count == 0:
        return "low"
    if hops <= 3 and constraint_count <= 2:
        return "medium"
    return "high"


def _statuses(entities, triples) -> dict:
    """Project status as of the given (live) triples - status changes over
    episodes, so the static entity attribute is only the fallback."""
    status = {eid: a.get("status") for eid, a in entities.items()}
    status.update({t["subject"]: t["object"] for t in triples if t["predicate"] == "status"})
    return status


def has_conflict_of_interest(person_id: str, project_id: str, entities: dict, triples: list[dict]) -> bool:
    """Conflict of interest is derived, never stored as a flag: person P has
    a COI with project X if P already leads a DIFFERENT active project Y
    that shares a sponsor organization with X - a competing stake in the
    same funder's money. This is fully explainable from the graph (which
    project, which sponsor, which shared funder) rather than an arbitrary
    label with no underlying reason.
    """
    project_sponsors = {t["subject"] for t in triples if t["predicate"] == "sponsors" and t["object"] == project_id}
    if not project_sponsors:
        return False
    status = _statuses(entities, triples)
    led_projects = {
        t["object"] for t in triples
        if t["predicate"] == "leads" and t["subject"] == person_id and t["object"] != project_id
    }
    for led_project in led_projects:
        if status.get(led_project) != "active":
            continue
        led_project_sponsors = {t["subject"] for t in triples if t["predicate"] == "sponsors" and t["object"] == led_project}
        if project_sponsors & led_project_sponsors:
            return True
    return False


def check_staffing_candidate(
    candidate_people: list[str],
    project_id: str,
    entities: dict,
    triples: list[dict],
    max_team_size: int = 4,
    max_active_projects_per_person: int = 2,
) -> bool:
    """Checkable staffing constraint set, matching reference doc §1's worked
    example: covers required skills, team size, per-person active-project
    load, and conflict-of-interest exclusion (see has_conflict_of_interest)."""
    if not candidate_people:
        return False
    if len(candidate_people) > max_team_size:
        return False

    required_skills = {t["object"] for t in triples if t["predicate"] == "requires_skill" and t["subject"] == project_id}
    covered_skills = {
        t["object"] for t in triples
        if t["predicate"] == "has_skill" and t["subject"] in candidate_people
    }
    if not required_skills.issubset(covered_skills):
        return False

    status = _statuses(entities, triples)
    active_project_counts: dict[str, int] = {}
    for t in triples:
        if t["predicate"] == "works_at" and status.get(t["object"]) == "active":
            active_project_counts[t["subject"]] = active_project_counts.get(t["subject"], 0) + 1
    if any(active_project_counts.get(p, 0) > max_active_projects_per_person for p in candidate_people):
        return False

    if any(has_conflict_of_interest(p, project_id, entities, triples) for p in candidate_people):
        return False

    return True


def make_task_candidate(task_id, tier, meaning, answer, reasoning_path, required_hops,
                        constraint_count, constraint_type, source_entities, as_of_episode, project=None) -> dict:
    """Task record (reference doc §5, extended with decisions 2.11-2.15). The
    answer is computed by code; `question` is filled in by the phrasing step."""
    return {"task_id": task_id, "tier": tier, "meaning": meaning,
            "question": None, "ground_truth_answer": answer, "reasoning_path": reasoning_path,
            "required_hops": required_hops, "constraint_count": constraint_count,
            "constraint_type": constraint_type, "source_entities": source_entities,
            "as_of_episode": as_of_episode, "project": project, "checks": {}, "status": None}


LOOKUP_MEANINGS = {
    "member_of": "Which team is {s} currently a member of?",
    "leads": "Which project does {s} currently lead?",
    "based_in": "Where is {s} currently based?",
    "reports_to": "Who does {s} currently report to?",
    "located_at": "Where is {s} currently located?",
    "status": "What is the current status of project {s}?",
    "availability": "What is the current availability of equipment {s}?",
}
STAFFING_MEANING = ("Propose a team of at most 4 people for project {p} that together covers all of the "
                    "project's required skills, where nobody is already working on more than 2 active "
                    "projects, and nobody has a conflict of interest (a person has one if they already "
                    "lead a different active project that shares a sponsor with {p}). Answer: the team members.")


def _low(live, triples, entities, rng, n, as_of):
    per_key = Counter((t["subject"], t["predicate"]) for t in live)
    changed = {(t["subject"], t["predicate"]) for t in triples if t["superseded_in_episode"] is not None}
    cands = [t for t in live if t["predicate"] in LOOKUP_MEANINGS and per_key[(t["subject"], t["predicate"])] == 1]
    rng.shuffle(cands)
    cands.sort(key=lambda t: (t["subject"], t["predicate"]) not in changed)  # changed facts first (stable)
    name = lambda x: display_name(x, entities)
    return [make_task_candidate(f"low_{i:02d}", "low",
                                LOOKUP_MEANINGS[t["predicate"]].format(s=name(t["subject"])),
                                [name(t["object"])], [t["fact_id"]], 1, 0, "single_fact",
                                [t["subject"]], as_of)
            for i, t in enumerate(cands[:n])]


def _medium(live, entities, rng, n, as_of):
    name = lambda x: display_name(x, entities)
    idx = defaultdict(list)
    for t in live:
        idx[(t["predicate"], "by_subject", t["subject"])].append(t)
        idx[(t["predicate"], "by_object", t["object"])].append(t)
    cands = []
    for p in sorted({t["object"] for t in live if t["predicate"] == "works_at"}):
        workers = idx[("works_at", "by_object", p)]
        skills_of = {w["subject"]: {s["object"]: s for s in idx[("has_skill", "by_subject", w["subject"])]}
                     for w in workers}
        for skill in sorted({k for ks in skills_of.values() for k in ks}):
            people = sorted(x for x, ks in skills_of.items() if skill in ks)
            if 1 <= len(people) < len(skills_of):  # the skill filter must exclude someone
                path = [w["fact_id"] for w in workers] + [skills_of[x][skill]["fact_id"] for x in people]
                cands.append(("filter", p, f"Which people currently working on project {name(p)} have the "
                              f"skill {name(skill)}? Answer: all of them.", [name(x) for x in people], path, 1))
        leaders = idx[("leads", "by_object", p)]
        if len(leaders) == 1:
            teams = idx[("member_of", "by_subject", leaders[0]["subject"])]
            if len(teams) == 1:
                cands.append(("chain", p, f"Which team is the current leader of project {name(p)} a member of?",
                              [name(teams[0]["object"])], [leaders[0]["fact_id"], teams[0]["fact_id"]], 0))
    rng.shuffle(cands)
    return [make_task_candidate(f"medium_{i:02d}", "medium", meaning, answer, path, 2, constraints,
                                tpl, [p], as_of)
            for i, (tpl, p, meaning, answer, path, constraints) in enumerate(cands[:n])]


def _high(live, entities, rng, n, as_of):
    name = lambda x: display_name(x, entities)
    status = _statuses(entities, live)
    people = sorted(e for e, a in entities.items() if a["entity_type"] == "Person")
    context = [t["fact_id"] for t in live if t["predicate"] in ("has_skill", "works_at", "leads", "sponsors", "status")]
    cands = []
    for p in sorted(e for e, a in entities.items() if a["entity_type"] == "Project" and status.get(e) == "active"):
        needed = {t["object"] for t in live if t["predicate"] == "requires_skill" and t["subject"] == p}
        if not needed:
            continue
        useful = [x for x in people if any(t["subject"] == x and t["object"] in needed
                                           for t in live if t["predicate"] == "has_skill")]
        # ponytail: brute force over teams of <=4 from people holding a needed skill;
        # fine for the pilot (8 people), needs a smarter search at full scale (180 people).
        team = next((list(c) for size in range(1, 5) for c in combinations(useful, size)
                     if check_staffing_candidate(list(c), p, entities, live)), None)
        if team:
            path = [t["fact_id"] for t in live if t["predicate"] == "requires_skill" and t["subject"] == p] + context
            cands.append((p, team, path))
    rng.shuffle(cands)
    return [make_task_candidate(f"high_{i:02d}", "high", STAFFING_MEANING.format(p=name(p)),
                                [name(x) for x in team], path, 4, 4, "staffing_with_conflict_of_interest",
                                [p], as_of, project=p)
            for i, (p, team, path) in enumerate(cands[:n])]


def generate_tasks(triples, entities, seed, per_level) -> list[dict]:
    as_of = max(t["episode_id"] for t in triples)  # "currently" = after the last episode
    live = current_state(triples, as_of)
    rng = random.Random(derive_seed(seed, "tasks"))
    return (_low(live, triples, entities, rng, per_level, as_of)
            + _medium(live, entities, rng, per_level, as_of)
            + _high(live, entities, rng, per_level, as_of))


PHRASE_SCHEMA = {"type": "object", "properties": {"question": {"type": "string"}},
                 "required": ["question"], "additionalProperties": False}


def phrase_task_as_question(task: dict, attempt: int = 0) -> str:
    """Haiku turns the code-written meaning into a natural question. It never
    sees the answer (decision 2.11)."""
    return call_llm("generation", "question_phrasing", "You write clear, natural workplace questions.",
                    load_prompt("question_phraser").format(meaning=task["meaning"]),
                    schema=PHRASE_SCHEMA, sample=attempt)["json"]["question"]


if __name__ == "__main__":
    from generation.graph_generator import generate_graph
    from generation.episode_splitter import split_into_episodes

    triples, entities = generate_graph(seed=7, pilot=True)
    episoded = split_into_episodes(triples, seed=7, pilot=True)
    last_episode = max(t["episode_id"] for t in episoded)
    live = current_state(episoded, as_of_episode=last_episode)

    # compute_hops on the real pilot graph: a member_of edge is 1 hop, an
    # unrelated/unreachable pair is None.
    member_of_pair = next(
        (t["subject"], t["object"]) for t in live if t["predicate"] == "member_of"
    )
    assert compute_hops(live, *member_of_pair) == 1
    assert compute_hops(live, "NoSuchEntity_0000", member_of_pair[1]) is None

    # Hand-picked classification examples.
    assert classify_complexity(hops=1, constraint_count=0) == "low"
    assert classify_complexity(hops=2, constraint_count=1) == "medium"
    assert classify_complexity(hops=5, constraint_count=3) == "high"

    # The checker rejects an empty candidate set (Review Focus: degenerate answers).
    any_project = next(eid for eid, a in entities.items() if a["entity_type"] == "Project")
    assert check_staffing_candidate([], any_project, entities, live) is False

    # The checker rejects a team over max size.
    all_people = [eid for eid, a in entities.items() if a["entity_type"] == "Person"]
    if len(all_people) > 4:
        assert check_staffing_candidate(all_people, any_project, entities, live, max_team_size=4) is False

    # has_conflict_of_interest is derived correctly from hand-built triples.
    # Person leads Project_0000; Project_0000 and Project_0001 share a sponsor
    # -> staffing them on Project_0001 is a COI.
    coi_triples = [
        {"subject": "PartnerOrganization_0000", "predicate": "sponsors", "object": "Project_0000"},
        {"subject": "PartnerOrganization_0000", "predicate": "sponsors", "object": "Project_0001"},
        {"subject": "Person_0000", "predicate": "leads", "object": "Project_0000"},
    ]
    coi_entities = {"Project_0000": {"status": "active"}, "Project_0001": {"status": "active"}}
    assert has_conflict_of_interest("Person_0000", "Project_0001", coi_entities, coi_triples) is True
    assert has_conflict_of_interest("Person_0001", "Project_0001", coi_entities, coi_triples) is False, (
        "an unrelated person must not be flagged"
    )
    assert check_staffing_candidate(["Person_0000"], "Project_0001", coi_entities, coi_triples) is False, (
        "checker must reject a candidate with a derived conflict of interest"
    )
    # Status is time-aware: once the led project is no longer active, the COI disappears.
    ended = coi_triples + [{"subject": "Project_0000", "predicate": "status", "object": "completed"}]
    assert has_conflict_of_interest("Person_0000", "Project_0001", coi_entities, ended) is False

    tasks = generate_tasks(episoded, entities, seed=7, per_level=5)
    assert tasks == generate_tasks(episoded, entities, seed=7, per_level=5), "task generation not deterministic"
    live_ids = {t["fact_id"] for t in live}
    for task in tasks:
        assert task["ground_truth_answer"], f"{task['task_id']}: empty answer"
        assert set(task["reasoning_path"]) <= live_ids, f"{task['task_id']}: path uses a non-current fact"
        assert classify_complexity(task["required_hops"], task["constraint_count"]) == task["tier"]
    for task in (t for t in tasks if t["tier"] == "high"):
        by_name = {a["display_name"]: e for e, a in entities.items()}
        team = [by_name[n] for n in task["ground_truth_answer"]]
        assert check_staffing_candidate(team, task["project"], entities, live)

    # Review Focus: a lookup on a changed fact uses the new value, never the old one.
    by_id = {t["fact_id"]: t for t in episoded}
    for task in (t for t in tasks if t["tier"] == "low"):
        fact = by_id[task["reasoning_path"][0]]
        old = [t for t in episoded if t["subject"] == fact["subject"] and t["predicate"] == fact["predicate"]
               and t["superseded_in_episode"] is not None]
        for o in old:
            if o["object"] != fact["object"]:
                assert task["ground_truth_answer"] != [display_name(o["object"], entities)], "stale answer"

    import os
    if os.environ.get("MEMARCH_LLM_DIR"):
        q = phrase_task_as_question(tasks[0])
        assert q.strip().endswith("?") and all(n not in q for n in tasks[0]["ground_truth_answer"])
        print(f"  phrased: {q}")

    counts = Counter(t["tier"] for t in tasks)
    print(f"generation/task_generator.py: OK (low {counts['low']}, medium {counts['medium']}, high {counts['high']})")
