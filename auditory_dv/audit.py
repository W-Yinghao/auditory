"""Directions C and D: CPU audits that decide whether the direction exists (counts only in results/).

C: do the never-analysed MFF segmented/averaged containers contain sessions that have no canonical continuous source?
D: does the CI workbook hold objective hearing / developmental measures for enough EEG-linked children?
Identity-bearing fields are hashed; per-container / per-row detail stays under private/.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from .runtime import ROOT, cfg, open_run, read_json, write_csv_atomic, write_json_atomic

STD_KEYS = {"stad", "standard", "std", "标准", "标准音"}
DEV_KEYS = {"devt", "deviant", "dev", "hdev", "ldev", "偏差", "偏差音"}


def _h(v) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


def _norm(p: str) -> str:
    b = Path(str(p).rstrip("/\\")).name.lower()
    return re.sub(r"\.(mff|raw)$", "", b)


class _UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def _cat_counts(s) -> dict:
    try:
        d = json.loads(s) if isinstance(s, str) else {}
    except json.JSONDecodeError:
        d = {}
    return {str(k).strip().lower(): int(v) for k, v in d.items() if isinstance(v, (int, float))}


def cmd_audit_c(args, config) -> dict:
    run = open_run("audit_c", args.run, config, args=vars(args))
    reg = read_json(ROOT / "private/mff_001/registry.json")
    hist = {h["container_id"]: h for h in read_json(ROOT / "private/mff_001/history.json")}
    idx = pd.read_csv(ROOT / "results/mff_001/container_index.csv")
    canon = set(pd.read_csv(ROOT / cfg(config, "sources.canonical_labels")).container_id)
    by_id = {r["container_id"]: r for r in reg}
    uf = _UF()
    base_of = {cid: _norm(r["path"]) for cid, r in by_id.items()}
    owner = defaultdict(set)
    for cid, b in base_of.items():
        owner[b].add(cid)
    for cid, h in hist.items():
        uf.find(cid)
        for sp in h.get("source_paths") or []:
            b = _norm(sp)
            uf.union(cid, f"src::{b}")
            for other in owner.get(b, ()):
                uf.union(cid, other)
    session_key = {}
    for cid, r in by_id.items():
        subj = _h(r.get("subject_fields"))
        key = f"sess::{subj}::{r.get('record_time')}"
        session_key[cid] = (subj, key)
        if r.get("record_time"):
            uf.union(cid, key)
    comps = defaultdict(list)
    for cid in by_id:
        comps[uf.find(cid)].append(cid)
    idx = idx.set_index("container_id")
    canon_subjects = {session_key[c][0] for c in canon if c in session_key}
    rows = []
    for root, members in comps.items():
        levels = Counter(idx.loc[m, "data_level"] if m in idx.index else "unknown" for m in members)
        has_canon = any(m in canon for m in members)
        seg_std = seg_dev = n_seg = 0
        for m in members:
            if m in idx.index and idx.loc[m, "data_level"] == "epochs":
                cc = _cat_counts(idx.loc[m, "category_counts"])
                n_seg += int(idx.loc[m, "n_storage_epochs"])
                seg_std += sum(v for k, v in cc.items() if k in STD_KEYS)
                seg_dev += sum(v for k, v in cc.items() if k in DEV_KEYS)
        subjects = {session_key[m][0] for m in members}
        rows.append({"component": _h(sorted(members)), "n_containers": len(members), "has_canonical": has_canon,
                     "levels": json.dumps(dict(levels)), "n_segments": n_seg, "seg_std": seg_std, "seg_dev": seg_dev,
                     "usable_segmented": bool(seg_std >= 80 and seg_dev >= 80),
                     "n_subjects": len(subjects), "known_subject": bool(subjects & canon_subjects),
                     "containers": json.dumps(sorted(members))})
    t = pd.DataFrame(rows)
    write_csv_atomic(t, run["private"] / "components.csv", private=True)
    extra = t[~t.has_canonical]
    gate = {"min_components_without_canonical": 50, "min_usable_segmented": 30}
    summary = {"containers": len(by_id), "components": int(len(t)), "components_with_canonical": int(t.has_canonical.sum()),
               "components_without_canonical": int(len(extra)),
               "without_canonical_by_levels": extra.levels.value_counts().head(10).to_dict(),
               "without_canonical_usable_segmented": int(extra.usable_segmented.sum()),
               "without_canonical_segments_total": int(extra.n_segments.sum()),
               "without_canonical_known_subject": int(extra.known_subject.sum()),
               "without_canonical_new_subject": int((~extra.known_subject).sum()),
               "gate": gate,
               "C1_pass": bool(len(extra) >= gate["min_components_without_canonical"]
                               and int(extra.usable_segmented.sum()) >= gate["min_usable_segmented"])}
    write_json_atomic(run["public"] / "summary_audit_c.json", summary, private=False)
    return summary


OBJECTIVE_PATTERNS = {
    "ABR": r"abr|脑干", "ASSR": r"assr|稳态", "OAE": r"oae|耳声发射", "aided_threshold": r"助听.*阈|助听听阈|aided",
    "unaided_threshold": r"裸耳|纯音|听阈|pta|阈值", "P1": r"\bp1\b|p1潜|p1波", "MMN": r"mmn|失匹配",
    "developmental": r"发育商|发育年龄|\bdq\b|\bda\b|gesell|格塞尔", "latency_amplitude": r"潜伏期|波幅|振幅",
    "activation_or_implant_date": r"开机|激活|植入|手术", "tympanometry": r"鼓室|声导抗",
}
OBJECTIVE_KEYS = ("ABR", "ASSR", "OAE", "aided_threshold", "unaided_threshold", "developmental")


def _num(v) -> bool:
    if v is None:
        return False
    if isinstance(v, (int, float)) and np.isfinite(v):
        return True
    s = str(v).strip()
    return bool(re.search(r"\d", s)) and s.lower() not in {"nan", "none"}


def cmd_audit_d(args, config) -> dict:
    import openpyxl
    run = open_run("audit_d", args.run, config, args=vars(args))
    rows = pd.read_csv(ROOT / cfg(config, "sources.ci_rows"))
    schema = read_json(ROOT / cfg(config, "sources.ci_schema"))
    elig = pd.read_csv(ROOT / cfg(config, "sources.ci_eligibility"))
    elig = elig[(elig.scope == "all_MFF_candidate_links") & (elig.stad_measurable == True)]  # noqa: E712
    eligible_pids = set(elig.participant_id)
    fmap = pd.read_csv(ROOT / "private/inventory_001/file_path_map.csv")
    wb_id = rows.source_workbook_file_id.dropna().iloc[0]
    path = fmap.set_index("file_id").loc[wb_id, "absolute_path"]
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    headers = {}
    for sh in schema:
        ws = wb.worksheets[int(sh["sheet_index"]) - 1]
        hr = int(sh["header_row"])
        headers[int(sh["sheet_index"])] = [("" if c is None else str(c)) for c in next(ws.iter_rows(min_row=hr, max_row=hr, values_only=True))]
    col_rows = []
    per_cat_pids = defaultdict(set)
    for sidx, hdr in headers.items():
        sub = rows[rows.source_sheet_index == sidx]
        for j, h in enumerate(hdr):
            cats = [k for k, pat in OBJECTIVE_PATTERNS.items() if re.search(pat, h.lower())]
            if not cats:
                continue
            n_all = n_elig = 0
            pids = set()
            for r in sub.itertuples():
                cells = json.loads(r.raw_cells_json) if isinstance(r.raw_cells_json, str) else []
                if j < len(cells) and _num(cells[j]):
                    n_all += 1
                    if r.participant_id in eligible_pids:
                        n_elig += 1
                        pids.add(r.participant_id)
            for c in cats:
                per_cat_pids[c] |= pids
            col_rows.append({"sheet": sidx, "column": j + 1, "header": h, "categories": "|".join(cats),
                             "nonempty_rows": n_all, "nonempty_eligible_rows": n_elig, "eligible_participants": len(pids)})
    cols = pd.DataFrame(col_rows)
    write_csv_atomic(cols, run["private"] / "objective_columns.csv", private=True)
    coverage = {c: len(per_cat_pids.get(c, set())) for c in OBJECTIVE_PATTERNS}
    gate = 25
    summary = {"eligible_linked_participants": len(eligible_pids), "classified_columns": int(len(cols)),
               "eligible_participants_with_value_by_category": coverage, "gate_min_participants": gate,
               "D_pass_categories": [c for c in OBJECTIVE_KEYS if coverage.get(c, 0) >= gate],
               "D_pass": any(coverage.get(c, 0) >= gate for c in OBJECTIVE_KEYS)}
    write_json_atomic(run["public"] / "summary_audit_d.json", summary, private=False)
    return summary
