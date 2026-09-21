# Memory Architecture Evaluation for Autonomous AI Agents

MSc practicum (NCI) comparing vector, knowledge-graph, and hybrid memory
architectures for autonomous agents, using a synthetic, contamination-free
dataset (fictional "Solstice Research Consortium").

## Status

Phase 1, Weeks 1-2: the no-LLM-inference slice of the dataset pipeline is
built - ontology, sizing/LLM config, invented-name generation, procedural
knowledge graph generation, episode/temporal replacement logic, and
task-complexity traversal. Every LLM-dependent step (document generation,
KG extraction, question phrasing, 5 of 6 validation checks) is a stub that
raises `NotImplementedError`, pending API key provisioning.

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Running the pipeline

```bash
./venv/bin/python schema/validate_ontology.py
./venv/bin/python -m generation.entity_namer
./venv/bin/python -m generation.graph_generator     # writes data/kg_pilot/
./venv/bin/python -m generation.episode_splitter
./venv/bin/python -m generation.task_generator
./venv/bin/python -m validation.level_accuracy_check
```

Each module is a deterministic, seeded, self-checking script - no test
framework, just an assert-based check under `if __name__ == "__main__":`.
