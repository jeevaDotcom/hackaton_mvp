# Frozen UCI-Scaler Shift

## Decision

Using the exact persisted UCI-development preprocessor, **0.00% of BD-KDD numeric feature cells** lie outside the corresponding UCI-development transformed min/max, and **0.00% of BD-KDD records** contain at least one such numeric value.

| feature | scaler_mean | scaler_scale | uci_t_min | uci_t_p1 | uci_t_p99 | uci_t_max | bd_t_min | bd_t_p1 | bd_t_p99 | bd_t_max | bd_below_uci_min_pct | bd_above_uci_max_pct | bd_outside_uci_range_pct | bd_beyond_2sd_pct | bd_beyond_3sd_pct | bd_beyond_5sd_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hemo | 12.5125 | 2.7314 | -2.8237 | -2.4437 | 1.8923 | 1.9358 | -2.0182 | -1.9816 | 1.6063 | 1.6430 | 0.0000 | 0.0000 | 0.0000 | 0.7085 | 0.0000 | 0.0000 |
| al | 0.9437 | 1.3451 | -0.7016 | -0.7016 | 2.2721 | 3.0155 | -0.7016 | -0.7016 | 2.2721 | 2.2721 | 0.0000 | 0.0000 | 0.0000 | 20.0405 | 0.0000 | 0.0000 |
| sg | 1.0177 | 0.0055 | -2.3119 | -2.3119 | 1.3235 | 1.3235 | -2.3119 | -2.3119 | 1.3235 | 1.3235 | 0.0000 | 0.0000 | 0.0000 | 19.1296 | 0.0000 | 0.0000 |
| pcv | 38.7812 | 7.9994 | -3.0979 | -2.6991 | 1.7775 | 1.9025 | -2.3478 | -2.3478 | 1.9025 | 1.9025 | 0.0000 | 0.0000 | 0.0000 | 8.4008 | 0.0000 | 0.0000 |
| sc | 2.9292 | 5.4609 | -0.4631 | -0.4448 | 2.7189 | 13.3806 | -0.4448 | -0.4210 | 2.1722 | 2.2067 | 0.0000 | 0.0000 | 0.0000 | 7.4899 | 0.0000 | 0.0000 |

The scaler mean/scale and all transformed reference bounds come from the persisted QSVC preprocessor. Because the scaler was fitted on UCI development data, transformed values are measured in UCI training standard deviations.

[Transformed distribution overlays](figures/frozen_scaler_overlays.png)
