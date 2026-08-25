# Post-Redesign Accessibility Check

Checked on **24 August 2026** using the final rendered Streamlit UI and shared theme source.

| Area | Evidence | Status |
|---|---|---|
| Contrast | Primary text/background `15.80:1`; secondary `5.63:1`; cobalt accent `5.37:1`; supported badge `5.06:1`; negative badge `5.49:1`; mixed badge corrected from `4.41:1` to `4.99:1`; neutral badge `4.60:1` | PASS |
| Font size | Body and captions remain readable; page titles, section headings, metric values, and verdict labels retain a clear scale at desktop, tablet, and mobile width | PASS |
| Focus visibility | Buttons, inputs, radios, and expanders use a three-pixel visible focus outline with two-pixel offset | PASS |
| Colour independence | Every verdict includes explicit text and a status dot; no conclusion depends on colour alone | PASS |
| Chart captions | Each scientific chart is followed by a plain-language interpretation and, where applicable, its artifact source | PASS |
| Mobile readability | 480 × 900 captures use a single-column comparison, collapsed navigation, readable labels, and no page-level horizontal overflow | PASS |
| Button targets | App-owned sidebar options and the evidence-download control meet the 44-pixel target. Streamlit's framework-owned collapse, Deploy, and menu controls remain 28 pixels | PASS WITH NOTE |
| Heading hierarchy | Every page has one H1; major scientific sections use H2; disease/replay records use H3 beneath the page hierarchy | PASS |
| Reduced motion | `prefers-reduced-motion` disables animation, transition, and smooth scrolling | PASS |

## Responsive checks

- Desktop: 956 × 1000, sidebar visible, `scrollWidth == clientWidth`.
- Tablet: 834 × 1083, stacked process flow and persistent sidebar, no page-level horizontal overflow.
- Mobile width: 480 × 900, sidebar collapsed for content capture, one-column comparison, no page-level horizontal overflow.
- Wide tables remain inside their own contained Streamlit region and do not create page-level horizontal scrolling.

## Outcome

**PASS WITH NOTE.** No blocking content-accessibility defects remain. The amber mixed-status contrast was corrected and revalidated. Streamlit's framework chrome retains three compact 28-pixel controls; they do not carry scientific content, while all Q-CARE-owned controls meet the intended target.
