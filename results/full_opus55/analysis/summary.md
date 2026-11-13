# Analysis: full_opus55

528 runs, 88 tasks, 2 seed(s), 0 errored (counted incorrect), 0 refused (counted incorrect), 17 majority ties (counted incorrect). Decisions 6.1/6.2/6.13.

## Descriptives

| condition | tier | tasks | seeds | accuracy | accuracy_sd_seeds | ci95_low | ci95_high | errors | refusals | steps | step_limit_rate | input_tokens | cached_tokens | output_tokens | cost_usd | latency_s | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vector | low | 30 | 2 | 0.5667 | 0.04714 | 0.392 | 0.7262 | 0 | 0 | 6.2 | 0.06667 | 3.895e+04 | 2.864e+04 | 844.6 | 0.07415 | 15.31 | 0.8333 |
| graph | low | 30 | 2 | 1 | 0 | 0.8865 | 1 | 0 | 0 | 2 | 0 | 2420 | 1115 | 207 | 0.01088 | 3.969 | 1 |
| hybrid | low | 30 | 2 | 1 | 0 | 0.8865 | 1 | 0 | 0 | 3.133 | 0 | 6966 | 3560 | 416.9 | 0.02607 | 6.864 | 1 |
| vector | medium | 30 | 2 | 0.6333 | 0 | 0.4551 | 0.7813 | 0 | 0 | 7.75 | 0.08333 | 1.032e+05 | 7.944e+04 | 1998 | 0.1747 | 25.52 | 0.8858 |
| graph | medium | 30 | 2 | 0.9667 | 0 | 0.8333 | 0.9941 | 0 | 0 | 2.917 | 0 | 5959 | 3234 | 566.9 | 0.0256 | 8.115 | 0.9948 |
| hybrid | medium | 30 | 2 | 0.9667 | 0 | 0.8333 | 0.9941 | 0 | 0 | 3.65 | 0 | 1.023e+04 | 5948 | 717.2 | 0.03691 | 9.857 | 0.9948 |
| vector | high | 28 | 2 | 0.4464 | 0.02525 | 0.2801 | 0.6257 | 0 | 0 | 8.911 | 0.05357 | 1.031e+05 | 8.058e+04 | 2320 | 0.1752 | 30.32 | 0.2942 |
| graph | high | 28 | 2 | 0.9643 | 0 | 0.8229 | 0.9937 | 0 | 0 | 4.393 | 0 | 1.305e+04 | 7879 | 1296 | 0.05331 | 15.48 | 0.0621 |
| hybrid | high | 28 | 2 | 0.9643 | 0 | 0.8229 | 0.9937 | 0 | 0 | 4.804 | 0 | 1.835e+04 | 1.152e+04 | 1484 | 0.06611 | 18.34 | 0.08851 |
| vector | all | 88 | 2 | 0.5511 | 0.02411 | 0.4473 | 0.6507 | 0 | 0 | 7.591 | 0.06818 | 8.127e+04 | 6.248e+04 | 1707 | 0.1406 | 23.57 | 0.6797 |
| graph | all | 88 | 2 | 0.9773 | 0 | 0.9209 | 0.9937 | 0 | 0 | 3.074 | 0 | 7008 | 3990 | 676 | 0.0294 | 9.045 | 0.6998 |
| hybrid | all | 88 | 2 | 0.9773 | 0 | 0.9209 | 0.9937 | 0 | 0 | 3.841 | 0 | 1.17e+04 | 6907 | 858.8 | 0.04251 | 11.53 | 0.7082 |

## McNemar (exact, majority across seeds)

| tier | a | b | tasks | both_correct | only_a_correct | only_b_correct | both_wrong | p_exact | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| low | vector | graph | 30 | 15 | 0 | 15 | 0 | 6.104e-05 | 0.0004272 |
| low | vector | hybrid | 30 | 15 | 0 | 15 | 0 | 6.104e-05 | 0.0004272 |
| low | graph | hybrid | 30 | 30 | 0 | 0 | 0 | 1 | 1 |
| medium | vector | graph | 30 | 15 | 1 | 14 | 0 | 0.0009766 | 0.004883 |
| medium | vector | hybrid | 30 | 15 | 1 | 14 | 0 | 0.0009766 | 0.004883 |
| medium | graph | hybrid | 30 | 29 | 0 | 0 | 1 | 1 | 1 |
| high | vector | graph | 28 | 9 | 0 | 18 | 1 | 7.629e-06 | 6.866e-05 |
| high | vector | hybrid | 28 | 9 | 0 | 18 | 1 | 7.629e-06 | 6.866e-05 |
| high | graph | hybrid | 28 | 27 | 0 | 0 | 1 | 1 | 1 |
| all | vector | graph | 88 | 39 | 1 | 47 | 1 | 3.482e-13 |  |
| all | vector | hybrid | 88 | 39 | 1 | 47 | 1 | 3.482e-13 |  |
| all | graph | hybrid | 88 | 86 | 0 | 0 | 2 | 1 |  |

## Mixed-effects models (vector and low are the references)

### correct

fitted

posterior mean/SD (logit scale); task random-intercept SD ~ 2.10. Cells at 0% or 100% accuracy (graph/low, hybrid/low): their terms lean on the prior.

| term | estimate | sd | ci95_low | ci95_high |
|---|---|---|---|---|
| Intercept | 0.6879 | 0.1757 | 0.3434 | 1.032 |
| condition[T.graph] | 4.959 | 0.5008 | 3.977 | 5.94 |
| condition[T.hybrid] | 4.959 | 0.5008 | 3.977 | 5.94 |
| tier[T.medium] | 0.2225 | 0.2993 | -0.3641 | 0.8091 |
| tier[T.high] | -0.9545 | 0.2996 | -1.542 | -0.3673 |
| condition[T.graph]:tier[T.medium] | -0.3639 | 0.7847 | -1.902 | 1.174 |
| condition[T.hybrid]:tier[T.medium] | -0.3639 | 0.7847 | -1.902 | 1.174 |
| condition[T.graph]:tier[T.high] | 0.7065 | 0.7802 | -0.8228 | 2.236 |
| condition[T.hybrid]:tier[T.high] | 0.7065 | 0.7802 | -0.8228 | 2.236 |

### steps

fitted

REML; task random-intercept variance 0.343

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | 6.2 | 0.1743 | 5.858 | 6.542 | 3.128e-277 |
| condition[T.graph] | -4.2 | 0.1947 | -4.582 | -3.818 | 3.035e-103 |
| condition[T.hybrid] | -3.067 | 0.1947 | -3.448 | -2.685 | 6.475e-56 |
| tier[T.medium] | 1.55 | 0.2465 | 1.067 | 2.033 | 3.19e-10 |
| tier[T.high] | 2.711 | 0.2508 | 2.219 | 3.202 | 3.166e-27 |
| condition[T.graph]:tier[T.medium] | -0.6333 | 0.2753 | -1.173 | -0.09377 | 0.02142 |
| condition[T.hybrid]:tier[T.medium] | -1.033 | 0.2753 | -1.573 | -0.4938 | 0.0001743 |
| condition[T.graph]:tier[T.high] | -0.3179 | 0.2802 | -0.867 | 0.2313 | 0.2566 |
| condition[T.hybrid]:tier[T.high] | -1.04 | 0.2802 | -1.59 | -0.4914 | 0.0002042 |

### log_cost

fitted

REML; task random-intercept variance 0.0336

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | -2.757 | 0.04577 | -2.847 | -2.668 | 0 |
| condition[T.graph] | -1.764 | 0.04417 | -1.851 | -1.678 | 0 |
| condition[T.hybrid] | -0.9146 | 0.04417 | -1.001 | -0.828 | 2.911e-95 |
| tier[T.medium] | 0.9731 | 0.06472 | 0.8462 | 1.1 | 4.383e-51 |
| tier[T.high] | 1.005 | 0.06587 | 0.8759 | 1.134 | 1.462e-52 |
| condition[T.graph]:tier[T.medium] | -0.1622 | 0.06246 | -0.2846 | -0.03976 | 0.009416 |
| condition[T.hybrid]:tier[T.medium] | -0.6476 | 0.06246 | -0.77 | -0.5252 | 3.456e-25 |
| condition[T.graph]:tier[T.high] | 0.5486 | 0.06357 | 0.424 | 0.6732 | 6.134e-18 |
| condition[T.hybrid]:tier[T.high] | -0.07927 | 0.06357 | -0.2039 | 0.04531 | 0.2124 |
