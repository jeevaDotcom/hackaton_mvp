"""Render the frozen Qiskit feature-map circuit as an offline text artifact."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.phase2.benchmark import build_feature_map


destination = ROOT / "artifacts/qsvc_z_reps1_8_circuit.txt"
circuit = build_feature_map("z_reps1", 8).decompose()
destination.write_text(str(circuit.draw(output="text", fold=-1)) + "\n")
print(f"Rendered {circuit.num_qubits}-qubit Qiskit circuit at depth {circuit.depth()} to {destination}")
