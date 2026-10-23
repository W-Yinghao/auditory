# DEP12 results: publication packaging (publish_038)

Some DEP12 result files are too large or too numerous to publish one by one. This note says what was packaged and how to restore the original layout. Packaging changes only the container: every member is byte-identical to the frozen build-time copy of the server file, except that where a text file named the private checkpoint-storage root it is replaced by the established placeholder (bundle members: column `placeholder_derived` of `bundles/BUNDLES_MANIFEST_038.tsv`; per-person tables: the source SHA256 below is of the server file).

## Per-person tables

The uncompressed `per_person_*.jsonl` files are not published in this release. Each is published as a gzip copy:

- `per_person_private.jsonl` (103680 lines, source SHA256 `22497842b604fe21…`) → `per_person_private.jsonl.gz`
- `per_person_private_mff.jsonl` (11664 lines, source SHA256 `b692bb297a52bc4c…`) → `per_person_private_mff.jsonl.gz`
- `per_person_public.jsonl` (206684 lines, source SHA256 `89e055d97a4f17be…`) → `per_person_public.jsonl.gz`

Split copies (if any) are independently readable gzip files; decompressing the parts in the order of the `.parts.tsv` manifest and concatenating them gives the whole table.

Note: `per_person_private.jsonl` published in publish_037 is the earlier, smaller snapshot of the same table. The `.jsonl.gz` copy published here supersedes it.

## Measurement and prediction bundles

Files under `measurement/` and `predictions/` that were already published one by one in publish_037 stay at their paths (updated in place if they changed). All other files of those two directories are packed in `bundles/measurement_038_*.tar.gz` and `bundles/predictions_038_*.tar.gz`; member names are paths relative to `results/auditory_alignment_v3/dep12/`, so extracting the bundles inside that directory restores the full layout. No path occurs both as a file and as a bundle member. `bundles/BUNDLES_MANIFEST_038.tsv` lists every member with its archive, size and SHA256.

- `measurement_038_001.tar.gz`: 349 members, 36134331 bytes
- `measurement_038_002.tar.gz`: 76 members, 36646754 bytes
- `measurement_038_003.tar.gz`: 84 members, 37432757 bytes
- `measurement_038_004.tar.gz`: 52 members, 30636518 bytes
- `predictions_038_001.tar.gz`: 708 members, 39350331 bytes
- `predictions_038_002.tar.gz`: 41 members, 22089966 bytes

DEP12 is in progress; these files are a build-time snapshot.
