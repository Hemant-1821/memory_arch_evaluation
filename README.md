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

Week 6: everything runs on the Anthropic API - Claude Haiku 5.5 writes documents and
phrases questions; Claude Sonnet 5.5 runs the agent, the closed-book / gold-context
checks, KG extraction and the fidelity / ambiguity checks. The Sol runs in
`results/pilot_full/` stay as development runs and still replay from the cache. The
agent passes every response block back unchanged and uses prompt caching. Haiku 5.5's
safety filter refused some harmless documents because of invented names ("Virel ..."
reads like "viral", "Vamtu-367" like a strain code), so the name generator no longer
makes such names; refusals are logged, retried within the existing attempts, and an
agent refusal is recorded as `refused` in the run. No fact links an entity to itself
any more (the generator and the episode splitter could make "X reports to X"), and
questions about who works on a project say the project's lead is not counted (`leads`
and `works_at` are separate relations). Rebuilt pilot: 38 documents (1 distractor
flagged), document accuracy 0.97, extraction precision 0.96 / recall 1.00, 13/13
questions kept, 1 writing refusal that passed on retry. Calibration run (13 tasks x 3
conditions, 1 seed) in `results/calibration_sonnet55/`: accuracy vector 11/13, graph
13/13, hybrid 13/13; average cost per run vector $0.040, graph $0.017, hybrid $0.021.
Full-run estimate (731 documents, 90 tasks, 5 seeds): about $10 for the dataset and $39
for the experiment, about $49 in total. Run-day steps are in `docs/run_day_checklist.md`;
a stopped run restarts with the same command and pays for nothing twice.

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

Needs the memory stores (`docker compose up -d`) and `ANTHROPIC_API_KEY` in `.env`. The
agent model is `backbone_model` in `configs/llm_config.yaml`; `--model gpt-6.1-sol`
replays the week-4/5 Azure runs from the cache.

```bash
./venv/bin/python -m agent.react                                   # self-check, no API calls
./venv/bin/python -m scripts.run_experiment --name calibration_sonnet55 --per-tier 30 --seeds 1 --max-usd 1.5
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
