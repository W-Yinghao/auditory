"""Read-only: BDF header labels (first 256 + 256*n bytes of each gzipped raw BDF) for all listening runs; checks identical order."""
import collections, glob, gzip, json, os
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0"
labs = collections.Counter(); fsn = collections.Counter(); n_ok = 0
for p in sorted(glob.glob(f"{D}/sub-*/ses-*/eeg/*_task-listeningActive_*_eeg.bdf.gz")):
    with gzip.open(p, "rb") as f:
        h = f.read(256); n = int(h[252:256]); h2 = f.read(256 * n)
    lab = tuple(h2[i * 16:(i + 1) * 16].decode().strip() for i in range(n))
    o = n * (16 + 80 + 8 + 8 + 8 + 8 + 8 + 80); ns = [int(h2[o + i * 8:o + (i + 1) * 8]) for i in range(n)]
    labs[lab] += 1; fsn[(ns[0], float(h[244:252]))] += 1; n_ok += 1
print("files", n_ok, "distinct label tuples", len(labs), "samples/record,record_dur", dict(fsn))
for l, c in labs.items(): print(c, len(l), l[:3], "...", l[62:])
