# Analysis: full_haiku55

1320 runs, 88 tasks, 5 seed(s), 0 errored (counted incorrect), 0 refused (counted incorrect), 0 majority ties (counted incorrect). Decisions 6.1/6.2/6.13.

## Descriptives

| condition | tier | tasks | seeds | accuracy | accuracy_sd_seeds | ci95_low | ci95_high | errors | refusals | steps | step_limit_rate | input_tokens | cached_tokens | output_tokens | cost_usd | latency_s | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vector | low | 30 | 5 | 0.5533 | 0.05578 | 0.3797 | 0.7149 | 0 | 0 | 4.107 | 0.006667 | 2.238e+04 | 1.406e+04 | 993.9 | 0.001678 | 7.869 | 0.8067 |
| graph | low | 30 | 5 | 1 | 0 | 0.8865 | 1 | 0 | 0 | 2.553 | 0 | 4060 | 2009 | 457.8 | 0.0005052 | 4.142 | 1 |
| hybrid | low | 30 | 5 | 0.98 | 0.02981 | 0.8534 | 0.9976 | 0 | 0 | 3.36 | 0 | 9133 | 4903 | 752 | 0.0009537 | 5.766 | 1 |
| vector | medium | 30 | 5 | 0.4267 | 0.05477 | 0.2681 | 0.6018 | 0 | 0 | 6.133 | 0.04 | 7.173e+04 | 5.129e+04 | 2715 | 0.004425 | 16.31 | 0.8481 |
| graph | medium | 30 | 5 | 0.9333 | 0.02357 | 0.7868 | 0.9815 | 0 | 0 | 3.687 | 0 | 1.004e+04 | 5927 | 1388 | 0.001267 | 8.373 | 0.9964 |
| hybrid | medium | 30 | 5 | 0.94 | 0.02789 | 0.7957 | 0.9844 | 0 | 0 | 3.973 | 0 | 1.491e+04 | 8962 | 1461 | 0.001563 | 8.707 | 0.9943 |
| vector | high | 28 | 5 | 0.1143 | 0.05868 | 0.04091 | 0.2807 | 0 | 0 | 9.821 | 0.75 | 2.132e+05 | 1.689e+05 | 6115 | 0.01028 | 34.56 | 0.4501 |
| graph | high | 28 | 5 | 0.85 | 0.02988 | 0.6768 | 0.9388 | 0 | 0 | 6.243 | 0.02143 | 4.073e+04 | 2.649e+04 | 5240 | 0.004665 | 25.15 | 0.1698 |
| hybrid | high | 28 | 5 | 0.85 | 0.04657 | 0.6768 | 0.9388 | 0 | 0 | 7.129 | 0.06429 | 6.299e+04 | 4.427e+04 | 6004 | 0.005785 | 29.02 | 0.2223 |
| vector | all | 88 | 5 | 0.3705 | 0.03647 | 0.277 | 0.4748 | 0 | 0 | 6.616 | 0.2545 | 9.991e+04 | 7.603e+04 | 3210 | 0.005351 | 19.24 | 0.7073 |
| graph | all | 88 | 5 | 0.9295 | 0.01482 | 0.8562 | 0.9669 | 0 | 0 | 4.114 | 0.006818 | 1.777e+04 | 1.113e+04 | 2296 | 0.002088 | 12.27 | 0.7346 |
| hybrid | all | 88 | 5 | 0.925 | 0.01296 | 0.8505 | 0.9639 | 0 | 0 | 4.768 | 0.02045 | 2.824e+04 | 1.881e+04 | 2665 | 0.002698 | 14.17 | 0.7506 |

## McNemar (exact, majority across seeds)

| tier | a | b | tasks | both_correct | only_a_correct | only_b_correct | both_wrong | p_exact | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| low | vector | graph | 30 | 16 | 0 | 14 | 0 | 0.0001221 | 0.0008545 |
| low | vector | hybrid | 30 | 16 | 0 | 14 | 0 | 0.0001221 | 0.0008545 |
| low | graph | hybrid | 30 | 30 | 0 | 0 | 0 | 1 | 1 |
| medium | vector | graph | 30 | 13 | 1 | 15 | 1 | 0.0005188 | 0.002594 |
| medium | vector | hybrid | 30 | 13 | 1 | 15 | 1 | 0.0005188 | 0.002594 |
| medium | graph | hybrid | 30 | 27 | 1 | 1 | 1 | 1 | 1 |
| high | vector | graph | 28 | 2 | 0 | 22 | 4 | 4.768e-07 | 4.292e-06 |
| high | vector | hybrid | 28 | 2 | 0 | 21 | 5 | 9.537e-07 | 7.629e-06 |
| high | graph | hybrid | 28 | 21 | 3 | 2 | 2 | 1 | 1 |
| all | vector | graph | 88 | 31 | 1 | 51 | 5 | 2.354e-14 |  |
| all | vector | hybrid | 88 | 31 | 1 | 50 | 6 | 4.619e-14 |  |
| all | graph | hybrid | 88 | 78 | 4 | 3 | 3 | 1 |  |

## Mixed-effects models (vector and low are the references)

### correct

fitted

posterior mean/SD (logit scale); task random-intercept SD ~ 2.52. Cells at 0% or 100% accuracy (graph/low): their terms lean on the prior.

| term | estimate | sd | ci95_low | ci95_high |
|---|---|---|---|---|
| Intercept | 0.4388 | 0.1103 | 0.2226 | 0.655 |
| condition[T.graph] | 6.057 | 0.2338 | 5.599 | 6.515 |
| condition[T.hybrid] | 5.066 | 0.2241 | 4.627 | 5.505 |
| tier[T.medium] | -0.8967 | 0.1808 | -1.251 | -0.5423 |
| tier[T.high] | -3.613 | 0.1797 | -3.965 | -3.261 |
| condition[T.graph]:tier[T.medium] | -0.8581 | 0.388 | -1.619 | -0.09766 |
| condition[T.hybrid]:tier[T.medium] | 0.251 | 0.3993 | -0.5316 | 1.034 |
| condition[T.graph]:tier[T.high] | 0.4101 | 0.3088 | -0.1951 | 1.015 |
| condition[T.hybrid]:tier[T.high] | 1.376 | 0.3075 | 0.7736 | 1.979 |

### steps

fitted

REML; task random-intercept variance 0.545

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | 4.107 | 0.161 | 3.791 | 4.422 | 1.936e-143 |
| condition[T.graph] | -1.553 | 0.1246 | -1.798 | -1.309 | 1.124e-35 |
| condition[T.hybrid] | -0.7467 | 0.1246 | -0.9909 | -0.5025 | 2.061e-09 |
| tier[T.medium] | 2.027 | 0.2277 | 1.58 | 2.473 | 5.647e-19 |
| tier[T.high] | 5.715 | 0.2318 | 5.26 | 6.169 | 3.159e-134 |
| condition[T.graph]:tier[T.medium] | -0.8933 | 0.1762 | -1.239 | -0.548 | 3.978e-07 |
| condition[T.hybrid]:tier[T.medium] | -1.413 | 0.1762 | -1.759 | -1.068 | 1.047e-15 |
| condition[T.graph]:tier[T.high] | -2.025 | 0.1793 | -2.377 | -1.674 | 1.403e-29 |
| condition[T.hybrid]:tier[T.high] | -1.946 | 0.1793 | -2.298 | -1.595 | 1.924e-27 |

### log_cost

fitted

REML; task random-intercept variance 0.0519

| term | estimate | sd | ci95_low | ci95_high | p |
|---|---|---|---|---|---|
| Intercept | -6.549 | 0.04844 | -6.644 | -6.454 | 0 |
| condition[T.graph] | -1.081 | 0.03512 | -1.15 | -1.012 | 5.412e-208 |
| condition[T.hybrid] | -0.5015 | 0.03512 | -0.5703 | -0.4326 | 3.012e-46 |
| tier[T.medium] | 1.066 | 0.06851 | 0.9314 | 1.2 | 1.467e-54 |
| tier[T.high] | 1.951 | 0.06972 | 1.815 | 2.088 | 2.253e-172 |
| condition[T.graph]:tier[T.medium] | -0.2013 | 0.04967 | -0.2987 | -0.104 | 5.055e-05 |
| condition[T.hybrid]:tier[T.medium] | -0.5677 | 0.04967 | -0.665 | -0.4703 | 3.013e-30 |
| condition[T.graph]:tier[T.high] | 0.2603 | 0.05055 | 0.1612 | 0.3593 | 2.629e-07 |
| condition[T.hybrid]:tier[T.high] | -0.1061 | 0.05055 | -0.2051 | -0.006976 | 0.03591 |
