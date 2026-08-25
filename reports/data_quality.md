# CKD data-quality audit

Generated from the untouched official ARFF. Target-stratified summaries are descriptive only and were not used to choose feature subsets.

| Feature | Type | Missing | Missing % | Unique | Range/categories | Logged raw anomalies |
|---|---|---|---|---|---|---|
| age | numeric_or_ordered | 9 | 2.2% | 76 | min=2.000, median=55.000, max=90.000 | none observed after explicit parser validation |
| bp | numeric_or_ordered | 12 | 3.0% | 10 | min=50.000, median=80.000, max=180.000 | none observed after explicit parser validation |
| sg | numeric_or_ordered | 47 | 11.8% | 5 | min=1.005, median=1.020, max=1.025 | none observed after explicit parser validation |
| al | numeric_or_ordered | 46 | 11.5% | 6 | min=0.000, median=0.000, max=5.000 | none observed after explicit parser validation |
| su | numeric_or_ordered | 49 | 12.2% | 6 | min=0.000, median=0.000, max=5.000 | none observed after explicit parser validation |
| rbc | categorical | 152 | 38.0% | 2 | ["abnormal", "normal"] | none observed after explicit parser validation |
| pc | categorical | 65 | 16.2% | 2 | ["abnormal", "normal"] | none observed after explicit parser validation |
| pcc | categorical | 4 | 1.0% | 2 | ["notpresent", "present"] | none observed after explicit parser validation |
| ba | categorical | 4 | 1.0% | 2 | ["notpresent", "present"] | none observed after explicit parser validation |
| bgr | numeric_or_ordered | 44 | 11.0% | 146 | min=22.000, median=121.000, max=490.000 | none observed after explicit parser validation |
| bu | numeric_or_ordered | 19 | 4.8% | 118 | min=1.500, median=42.000, max=391.000 | none observed after explicit parser validation |
| sc | numeric_or_ordered | 17 | 4.2% | 84 | min=0.400, median=1.300, max=76.000 | none observed after explicit parser validation |
| sod | numeric_or_ordered | 87 | 21.8% | 34 | min=4.500, median=138.000, max=163.000 | none observed after explicit parser validation |
| pot | numeric_or_ordered | 88 | 22.0% | 40 | min=2.500, median=4.400, max=47.000 | none observed after explicit parser validation |
| hemo | numeric_or_ordered | 52 | 13.0% | 115 | min=3.100, median=12.650, max=17.800 | none observed after explicit parser validation |
| pcv | numeric_or_ordered | 71 | 17.8% | 42 | min=9.000, median=40.000, max=54.000 | {"raw_whitespace_or_tab_variants": ["'\\t43'", "'\\t?'"]} |
| wc | numeric_or_ordered | 106 | 26.5% | 89 | min=2200.000, median=8000.000, max=26400.000 | {"raw_whitespace_or_tab_variants": ["'\\t6200'", "'\\t8400'", "'\\t?'"]} |
| rc | numeric_or_ordered | 131 | 32.8% | 45 | min=2.100, median=4.800, max=8.000 | {"raw_whitespace_or_tab_variants": ["'\\t?'"]} |
| htn | categorical | 2 | 0.5% | 2 | ["no", "yes"] | none observed after explicit parser validation |
| dm | categorical | 2 | 0.5% | 2 | ["no", "yes"] | {"raw_whitespace_or_tab_variants": ["' yes'", "'\\tno'", "'\\tyes'"]} |
| cad | categorical | 2 | 0.5% | 2 | ["no", "yes"] | {"raw_whitespace_or_tab_variants": ["'\\tno'"]} |
| appet | categorical | 1 | 0.2% | 2 | ["good", "poor"] | none observed after explicit parser validation |
| pe | categorical | 1 | 0.2% | 2 | ["no", "yes"] | none observed after explicit parser validation |
| ane | categorical | 1 | 0.2% | 2 | ["no", "yes"] | none observed after explicit parser validation |

## Transformation boundary

The raw parser strips logged whitespace/tabs, repairs only the three explicitly logged delimiter anomalies, maps `?` to missing, validates every categorical domain, and maps `ckd/notckd` to `1/0`. Imputation, encoding and scaling are not written into this CSV; they remain fold-fitted sklearn transformers.
