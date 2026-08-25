# Data provenance

- Source: [https://archive.ics.uci.edu/static/public/336/chronic+kidney+disease.zip](https://archive.ics.uci.edu/static/public/336/chronic+kidney+disease.zip)
- Retrieval date: 2026-08-24
- Official ZIP SHA-256: `3f0d0e5bab0f453165acfa2c77eae695393089c5b338cb4cd98339c96a26a585`
- ARFF SHA-256: `0f3360c0e9239d3d211bfbbdedbe818e4569e6d7399e7398c9b464f6e8feeebe`
- Raw rows: 400
- Predictors: 24
- Target: {'not_ckd': 150, 'ckd': 250}
- Duplicate rows including target: 0
- Missing predictor cells: 1012 across 242 rows

## Explicit raw repairs

| Row ID | Rule | Reason |
|---|---|---|
| ckd-0070 | remove_trailing_empty_field | A trailing comma created an empty 26th field; the empty terminal field was removed. |
| ckd-0073 | remove_trailing_empty_field | A trailing comma created an empty 26th field; the empty terminal field was removed. |
| ckd-0370 | remove_spurious_empty_delimiter | A single empty token shifted otherwise valid trailing categorical values; the empty token was removed. |

## Whitespace variants

```json
{
  "cad": [
    "'\\tno'"
  ],
  "dm": [
    "' yes'",
    "'\\tno'",
    "'\\tyes'"
  ],
  "pcv": [
    "'\\t43'",
    "'\\t?'"
  ],
  "rc": [
    "'\\t?'"
  ],
  "target": [
    "'ckd\\t'"
  ],
  "wc": [
    "'\\t6200'",
    "'\\t8400'",
    "'\\t?'"
  ]
}
```

## Target cleanup

- strip leading/trailing spaces and tabs
- convert to lowercase
- map 'ckd' to 1 and 'notckd' to 0
- reject every other target token
