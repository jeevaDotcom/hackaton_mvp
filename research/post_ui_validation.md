# Post-UI Validation Report

Originally validated on 24 August 2026 after the Apple-HIG-inspired redesign; revalidated on **25 August 2026** after the Phase 3D interpretation freeze.

## 1. UI files changed

- `app.py`: removed the remaining hard-coded CKD classical AUC display literal and routed it through `ResultsRepository.reference_metric()`.
- `src/ui_theme.py`: darkened the shared mixed-status token from `#8A681F` to `#806019`, raising badge contrast from `4.41:1` to `4.99:1`.
- Submission and demo documentation was refreshed to match the final navigation and evidence order.

## 2. Total tests passed

**71 passed** on the final Phase 3D run.

## 3. Screenshots regenerated

**16 total** in `submission/screenshots/`: 13 desktop evidence screenshots plus 3 responsive screenshots. Phase 3D added the feature-transportability plot and serum-creatinine comparison.

## 4. Responsive screenshots generated

- `mobile_overview.png` — 480 × 900
- `mobile_external_shift.png` — 480 × 900
- `tablet_ckd_benchmark.png` — 834 × 1083

## 5. Screenshot metric validation result

**PASS — 16/16.** Zero stale or illustrative scientific values. See `submission/screenshot_validation.md`.

## 6. Accessibility status

**PASS WITH NOTE.** Contrast, focus, text-plus-colour status, captions, mobile readability, target sizes, heading hierarchy, and reduced-motion behaviour were checked. One mixed-badge contrast defect was corrected. Q-CARE-owned targets meet 44 pixels; three framework-owned Streamlit chrome controls remain 28 pixels. See `submission/accessibility_check.md`.

## 7. Demo script refreshed

Both the two-minute and 60-second scripts now use the exact final sidebar labels and the shortest rehearsed route through Feature reduction, Classical vs quantum, Runtime transparency, external shift, Missingness stress, and Final evidence summary.

## 8. README refreshed

The project README and submission summary now link to the final hero, screenshot index, metric audit, accessibility check, and offline demo backup.

## 9. Reproducibility status

**PASS.** Dependencies are internally consistent, the claim registry returns zero errors, scientific artifacts remain unchanged, and the app runs from frozen local files without an IBM Quantum or dataset network request.

## 10. Remaining UI issues

No blocking issues. At mobile widths the Streamlit sidebar must be collapsed before presenting; wide dataframes use contained component scrolling, while the page itself has no horizontal overflow. Streamlit's framework-owned collapse, Deploy, and menu controls remain 28 pixels.

## 11. Final live URL

Temporary validation instance: `http://localhost:8520`. Default launch remains `http://localhost:8501`.

## 12. Readiness

**READY**
