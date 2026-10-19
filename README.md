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
`data/llm_cache/` and `data/llm_calls.jsonl`. The agent loop is the next phase.

Week 3: local memory stores - Qdrant (vector condition: overlapping word chunks,
local `bge-small` embeddings, old chunks never removed) and Neo4j (graph
condition: extracted KG where a newer fact invalidates the old edge, queried via
four fixed tools). The pipeline also runs at full size with `--full`.

Week 4: the experiment agent - one ReAct loop for all three conditions (only the
tool list changes; the hybrid agent picks vector or graph tools per step), max 10
steps, backbone GPT-6.1 Sol on Azure. Each run records correctness, steps, tokens
(incl. cached), latency and fact recall. End-to-end pilot test (3 tasks x 3
conditions): results in `results/e2e_pilot/`.

Week 5: the closed-book and gold-context checks now run on the backbone (Sol), so
they test the same model as the agent (pilot: 12/12 questions kept). Full pilot run,
12 tasks x 3 conditions, in `results/pilot_full/`: accuracy vector 11/12, graph
12/12, hybrid 12/12; average cost per run vector $0.022, graph $0.007, hybrid
$0.008. The graph tools `follow_relation` and `filter_by_attribute` now return
whole links (subject, predicate, object), so fact recall sees both names of a fact.
Full-size estimate (729 documents, 90 tasks): about $12 Claude for the dataset,
about $4 Azure per seed for the experiment.

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY to .env (git-ignored)
```

## Memory stores

```bash
docker compose up -d                          # Qdrant :6333, Neo4j :7474/:7687 (localhost only)
./venv/bin/python -m memory.vector_store      # self-checks (need the stores running)
./venv/bin/python -m memory.graph_store
./venv/bin/python -m scripts.load_memory data/kg_pilot
```

## Running the experiment

Needs the memory stores (`docker compose up -d`) and `AZURE_OPENAI_ENDPOINT` /
`AZURE_OPENAI_API_KEY` in `.env` (deployment names live in `configs/llm_config.yaml`).

```bash
./venv/bin/python -m agent.react                                   # self-check, no API calls
./venv/bin/python -m scripts.run_experiment --name pilot_full --per-tier 30 --seeds 1 --max-usd 1.0
```

Runs are seed-major and replay from the cache for free; `--max-usd` stops early if
the projected cost of the whole run is too high.

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
./venv/bin/python -m scripts.run_pipeline          # pilot; add --full for the full dataset
```

Human review sheets land in `data/kg_pilot/review/`. Each module is a
deterministic, seeded, self-checking script - no test framework, just an
assert-based check under `if __name__ == "__main__":`. Every data file carries a
canary string asking that it be excluded from AI training data.
