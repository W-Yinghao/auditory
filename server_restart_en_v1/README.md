# Pediatric auditory EEG: server restart package

2026-09-16 | English edition | Design the project from the data audit

**Start with `00_server_start_message.md`.** Send that message and this complete package to the server analysis assistant. The first deliverable is a data audit and feasibility report.

| File | Purpose |
|---|---|
| `00_server_start_message.md` | Ready-to-copy startup message |
| `01_project_brief.md` | Project background, historical reconciliation counts, and first-round priorities |
| `02_research_questions_and_analysis_plan.md` | Candidate designs covering measurement, associations, function, and computational methods |
| `03_legacy_review_and_corrections.md` | Scope of the completed review and corrections to historical interpretations |
| `04_phase0_deliverables_and_data_dictionary.md` | Required tables, figures, matching fields, and inventory-script instructions |
| `templates/` | Empty table headers and a report template for the server analysis |
| `scripts/first_pass_inventory.py` | Read-only file inventory using the Python standard library; no EEG parsing |
| `tests/test_first_pass_inventory.py` | Targeted verification of the inventory script |
| `evidence/` | Verified aggregate results and source checks; no child-level clinical data |
| `MANIFEST.sha256` | Checksums of the package files |

This package contains no EEG, original clinical tables, child-level derived tables, identity mappings, or legacy model code. Keep the original `EEG-SIR_sync_bundle.zip` as an internal historical source, with its private material retained on the server. This package has been prepared locally; no server connection or upload has been performed.

Verify participant counts, experimental conditions, and matching before choosing the primary endpoint and narrative. Documents 01-03 explain the research rationale; document 04 specifies the first-round work.

All filenames and written content in this edition are in English. Historical sources with non-English titles are described using English labels; these labels do not imply that the source files were renamed. Source content checksums are unchanged, and the evidence metadata also records hashes of original source paths where needed. Synthetic Unicode strings in the tests are represented using Python escapes to preserve Unicode coverage while keeping the source text ASCII.
