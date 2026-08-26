"""Train and freeze the additional live VQC research model exactly once."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
import qiskit
import qiskit_machine_learning
from qiskit.circuit.library import real_amplitudes, z_feature_map
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.algorithms import VQC
from qiskit_machine_learning.optimizers import COBYLA
from qiskit_machine_learning.utils import algorithm_globals

from src.phase1.data import TARGET, load_official_arff, sha256
from src.phase1.modeling import binary_metrics, make_preprocessor
from src.phase2.benchmark import CLINICAL_SIGNATURES


SEED = 20260826


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--root", type=Path, default=PROJECT_ROOT)
    value.add_argument("--features", type=int, choices=(8, 6), default=8)
    value.add_argument("--maxiter", type=int, default=40)
    value.add_argument("--shots", type=int, default=1024)
    value.add_argument("--reuse-model", action="store_true", help="Finalize artifacts from the existing frozen model without fitting")
    return value


def json_dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def model_metrics(y: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float]:
    return binary_metrics(y, (scores >= threshold).astype(int), scores)


def comparator_metrics(root: Path, name: str, raw: pd.DataFrame, y: np.ndarray) -> dict[str, float]:
    bundle = joblib.load(root / f"artifacts/models/{name}")
    matrix = np.asarray(bundle["preprocessor"].transform(raw[bundle["features"]]), dtype=float)
    estimator = bundle["model"]
    scores = np.asarray(estimator.decision_function(matrix), dtype=float)
    predictions = np.asarray(estimator.predict(matrix), dtype=int)
    return binary_metrics(y, predictions, scores)


def complete_profile(row: pd.Series, features: list[str]) -> dict[str, object]:
    profile: dict[str, object] = {}
    for feature in features:
        value = row[feature]
        profile[feature] = str(value) if feature in {"dm", "appet", "htn"} else float(value)
    return profile


def main() -> None:
    args = parser().parse_args()
    root = args.root.resolve()
    output = root / "artifacts/live_vqc"
    model_dir = output / "model"
    preprocessor_dir = output / "preprocessor"
    model_dir.mkdir(parents=True, exist_ok=True)
    preprocessor_dir.mkdir(parents=True, exist_ok=True)

    features = list(CLINICAL_SIGNATURES[args.features])
    if features not in [CLINICAL_SIGNATURES[8], CLINICAL_SIGNATURES[6]]:
        raise RuntimeError("Live VQC must use a validated frozen feature representation")

    parsed = load_official_arff(root / "data/raw/chronic_kidney_disease.arff")
    frame = parsed.frame.set_index("row_id")
    split = json.loads((root / "artifacts/splits.json").read_text())
    development = frame.loc[split["development_row_ids"]].copy()
    holdout = frame.loc[split["locked_test_row_ids"]].copy()

    if args.reuse_model:
        preprocessor = joblib.load(preprocessor_dir / "preprocessor.joblib")
        train_matrix = np.asarray(preprocessor.transform(development[features]), dtype=float)
    else:
        preprocessor = make_preprocessor(features, scale=True)
        train_matrix = np.asarray(preprocessor.fit_transform(development[features], development[TARGET]), dtype=float)
    test_matrix = np.asarray(preprocessor.transform(holdout[features]), dtype=float)
    if train_matrix.shape[1] != len(features) or test_matrix.shape[1] != len(features):
        raise RuntimeError("Preprocessing changed the frozen VQC information budget")

    y_train = development[TARGET].to_numpy(dtype=int)
    y_test = holdout[TARGET].to_numpy(dtype=int)
    feature_map = z_feature_map(len(features), reps=1)
    ansatz = real_amplitudes(len(features), reps=1, entanglement="linear")
    trace: list[dict[str, object]] = []

    def callback(weights: np.ndarray, objective: float) -> None:
        trace.append(
            {
                "evaluation": len(trace) + 1,
                "objective": float(objective),
                "weight_norm": float(np.linalg.norm(weights)),
            }
        )
        if len(trace) == 1 or len(trace) % 5 == 0:
            print(f"evaluation={len(trace):02d} objective={objective:.6f}", flush=True)

    if args.reuse_model:
        vqc = VQC.from_dill(model_dir / "vqc.model")
        trace = pd.read_csv(output / "training_trace.csv").to_dict("records")
        training_runtime = float(json.loads((output / "metrics.json").read_text())["training_runtime_seconds"])
    else:
        sampler = StatevectorSampler(default_shots=args.shots, seed=SEED)
        optimizer = COBYLA(maxiter=args.maxiter)
        rng = np.random.default_rng(SEED)
        initial_point = rng.uniform(-np.pi, np.pi, size=ansatz.num_parameters)
        algorithm_globals.random_seed = SEED
        vqc = VQC(
            feature_map=feature_map,
            ansatz=ansatz,
            optimizer=optimizer,
            sampler=sampler,
            initial_point=initial_point,
            callback=callback,
        )
        started = time.perf_counter()
        vqc.fit(train_matrix, y_train)
        training_runtime = float(time.perf_counter() - started)
    weights = np.asarray(vqc.weights, dtype=float)
    circuit = feature_map.compose(ansatz)
    input_parameters = list(feature_map.parameters)
    weight_parameters = list(ansatz.parameters)
    live_inference_shots = 4096
    vqc.neural_network.sampler = StatevectorSampler(default_shots=live_inference_shots, seed=SEED)
    test_scores = np.asarray(vqc.predict_proba(test_matrix), dtype=float)[:, 1]
    vqc_metrics = model_metrics(y_test, test_scores, 0.5)

    if not args.reuse_model:
        vqc.to_dill(model_dir / "vqc.model")
        np.save(model_dir / "weights.npy", weights)
        joblib.dump(preprocessor, preprocessor_dir / "preprocessor.joblib")
        pd.DataFrame(trace).to_csv(output / "training_trace.csv", index=False)
        (output / "circuit.txt").write_text(str(circuit.decompose().draw(output="text", fold=118)) + "\n")

    reload_model = VQC.from_dill(model_dir / "vqc.model")
    if np.asarray(reload_model.predict(test_matrix[:2])).shape[0] != 2:
        raise RuntimeError("Reloaded VQC smoke test failed")

    classical = comparator_metrics(root, "final_classical_8.joblib", holdout, y_test)
    qsvc = comparator_metrics(root, "final_qsvc_8.joblib", holdout, y_test)
    if min(vqc_metrics["sensitivity"], vqc_metrics["specificity"], vqc_metrics["f1"], vqc_metrics["roc_auc"]) >= 0.80:
        decision = "STRONG DEMO MODEL"
    elif min(vqc_metrics["sensitivity"], vqc_metrics["specificity"]) >= 0.60 and vqc_metrics["f1"] >= 0.65:
        decision = "USABLE RESEARCH DEMO"
    else:
        decision = "WEAK — DISPLAY WITH CAUTION"

    reference = development[features + [TARGET]].reset_index(drop=True)
    reference.to_csv(output / "reference_records.csv", index=False)
    reference_matrix = np.asarray(preprocessor.transform(reference[features]), dtype=float)
    pairwise = np.linalg.norm(reference_matrix[:, None, :] - reference_matrix[None, :, :], axis=2)
    np.fill_diagonal(pairwise, np.inf)
    nearest_distances = pairwise.min(axis=1)
    distance_tertiles = np.quantile(nearest_distances, [1 / 3, 2 / 3]).tolist()
    no_match_threshold = float(np.quantile(nearest_distances, 0.95) * 2.0)

    complete_mask = development[features].notna().all(axis=1)
    complete = development.loc[complete_mask].copy()
    complete_matrix = np.asarray(preprocessor.transform(complete[features]), dtype=float)
    vqc.neural_network.sampler = StatevectorSampler(default_shots=live_inference_shots, seed=SEED)
    complete_scores = np.asarray(vqc.predict_proba(complete_matrix), dtype=float)[:, 1]

    def class_medoid(target: int) -> pd.Series:
        positions = np.flatnonzero(complete[TARGET].to_numpy(dtype=int) == target)
        subset = complete_matrix[positions]
        centroid = subset.mean(axis=0)
        selected = positions[int(np.argmin(np.linalg.norm(subset - centroid, axis=1)))]
        return complete.iloc[int(selected)]

    complete_predictions: list[np.ndarray] = []
    for filename in ("final_classical_8.joblib", "final_qsvc_8.joblib"):
        bundle = joblib.load(root / f"artifacts/models/{filename}")
        comparator_matrix = np.asarray(bundle["preprocessor"].transform(complete[bundle["features"]]), dtype=float)
        complete_predictions.append(np.asarray(bundle["model"].predict(comparator_matrix), dtype=int))
    vqc_predictions = (complete_scores >= 0.5).astype(int)
    disagreement = (vqc_predictions != complete_predictions[0]) | (vqc_predictions != complete_predictions[1])
    candidate_positions = np.flatnonzero(disagreement)
    if len(candidate_positions):
        borderline_position = int(candidate_positions[np.argmin(np.abs(complete_scores[candidate_positions] - 0.5))])
        mixed_source = "Actual complete UCI development record with model disagreement and VQC score nearest the decision threshold"
    else:
        borderline_position = int(np.argmin(np.abs(complete_scores - 0.5)))
        mixed_source = "Actual complete UCI development record with VQC score nearest the decision threshold"
    presets = {
        "ckd_like": {
            "label": "Example A — UCI CKD-like profile",
            "source": "Actual complete UCI development record nearest the CKD-class centroid",
            "profile": complete_profile(class_medoid(1), features),
        },
        "non_ckd_like": {
            "label": "Example B — UCI non-CKD-like profile",
            "source": "Actual complete UCI development record nearest the non-CKD-class centroid",
            "profile": complete_profile(class_medoid(0), features),
        },
        "mixed": {
            "label": "Example C — Borderline/mixed profile",
            "source": mixed_source,
            "profile": complete_profile(complete.iloc[borderline_position], features),
        },
    }
    json_dump(output / "presets.json", presets)

    training_reference: dict[str, object] = {}
    observed_ranges: dict[str, object] = {}
    for feature in features:
        if feature in {"dm", "appet", "htn"}:
            training_reference[feature] = str(development[feature].mode(dropna=True).iloc[0])
            observed_ranges[feature] = sorted(str(value) for value in development[feature].dropna().unique())
        else:
            training_reference[feature] = float(development[feature].median())
            observed_ranges[feature] = [float(development[feature].min()), float(development[feature].max())]

    model_sha = sha256(model_dir / "vqc.model")
    weights_sha = sha256(model_dir / "weights.npy")
    preprocessor_sha = sha256(preprocessor_dir / "preprocessor.joblib")
    metadata = {
        "artifact_status": "frozen live research demonstration",
        "generated_on": date.today().isoformat(),
        "seed": SEED,
        "training_dataset": "UCI CKD only",
        "training_split": "existing frozen 320-row development split",
        "evaluation_split": "existing frozen 80-row locked holdout; previously used in earlier phases and not prospective",
        "feature_order": features,
        "representation": f"validated {len(features)}-variable clinical representation",
        "qubits": len(features),
        "feature_map": "ZFeatureMap",
        "feature_map_reps": 1,
        "ansatz": "RealAmplitudes",
        "ansatz_reps": 1,
        "ansatz_entanglement": "linear",
        "optimizer": "COBYLA",
        "optimizer_max_iterations": args.maxiter,
        "optimizer_evaluations": len(trace),
        "training_sampler": f"StatevectorSampler with {args.shots} shots",
        "live_inference": "deterministic exact NumPy statevector execution of the frozen trained VQC circuit",
        "live_inference_shots": live_inference_shots,
        "live_inference_seed": SEED,
        "classification_threshold": 0.5,
        "score_semantics": "class-1 circuit measurement weight; not calibrated as a disease probability",
        "weight_parameter_names": [parameter.name for parameter in weight_parameters],
        "weight_count": len(weights),
        "training_reference": training_reference,
        "observed_development_ranges": observed_ranges,
        "similarity_distance_tertiles": distance_tertiles,
        "similarity_no_match_threshold": no_match_threshold,
        "model_path": "artifacts/live_vqc/model/vqc.model",
        "model_sha256": model_sha,
        "weights_path": "artifacts/live_vqc/model/weights.npy",
        "weights_sha256": weights_sha,
        "preprocessor_path": "artifacts/live_vqc/preprocessor/preprocessor.joblib",
        "preprocessor_sha256": preprocessor_sha,
        "raw_data_sha256": parsed.provenance["raw_sha256"],
        "splits_sha256": sha256(root / "artifacts/splits.json"),
        "qiskit_version": qiskit.__version__,
        "qiskit_machine_learning_version": qiskit_machine_learning.__version__,
        "architecture_difference": {
            "QSVC": "non-trainable quantum feature map plus fidelity kernel plus classical SVM",
            "VQC": "trainable parameterised quantum circuit plus classical optimizer",
        },
    }
    json_dump(output / "metadata.json", metadata)
    json_dump(
        output / "metrics.json",
        {
            "performance_decision": decision,
            "training_runtime_seconds": training_runtime,
            "vqc": vqc_metrics,
            "rbf_svm_existing_comparator": classical,
            "qsvc_existing_comparator": qsvc,
            "evaluation_note": "All metrics use the existing frozen 80-row UCI holdout; VQC scores are uncalibrated circuit measurement weights.",
        },
    )
    print(json.dumps({"decision": decision, "runtime_seconds": training_runtime, "vqc": vqc_metrics}, indent=2))


if __name__ == "__main__":
    main()
