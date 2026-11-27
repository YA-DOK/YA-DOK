# YA-DOK — Member 07

Evidence-review draft, 27 November 2026. Baseline: develop / 15f3221 (short revision observed; leader confirmation pending).

## Contents
- Report (DOCX/PDF): tasks 7.1–7.5, technology table, feature matrix, proposed roadmap.
- diagrams/: Graphviz DOT and Mermaid MMD editable sources, PNG/PDF exports.

## Reproduce / verify
1. Clone https://github.com/YA-DOK/YA-DOK and check out 15f3221; confirm full SHA with `git rev-parse HEAD`.
2. Inspect the route files listed in the report. Compare the supplied Blueprint and synthetic fixture locally; do not commit patient identifiers, secrets or unapproved clinical data.
3. Render DOT with `dot -Tpng diagrams/01_data_flow.dot -o diagrams/01_data_flow.png` (use `-Tpdf` for PDF). Open MMD in a Mermaid-compatible editor; export PNG/PDF there (layout may differ from included exports).
4. If authorized, configure an isolated environment using repository README and empty-secret example files. Inspect `/docs` and `/api/health`; run agreed tests only against isolated data. Do not import the approved-labeled fixture unchanged into the draft-only route.
5. Record actual results and revise report; no runtime tests were run for this package.

## Limitations
Clinical approval metadata conflicts with unreviewed provenance; publication, collection/preprocessing, frontend integration, scoring, production deployment and official roadmap are unverified. No clinical data or secrets are bundled.
