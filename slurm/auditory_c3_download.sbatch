#!/bin/bash
#SBATCH --job-name=c3_dl
# C3 v1 P0 data acquisition (AUDITORY_C3_SERVER_PACKAGE_v1_20261003, 02_DATASET_REGISTER). Public CC-BY sources only.
# Usage: sbatch slurm/auditory_c3_download.sbatch <fau_tud|dtu_snhl|federici>
# Resumable (curl -C -) and preemption-safe: a file is moved into place only after its published checksum matches.
#SBATCH --qos=runfill
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_c3/logs/%x-%j.log
set -euo pipefail
umask 022
SRC="${1:?source}"
ROOT=/projects/EEG-foundation-model/auditory_public
mkdir -p "$ROOT"
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} src=$SRC"

fetch() {  # fetch <url> <dest> <algo:md5|sha256> <expected>
  local url=$1 dest=$2 algo=$3 exp=$4
  if [ -f "$dest" ]; then echo "present $dest"; return 0; fi
  mkdir -p "$(dirname "$dest")"
  curl -sS -L --fail -C - --retry 20 --retry-delay 30 --retry-all-errors -o "$dest.part" "$url"
  local got; got=$(${algo}sum "$dest.part" | cut -d' ' -f1)
  if [ "$got" != "$exp" ]; then echo "CHECKSUM_MISMATCH $dest $algo got=$got exp=$exp"; mv "$dest.part" "$dest.bad"; return 1; fi
  mv "$dest.part" "$dest"; echo "ok $algo $exp $(stat -c %s "$dest") $dest"
}

zenodo_record() {  # zenodo_record <record_id> <dest_dir> [skip_key ...]
  local rec=$1 dir=$2; shift 2
  mkdir -p "$dir"
  curl -sS --fail --retry 10 "https://zenodo.org/api/records/$rec" > "$dir/zenodo_record_$rec.json"
  python3 - "$dir/zenodo_record_$rec.json" "$@" > "$dir/.files.tsv" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1])); skip = set(sys.argv[2:])
for f in d["files"]:
    if f["key"] in skip: continue
    algo, val = f["checksum"].split(":")
    print(f["key"], f["links"]["self"], algo, val, sep="\t")
EOF
  while IFS=$'\t' read -r key url algo val; do fetch "$url" "$dir/$key" "$algo" "$val"; done < "$dir/.files.tsv"
}

case "$SRC" in
  fau_tud)
    B=$ROOT/fau_tud
    # stimuli.zip is byte-identical across the three records (same published md5); fetched once from the HA record.
    zenodo_record 17927767 "$B/zenodo_17927767_ha"
    zenodo_record 17952844 "$B/zenodo_17952844_ci" stimuli.zip
    zenodo_record 17952231 "$B/zenodo_17952231_th" stimuli.zip
    for r in "$B"/zenodo_*/zenodo_record_*.json; do python3 -c "import json,sys;print(sys.argv[1],[f['checksum'] for f in json.load(open(sys.argv[1]))['files'] if f['key']=='stimuli.zip'])" "$r"; done
    [ -d "$B/stimuli" ] || { mkdir -p "$B/stimuli.tmp" && unzip -q "$B/zenodo_17927767_ha/stimuli.zip" -d "$B/stimuli.tmp" && mv "$B/stimuli.tmp" "$B/stimuli"; }
    for z in "$B"/zenodo_*/raw_*.zip; do d="${z%.zip}"; [ -d "$d" ] || { unzip -q "$z" -d "$d.tmp" && mv "$d.tmp" "$d"; }; done
    ;;
  dtu_snhl)
    B=$ROOT/dtu_snhl
    zenodo_record 3618205 "$B/zenodo_3618205"
    [ -d "$B/ds-eeg-snhl" ] || { mkdir -p "$B/extract.tmp" && tar -xf "$B/zenodo_3618205/ds-eeg-snhl.tar" -C "$B/extract.tmp" && mv "$B/extract.tmp" "$B/ds-eeg-snhl"; }
    ;;
  federici)
    B=$ROOT/federici_ci_children/mendeley_nzg5g2gzrd_v2
    mkdir -p "$B"
    curl -sS --fail --retry 10 "https://data.mendeley.com/public-api/datasets/nzg5g2gzrd" > "$B/mendeley_dataset_v2.json"
    python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['version']==2 and len(d['files'])>0, (d.get('version'), len(d.get('files',[])))" "$B/mendeley_dataset_v2.json"
    curl -sS --fail --retry 10 "https://data.mendeley.com/public-api/datasets/nzg5g2gzrd/folders/2" > "$B/mendeley_folders_v2.json"
    if [ ! -f "$B/nzg5g2gzrd-2.zip" ]; then
      curl -sS -L --fail --retry 20 --retry-delay 30 --retry-all-errors -o "$B/nzg5g2gzrd-2.zip.part" "https://data.mendeley.com/public-api/zip/nzg5g2gzrd/download/2"
      mv "$B/nzg5g2gzrd-2.zip.part" "$B/nzg5g2gzrd-2.zip"
    fi
    [ -d "$B/files" ] || { mkdir -p "$B/files.tmp" && unzip -q "$B/nzg5g2gzrd-2.zip" -d "$B/files.tmp" && mv "$B/files.tmp" "$B/files"; }
    # Every extracted file must match a published sha256 for its filename; the zip itself has no published checksum.
    python3 - "$B" <<'EOF'
import hashlib, json, os, sys, collections
B = sys.argv[1]
pub = collections.defaultdict(set)
for f in json.load(open(os.path.join(B, "mendeley_dataset_v2.json")))["files"]:
    pub[f["filename"]].add(f["content_details"]["sha256_hash"])
n_pub = sum(len(v) for v in pub.values())
ok = bad = extra = 0; seen = set()
for dp, _, fs in os.walk(os.path.join(B, "files")):
    for fn in fs:
        h = hashlib.sha256(open(os.path.join(dp, fn), "rb").read()).hexdigest()
        if fn not in pub: extra += 1; print("EXTRA", os.path.join(dp, fn)); continue
        if h in pub[fn]: ok += 1; seen.add((fn, h))
        else: bad += 1; print("SHA_MISMATCH", os.path.join(dp, fn))
print(f"federici_verify published_entries={sum(1 for _ in json.load(open(os.path.join(B,'mendeley_dataset_v2.json')))['files'])} distinct_published={n_pub} matched_files={ok} distinct_matched={len(seen)} mismatched={bad} extra={extra}")
if bad: sys.exit(1)
EOF
    ;;
  *) echo "unknown source $SRC"; exit 2;;
esac
du -sh "$ROOT"/* || true
echo "done $(date -Is) src=$SRC"
