# Judge Question Bank

Each concise answer is suitable for the room. Use the expansion only when challenged.

## TOP 10 most likely

| Rank | Judge question | Safest evidence-backed answer |
|---:|---|---|
| 1 | Where is the quantum advantage? | None was demonstrated. QSVC was internally competitive, but slower and less robust; neither model retained reliable discrimination on BD-KDD. |
| 2 | If classical ML is faster and slightly better, why use quantum at all? | Quantum was the hypothesis under test. The result identifies a narrow competitive case and prevents an unjustified investment or deployment claim. |
| 3 | Why only 400 CKD records? | That is the complete UCI CKD benchmark; its size is disclosed, repeated resampling is used, and transfer is tested rather than assumed. |
| 4 | Why is internal ROC-AUC almost perfect? | The benchmark is unusually separable under this protocol, which is why cross-cohort transportability must be tested rather than assumed. |
| 5 | Why did external validation fail? | Target comparability was only partial, all eight feature-label signals flattened, and both model AUC intervals included chance; we therefore call it a cross-cohort stress test. |
| 6 | Why no entanglement? | The lowest-depth tested map gave the best evidence; added complexity did not improve results, weakening any strong quantum-advantage interpretation. |
| 7 | Why did you reject VQC? | QSVC already answered the controlled kernel question; VQC would add optimisation variance and cost without evidence that it would fix the observed limitations. |
| 8 | Can this run on real quantum hardware? | The circuit is Qiskit-compatible, but only exact, finite-shot, and limited noise simulation were tested—no hardware readiness is claimed. |
| 9 | Is this actually an early disease-detection solution? | No. It is biomedical QML benchmarking infrastructure, not a prospective screening, diagnostic, or patient-risk product. |
| 10 | What exactly is novel? | The integrated methodology: leakage-free stable selection, matched information budgets, paired benchmarking, stress tests, runtime, shift, cross-disease evidence, and governed negative results. |

## A. Problem / healthcare

### 1. What problem are you solving?

**Concise:** Biomedical benchmarks can look excellent while hiding poor robustness, extreme compute cost, or failed transfer. Q-CARE makes those failure modes part of the result.

**Expansion:** It standardises paired classical/QSVC comparisons, stress tests, runtime accounting, cross-cohort transportability audits, and claim control. It is evaluation infrastructure, not a diagnostic workflow.

**Evidence:** `submission/problem_statement_mapping.md`; `src/results_repository.py`.

### 2. Is this really early disease detection?

**Concise:** It evaluates classification evidence relevant to healthcare ML research, but it is not an early-detection or screening product.

**Expansion:** The datasets do not establish prospective early detection, and no patient-level workflow is exposed. “Biomedical QML benchmarking” is the supported positioning.

**Evidence:** `research/phase4_ui_audit.md`; `README.md`.

### 3. Can doctors use this?

**Concise:** Not for patient care. Researchers can use the platform to inspect benchmark evidence and limitations.

**Expansion:** There is no prospective validation, clinical workflow study, calibrated patient-risk output, or medical-device evaluation. The footer excludes diagnosis, treatment, decisions, and triage.

**Evidence:** `app.py`; `research/final_claims.md`.

## B. ML methodology

### 4. Why compare with RBF SVM?

**Concise:** It is a strong, structurally comparable kernel baseline for a quantum-kernel SVM.

**Expansion:** Both methods express classification through pairwise similarity, so matched folds, features, preprocessing, and regularisation isolate the kernel construction more fairly than an unrelated baseline would.

**Evidence:** `research/experiment_protocol.md`; `src/phase2/benchmark.py`.

### 5. Why not deep learning?

**Concise:** With 400 CKD records, a kernel baseline is more proportionate and makes the quantum-kernel comparison interpretable.

**Expansion:** Phase 1 established classical references for this tabular, small-sample setting. Q-CARE is not a universal model bake-off; it tests a focused classical-versus-quantum kernel question.

**Evidence:** `artifacts/development_cv_results.csv`; `research/phase1_decision.md`.

### 6. How did you prevent leakage?

**Concise:** Preprocessing and feature selection were fitted inside training partitions, with frozen splits and explicit fit audits.

**Expansion:** Imputation, scaling, encoding, and selection do not learn from validation, locked-test, robustness-test, or external labels. The paired models share the same folds.

**Evidence:** `artifacts/selection_fit_audit.json`; `artifacts/quantum_preprocessing_audit.json`; `artifacts/splits.json`.

## C. Quantum computing

### 7. Why quantum at all?

**Concise:** Because healthcare QML claims need controlled evidence. The experiment tests whether a quantum kernel remains competitive when feature budget and validation are fair.

**Expansion:** QSVC is a concrete quantum representation method with measurable resource cost. Negative evidence is still valuable because it prevents an unsupported path toward deployment.

**Evidence:** `artifacts/quantum_config.json`; `research/quantum_resource_protocol.md`.

### 8. Where is the quantum advantage?

**Concise:** We did not demonstrate one. QSVC was internally competitive, but much slower and less robust; neither model retained reliable discrimination on BD-KDD.

**Expansion:** “Competitive” means within a predefined 0.05 descriptive tolerance at eight and six variables. It does not mean superiority, acceleration, clinical non-inferiority, or generalisation.

**Evidence:** `submission/quantum_advantage_answer.md`; `artifacts/phase3/reference_cv_summary.csv`.

### 9. Why no entanglement?

**Concise:** The lowest-depth tested feature map gave the best evidence; added complexity did not improve the measured result.

**Expansion:** The search was deliberately limited. The absence of entanglement weakens any distinctly quantum representational claim, and Q-CARE reports that limitation explicitly.

**Evidence:** `artifacts/quantum_config.json`; `artifacts/qsvc_z_reps1_8_circuit.txt`.

### 9A. Why did you reject VQC?

**Concise:** VQC added optimisation variance and cost without evidence that it would resolve the limitations already exposed by QSVC.

**Expansion:** Phase 2 asked whether a controlled quantum-kernel method could remain competitive at equal feature budgets. QSVC answered that question and exposed runtime, robustness, and transfer limitations. A variational classifier would introduce trainable-circuit optimisation, seed sensitivity, and another search surface, but the evidence did not identify a limitation that VQC would clearly fix. The Phase 2 decision therefore recorded VQC as NO-GO rather than adding complexity for novelty theatre.

**Evidence:** `research/phase2_decision.md`; `artifacts/quantum_development_choice.json`.

## D. Dataset

### 10. Why only 400 CKD records?

**Concise:** That is the complete UCI CKD benchmark. We treat its size as a limitation and test transfer rather than pretending it represents deployment.

**Expansion:** Frozen development and locked-test partitions, repeated resampling, fold-local selection, and BD-KDD transfer reduce—but do not remove—the uncertainty created by a small, single-site dataset.

**Evidence:** `artifacts/data_provenance.json`; `reports/data_provenance.md`.

### 11. Why use eight features?

**Concise:** Eight was the stable primary signature selected within training partitions and retained strong performance; six was a compact secondary benchmark.

**Expansion:** Stability includes selection frequency, mean rank, and pairwise Jaccard evidence. Four variables were kept only as a stress test and not retained.

**Evidence:** `reports/feature_stability.csv`; `reports/feature_stability_overall.csv`.

### 12. Are eight features equal to eight clinical tests?

**Concise:** No. Variables do not map one-to-one to orders, visits, or costs.

**Expansion:** Some measures can share a specimen or workflow, and clinical sufficiency was never evaluated. Q-CARE claims a statistical feature budget only.

**Evidence:** `research/final_claims.md`; `artifacts/claim_registry.json`.

## E. Statistics

### 13. Why is ROC-AUC almost 1.0?

**Concise:** The UCI CKD benchmark is highly separable under this protocol, which is exactly why cross-cohort transportability must be tested.

**Expansion:** Repeated cross-validation confirms the internal result but cannot make the cohort representative. We present the unusually high value as a limitation, not proof of clinical performance.

**Evidence:** `artifacts/phase3/reference_cv_summary.csv`; `research/phase3_results.md`.

### 14. Isn’t the dataset too easy?

**Concise:** Internally, yes—it appears unusually separable. Q-CARE’s main lesson comes from showing that the easy benchmark did not transfer.

**Expansion:** Both classical and quantum models score extremely highly internally. BD-KDD exposes the risk of optimising the story around one cohort, although target comparability with UCI is only partial.

**Evidence:** `artifacts/phase3/reference_cv_summary.csv`; `artifacts/phase3/external_ckd_metrics.csv`.

### 15. Is the 0.05 tolerance statistically validated?

**Concise:** No. It is a predefined descriptive competitiveness rule, not a clinical non-inferiority margin.

**Expansion:** Repeated paired results support transparent comparison, but the tolerance is not a powered hypothesis test and is never framed as clinical equivalence.

**Evidence:** `research/experiment_protocol.md`; `research/final_claims.md`.

## F. Cross-cohort transportability

### 16. Why did external validation fail?

**Concise:** We cannot attribute it to one pure mechanism. Target comparability was only partial, and all eight strong UCI feature-label relationships flattened toward chance in BD-KDD.

**Expansion:** RBF SVM ROC-AUC was 0.511 [0.475-0.546] and QSVC ROC-AUC was 0.525 [0.489-0.561]. Both intervals included chance. We therefore report a cross-cohort transportability failure rather than a quantum-specific failure or clean conditional-shift proof.

**Evidence:** `reports/root_cause/target_definition_audit.md`; `reports/root_cause/univariate_auc.md`; `reports/root_cause/external_auc_bootstrap.md`.

### 16a. Did QSVC outperform SVM externally?

**Concise:** No. The point estimates differ, but the paired interval includes zero.

**Expansion:** QSVC AUC was 0.525 and SVM 0.511, but the paired 95% interval for the difference was -0.029 to +0.058. The difference is not distinguishable from sampling variation.

**Evidence:** `reports/root_cause/external_auc_bootstrap.md`.

### 16b. Could scaling have fixed it?

**Concise:** No simple monotonic scaling can restore ranking signal that is absent within the external cohort.

**Expansion:** All eight within-BD-KDD univariate AUCs were approximately 0.5, and clipping/bounded-encoding experiments did not recover reliable discrimination. A monotonic transform preserves ranking.

**Evidence:** `reports/root_cause/univariate_auc.md`; `reports/root_cause/external_auc_bootstrap.md`.

### 17. Could the external dataset mapping be wrong?

**Concise:** The mapping was audited by names, units, ranges, categories, and coverage, but residual semantic mismatch remains a limitation.

**Expansion:** All eight primary variables could be aligned and the model was applied without selection or retraining. Compatible labels and units do not establish equivalent target definitions, measurement processes, or populations; the target-comparability rating is PARTIAL.

**Evidence:** `reports/validation/external_dataset_audit.md`; `artifacts/data_provenance.json`.

### 18. Why not recalibrate or retrain on BD-KDD?

**Concise:** Because the question was zero-adaptation cross-cohort transport. Retraining would answer a different question.

**Expansion:** The full signature and trained pipeline were frozen to expose transportability risk. A later study could measure adaptation, but it must remain separate from the untouched cross-cohort stress test.

**Evidence:** `research/phase3_decision.md`; `src/phase3/validation.py`.

## G. Novelty

### 19. What is novel here?

**Concise:** The novelty is the integrated evidence method: matched budgets, stable selection, robustness, runtime, transportability, cross-disease testing, and explicit negative findings.

**Expansion:** Q-CARE does not claim a new quantum algorithm. It combines controls that are often reported separately into one reproducible decision framework and artifact-driven interface.

**Evidence:** `submission/novelty_statement.md`; `submission/problem_statement_mapping.md`.

### 20. Is this publishable?

**Concise:** It is a credible pilot methodology and negative-results study; publication would benefit from more cohorts, prospective protocol registration, and hardware experiments.

**Expansion:** The leakage controls, paired budgets, stress tests, and internal-stability-versus-external-transportability result are useful. The small datasets, partial target comparability, and simulator-only quantum evidence limit the present scope.

**Evidence:** `research/phase5_decision.md`; `reports/quantum/resource_comparison.md`.

### 21. Isn’t this just a dashboard?

**Concise:** No. The dashboard is the final evidence surface over three experimental phases, frozen artifacts, provenance, validation, and automated claim checks.

**Expansion:** The interface deliberately performs no expensive training. Its value comes from the reproducible pipeline and governed results beneath it.

**Evidence:** `scripts/run_phase1.py`; `scripts/run_phase2.py`; `scripts/run_phase3.py`; `src/results_repository.py`.

## H. Scalability

### 22. Is 464× slower useful?

**Concise:** Not as an efficiency result. It is useful evidence against assuming the quantum method is deployment-ready.

**Expansion:** The ratio is local exact-statevector fit time, not hardware timing. Kernel construction also grows with sample pairs, so scaling is an open limitation.

**Evidence:** `reports/quantum/resource_comparison.csv`; `research/quantum_resource_protocol.md`.

### 23. What happens with thousands of records?

**Concise:** Pairwise quantum-kernel evaluation becomes substantially more expensive; Q-CARE has not demonstrated large-cohort scalability.

**Expansion:** Approximation, subsampling, caching, kernel compression, and hardware-aware execution are future research directions, not delivered capabilities.

**Evidence:** `reports/quantum/resource_comparison.md`.

### 24. Can this run on IBM Quantum?

**Concise:** The circuit is Qiskit-compatible, but reliable end-to-end execution on IBM hardware was not tested.

**Expansion:** Hardware would add transpilation, queueing, shot noise, device noise, drift, and mitigation choices. Simulator compatibility is delivered; hardware readiness is prohibited.

**Evidence:** `artifacts/quantum_environment.json`; `artifacts/quantum_config.json`.

## I. Deployment

### 25. Did you use real quantum hardware?

**Concise:** No. Primary evidence uses exact local statevector evaluation, with separate finite-shot and limited simulated-noise tests.

**Expansion:** No result includes hardware latency, calibration drift, or error mitigation. The UI states this wherever runtime is interpreted.

**Evidence:** `artifacts/quantum_environment.json`; `artifacts/quantum_noise_results.csv`.

### 26. How close is this to production?

**Concise:** The benchmarking platform is demo-ready; the biomedical models are not clinically deployable.

**Expansion:** Production research tooling would need packaging, CI, versioned artifact storage, and more datasets. Clinical use additionally requires prospective validation, governance, workflow study, and regulatory work.

**Evidence:** `submission/reproducibility_check.md`; `README.md`.

### 27. What would you do next?

**Concise:** Build transportability into the study design before model development, then compare classical and quantum models only after targets and measurements are harmonised.

**Expansion:** Identify external cohorts first; harmonise target definitions, units, and measurement protocols; identify common features; optimise transportability-aware feature selection rather than internal performance alone; use multi-site development data and leave-one-site-out validation; reserve a final untouched external cohort; only then compare classical and quantum models.

**Evidence:** `research/phase5_decision.md`.

## J. Ethics / clinical use

### 28. Could this harm patients?

**Concise:** It could if benchmark results were misrepresented as clinical guidance, which is why Q-CARE removes patient inputs and blocks such claims.

**Expansion:** Claim validation, persistent responsible-use language, and cross-cohort failure visibility reduce presentation risk, though they do not replace clinical governance.

**Evidence:** `artifacts/claim_registry.json`; `tests/test_phase4.py`; `app.py`.

### 29. How do you handle population bias?

**Concise:** We expose provenance and avoid averaging across populations; the BD-KDD result is treated as a stress test with PARTIAL target comparability.

**Expansion:** UCI CKD, BD-KDD, Cleveland, and Pima have distinct origins. No fairness conclusion is claimed without subgroup labels and adequate sample sizes.

**Evidence:** `reports/data_provenance.md`; `reports/validation/external_dataset_audit.md`.

### 30. Is Pima an Indian population dataset?

**Concise:** No. It represents women of Pima heritage near Phoenix, Arizona.

**Expansion:** The dashboard states this explicitly to prevent geographic and population misrepresentation.

**Evidence:** `artifacts/data_provenance.json`; `app.py`.

## K. Business / product value

### 31. Who is the user?

**Concise:** Biomedical ML and quantum-ML research teams that need fair, auditable benchmark decisions before considering deployment.

**Expansion:** The workflow can support internal model-governance reviews, reproducibility packages, and evidence communication. It is not marketed to patients or clinicians as a diagnostic tool.

**Evidence:** `submission/README_SUBMISSION.md`; `README.md`.

### 32. What is the product value if quantum failed?

**Concise:** Preventing an unsupported quantum deployment path is valuable; Q-CARE turns negative evidence into an auditable decision.

**Expansion:** The same evidence layer also identifies the narrow cases where QSVC remains competitive, while preserving runtime and transfer context.

**Evidence:** `artifacts/claim_registry.json`; `research/phase4_decision.md`.

### 33. What impact can Q-CARE have?

**Concise:** It can raise the evidence standard for healthcare QML prototypes by making fair baselines and failure tests difficult to omit.

**Expansion:** Impact is methodological at this stage. No healthcare outcome, cost saving, or workflow benefit has been measured.

**Evidence:** `submission/novelty_statement.md`; `submission/final_claim_review.md`.

## L. Hackathon feasibility

### 34. What did you build during the project?

**Concise:** A three-phase experiment pipeline, frozen artifact repository, five-page evidence dashboard, claim validator, tests, and complete demo/submission package.

**Expansion:** Phase 1 established data and classical references; Phase 2 made the matched quantum comparison; Phase 3 added robustness and transfer; Phase 4 productised the evidence.

**Evidence:** `research/phase1_results.md` through `research/phase4_results.md`.

### 35. Does the demo require network or quantum training?

**Concise:** No. It loads precomputed local artifacts and works offline after dependencies and data are present.

**Expansion:** The replay is a repository lookup. It never contacts IBM Quantum or retrains QSVC during Streamlit interaction.

**Evidence:** `src/results_repository.py`; `tests/test_phase4.py`.

### 36. How do we know the numbers were not changed for the pitch?

**Concise:** Headline values are read from frozen artifacts and checked against a claim registry and automated tests.

**Expansion:** The final model manifest carries artifact identity and hashes; application-source tests compare displayed repository values with those artifacts and reject prohibited claims.

**Evidence:** `artifacts/final_model_manifest.json`; `artifacts/claim_registry.json`; `tests/test_phase4.py`.

## Rehearsal rule

Rehearse the TOP 10 in order. Lead with the direct answer, give one measured value, and stop unless the judge asks for the expansion.
