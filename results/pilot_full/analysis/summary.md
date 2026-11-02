# Analysis: pilot_full

36 runs, 12 tasks, 1 seed(s), 0 errored (counted incorrect), 0 majority ties (counted incorrect). Decisions 6.1/6.2.

## Descriptives

| condition | tier | tasks | seeds | accuracy | accuracy_sd_seeds | ci95_low | ci95_high | errors | steps | step_limit_rate | input_tokens | cached_tokens | output_tokens | cost_usd | latency_s | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vector | low | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 2.4 | 0 | 1957 | 219.2 | 96.2 | 0.00446 | 4.869 | 1 |
| graph | low | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 2.6 | 0 | 1165 | 0 | 79.6 | 0.003127 | 4.869 | 1 |
| hybrid | low | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 2.8 | 0 | 1610 | 0 | 90 | 0.004119 | 5.438 | 1 |
| vector | medium | 5 | 1 | 0.8 |  | 0.3755 | 0.9638 | 0 | 5 | 0 | 2.23e+04 | 1.324e+04 | 566.8 | 0.02512 | 19.2 | 1 |
| graph | medium | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 3.4 | 0 | 2477 | 234.2 | 189 | 0.006398 | 8.251 | 1 |
| hybrid | medium | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 3.8 | 0 | 3811 | 1012 | 218.6 | 0.007885 | 9.134 | 1 |
| vector | high | 2 | 1 | 1 |  | 0.3424 | 1 | 0 | 8 | 0 | 6.909e+04 | 5.126e+04 | 1305 | 0.05382 | 40.41 | 1 |
| graph | high | 2 | 1 | 1 |  | 0.3424 | 1 | 0 | 4.5 | 0 | 6518 | 1816 | 533.5 | 0.01492 | 16.2 | 0.8187 |
| hybrid | high | 2 | 1 | 1 |  | 0.3424 | 1 | 0 | 5 | 0 | 8154 | 3162 | 595 | 0.01625 | 19.3 | 0.9151 |
| vector | all | 12 | 1 | 0.9167 |  | 0.6461 | 0.9851 | 0 | 4.417 | 0 | 2.162e+04 | 1.415e+04 | 493.8 | 0.0213 | 16.77 | 1 |
| graph | all | 12 | 1 | 1 |  | 0.7575 | 1 | 0 | 3.25 | 0 | 2604 | 400.2 | 200.8 | 0.006456 | 8.166 | 0.9698 |
| hybrid | all | 12 | 1 | 1 |  | 0.7575 | 1 | 0 | 3.583 | 0 | 3618 | 948.8 | 227.8 | 0.00771 | 9.288 | 0.9858 |

## McNemar (exact, majority across seeds)

| tier | a | b | tasks | both_correct | only_a_correct | only_b_correct | both_wrong | p_exact | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| low | vector | graph | 5 | 5 | 0 | 0 | 0 | 1 | 1 |
| low | vector | hybrid | 5 | 5 | 0 | 0 | 0 | 1 | 1 |
| low | graph | hybrid | 5 | 5 | 0 | 0 | 0 | 1 | 1 |
| medium | vector | graph | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| medium | vector | hybrid | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| medium | graph | hybrid | 5 | 5 | 0 | 0 | 0 | 1 | 1 |
| high | vector | graph | 2 | 2 | 0 | 0 | 0 | 1 | 1 |
| high | vector | hybrid | 2 | 2 | 0 | 0 | 0 | 1 | 1 |
| high | graph | hybrid | 2 | 2 | 0 | 0 | 0 | 1 | 1 |
| all | vector | graph | 12 | 11 | 0 | 1 | 0 | 1 |  |
| all | vector | hybrid | 12 | 11 | 0 | 1 | 0 | 1 |  |
| all | graph | hybrid | 12 | 12 | 0 | 0 | 0 | 1 |  |

## Mixed-effects models (vector and low are the references)

### correct

fitted

posterior mean/SD (logit scale); task random-intercept SD ~ 0.78. Cells at 0% or 100% accuracy (vector/low, vector/high, graph/low, graph/medium, graph/high, hybrid/low, hybrid/medium, hybrid/high): their terms lean on the prior.

| term | estimate | sd | ci95_low | ci95_high |
|---|---|---|---|---|
| Intercept | 3.139 | 0.8005 | 1.57 | 4.708 |
| condition[T.graph] | 1.693 | 1.349 | -0.9505 | 4.336 |
| condition[T.hybrid] | 1.693 | 1.349 | -0.9505 | 4.336 |
| tier[T.medium] | -0.2113 | 1.054 | -2.276 | 1.854 |
| tier[T.high] | 1.024 | 1.538 | -1.99 | 4.038 |
| condition[T.graph]:tier[T.medium] | 0.8503 | 1.599 | -2.283 | 3.984 |
| condition[T.hybrid]:tier[T.medium] | 0.8503 | 1.599 | -2.283 | 3.984 |
| condition[T.graph]:tier[T.high] | 0.3033 | 1.832 | -3.288 | 3.895 |
| condition[T.hybrid]:tier[T.high] | 0.3033 | 1.832 | -3.288 | 3.895 |

### steps

fitted

REML; task random-intercept variance 0.378

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | 2.4 | 0.453 | 1.512 | 3.288 | 1.169e-07 |
| condition[T.graph] | 0.2 | 0.5092 | -0.798 | 1.198 | 0.6945 |
| condition[T.hybrid] | 0.4 | 0.5092 | -0.598 | 1.398 | 0.4321 |
| tier[T.medium] | 2.6 | 0.6406 | 1.344 | 3.856 | 4.936e-05 |
| tier[T.high] | 5.6 | 0.8474 | 3.939 | 7.261 | 3.892e-11 |
| condition[T.graph]:tier[T.medium] | -1.8 | 0.7201 | -3.211 | -0.3887 | 0.01243 |
| condition[T.hybrid]:tier[T.medium] | -1.6 | 0.7201 | -3.011 | -0.1887 | 0.02628 |
| condition[T.graph]:tier[T.high] | -3.7 | 0.9526 | -5.567 | -1.833 | 0.0001027 |
| condition[T.hybrid]:tier[T.high] | -3.4 | 0.9526 | -5.267 | -1.533 | 0.000358 |

### log_cost

fitted

REML; task random-intercept variance 0.0858

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | -5.473 | 0.193 | -5.851 | -5.094 | 5.989e-177 |
| condition[T.graph] | -0.316 | 0.2004 | -0.7087 | 0.07675 | 0.1148 |
| condition[T.hybrid] | -0.05419 | 0.2004 | -0.4469 | 0.3385 | 0.7868 |
| tier[T.medium] | 1.563 | 0.2729 | 1.028 | 2.098 | 1.02e-08 |
| tier[T.high] | 2.481 | 0.361 | 1.774 | 3.189 | 6.258e-12 |
| condition[T.graph]:tier[T.medium] | -0.8473 | 0.2834 | -1.403 | -0.2919 | 0.002788 |
| condition[T.hybrid]:tier[T.medium] | -0.9327 | 0.2834 | -1.488 | -0.3773 | 0.0009963 |
| condition[T.graph]:tier[T.high] | -0.923 | 0.3749 | -1.658 | -0.1883 | 0.01381 |
| condition[T.hybrid]:tier[T.high] | -1.088 | 0.3749 | -1.823 | -0.3537 | 0.003691 |
