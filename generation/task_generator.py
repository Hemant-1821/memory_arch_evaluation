"""Graph-traversal half of task generation: hop counts, constraint counting,
low/medium/high classification, and a staffing constraint-checker. Pure
graph algorithm work - question phrasing (LLM) is stubbed separately.
"""
import networkx as nx


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

    led_projects = {
        t["object"] for t in triples
        if t["predicate"] == "leads" and t["subject"] == person_id and t["object"] != project_id
    }
    for led_project in led_projects:
        if entities.get(led_project, {}).get("status") != "active":
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

    active_project_counts: dict[str, int] = {}
    for t in triples:
        if t["predicate"] == "works_at" and entities.get(t["object"], {}).get("status") == "active":
            active_project_counts[t["subject"]] = active_project_counts.get(t["subject"], 0) + 1
    if any(active_project_counts.get(p, 0) > max_active_projects_per_person for p in candidate_people):
        return False

    if any(has_conflict_of_interest(p, project_id, entities, triples) for p in candidate_people):
        return False

    return True


def make_task_candidate(
    task_id: str, tier: str, reasoning_path: list[str], required_hops: int,
    constraint_type: str, source_entities: list[str], as_of_episode: int,
) -> dict:
    """Matches reference doc §5's task record schema. question/ground_truth_answer
    are populated later by the LLM phrasing step (out of scope here)."""
    return {
        "task_id": task_id,
        "tier": tier,
        "question": None,
        "ground_truth_answer": None,
        "reasoning_path": reasoning_path,
        "required_hops": required_hops,
        "constraint_type": constraint_type,
        "source_entities": source_entities,
        "as_of_episode": as_of_episode,
        "validation": {"closed_book_passed": None, "fidelity_score": None, "ambiguity_checked": None},
    }


def phrase_task_as_question(candidate: dict) -> str:
    """Stub: turning a validated (entities, path, constraints) tuple into a
    natural-language question is an LLM step."""
    raise NotImplementedError("requires the generation-model LLM - see reference doc §3.1 step 7")


if __name__ == "__main__":
    from generation.graph_generator import generate_graph
    from generation.episode_splitter import split_into_episodes, current_state

    triples, entities = generate_graph(seed=7, pilot=True)
    episoded = split_into_episodes(triples, seed=7, pilot=True)
    last_episode = max(t["episode_id"] for t in episoded)
    live = current_state(episoded, as_of_episode=last_episode)

    # compute_hops on the real pilot graph: a member_of edge is 1 hop, an
    # unrelated/unreachable pair is None. Named as a produced interface in
    # the plan's Interfaces block but not otherwise exercised - covering it
    # directly instead of leaving it as an untested deliverable.
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

    # has_conflict_of_interest is derived correctly from hand-built triples
    # (deterministic - not dependent on whether the pilot RNG happened to
    # produce a COI this run). Person leads Project_0000; Project_0000 and
    # Project_0001 share a sponsor -> staffing them on Project_0001 is a COI.
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

    # make_task_candidate produces the exact reference-doc schema shape.
    candidate = make_task_candidate(
        "pilot_001", "low", [any_project], 1, "single_fact", [any_project], last_episode
    )
    assert candidate["question"] is None and candidate["ground_truth_answer"] is None
    assert set(candidate.keys()) == {
        "task_id", "tier", "question", "ground_truth_answer", "reasoning_path",
        "required_hops", "constraint_type", "source_entities", "as_of_episode", "validation",
    }

    print("generation/task_generator.py: OK (classification + staffing checker verified)")
