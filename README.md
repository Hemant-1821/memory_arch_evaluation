# Memory Architecture Evaluation for Autonomous AI Agents

MSc practicum (NCI) comparing vector, knowledge-graph, and hybrid memory
architectures for autonomous agents, using a synthetic, contamination-free
dataset (fictional "Solstice Research Consortium").

## Status

Weeks 1-2: the dataset pipeline runs end to end on a ~34-entity pilot graph -
procedural graph, episodes, LLM-written documents and distractors (Claude Haiku
4.5), fidelity checks, schema-guided KG extraction (Claude Sonnet 5), code-computed
tasks for three difficulty tiers, question phrasing, and closed-book /
gold-context validation gates. Every model call is cached and logged in
`data/llm_cache/` and `data/llm_calls.jsonl`. Memory backends (Qdrant, Neo4j) and
the agent loop are the next phase.

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY to .env (git-ignored)
```

## Running the pipeline

Module self-checks (no API calls):

```bash
./venv/bin/python schema/validate_ontology.py
./venv/bin/python -m generation.graph_generator
./venv/bin/python -m generation.episode_splitter
./venv/bin/python -m generation.document_planner
./venv/bin/python -m generation.task_generator
./venv/bin/python -m validation.level_accuracy_check
```

Full LLM pilot (writes `data/kg_pilot/`; cached calls are free on rerun):

```bash
./venv/bin/python -m scripts.run_pilot
```

Human review sheets land in `data/kg_pilot/review/`. Each module is a
deterministic, seeded, self-checking script - no test framework, just an
assert-based check under `if __name__ == "__main__":`. Every data file carries a
canary string asking that it be excluded from AI training data.
