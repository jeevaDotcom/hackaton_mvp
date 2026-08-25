# BD-KDD Target Profile

## BD-KDD

- Total records: **988**.
- Kidney disease (`1`): **507**.
- Healthy/non-CKD (`0`): **481**.
- Kidney-disease prevalence: **51.32%**.
- Exact raw target labels: `{0: 481, 1: 507}`.
- Canonical mapping: raw `0 → healthy/non-CKD → 0`; raw `1 → kidney disease → 1`.

## UCI comparison

- Full source cohort: **400**; CKD **250**, non-CKD **150**, CKD prevalence **62.50%**.
- Frozen development cohort: **320**; CKD **200**, non-CKD **120**, CKD prevalence **62.50%**.
- Raw labels are `ckd` and `notckd`; whitespace is stripped before canonical `ckd → 1`, `notckd → 0` mapping.

The prevalence difference is descriptive. Prevalence alone neither proves nor disproves target comparability.
