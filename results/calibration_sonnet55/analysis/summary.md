# Analysis: calibration_sonnet55

39 runs, 13 tasks, 1 seed(s), 0 errored (counted incorrect), 0 refused (counted incorrect), 0 majority ties (counted incorrect). Decisions 6.1/6.2/6.13.

## Descriptives

| condition | tier | tasks | seeds | accuracy | accuracy_sd_seeds | ci95_low | ci95_high | errors | refusals | steps | step_limit_rate | input_tokens | cached_tokens | output_tokens | cost_usd | latency_s | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vector | low | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 3.2 | 0 | 1.278e+04 | 6726 | 500 | 0.02146 | 11.06 | 1 |
| graph | low | 5 | 1 | 0.8 |  | 0.3755 | 0.9638 | 0 | 0 | 2.4 | 0 | 3187 | 689.8 | 284.6 | 0.009223 | 8.367 | 1 |
| hybrid | low | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 3 | 0 | 6202 | 2096 | 380.4 | 0.01448 | 9.628 | 1 |
| vector | medium | 5 | 1 | 0.8 |  | 0.3755 | 0.9638 | 0 | 0 | 5 | 0 | 4.27e+04 | 2.881e+04 | 1271 | 0.0532 | 14.9 | 1 |
| graph | medium | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 4 | 0 | 9839 | 5225 | 754 | 0.02011 | 7.784 | 1 |
| hybrid | medium | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 4.2 | 0 | 1.263e+04 | 7818 | 772.4 | 0.0213 | 8.387 | 1 |
| vector | high | 3 | 1 | 1 |  | 0.4385 | 1 | 0 | 0 | 5.667 | 0 | 5.907e+04 | 3.763e+04 | 2287 | 0.084 | 22.39 | 0.9812 |
| graph | high | 3 | 1 | 1 |  | 0.4385 | 1 | 0 | 0 | 5.667 | 0 | 1.898e+04 | 1.148e+04 | 1727 | 0.03831 | 18.11 | 0.9254 |
| hybrid | high | 3 | 1 | 1 |  | 0.4385 | 1 | 0 | 0 | 6.333 | 0 | 2.906e+04 | 1.985e+04 | 2045 | 0.04745 | 21.44 | 0.9162 |
| vector | all | 13 | 1 | 0.9231 |  | 0.6669 | 0.9863 | 0 | 0 | 4.462 | 0 | 3.497e+04 | 2.235e+04 | 1209 | 0.0481 | 15.15 | 0.9957 |
| graph | all | 13 | 1 | 0.9231 |  | 0.6669 | 0.9863 | 0 | 0 | 3.769 | 0 | 9389 | 4924 | 798.1 | 0.02012 | 10.39 | 0.9828 |
| hybrid | all | 13 | 1 | 1 |  | 0.7719 | 1 | 0 | 0 | 4.231 | 0 | 1.395e+04 | 8394 | 915.2 | 0.02471 | 11.88 | 0.9807 |

## McNemar (exact, majority across seeds)

| tier | a | b | tasks | both_correct | only_a_correct | only_b_correct | both_wrong | p_exact | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| low | vector | graph | 5 | 4 | 1 | 0 | 0 | 1 | 1 |
| low | vector | hybrid | 5 | 5 | 0 | 0 | 0 | 1 | 1 |
| low | graph | hybrid | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| medium | vector | graph | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| medium | vector | hybrid | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| medium | graph | hybrid | 5 | 5 | 0 | 0 | 0 | 1 | 1 |
| high | vector | graph | 3 | 3 | 0 | 0 | 0 | 1 | 1 |
| high | vector | hybrid | 3 | 3 | 0 | 0 | 0 | 1 | 1 |
| high | graph | hybrid | 3 | 3 | 0 | 0 | 0 | 1 | 1 |
| all | vector | graph | 13 | 11 | 1 | 1 | 0 | 1 |  |
| all | vector | hybrid | 13 | 12 | 0 | 1 | 0 | 1 |  |
| all | graph | hybrid | 13 | 12 | 0 | 1 | 0 | 1 |  |

## Mixed-effects models (vector and low are the references)

### correct

fitted

posterior mean/SD (logit scale); task random-intercept SD ~ 0.80. Cells at 0% or 100% accuracy (vector/low, vector/high, graph/medium, graph/high, hybrid/low, hybrid/medium, hybrid/high): their terms lean on the prior.

| term | estimate | sd | ci95_low | ci95_high |
|---|---|---|---|---|
| Intercept | 2.603 | 0.6784 | 1.274 | 3.933 |
| condition[T.graph] | 0.1694 | 1.022 | -1.834 | 2.172 |
| condition[T.hybrid] | 1.849 | 1.306 | -0.7103 | 4.408 |
| tier[T.medium] | 0.2319 | 1.011 | -1.749 | 2.213 |
| tier[T.high] | 1.552 | 1.389 | -1.17 | 4.274 |
| condition[T.graph]:tier[T.medium] | 1.333 | 1.467 | -1.542 | 4.209 |
| condition[T.hybrid]:tier[T.medium] | 0.7942 | 1.612 | -2.365 | 3.953 |
| condition[T.graph]:tier[T.high] | 0.6573 | 1.681 | -2.638 | 3.953 |
| condition[T.hybrid]:tier[T.high] | 0.3519 | 1.8 | -3.176 | 3.88 |

### steps

fitted

REML; task random-intercept variance 0.898

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | 3.2 | 0.6773 | 1.873 | 4.527 | 2.301e-06 |
| condition[T.graph] | -0.8 | 0.7471 | -2.264 | 0.6644 | 0.2843 |
| condition[T.hybrid] | -0.2 | 0.7471 | -1.664 | 1.264 | 0.7889 |
| tier[T.medium] | 1.8 | 0.9578 | -0.07721 | 3.677 | 0.0602 |
| tier[T.high] | 2.467 | 1.106 | 0.2991 | 4.634 | 0.02572 |
| condition[T.graph]:tier[T.medium] | -0.2 | 1.057 | -2.271 | 1.871 | 0.8499 |
| condition[T.hybrid]:tier[T.medium] | -0.6 | 1.057 | -2.671 | 1.471 | 0.5701 |
| condition[T.graph]:tier[T.high] | 0.8 | 1.22 | -1.591 | 3.191 | 0.512 |
| condition[T.hybrid]:tier[T.high] | 0.8667 | 1.22 | -1.525 | 3.258 | 0.4775 |

### log_cost

fitted

REML; task random-intercept variance 0.0885

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | -3.988 | 0.2274 | -4.434 | -3.542 | 7.526e-69 |
| condition[T.graph] | -0.7217 | 0.2608 | -1.233 | -0.2106 | 0.005652 |
| condition[T.hybrid] | -0.3121 | 0.2608 | -0.8233 | 0.199 | 0.2314 |
| tier[T.medium] | 0.8995 | 0.3216 | 0.2692 | 1.53 | 0.005159 |
| tier[T.high] | 1.502 | 0.3714 | 0.7743 | 2.23 | 5.231e-05 |
| condition[T.graph]:tier[T.medium] | -0.2601 | 0.3688 | -0.983 | 0.4628 | 0.4806 |
| condition[T.hybrid]:tier[T.medium] | -0.6221 | 0.3688 | -1.345 | 0.1008 | 0.09167 |
| condition[T.graph]:tier[T.high] | -0.06176 | 0.4259 | -0.8965 | 0.773 | 0.8847 |
| condition[T.hybrid]:tier[T.high] | -0.2532 | 0.4259 | -1.088 | 0.5815 | 0.5522 |
