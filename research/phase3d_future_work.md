# Phase 3D Future Work — Transportability-Aware Development

## Priority

Future Q-CARE work should treat external transportability as a design constraint established before model development, not as a final test added after internal optimisation.

## Required study sequence

1. Identify candidate external cohorts before model development.
2. Harmonise target definitions, including diagnostic criteria, chronicity, staging, and negative-control construction.
3. Harmonise units, assay methods, coding rules, and measurement protocols.
4. Identify features that are truly common across sites at both semantic and measurement levels.
5. Optimise feature selection for cross-site transportability, not internal performance or internal selection stability alone.
6. Use multi-site development data where governance and provenance permit.
7. Perform leave-one-site-out validation during development.
8. Reserve a final untouched external cohort with documented target comparability.
9. Only then compare classical and quantum models under identical information and compute-accounting rules.

## Transportability-aware feature selection

**Transportability-aware feature selection** means favouring variables whose definitions, measurement processes, availability, and feature-label relationships remain sufficiently stable across development sites. It is distinct from selecting variables that recur across folds inside one cohort.

The Phase 3C finding motivates this future direction: all eight variables were internally stable, yet all eight signed feature-label associations flattened toward chance in BD-KDD. This one experiment does not establish a universal law, and the proposed method is not implemented in the current frozen benchmark.

## What not to do

- Do not retune the frozen UCI models on BD-KDD and relabel the result as external validation.
- Do not optimise target definitions after observing model performance.
- Do not select a site because it makes one model family look favourable.
- Do not compare classical and quantum methods until target and measurement compatibility gates pass.

## Decision gate

Proceed to a final model-family comparison only when target comparability is documented, common-feature semantics are verified, leave-one-site-out results are reported with uncertainty, and a final untouched cohort remains available.
