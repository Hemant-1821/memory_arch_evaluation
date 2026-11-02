# Run-day checklist: full dataset + full experiment

Only on the user's explicit go. Every command runs from the repo root. Anything that can
call a paid model starts with `AZURE_OPENAI_API_KEY=blocked` (Azure is not used any more).
Expected cost: about $49 in total (dataset ~$10, experiment ~$7.9 per
seed); expected time: pipeline ~3 h, experiment ~4 h. Keep the terminal open.

## Pre-flight

1. Branch and clean tree (only `.claude/` may show as untracked):
   ```bash
   git switch week-6-claude-models     # or main, once week 6 is merged
   git status --short
   ```
2. Disk: at least 15 GB free (Docker's disk got corrupted at 0 free in week 3).
   ```bash
   df -h .
   ```
3. Backup of data and results:
   ```bash
   tar czf ~/memarch_backup_$(date +%Y%m%d_%H%M).tgz data results configs
   ```
4. Memory stores up and healthy:
   ```bash
   docker compose up -d && docker compose ps
   ./venv/bin/python -m memory.vector_store && ./venv/bin/python -m memory.graph_store
   ```
5. Self-checks (no API calls; the splitter check covers "no self-loop facts" at full size):
   ```bash
   ./venv/bin/python schema/validate_ontology.py
   for m in generation.graph_generator generation.episode_splitter generation.document_planner \
            generation.task_generator generation.facts validation.level_accuracy_check \
            validation.grading agent.react; do ./venv/bin/python -m $m || break; done
   ```
6. API key present (prints only True/False, never the key):
   ```bash
   ./venv/bin/python -c "import os, generation.llm_client; print('key set:', bool(os.environ.get('ANTHROPIC_API_KEY')))"
   ```
7. Note the starting point, for the cost checkpoints and the refusal count:
   ```bash
   wc -l < data/llm_calls.jsonl                      # write down as L0
   ./venv/bin/python -c "from generation.llm_client import spent_usd; print(round(spent_usd(), 2))"   # S0
   ```
8. Set the cap (`budget.cap_usd` in `configs/llm_config.yaml`) to **S0 + 75**. Reason: the
   projection is $49; x1.5 margin for bigger full-size prompts and retries is ~$74,
   rounded up. The cap is only a runaway guard - one full rerun would still fit in the $200 credit.

## Run, in this order

9. Full dataset (~3 h; writes `data/kg_full/`):
   ```bash
   AZURE_OPENAI_API_KEY=blocked caffeinate -i ./venv/bin/python -u -m scripts.run_pipeline --full 2>&1 | tee -a private/full_pipeline.log
   ```
10. Check the dataset before spending on the experiment:
    ```bash
    cat data/kg_full/summary.json
    ./venv/bin/python -c "import json; r=[json.loads(l) for l in open('data/llm_calls.jsonl')][L0:]; print(len(r), 'calls', round(sum(x['cost_usd'] for x in r), 2), 'USD, refusals:', [(x['step'], x.get('refusal_category')) for x in r if x.get('stop_reason') == 'refusal'])"
    ```
    (replace `L0`.) Go on only if: documents 731, flagged a handful at most, document accuracy and
    extraction precision/recall close to the pilot (0.97 / 0.96 / 1.00), kept tasks close to 30 per
    tier, every refusal in `document_writing` and retried. Skim `data/kg_full/review/questions.csv`
    and the flagged rows of `documents.csv`.
11. Load the memory stores (smoke test prints one question and hits from both stores):
    ```bash
    ./venv/bin/python -m scripts.load_memory data/kg_full
    ```
12. Full experiment, 5 seeds (~4 h):
    ```bash
    AZURE_OPENAI_API_KEY=blocked caffeinate -i ./venv/bin/python -u -m scripts.run_experiment --dataset data/kg_full --name full_sonnet55 --per-tier 30 --seeds 5 --max-usd 60 2>&1 | tee -a private/full_experiment.log
    ```
    `--max-usd 60` = the experiment projection (~$39) x1.5. Runs go low, medium, high
    within each seed, so the projected total is only meaningful after the first seed.
13. Check the runs:
    ```bash
    cat results/full_sonnet55/summary.json
    ./venv/bin/python -c "import json; r=[json.loads(l) for l in open('results/full_sonnet55/runs.jsonl')]; print(len(r), 'runs; errors', sum(bool(x.get('error')) for x in r), '; refused', sum(bool(x.get('refused')) for x in r), '; step limit', sum(bool(x.get('hit_step_limit')) for x in r))"
    ```
    Expect 0 errors. Any error run: see "If something goes wrong", then rerun step 12.

## Cost checkpoints

- After step 9: spend since S0 should be near $10. Above $15: stop and find out why.
- During step 12: each line prints the run cost; after seed 1 (270 runs) spend should be near
  $7.9. The script stops itself if the projected total passes `--max-usd`.
- Spend since the start at any time:
  ```bash
  ./venv/bin/python -c "from generation.llm_client import spent_usd; print(round(spent_usd() - S0, 2))"
  ```

## If something goes wrong

Restart = the **same command**. Every finished model call is cached in `data/llm_cache/` and replays
for free. Evidence (week 6): the pilot pipeline was killed after 72 paid calls and the calibration
after 6 runs; on restart 0 of those calls were billed again, the 6 runs replayed identically.
Only a call that was in flight at the moment of the kill can be paid twice (it is billed but never
logged); that is one call, a cent or two.

- **Crash, Ctrl-C, power or network loss, Docker down:** `docker compose up -d` if needed, rerun the
  same command. `run_experiment` rewrites `runs.jsonl` from the start; finished runs replay.
- **Refusal while writing a document:** counted as a failed attempt and retried; nothing to do.
- **"refused on all 3 attempts - stopping" (pipeline):** do not edit or skip the document. Note
  the doc_id and category and tell the user. Pre-agreed fallback (user, 2026-11-02): all document
  writing moves to Haiku 4.5, never mixed; that is the user's call.
- **Refusal in phrasing, checks, extraction or gates (pipeline stops):** stop and report (6.8).
- **Agent refusal:** recorded as `refused: true` in the run, the experiment continues; report the count.
- **`BudgetExceeded: logged spend ... >= cap`:** the pipeline stops. In `run_experiment` it is
  recorded as a failed run with an `error` and every later run fails at once ($0): press Ctrl-C,
  check the spend, raise `cap_usd` if the spend is expected, rerun the same command.
- **`one call cost $... > $0.05`:** that run is recorded with an `error`; the expensive turn is
  already cached. Look at it; if it is legitimate, raise `max_call_usd` and rerun the same command
  (the turn replays free).
- **`STOP: projected $... > --max-usd`:** check the per-run costs; rerun with a higher `--max-usd`
  only if they are explained.

## Afterwards: commit (on the week branch, no push until reviewed)

```bash
git status --short     # never add private/, .claude/, .env or results/*/analysis/
git add configs/llm_config.yaml data/kg_full data/llm_cache data/llm_calls.jsonl
git commit -m "data: full dataset - <documents, accuracy, P/R, kept per tier, refusals, cost>"
git add results/full_sonnet55/runs.jsonl results/full_sonnet55/summary.json data/llm_cache data/llm_calls.jsonl
git commit -m "data: full experiment, 5 seeds - <accuracy per condition, refusals, cost>"
```

Then add the numbers and the spend to the decision log. The analysis
(`scripts/analyse_results.py`) waits for the agreed discussion of its settings.
