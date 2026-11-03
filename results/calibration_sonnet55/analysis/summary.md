# Analysis: calibration_sonnet55

39 runs, 13 tasks, 1 seed(s), 0 errored (counted incorrect), 0 refused (counted incorrect), 0 majority ties (counted incorrect). Decisions 6.1/6.2/6.13.

## Descriptives

| condition | tier | tasks | seeds | accuracy | accuracy_sd_seeds | ci95_low | ci95_high | errors | refusals | steps | step_limit_rate | input_tokens | cached_tokens | output_tokens | cost_usd | latency_s | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vector | low | 5 | 1 | 0.8 |  | 0.3755 | 0.9638 | 0 | 0 | 2.8 | 0 | 7360 | 2966 | 392.8 | 0.0155 | 8.629 | 1 |
| graph | low | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 2.4 | 0 | 3168 | 1146 | 249.8 | 0.007779 | 5.463 | 1 |
| hybrid | low | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 2.8 | 0 | 5558 | 2473 | 331.2 | 0.01152 | 6.386 | 1 |
| vector | medium | 5 | 1 | 0.8 |  | 0.3755 | 0.9638 | 0 | 0 | 4.6 | 0 | 3.201e+04 | 2.045e+04 | 1126 | 0.04424 | 13.77 | 1 |
| graph | medium | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 4 | 0 | 9805 | 6639 | 711.8 | 0.01636 | 8.277 | 1 |
| hybrid | medium | 5 | 1 | 1 |  | 0.5655 | 1 | 0 | 0 | 3.8 | 0 | 9793 | 6114 | 711.4 | 0.01753 | 7.039 | 1 |
| vector | high | 3 | 1 | 1 |  | 0.4385 | 1 | 0 | 0 | 5 | 0 | 4.386e+04 | 2.562e+04 | 2194 | 0.07266 | 19.15 | 1 |
| graph | high | 3 | 1 | 1 |  | 0.4385 | 1 | 0 | 0 | 5.667 | 0 | 1.879e+04 | 1.295e+04 | 1556 | 0.03274 | 13.87 | 0.9439 |
| hybrid | high | 3 | 1 | 1 |  | 0.4385 | 1 | 0 | 0 | 6 | 0 | 2.686e+04 | 1.872e+04 | 1910 | 0.04318 | 17.67 | 0.9347 |
| vector | all | 13 | 1 | 0.8462 |  | 0.5777 | 0.9567 | 0 | 0 | 4 | 0 | 2.526e+04 | 1.492e+04 | 1091 | 0.03975 | 13.03 | 1 |
| graph | all | 13 | 1 | 1 |  | 0.7719 | 1 | 0 | 0 | 3.769 | 0 | 9326 | 5983 | 729 | 0.01684 | 8.485 | 0.9871 |
| hybrid | all | 13 | 1 | 1 |  | 0.7719 | 1 | 0 | 0 | 3.923 | 0 | 1.21e+04 | 7623 | 841.8 | 0.02114 | 9.241 | 0.9849 |

## McNemar (exact, majority across seeds)

| tier | a | b | tasks | both_correct | only_a_correct | only_b_correct | both_wrong | p_exact | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| low | vector | graph | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| low | vector | hybrid | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| low | graph | hybrid | 5 | 5 | 0 | 0 | 0 | 1 | 1 |
| medium | vector | graph | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| medium | vector | hybrid | 5 | 4 | 0 | 1 | 0 | 1 | 1 |
| medium | graph | hybrid | 5 | 5 | 0 | 0 | 0 | 1 | 1 |
| high | vector | graph | 3 | 3 | 0 | 0 | 0 | 1 | 1 |
| high | vector | hybrid | 3 | 3 | 0 | 0 | 0 | 1 | 1 |
| high | graph | hybrid | 3 | 3 | 0 | 0 | 0 | 1 | 1 |
| all | vector | graph | 13 | 11 | 0 | 2 | 0 | 0.5 |  |
| all | vector | hybrid | 13 | 11 | 0 | 2 | 0 | 0.5 |  |
| all | graph | hybrid | 13 | 13 | 0 | 0 | 0 | 1 |  |

## Mixed-effects models (vector and low are the references)

### correct

fitted

posterior mean/SD (logit scale); task random-intercept SD ~ 0.82. Cells at 0% or 100% accuracy (vector/high, graph/low, graph/medium, graph/high, hybrid/low, hybrid/medium, hybrid/high): their terms lean on the prior.

| term | estimate | sd | ci95_low | ci95_high |
|---|---|---|---|---|
| Intercept | 2.206 | 0.6909 | 0.8522 | 3.561 |
| condition[T.graph] | 2.042 | 1.27 | -0.447 | 4.531 |
| condition[T.hybrid] | 2.042 | 1.27 | -0.447 | 4.531 |
| tier[T.medium] | 0.3114 | 1.009 | -1.667 | 2.29 |
| tier[T.high] | 1.529 | 1.389 | -1.194 | 4.251 |
| condition[T.graph]:tier[T.medium] | 0.827 | 1.601 | -2.311 | 3.965 |
| condition[T.hybrid]:tier[T.medium] | 0.827 | 1.601 | -2.311 | 3.965 |
| condition[T.graph]:tier[T.high] | 0.3877 | 1.784 | -3.109 | 3.884 |
| condition[T.hybrid]:tier[T.high] | 0.3877 | 1.784 | -3.109 | 3.884 |

### steps

fitted

REML; task random-intercept variance 0.773

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | 2.8 | 0.5506 | 1.721 | 3.879 | 3.661e-07 |
| condition[T.graph] | -0.4 | 0.5449 | -1.468 | 0.6679 | 0.4629 |
| condition[T.hybrid] | -1.312e-15 | 0.5449 | -1.068 | 1.068 | 1 |
| tier[T.medium] | 1.8 | 0.7786 | 0.274 | 3.326 | 0.02079 |
| tier[T.high] | 2.2 | 0.8991 | 0.4379 | 3.962 | 0.0144 |
| condition[T.graph]:tier[T.medium] | -0.2 | 0.7706 | -1.71 | 1.31 | 0.7952 |
| condition[T.hybrid]:tier[T.medium] | -0.8 | 0.7706 | -2.31 | 0.7103 | 0.2992 |
| condition[T.graph]:tier[T.high] | 1.067 | 0.8898 | -0.6773 | 2.811 | 0.2306 |
| condition[T.hybrid]:tier[T.high] | 1 | 0.8898 | -0.7439 | 2.744 | 0.2611 |

### log_cost

fitted

REML; task random-intercept variance 0.119

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | -4.241 | 0.1894 | -4.612 | -3.87 | 4.587e-111 |
| condition[T.graph] | -0.6287 | 0.1554 | -0.9332 | -0.3242 | 5.206e-05 |
| condition[T.hybrid] | -0.2777 | 0.1554 | -0.5822 | 0.02684 | 0.0739 |
| tier[T.medium] | 1.028 | 0.2679 | 0.5032 | 1.553 | 0.0001237 |
| tier[T.high] | 1.602 | 0.3093 | 0.9959 | 2.208 | 2.221e-07 |
| condition[T.graph]:tier[T.medium] | -0.3936 | 0.2197 | -0.8243 | 0.03711 | 0.07328 |
| condition[T.hybrid]:tier[T.medium] | -0.688 | 0.2197 | -1.119 | -0.2573 | 0.001743 |
| condition[T.graph]:tier[T.high] | -0.1604 | 0.2537 | -0.6577 | 0.3369 | 0.5273 |
| condition[T.hybrid]:tier[T.high] | -0.2293 | 0.2537 | -0.7266 | 0.268 | 0.3662 |
