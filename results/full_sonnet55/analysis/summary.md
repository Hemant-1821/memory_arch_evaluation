# Analysis: full_sonnet55

1320 runs, 88 tasks, 5 seed(s), 0 errored (counted incorrect), 0 refused (counted incorrect), 0 majority ties (counted incorrect). Decisions 6.1/6.2/6.13.

## Descriptives

| condition | tier | tasks | seeds | accuracy | accuracy_sd_seeds | ci95_low | ci95_high | errors | refusals | steps | step_limit_rate | input_tokens | cached_tokens | output_tokens | cost_usd | latency_s | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vector | low | 30 | 5 | 0.5733 | 0.02789 | 0.3982 | 0.7319 | 0 | 0 | 4.447 | 0.07333 | 2.595e+04 | 1.799e+04 | 643.1 | 0.02811 | 9.345 | 0.8067 |
| graph | low | 30 | 5 | 1 | 0 | 0.8865 | 1 | 0 | 0 | 2.373 | 0 | 3302 | 1604 | 237.1 | 0.006775 | 3.794 | 1 |
| hybrid | low | 30 | 5 | 0.9933 | 0.01491 | 0.875 | 0.9997 | 0 | 0 | 2.66 | 0 | 5273 | 2777 | 303.1 | 0.009547 | 4.74 | 1 |
| vector | medium | 30 | 5 | 0.5533 | 0.03801 | 0.3797 | 0.7149 | 0 | 0 | 7.287 | 0.26 | 9.19e+04 | 7.061e+04 | 1721 | 0.07748 | 18.68 | 0.8637 |
| graph | medium | 30 | 5 | 0.9667 | 1.241e-16 | 0.8333 | 0.9941 | 0 | 0 | 3.367 | 0 | 7240 | 4262 | 623.9 | 0.0141 | 7.151 | 0.9967 |
| hybrid | medium | 30 | 5 | 0.9667 | 1.241e-16 | 0.8333 | 0.9941 | 0 | 0 | 3.3 | 0 | 7905 | 4519 | 619.6 | 0.01511 | 7.169 | 0.9948 |
| vector | high | 28 | 5 | 0.4143 | 0.04072 | 0.2532 | 0.596 | 0 | 0 | 8.907 | 0.3357 | 1.305e+05 | 1.019e+05 | 2635 | 0.108 | 26.92 | 0.362 |
| graph | high | 28 | 5 | 0.9071 | 0.01956 | 0.7459 | 0.9702 | 0 | 0 | 5.229 | 0 | 2.098e+04 | 1.328e+04 | 1801 | 0.03857 | 16.55 | 0.1049 |
| hybrid | high | 28 | 5 | 0.9357 | 0.02988 | 0.783 | 0.9832 | 0 | 0 | 5.643 | 0 | 2.928e+04 | 1.952e+04 | 1961 | 0.04594 | 18.06 | 0.1392 |
| vector | all | 88 | 5 | 0.5159 | 0.01296 | 0.413 | 0.6175 | 0 | 0 | 6.834 | 0.2205 | 8.17e+04 | 6.263e+04 | 1644 | 0.07037 | 18.12 | 0.6846 |
| graph | all | 88 | 5 | 0.9591 | 0.006224 | 0.8951 | 0.9847 | 0 | 0 | 3.62 | 0 | 1.027e+04 | 6226 | 866.4 | 0.01939 | 8.997 | 0.7141 |
| hybrid | all | 88 | 5 | 0.9659 | 0.01136 | 0.9045 | 0.9883 | 0 | 0 | 3.827 | 0 | 1.381e+04 | 8699 | 938.5 | 0.02302 | 9.807 | 0.7244 |

## McNemar (exact, majority across seeds)

| tier | a | b | tasks | both_correct | only_a_correct | only_b_correct | both_wrong | p_exact | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| low | vector | graph | 30 | 17 | 0 | 13 | 0 | 0.0002441 | 0.001709 |
| low | vector | hybrid | 30 | 17 | 0 | 13 | 0 | 0.0002441 | 0.001709 |
| low | graph | hybrid | 30 | 30 | 0 | 0 | 0 | 1 | 1 |
| medium | vector | graph | 30 | 14 | 1 | 15 | 0 | 0.0005188 | 0.002594 |
| medium | vector | hybrid | 30 | 14 | 1 | 15 | 0 | 0.0005188 | 0.002594 |
| medium | graph | hybrid | 30 | 29 | 0 | 0 | 1 | 1 | 1 |
| high | vector | graph | 28 | 10 | 0 | 15 | 3 | 6.104e-05 | 0.0004883 |
| high | vector | hybrid | 28 | 10 | 0 | 16 | 2 | 3.052e-05 | 0.0002747 |
| high | graph | hybrid | 28 | 25 | 0 | 1 | 2 | 1 | 1 |
| all | vector | graph | 88 | 41 | 1 | 43 | 3 | 5.116e-12 |  |
| all | vector | hybrid | 88 | 41 | 1 | 44 | 2 | 2.615e-12 |  |
| all | graph | hybrid | 88 | 84 | 0 | 1 | 3 | 1 |  |

## Mixed-effects models (vector and low are the references)

### correct

fitted

posterior mean/SD (logit scale); task random-intercept SD ~ 3.84. Cells at 0% or 100% accuracy (graph/low): their terms lean on the prior.

| term | estimate | sd | ci95_low | ci95_high |
|---|---|---|---|---|
| Intercept | 1.099 | 0.1392 | 0.8267 | 1.372 |
| condition[T.graph] | 6.836 | 0.3508 | 6.149 | 7.524 |
| condition[T.hybrid] | 6.571 | 0.3617 | 5.862 | 7.28 |
| tier[T.medium] | -0.05704 | 0.2276 | -0.5032 | 0.3891 |
| tier[T.high] | -1.675 | 0.2257 | -2.117 | -1.232 |
| condition[T.graph]:tier[T.medium] | -0.7091 | 0.5726 | -1.831 | 0.4131 |
| condition[T.hybrid]:tier[T.medium] | -0.4645 | 0.5697 | -1.581 | 0.6522 |
| condition[T.graph]:tier[T.high] | -0.2139 | 0.5205 | -1.234 | 0.8063 |
| condition[T.hybrid]:tier[T.high] | 1.309 | 0.5996 | 0.1333 | 2.484 |

### steps

fitted

REML; task random-intercept variance 0.762

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | 4.447 | 0.1872 | 4.08 | 4.814 | 1.168e-124 |
| condition[T.graph] | -2.073 | 0.139 | -2.346 | -1.801 | 2.614e-50 |
| condition[T.hybrid] | -1.787 | 0.139 | -2.059 | -1.514 | 8.251e-38 |
| tier[T.medium] | 2.84 | 0.2648 | 2.321 | 3.359 | 7.794e-27 |
| tier[T.high] | 4.46 | 0.2695 | 3.932 | 4.989 | 1.571e-61 |
| condition[T.graph]:tier[T.medium] | -1.847 | 0.1966 | -2.232 | -1.461 | 5.787e-21 |
| condition[T.hybrid]:tier[T.medium] | -2.2 | 0.1966 | -2.585 | -1.815 | 4.504e-29 |
| condition[T.graph]:tier[T.high] | -1.605 | 0.2001 | -1.997 | -1.213 | 1.026e-15 |
| condition[T.hybrid]:tier[T.high] | -1.478 | 0.2001 | -1.87 | -1.086 | 1.516e-13 |

### log_cost

fitted

REML; task random-intercept variance 0.0525

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | -3.825 | 0.04877 | -3.92 | -3.729 | 0 |
| condition[T.graph] | -1.188 | 0.03544 | -1.257 | -1.118 | 3.056e-246 |
| condition[T.hybrid] | -0.8643 | 0.03544 | -0.9337 | -0.7948 | 2.555e-131 |
| tier[T.medium] | 1.167 | 0.06897 | 1.032 | 1.303 | 2.885e-64 |
| tier[T.high] | 1.583 | 0.07019 | 1.445 | 1.72 | 1.452e-112 |
| condition[T.graph]:tier[T.medium] | -0.4824 | 0.05013 | -0.5806 | -0.3841 | 6.352e-22 |
| condition[T.hybrid]:tier[T.medium] | -0.7388 | 0.05013 | -0.8371 | -0.6406 | 3.598e-49 |
| condition[T.graph]:tier[T.high] | 0.1245 | 0.05101 | 0.02453 | 0.2245 | 0.01465 |
| condition[T.hybrid]:tier[T.high] | -0.02353 | 0.05101 | -0.1235 | 0.07646 | 0.6447 |
