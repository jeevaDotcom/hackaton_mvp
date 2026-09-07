# Q-CARE Demo Readiness

## Q-CARE technical status

**READY for the stated research-prototype demo scope.**

Input modes:

- Single Patient
- CSV Batch
- Scan Report

Frozen models:

- RBF-SVM
- QSVC
- VQC

Exports:

- Batch CSV
- Research PDF for Single Patient, Scan Report, and CSV Batch

Responsible limits:

- No diagnosis
- No calibrated disease probability
- No Stage 1–5 prediction
- No demonstrated quantum advantage
- External transportability not established

Final test count: **151 passed, 0 failed, 5 existing warnings**.

Run command:

```bash
source .venv/bin/activate
streamlit run app.py --server.port 8501
```

AI Research Assistant: **NOT IMPLEMENTED — OPTIONAL FUTURE ENHANCEMENT**. The Research PDF contains a deterministic automated evidence summary, not a conversational assistant.
