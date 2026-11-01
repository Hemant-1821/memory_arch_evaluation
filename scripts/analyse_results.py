"""Turns an experiment's runs into the thesis tables, charts and statistics: the
pre-registered analysis of decisions 6.1/6.2, run in full and reported whether
significant or not. No LLM calls, no network.

Run: python -m scripts.analyse_results results/<name>     (no argument: self-check)

Writes results/<name>/analysis/:
  descriptives.csv  per condition x tier (+ tier "all"): accuracy (mean across seeds, SD across
                    seeds, 95% Wilson CI with the task as the unit), mean steps, step-limit rate,
                    tokens, cost, latency, recall, error count
  mcnemar.csv       exact McNemar for each condition pair, per tier and overall, on the majority
                    result per task across seeds; Holm-adjusted p across the 9 per-tier tests
  stats.json        the McNemar rows + three mixed models (correctness, steps, log cost), each
                    either fitted or "not estimable on this data: <reason>"
  summary.md        all of the above as Markdown
  accuracy_by_tier.png, steps_by_tier.png, cost_by_tier.png
Runs with an `error` count as incorrect, are counted separately, and are left out of the
step/token/cost/latency/recall means (they have none).
"""
import json
import sys
import tempfile
import warnings
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

CONDITIONS, TIERS = ["vector", "graph", "hybrid"], ["low", "medium", "high"]
COLOURS = {"vector": "#0072B2", "graph": "#E69F00", "hybrid": "#009E73"}  # Okabe-Ito, colour-blind-safe
MARKERS = {"vector": "o", "graph": "s", "hybrid": "^"}  # second cue, so colour never carries identity alone
METRICS = ["steps", "hit_step_limit", "input_tokens", "cached_tokens", "output_tokens",
           "cost_usd", "latency_s", "recall"]


def load_runs(path) -> pd.DataFrame:
    df = pd.read_json(path, lines=True)
    df["errored"] = df["error"].notna()
    df["correct"] = df["correct"].astype(bool) & ~df["errored"]
    df[METRICS] = df[METRICS].astype(float)  # errored runs have no steps etc. -> NaN
    return df


def descriptives(df) -> pd.DataFrame:
    """Decision 6.1. The Wilson interval takes the task as the unit (n = tasks, accuracy
    averaged over seeds), since seeds of the same task are not independent observations."""
    rows = []
    for tier in TIERS + ["all"]:
        for cond in CONDITIONS:
            g = df[(df.condition == cond) & ((df.tier == tier) | (tier == "all"))]
            if g.empty:
                continue
            per_seed = g.groupby("seed")["correct"].mean()
            n = g["task_id"].nunique()
            low, high = proportion_confint(per_seed.mean() * n, n, method="wilson")
            rows.append({"condition": cond, "tier": tier, "tasks": n, "seeds": len(per_seed),
                         "accuracy": per_seed.mean(), "accuracy_sd_seeds": per_seed.std(),
                         "ci95_low": low, "ci95_high": high, "errors": int(g["errored"].sum()),
                         **g[METRICS].mean().rename({"hit_step_limit": "step_limit_rate"})})
    return pd.DataFrame(rows)


def majority(df) -> pd.DataFrame:
    """Per task (rows) x condition (columns), the majority result across seeds (decision 6.2).
    Seed counts are odd, so no ties; a tie from a partial run counts as incorrect."""
    return df.groupby(["task_id", "tier", "condition"])["correct"].mean().gt(0.5).unstack("condition")


def mcnemar_tests(df) -> pd.DataFrame:
    """Decision 6.2: exact McNemar (binomial on the discordant pairs) per condition pair,
    per tier and overall. Holm adjusts across the 9 per-tier tests; both p are reported."""
    maj, rows = majority(df), []
    for tier in TIERS + ["all"]:
        sub = maj if tier == "all" else maj[maj.index.get_level_values("tier") == tier]
        for a, b in combinations(CONDITIONS, 2):
            pair = sub.reindex(columns=[a, b]).dropna().astype(bool)
            if pair.empty:
                continue
            x, y = pair[a], pair[b]
            table = [[(x & y).sum(), (x & ~y).sum()], [(~x & y).sum(), (~x & ~y).sum()]]
            rows.append({"tier": tier, "a": a, "b": b, "tasks": len(pair), "both_correct": table[0][0],
                         "only_a_correct": table[0][1], "only_b_correct": table[1][0],
                         "both_wrong": table[1][1], "p_exact": mcnemar(table, exact=True).pvalue})
    out = pd.DataFrame(rows)
    per_tier = out["tier"] != "all"
    out.loc[per_tier, "p_holm"] = multipletests(out.loc[per_tier, "p_exact"], method="holm")[1]
    return out


def _bayes_glmm(d):
    """correctness ~ condition * tier + (1 | task), variational Bayes with statsmodels' default
    N(0, 2^2) prior on the fixed effects (logit scale)."""
    model = BinomialBayesMixedGLM.from_formula("correct ~ condition * tier", {"task": "0 + C(task_id)"}, d)
    fit = model.fit_vb()
    t = pd.DataFrame({"estimate": fit.fe_mean, "sd": fit.fe_sd}, index=model.exog_names)
    t = t.assign(ci95_low=t.estimate - 1.96 * t.sd, ci95_high=t.estimate + 1.96 * t.sd)
    acc = d.groupby(["condition", "tier"], observed=True)["correct"].mean()
    separated = [f"{c}/{tier}" for (c, tier), a in acc.items() if a in (0, 1)]
    note = (f"posterior mean/SD (logit scale); task random-intercept SD ~ {np.exp(fit.vcp_mean[0]):.2f}. "
            + (f"Cells at 0% or 100% accuracy ({', '.join(separated)}): their terms lean on the prior."
               if separated else "No cell at 0% or 100% accuracy."))
    return t, note


def _lmm(d, y):
    fit = smf.mixedlm(f"{y} ~ condition * tier", d, groups=d["task_id"]).fit()
    ci = fit.conf_int()
    t = pd.DataFrame({"estimate": fit.fe_params, "sd": fit.bse_fe, "ci95_low": ci[0], "ci95_high": ci[1],
                      "p": fit.pvalues}).loc[fit.fe_params.index]
    return t, f"REML; task random-intercept variance {fit.cov_re.iloc[0, 0]:.3g}"


def _records(df) -> list:
    """JSON-ready rows, NaN -> null, full float precision (to_json rounds tiny p-values to 0)."""
    return df.astype(object).where(df.notna(), None).to_dict("records")


def _fit(fn, *args) -> dict:
    """Any failure becomes 'not estimable on this data: <reason>' instead of a crash (decision 6.2)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            terms, note = fn(*args)
            if not np.isfinite(terms.to_numpy(float)).all():
                raise ValueError("non-finite estimates")
        except Exception as e:
            return {"result": f"not estimable on this data: {type(e).__name__}: {e}"}
    return {"result": "fitted", "note": note, "warnings": sorted({str(w.message) for w in caught}),
            "terms": _records(terms.reset_index(names="term"))}


def mixed_models(df) -> dict:
    """Decision 6.1, the main test (hybrid's advantage grows with complexity -> the
    condition[T.hybrid]:tier[T.*] terms). Every seed's run is an observation; vector and low
    are the references."""
    d = df.assign(condition=pd.Categorical(df.condition, CONDITIONS).remove_unused_categories(),
                  tier=pd.Categorical(df.tier, TIERS).remove_unused_categories(),
                  correct=df.correct.astype(int), log_cost=np.log(df.cost_usd.where(df.cost_usd > 0)))
    return {"correct": _fit(_bayes_glmm, d),
            **{y: _fit(_lmm, d.dropna(subset=[y]), y) for y in ("steps", "log_cost")}}


def _chart(desc, column, ylabel, path, ci=False) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    for i, cond in enumerate(CONDITIONS):
        g = desc[desc.condition == cond].set_index("tier").reindex(TIERS)
        yerr = [g[column] - g.ci95_low, g.ci95_high - g[column]] if ci else None
        ax.errorbar(np.arange(len(TIERS)) + (i - 1) * 0.08, g[column], yerr=yerr, label=cond, capsize=4,
                    color=COLOURS[cond], marker=MARKERS[cond], markersize=8, linewidth=2)
    ax.set_xticks(range(len(TIERS)), TIERS)
    ax.set(xlabel="task complexity tier", ylabel=ylabel, ylim=(0, None))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(title="memory", frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def _md(df) -> str:
    cells = df.astype(object).where(df.notna(), "").map(lambda v: f"{v:.4g}" if isinstance(v, float) else v)
    return "\n".join(["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
                     + ["| " + " | ".join(map(str, r)) + " |" for r in cells.itertuples(index=False)])


def analyse(run_dir) -> dict:
    run_dir = Path(run_dir)
    out = run_dir / "analysis"
    out.mkdir(exist_ok=True)
    df = load_runs(run_dir / "runs.jsonl")
    desc, mc, models = descriptives(df), mcnemar_tests(df), mixed_models(df)
    ties = int(df.groupby(["task_id", "condition"])["correct"].mean().eq(0.5).sum())
    stats = {"runs": len(df), "tasks": df.task_id.nunique(), "seeds": df.seed.nunique(),
             "errors": int(df.errored.sum()), "majority_ties": ties,
             "mcnemar": _records(mc), "mixed_models": models}

    desc.to_csv(out / "descriptives.csv", index=False)
    mc.to_csv(out / "mcnemar.csv", index=False)
    (out / "stats.json").write_text(json.dumps(stats, indent=2))
    _chart(desc, "accuracy", "accuracy (95% Wilson CI)", out / "accuracy_by_tier.png", ci=True)
    _chart(desc, "steps", "mean steps per run", out / "steps_by_tier.png")
    _chart(desc, "cost_usd", "mean cost per run (USD)", out / "cost_by_tier.png")

    md = [f"# Analysis: {run_dir.name}", "",
          f"{stats['runs']} runs, {stats['tasks']} tasks, {stats['seeds']} seed(s), {stats['errors']} errored "
          f"(counted incorrect), {ties} majority ties (counted incorrect). Decisions 6.1/6.2.", "",
          "## Descriptives", "", _md(desc), "", "## McNemar (exact, majority across seeds)", "", _md(mc), "",
          "## Mixed-effects models (vector and low are the references)"]
    for name, m in models.items():
        md += ["", f"### {name}", "", m["result"]]
        if m["result"] == "fitted":
            md += ["", m["note"], "", _md(pd.DataFrame(m["terms"]))] + [f"\nwarning: {w}" for w in m["warnings"]]
    (out / "summary.md").write_text("\n".join(md) + "\n")
    print(f"wrote {out}/")
    return stats


def demo() -> None:
    """Synthetic runs: 30 tasks per tier, 3 seeds. Low: all conditions right on tasks 0-26. High:
    vector right on 0-11, graph on 0-19, hybrid on 0-27. Seed 2 flips every vector result and
    one run errors, so the majority vote must recover the design."""
    rng, runs = np.random.default_rng(0), []
    design = {"low": {"vector": 27, "graph": 27, "hybrid": 27}, "medium": {"vector": 20, "graph": 24, "hybrid": 26},
              "high": {"vector": 12, "graph": 20, "hybrid": 28}}
    for seed in range(3):
        for tier, cut in design.items():
            for i in range(30):
                for cond in CONDITIONS:
                    steps = 2 + TIERS.index(tier) + CONDITIONS.index(cond) % 2 + int(rng.integers(0, 3))
                    runs.append({"task_id": f"{tier}_{i:02}", "tier": tier, "condition": cond, "seed": seed,
                                 "correct": (i < cut[cond]) != (seed == 2 and cond == "vector"), "steps": steps,
                                 "hit_step_limit": False, "input_tokens": 500 * steps, "cached_tokens": 0,
                                 "output_tokens": 40 * steps, "cost_usd": 0.0012 * steps * rng.uniform(0.8, 1.2),
                                 "latency_s": 2.0 * steps, "recall": 1.0, "error": None})
    runs[-1] = {k: runs[-1][k] for k in ("task_id", "tier", "condition", "seed")} | {"correct": True, "error": "boom"}
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "runs.jsonl").write_text("\n".join(map(json.dumps, runs)))
        stats = analyse(tmp)
        assert {p.name for p in Path(tmp, "analysis").iterdir()} >= {"summary.md", "accuracy_by_tier.png"}
        df = load_runs(Path(tmp, "runs.jsonl"))
    mc = {(r["tier"], r["a"], r["b"]): r for r in stats["mcnemar"]}
    assert stats["errors"] == 1 and stats["majority_ties"] == 0
    assert mc["high", "vector", "hybrid"]["only_b_correct"] == 16 and mc["high", "vector", "hybrid"]["only_a_correct"] == 0
    assert mc["high", "vector", "hybrid"]["p_exact"] < 0.001
    assert mc["low", "vector", "hybrid"]["p_exact"] == 1.0, "equal on low -> no discordant pairs"
    assert sum(r["p_holm"] is not None for r in stats["mcnemar"]) == 9
    assert all(r["p_holm"] >= r["p_exact"] for r in stats["mcnemar"] if r["tier"] != "all")
    for m in stats["mixed_models"].values():
        assert m["result"] == "fitted" or m["result"].startswith("not estimable"), m
    if (glmm := stats["mixed_models"]["correct"])["result"] == "fitted":
        terms = {t["term"]: t["estimate"] for t in glmm["terms"]}
        assert terms["condition[T.hybrid]:tier[T.high]"] > 0, terms
    assert all("result" in m for m in mixed_models(df[df.task_id == "low_00"]).values()), "tiny data, no crash"
    print("scripts/analyse_results.py: OK (McNemar, majority vote, Holm, mixed models, charts)")


if __name__ == "__main__":
    analyse(sys.argv[1]) if len(sys.argv) > 1 else demo()
