# Local verification evidence

`aggregate_verified.json` contains aggregate recomputations from the anonymized clinical tables in the legacy synchronization package. It contains no child-level identifiers, clinical rows, names, or source paths. It does not replace an audit of the original EEG on the server.

`source_checks.json` records source-content checksums, archive integrity, the actual review scope, and local verification of the inventory helper. English labels describe historical documents whose original titles were not in English. These labels are not literal renamed source paths. Original UTF-8 path hashes and unchanged content checksums preserve the connection to the historical archive without reproducing non-English filenames in this edition.

The clinical recomputation used NumPy, pandas, SciPy, and statsmodels. Its code is retained in the original local project at `outputs/server_restart_20260916_audit/audit_clocks.py`; this package does not include that version with its hard-coded local paths. A server recheck should use the original clinical tables and clinical inventories rebuilt from the current matching, with these aggregate values used only for historical reconciliation.

Interpret the evidence as follows:

- These values are exploratory recomputations, not new confirmatory hypothesis tests.
- Additional metrics such as REML and LOCO were used to check the old interpretations; they are not results that must be carried into the new paper.
- The original clinical workbook was not reread in this review. Field units, identity, and dates still require source verification.
- The inventory script was tested on Windows. Linux permission handling is implemented but was not empirically tested in this Windows environment.

Repackaging and translation do not change the numerical evidence. The English edition preserves the aggregate JSON byte-for-byte and regenerates package checksums after translating the documents and source labels.
