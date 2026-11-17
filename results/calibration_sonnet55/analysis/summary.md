# Analysis: calibration_sonnet55

39 runs, 13 tasks, 1 seed(s), 0 errored (counted incorrect), 0 refused (counted incorrect), 0 majority ties (counted incorrect). Decisions 6.1/6.2/6.13.

## Descriptives

| condition | tier | tasks | seeds | accuracy | accuracy_sd_seeds | ci95_low | ci95_high | errors | refusals | steps | step_limit_rate | input_tokens | cached_tokens | output_tokens | cost_usd | latency_s | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vector | low | 5 | 1 | 0.8 |  | 0.3755 | 0.9638 | 0 | 0 | 2.8 | 0 | 8759 | 3002 | 379 | 0.01848 | 8.874 | 0.8 |
| graph | low | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 2.4 | 0 | 3176 | 907.6 | 251.8 | 0.008276 | 5.493 | 1 |
| hybrid | low | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 3.2 | 0 | 7235 | 2690 | 382.2 | 0.01545 | 7.476 | 1 |
| vector | medium | 5 | 1 | 0.8 |  | 0.3755 | 0.9638 | 0 | 0 | 4.6 | 0 | 3.674e+04 | 2.335e+04 | 1169 | 0.04749 | 13.5 | 1 |
| graph | medium | 5 | 1 | 0.8 |  | 0.3755 | 0.9638 | 0 | 0 | 3.6 | 0 | 8474 | 4857 | 717.6 | 0.0167 | 7.139 | 1 |
| hybrid | medium | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 4.4 | 0 | 1.427e+04 | 9117 | 801.2 | 0.02181 | 8.797 | 1 |
| vector | high | 3 | 1 | 1 |  | 0.4385 | 1 | 0 | 0 | 6 | 0 | 6.273e+04 | 4.13e+04 | 2372 | 0.08143 | 22.17 | 1 |
| graph | high | 3 | 1 | 1 |  | 0.4385 | 1 | 0 | 0 | 5.333 | 0 | 1.672e+04 | 9516 | 1556 | 0.03452 | 14.32 | 0.9439 |
| hybrid | high | 3 | 1 | 1 |  | 0.4385 | 1 | 0 | 0 | 6.667 | 0 | 3.22e+04 | 2.167e+04 | 2040 | 0.04889 | 21.14 | 0.9532 |
| vector | all | 13 | 1 | 0.8462 |  | 0.5777 | 0.9567 | 0 | 0 | 4.231 | 0 | 3.198e+04 | 1.967e+04 | 1143 | 0.04416 | 13.72 | 0.9231 |
| graph | all | 13 | 1 | 0.9231 |  | 0.6669 | 0.9863 | 0 | 0 | 3.538 | 0 | 8340 | 4413 | 731.8 | 0.01757 | 8.162 | 0.9871 |
| hybrid | all | 13 | 1 | 1 |  | 0.7719 | 1 | 0 | 0 | 4.462 | 0 | 1.57e+04 | 9541 | 926 | 0.02561 | 11.14 | 0.9892 |

## McNemar (exact, majority across seeds)

| tier | a | b | tasks | both_correct | only_a_correct | only_b_correct | both_wrong | p_exact | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| low | vector | graph | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| low | vector | hybrid | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| low | graph | hybrid | 5 | 5 | 0 | 0 | 0 | 1 | 1 |
| medium | vector | graph | 5 | 4 | 0 | 0 | 1 | 1 | 1 |
| medium | vector | hybrid | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| medium | graph | hybrid | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| high | vector | graph | 3 | 3 | 0 | 0 | 0 | 1 | 1 |
| high | vector | hybrid | 3 | 3 | 0 | 0 | 0 | 1 | 1 |
| high | graph | hybrid | 3 | 3 | 0 | 0 | 0 | 1 | 1 |
| all | vector | graph | 13 | 11 | 0 | 1 | 1 | 1 |  |
| all | vector | hybrid | 13 | 11 | 0 | 2 | 0 | 0.5 |  |
| all | graph | hybrid | 13 | 12 | 0 | 1 | 0 | 1 |  |

## Mixed-effects models (vector and low are the references)

### correct

fitted

posterior mean/SD (logit scale); task random-intercept SD ~ 1.56. Cells at 0% or 100% accuracy (vector/high, graph/low, graph/high, hybrid/low, hybrid/medium, hybrid/high): their terms lean on the prior.

| term | estimate | sd | ci95_low | ci95_high |
|---|---|---|---|---|
| Intercept | 2.473 | 0.6528 | 1.194 | 3.753 |
| condition[T.graph] | 1.24 | 1.024 | -0.7668 | 3.246 |
| condition[T.hybrid] | 2.178 | 1.289 | -0.3485 | 4.704 |
| tier[T.medium] | -0.02422 | 0.8959 | -1.78 | 1.732 |
| tier[T.high] | 1.538 | 1.408 | -1.22 | 4.297 |
| condition[T.graph]:tier[T.medium] | -0.6549 | 1.259 | -3.122 | 1.812 |
| condition[T.hybrid]:tier[T.medium] | 1.007 | 1.592 | -2.113 | 4.127 |
| condition[T.graph]:tier[T.high] | 0.4859 | 1.75 | -2.943 | 3.915 |
| condition[T.hybrid]:tier[T.high] | 0.3525 | 1.808 | -3.19 | 3.895 |

### steps

fitted

REML; task random-intercept variance 1.41

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | 2.8 | 0.6518 | 1.522 | 4.078 | 1.742e-05 |
| condition[T.graph] | -0.4 | 0.5342 | -1.447 | 0.6469 | 0.454 |
| condition[T.hybrid] | 0.4 | 0.5342 | -0.6469 | 1.447 | 0.454 |
| tier[T.medium] | 1.8 | 0.9218 | -0.006761 | 3.607 | 0.05086 |
| tier[T.high] | 3.2 | 1.064 | 1.114 | 5.286 | 0.002645 |
| condition[T.graph]:tier[T.medium] | -0.6 | 0.7554 | -2.081 | 0.8806 | 0.427 |
| condition[T.hybrid]:tier[T.medium] | -0.6 | 0.7554 | -2.081 | 0.8806 | 0.427 |
| condition[T.graph]:tier[T.high] | -0.2667 | 0.8723 | -1.976 | 1.443 | 0.7598 |
| condition[T.hybrid]:tier[T.high] | 0.2667 | 0.8723 | -1.443 | 1.976 | 0.7598 |

### log_cost

fitted

REML; task random-intercept variance 0.13

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | -4.031 | 0.2093 | -4.441 | -3.62 | 1.201e-82 |
| condition[T.graph] | -0.7721 | 0.1884 | -1.141 | -0.4027 | 4.182e-05 |
| condition[T.hybrid] | -0.2265 | 0.1884 | -0.5959 | 0.1428 | 0.2293 |
| tier[T.medium] | 0.8589 | 0.296 | 0.2788 | 1.439 | 0.003708 |
| tier[T.high] | 1.507 | 0.3418 | 0.8367 | 2.176 | 1.044e-05 |
| condition[T.graph]:tier[T.medium] | -0.2911 | 0.2665 | -0.8134 | 0.2312 | 0.2747 |
| condition[T.hybrid]:tier[T.medium] | -0.6596 | 0.2665 | -1.182 | -0.1373 | 0.01332 |
| condition[T.graph]:tier[T.high] | -0.08458 | 0.3077 | -0.6877 | 0.5185 | 0.7834 |
| condition[T.hybrid]:tier[T.high] | -0.2763 | 0.3077 | -0.8794 | 0.3268 | 0.3692 |
