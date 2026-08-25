# Quantum Angle and Periodicity Audit

## Concrete installed mapping

Qiskit generated a one-repetition `ZFeatureMap` with one Hadamard and `P(2*x[i])` per qubit. The decomposed installed circuit contains phase expressions `['2*x[0]', '2*x[1]', '2*x[2]', '2*x[3]', '2*x[4]', '2*x[5]', '2*x[6]', '2*x[7]']`. Therefore the audited phase is `2x`, and the fidelity kernel is periodic in each scaled input with period `π`.

| output_feature | source_feature | uci_x_min | uci_x_max | bd_x_min | bd_x_max | uci_phase_min | uci_phase_max | bd_phase_min | bd_phase_max | uci_phase_mod_min | uci_phase_mod_max | bd_phase_mod_min | bd_phase_mod_max | uci_principal_wrap_pct | bd_principal_wrap_pct | uci_abs_ge_2pi_pct | bd_abs_ge_2pi_pct | uci_max_full_periods_from_zero | bd_max_full_periods_from_zero | uci_unique_x | bd_unique_x | uci_distinct_x_near_modulo_pairs | bd_distinct_x_near_modulo_pairs | cross_distinct_x_near_modulo_pairs | cross_angular_distance_median | cross_angular_distance_p5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hemo | hemo | -2.8237 | 1.9358 | -2.0182 | 1.6430 | -5.6474 | 3.8717 | -4.0364 | 3.2859 | 0.0641 | 6.2740 | 0.0641 | 6.2740 | 12.5000 | 13.4615 | 0.0000 | 0.0000 | 0 | 0 | 108 | 101 | 0 | 0 | 0 | 1.5969 | 0.1464 |
| al | al | -0.7016 | 3.0155 | -0.7016 | 2.2721 | -1.4032 | 6.0311 | -1.4032 | 4.5442 | 0.0836 | 6.0311 | 0.0836 | 4.8800 | 7.1875 | 20.0405 | 0.0000 | 0.0000 | 0 | 0 | 6 | 5 | 0 | 0 | 0 | 1.4869 | 0.0000 |
| sg | sg | -2.3119 | 1.3235 | -2.3119 | 1.3235 | -4.6239 | 2.6471 | -4.6239 | 2.6471 | 0.8293 | 5.2948 | 0.8293 | 5.2948 | 1.8750 | 19.1296 | 0.0000 | 0.0000 | 0 | 0 | 5 | 5 | 0 | 0 | 0 | 1.8177 | 0.0000 |
| pcv | pcv | -3.0979 | 1.9025 | -2.3478 | 1.9025 | -6.1958 | 3.8050 | -4.6957 | 3.8050 | 0.0547 | 6.0879 | 0.0547 | 6.0879 | 14.0625 | 26.8219 | 0.0000 | 0.0000 | 0 | 0 | 41 | 35 | 0 | 0 | 0 | 1.5328 | 0.2500 |
| sc | sc | -0.4631 | 13.3806 | -0.4448 | 2.2067 | -0.9263 | 26.7612 | -0.8897 | 4.4134 | 0.0259 | 6.2725 | 0.0039 | 6.2798 | 5.0000 | 21.4575 | 0.9375 | 0.0000 | 4 | 0 | 74 | 725 | 0 | 0 | 13 | 1.7177 | 0.1318 |
| dm_yes | dm | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 0.0000 | 0.0000 |
| appet_poor | appet | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 0.0000 | 0.0000 |
| htn_yes | htn | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 2.0000 | 0.0000 |

`principal_wrap_pct` counts phase values outside `[−π, π]`; `abs_ge_2pi_pct` counts values at least one complete phase period from zero. Near-modulo pairs require transformed values to differ by more than 0.5 while their circular phase distance is below 0.01 radians.

`quantum_angle_audit.csv` contains every UCI-development and BD-KDD transformed value, actual phase, modulo phase, principal-wrap flag, and full-period count. `quantum_angle_summary.csv` contains the table above.

## Plots

- [Scaled value → phase](figures/angle_scaled_to_phase.png)
- [Scaled value → phase modulo 2π](figures/angle_scaled_to_modulo.png)
- [UCI vs BD-KDD modulo-angle distributions](figures/angle_modulo_distributions.png)
- [Per-feature wrap counts](figures/angle_wrap_counts.png)

Phase wrapping alone is not labelled clinically meaningful aliasing. The state-collision audit tests whether high-distance clinical representations actually receive high fidelity.
