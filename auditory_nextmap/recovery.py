"""B0: recover MFF experimental semantics, non-canonical identities/ages, SET bridges and BDF clock candidates
(execution spec sections 6-8; protocol section 4). Everything per record / per person stays under private/;
results/ receives counts only.

Evidence grades: DIRECT (explicit metadata of the record itself, e.g. its own segmentation rule or CELL definition),
LINKED (a verified processing-lineage edge carries a DIRECT label back to the source recording), SCOPED (a batch /
directory label whose scope contains the record), CANDIDATE (names, SOA, similarity: only used to locate files),
UNKNOWN / CONFLICT. Each claim field is graded on its own; strong conflicts stay CONFLICT.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from .runtime import ROOT, ProvenanceError, cfg, close_run, open_run, write_csv_atomic, write_json_atomic

# ---------------------------------------------------------------------- vocabulary (stimulus / task literals only)
VOCAB = [
    ("wav", re.compile(r"[A-Za-z0-9_\-]+\.wav", re.I)),
    ("hz", re.compile(r"(?<![\d.])\d{3,4}\s?hz\b", re.I)),
    ("sound_k", re.compile(r"sound\s?\d+(\.\d+)?k\b", re.I)),
    ("rensheng", re.compile(r"rensheng[a-z]*\d?", re.I)),
    ("syllable", re.compile(r"\b(?:ba[1-4]?ba[1-4]?|bapa|ba[1-4]?|pa[1-4]?)\b", re.I)),
    ("puretone", re.compile(r"pure\s?tone", re.I)),
    ("tone_word", re.compile(r"\btones?\b", re.I)),
    ("role_code", re.compile(r"\b(?:stad|devt|hdev|ldev|standard|deviant)\b", re.I)),
    ("paradigm", re.compile(r"\b(?:mmn|oddball|syllab\w*)\b", re.I)),
    ("zh", re.compile(r"纯音|声调|音节|人声|言语|短音")),
]
ROLE_OF_CODE = {"stad": "standard", "devt": "deviant", "hdev": "high_deviant", "ldev": "low_deviant"}
SETTINGS_RULE = re.compile(r'^(\d+): Rules for category "(.*)"$')
CELL_RULE = re.compile(r'^Cell is "(.*)"$')
CODE_RULE = re.compile(r'^Code is "(.*)"')


def vocab_hits(text: str) -> list[tuple[str, str]]:
    out = []
    for kind, rx in VOCAB:
        for m in rx.finditer(text or ""):
            out.append((kind, m.group(0).lower().replace(" ", "")))
    return out


def _h(v) -> str:
    return "H" + hashlib.sha256(str(v).encode("utf-8")).hexdigest()[:12]


def name_semantics(stimulus: str) -> dict:
    """Literal reading of a stimulus file / cell name (audio itself is not available)."""
    s = stimulus.lower()
    out = {"task_family": "other", "physical_frequency_hz": None, "lexical_tone_label": None, "token_id": s}
    m = re.search(r"(\d{3,4})\s?hz", s)
    k = re.search(r"sound\s?(\d+(?:\.\d+)?)k", s)
    if m or k:
        out["task_family"] = "puretone"
        out["physical_frequency_hz"] = float(m.group(1)) if m else float(k.group(1)) * 1000.0
    elif re.search(r"(rensheng)?(ba|pa)\d?\.wav$|(rensheng)?(ba|pa)\d?$", s):
        syl = re.search(r"(ba|pa)(\d?)(?:\.wav)?$", s)
        out["task_family"] = "syllable"
        out["token_id"] = syl.group(1) + (syl.group(2) or "")
        out["lexical_tone_label"] = ("T" + syl.group(2)) if syl.group(2) else None
    return out


def pair_family(names: list[str]) -> str:
    """Task family of a two-category rule: two frequencies -> puretone; ba vs pa -> bapa; ba vs ba4 -> ba1ba4."""
    sem = [name_semantics(n) for n in names]
    if all(x["task_family"] == "puretone" for x in sem):
        return "puretone"
    if all(x["task_family"] == "syllable" for x in sem):
        toks = {x["token_id"].rstrip("1234") for x in sem}
        return "bapa" if toks == {"ba", "pa"} else ("ba1ba4" if toks == {"ba"} else "lexical_tone_other")
    return "other"


# ---------------------------------------------------------------------- shared tables

class Ledgers:
    def __init__(self, config: dict):
        self.config = config
        self.reg = {r["container_id"]: r for r in json.loads((ROOT / cfg(config, "sources.mff_registry")).read_text())}
        self.hist = {h["container_id"]: h for h in json.loads((ROOT / cfg(config, "sources.mff_history")).read_text())}
        idx = pd.read_csv(ROOT / "results/mff_001/container_index.csv")
        idx = idx[~idx.container_id.duplicated()].set_index("container_id")
        idx["event_interval_median_s"] = pd.to_numeric(idx["event_interval_median_s"], errors="coerce")
        self.idx = idx
        self.label_map = json.loads((ROOT / "private/mff_001/label_map.json").read_text())
        self.canon = pd.read_csv(ROOT / cfg(config, "sources.canonical_labels")).set_index("container_id")
        comp = pd.read_csv(ROOT / cfg(config, "sources.dv_components"))
        self.components = {r.component: {"members": json.loads(r.containers), "has_canonical": bool(r.has_canonical),
                                         "levels": json.loads(r.levels), "known_subject": bool(r.known_subject)}
                           for r in comp.itertuples()}
        self.comp_of = {m: c for c, d in self.components.items() for m in d["members"]}
        clues = pd.read_csv(ROOT / "results/assets_001/condition_clues.csv")
        self.clue = dict(zip(clues.container_id, clues.condition_clue))
        self._fmap = None

    @property
    def fmap(self) -> dict:
        if self._fmap is None:
            with open(ROOT / cfg(self.config, "sources.file_path_map"), newline="", encoding="utf-8") as h:
                self._fmap = {r["file_id"]: r["absolute_path"] for r in csv.DictReader(h)}
        return self._fmap

    def files(self, cid: str) -> list[Path]:
        return [Path(self.fmap[f]) for f in self.reg[cid]["files"] if f in self.fmap]

    def event_codes(self, cid: str) -> Counter:
        if cid not in self.idx.index or not isinstance(self.idx.loc[cid, "event_code_counts"], str):
            return Counter()
        raw = json.loads(self.idx.loc[cid, "event_code_counts"])
        return Counter({self.label_map.get(k, k): int(v) for k, v in raw.items()})

    def basename(self, path: str) -> str:
        return re.sub(r"\.(mff|raw)$", "", Path(str(path).rstrip("/\\").replace("\\", "/")).name.lower())

    def lineage_edges(self) -> list[dict]:
        """derived -> source edges from history source_paths; verified only with a unique basename owner AND the same
        candidate acquisition id or record time (same-name files are not automatically the same source)."""
        owner = defaultdict(list)
        for cid, r in self.reg.items():
            owner[self.basename(r["path"])].append(cid)
        edges = []
        for cid, h in self.hist.items():
            for sp in h.get("source_paths") or []:
                cands = [c for c in owner.get(self.basename(sp), []) if c != cid]
                if not cands:
                    continue
                acq_of_cands = {self.reg[c]["candidate_acquisition_id"] for c in cands}
                for src in cands:
                    same_acq = self.reg[src]["candidate_acquisition_id"] == self.reg[cid]["candidate_acquisition_id"]
                    same_time = bool(self.reg[src]["record_time"]) and self.reg[src]["record_time"] == self.reg[cid]["record_time"]
                    # several owners of one basename are acceptable only when they are versions of ONE acquisition
                    verified = (same_acq or same_time) and (len(cands) == 1 or len(acq_of_cands) == 1)
                    edges.append({"edge_id": _h((cid, src)), "derived": cid, "source": src, "unique_basename": len(cands) == 1,
                                  "same_acquisition_id": bool(same_acq), "same_record_time": bool(same_time),
                                  "verified": bool(verified)})
        return edges


def normalise_role(category: str) -> str:
    c = category.strip().lower()
    if c in ("standard", "stad", "std", "标准", "标准音"):
        return "standard"
    if c in ("deviant", "devt", "devat", "dev", "devi", "偏差", "偏差音"):
        return "deviant"
    return {"hdev": "high_deviant", "ldev": "low_deviant"}.get(c, "other")


def segmentation_rules(settings: list[str]) -> list[dict]:
    """[{category, codes, cells}] from a Net Station segmentation settings list."""
    rules, cur = [], None
    for line in settings:
        m = SETTINGS_RULE.match(line.strip())
        if m:
            cur = {"category": m.group(2), "codes": [], "cells": []}
            rules.append(cur)
            continue
        if cur is None:
            continue
        m = CODE_RULE.match(line.strip())
        if m:
            cur["codes"].append(m.group(1))
        m = CELL_RULE.match(line.strip())
        if m:
            cur["cells"].append(m.group(1))
    return rules


# ---------------------------------------------------------------------- count-based verification helpers

def decoded_counts(L, cid: str, column: str) -> dict:
    raw = L.idx.loc[cid, column] if cid in L.idx.index else None
    return json.loads(raw) if isinstance(raw, str) and raw.strip().startswith("{") else {}


def stm_cell_classes(L, cid: str) -> list[tuple[str, int]]:
    """cel# value counts of stm+ events (container index numeric-key ledger), largest first."""
    out = Counter()
    for k, counts in decoded_counts(L, cid, "numeric_event_key_counts").items():
        if "|" not in k or not isinstance(counts, dict):
            continue
        code_tok, key_tok = k.split("|", 1)
        if L.label_map.get(code_tok, code_tok).lower() == "stm+" and L.label_map.get(key_tok, key_tok) == "cel#":
            for v, n in counts.items():
                out[str(v)] += int(n)
    return out.most_common()


def role_counts_from_categories(L, cid: str) -> Counter:
    out = Counter()
    for k, v in decoded_counts(L, cid, "category_counts").items():
        out[normalise_role(L.label_map.get(k, k))] += int(v)
    return out


def counts_match(a: int, b: int, tol: float = 0.10) -> bool:
    return a > 0 and b > 0 and abs(a - b) <= tol * max(a, b)


def log_semantics(hits: list) -> dict:
    """Task families named in a container's Net Station log and the stimulus-file token counts."""
    toks = Counter()
    for kind, tok, n in hits:
        toks[(kind, tok)] += int(n)
    fams = set()
    names = [t for (k, t) in toks if k in ("wav", "hz", "sound_k", "rensheng")]
    if any(re.search(r"\d{3,4}hz|sound\d", t) for t in names):
        fams.add("puretone")
    if any("renshengpa" in t for t in names):
        fams.add("bapa")
    if any(re.search(r"renshengba[1-4]", t) for t in names):
        fams.add("ba1ba4")
    if any(re.fullmatch(r"\d+(_\d+)?[a-z]*\.wav", t) for t in names):
        fams.add("numbered_wav_unknown")
    wav = Counter({t: n for (k, t), n in toks.items() if k == "wav"})
    return {"families": sorted(fams), "wav_counts": wav.most_common()}


# ---------------------------------------------------------------------- U1 raw metadata scan (read-only)

def scan_events_xml(path: Path) -> dict:
    """Codes, string-valued keys (vocabulary values kept, other strings hashed) and CELL definitions."""
    codes, strings, cells = Counter(), Counter(), []
    try:
        for _ev, el in ET.iterparse(str(path), events=("end",)):
            if el.tag.rsplit("}", 1)[-1] != "event":
                continue
            code, label, keys = "", "", {}
            for ch in el:
                t = ch.tag.rsplit("}", 1)[-1]
                if t == "code":
                    code = (ch.text or "").strip()
                elif t == "label":
                    label = (ch.text or "").strip()
                elif t == "keys":
                    for k in ch:
                        kc = dt = ""
                        for kk in k:
                            tt = kk.tag.rsplit("}", 1)[-1]
                            if tt == "keyCode":
                                kc = (kk.text or "").strip()
                            elif tt == "data":
                                dt = (kk.text or "").strip()
                        keys[kc] = dt
            codes[code] += 1
            for kc, dt in list(keys.items()) + ([("label", label)] if label else []):
                if dt and not re.fullmatch(r"[-+]?\d+(\.\d+)?", dt):
                    hits = vocab_hits(dt)
                    strings[(code, kc, dt.lower() if hits else _h(dt))] += 1
            if code.upper() == "CELL":
                cells.append({k: (v if (vocab_hits(v) or re.fullmatch(r"[-+]?\d+(\.\d+)?", v or "")) else _h(v))
                              for k, v in keys.items()})
            el.clear()
    except ET.ParseError as exc:
        return {"error": f"parse_error:{exc}"}
    return {"codes": dict(codes), "strings": [list(k) + [n] for k, n in strings.items()], "cells": cells}


def rtf_plain(raw: str) -> str:
    """RTF -> plain text: \\'hh runs decoded as GBK (Chinese), control words and braces removed."""
    def dec(m):
        try:
            return bytes.fromhex(m.group(0).replace("\\'", "")).decode("gbk", errors="ignore")
        except ValueError:
            return " "
    s = re.sub(r"(?:\\'[0-9a-fA-F]{2})+", dec, raw)
    s = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", s)
    return re.sub(r"[{}\\]", " ", s)


def scan_text_file(path: Path) -> Counter:
    try:
        data = path.read_bytes()[:2_000_000]
    except OSError:
        return Counter()
    raw = data.decode("utf-8", errors="ignore")
    if path.suffix.lower() == ".rtf":
        raw = rtf_plain(raw)
    return Counter(vocab_hits(raw))


def cmd_recover_u1(args, config, run) -> dict:
    L = Ledgers(config)
    edges = L.lineage_edges()
    scope = set(L.canon.index) | {m for d in L.components.values() if not d["has_canonical"] for m in d["members"]}
    scope |= {e["derived"] for e in edges if e["source"] in scope}
    scan_dir = run["private"] / "scan"
    reuse = (ROOT / cfg(config, "paths.private_relative") / args.reuse_scan / "scan") if getattr(args, "reuse_scan", "") else None
    scans, reused = {}, 0
    for cid in sorted(scope):
        p = scan_dir / f"{cid}.json"
        if not p.exists() and reuse is not None and (reuse / f"{cid}.json").exists():
            write_json_atomic(p, json.loads((reuse / f"{cid}.json").read_text()), private=True)   # read-only reuse
            reused += 1
        if not p.exists():
            out = {"events": {}, "text_hits": {}}
            for f in L.files(cid):
                name = f.name
                if name.startswith("Events_") and name.endswith(".xml"):
                    out["events"][_h(name)] = scan_events_xml(f)
                elif name in ("recordingSettings.xml", "lastSettings.xml", "techNote.rtf", "subject.xml") or name.startswith("log_"):
                    hits = scan_text_file(f)
                    if hits:
                        out["text_hits"][name if not name.startswith("log_") else "log_txt"] = [list(k) + [v] for k, v in hits.items()]
            write_json_atomic(p, out, private=True)
        scans[cid] = json.loads(p.read_text())
    claims = []

    def claim(cid, field, value, grade, *, evidence, locator, lineage="", scope_def="", conflict="none", raw="", review="auto"):
        claims.append({"record_id": cid, "acquisition_id": L.reg[cid]["candidate_acquisition_id"], "claim_field": field,
                       "claim_value": value, "evidence_grade": grade, "evidence_file_id": evidence, "evidence_locator": locator,
                       "lineage_edge_ids": lineage, "scope_definition": scope_def, "conflict_status": conflict,
                       "review_status": review, "raw_literal": raw,
                       "canonical": cid in L.canon.index, "component": L.comp_of.get(cid, "")})
    # (1) path task literal (directory label) -> SCOPED; (2) event-code roles -> DIRECT
    for cid in sorted(scope):
        if cid in L.canon.index:
            t = L.canon.loc[cid, "protocol_task"]
            if t != "unknown":
                claim(cid, "task_family", "ba1ba4" if t == "tone" else t, "SCOPED", evidence="canonical_source_labels",
                      locator="protocol_task", scope_def="original path / subject literal (task_literal rule)")
        codes = L.event_codes(cid)
        for code, role in ROLE_OF_CODE.items():
            if codes.get(code, 0) > 0:
                claim(cid, "presentation_role", role, "DIRECT", evidence="container_index", locator=f"event_code:{code}",
                      raw=code)
        if cid in L.clue:
            claim(cid, "context_id", L.clue[cid], "SCOPED", evidence="condition_clues", locator="directory label",
                  scope_def="directory label, not acquisition verified")
        if cid in L.idx.index and np.isfinite(L.idx.loc[cid, "event_interval_median_s"]):
            claim(cid, "soa_median_s", round(float(L.idx.loc[cid, "event_interval_median_s"]), 3), "CANDIDATE",
                  evidence="container_index", locator="event_interval_median_s", review="locator_only")
    # (3) segmentation rules with Cell literals -> DIRECT for the derived container, LINKED to verified sources
    rule_sets = {}
    for cid in sorted(scope):
        rules = [r for r in segmentation_rules(L.hist.get(cid, {}).get("settings") or []) if r["cells"]]
        if rules:
            rule_sets[cid] = rules
            fam = pair_family([c for r in rules for c in r["cells"]])
            for r in rules:
                for cell in r["cells"]:
                    sem = name_semantics(cell)
                    claim(cid, f"stimulus_id[{r['category'].lower()}]", cell, "DIRECT", evidence="history.settings",
                          locator=f"rule:{r['category']}|code:{'+'.join(r['codes'])}", raw=cell,
                          review="name_literal_audio_unverified")
                    if sem["physical_frequency_hz"]:
                        claim(cid, f"physical_frequency_hz[{r['category'].lower()}]", sem["physical_frequency_hz"], "DIRECT",
                              evidence="history.settings", locator=f"rule:{r['category']}", raw=cell,
                              review="name_literal_audio_unverified")
                    if sem["lexical_tone_label"]:
                        claim(cid, f"lexical_tone_label[{r['category'].lower()}]", sem["lexical_tone_label"], "DIRECT",
                              evidence="history.settings", locator=f"rule:{r['category']}", raw=cell,
                              review="name_literal_audio_unverified")
            claim(cid, "task_family", fam, "DIRECT", evidence="history.settings", locator="segmentation rule pair",
                  review="name_literal_audio_unverified")
    cel_map = {}
    for e in edges:
        d, src_ = e["derived"], e["source"]
        if e["verified"] or d not in rule_sets or not e["unique_basename"]:
            continue
        if L.idx.loc[d, "data_level"] != "epochs" or L.idx.loc[src_, "data_level"] != "continuous_or_discontinuous":
            continue
        rc_ = role_counts_from_categories(L, d)
        cls = stm_cell_classes(L, src_)
        if len(cls) >= 2 and counts_match(rc_.get("standard", 0), cls[0][1]) and counts_match(rc_.get("deviant", 0), cls[1][1]):
            e["verified"] = True
            e["verification"] = "category_counts_match_stm_cel_classes"
            cel_map[(d, src_)] = {"standard": cls[0][0], "deviant": cls[1][0]}
    out_edges = defaultdict(list)
    for e in edges:
        out_edges[e["derived"]].append(e)
    for start, rules in rule_sets.items():
        fam = pair_family([c for r in rules for c in r["cells"]])
        seen, frontier = {start}, [(start, [], True)]
        while frontier:                                   # breadth-first along source edges (derived -> source)
            node, path, all_verified = frontier.pop(0)
            for e in out_edges.get(node, []):
                if e["source"] in seen:
                    continue
                seen.add(e["source"])
                chain, ok = path + [e["edge_id"]], all_verified and e["verified"]
                frontier.append((e["source"], chain, ok))
                if e["source"] not in scope:
                    continue
                grade = "LINKED" if ok else "CANDIDATE"
                for r in rules:
                    for cell in r["cells"]:
                        claim(e["source"], f"stimulus_id[{r['category'].lower()}]", cell, grade, evidence="history.settings",
                              locator=f"derived:{start}|hops:{len(chain)}|rule:{r['category']}", lineage="|".join(chain),
                              raw=cell, review="name_literal_audio_unverified")
                claim(e["source"], "task_family", fam, grade, evidence="history.settings",
                      locator=f"derived:{start}|hops:{len(chain)}", lineage="|".join(chain), review="name_literal_audio_unverified")
    # (4) the record's own Events XML: CELL definitions and string keys with stimulus vocabulary -> DIRECT
    for cid, sc in scans.items():
        for fh, ev in sc["events"].items():
            for cell in ev.get("cells", []):
                vals = [v for v in cell.values() if isinstance(v, str) and vocab_hits(v)]
                for v in vals:
                    claim(cid, "cell_definition", v, "DIRECT", evidence=f"Events:{fh}", locator="CELL event keys", raw=v,
                          review="name_literal_audio_unverified")
            for code, kc, val, n in ev.get("strings", []):
                if not str(val).startswith("H"):
                    claim(cid, "event_string_key", f"{code}|{kc}|{val}", "DIRECT", evidence=f"Events:{fh}",
                          locator=f"code:{code}|key:{kc}|n:{n}", raw=str(val), review="name_literal_audio_unverified")
        for fname, hits in sc["text_hits"].items():
            for kind, tok, n in hits:
                if kind in ("role_code",):
                    continue
                claim(cid, "free_text_vocab", f"{kind}:{tok}", "SCOPED" if fname != "subject.xml" else "CANDIDATE",
                      evidence=fname, locator=f"count:{n}", scope_def="free text / settings file of this container",
                      raw=tok, review="token_only_no_context")
    for cid, sc in scans.items():
        hits = sc["text_hits"].get("log_txt")
        if not hits:
            continue
        sem = log_semantics(hits)
        fams = [f for f in sem["families"] if f != "numbered_wav_unknown"]
        codes = L.event_codes(cid)
        std, dev = codes.get("stad", 0), codes.get("devt", 0)
        wav = sem["wav_counts"]
        verified = len(fams) == 1 and len(wav) >= 2 and counts_match(wav[0][1], std) and counts_match(wav[1][1], dev)
        if len(fams) == 1:
            claim(cid, "task_family", fams[0], "DIRECT" if verified else "SCOPED", evidence="log_txt",
                  locator="stimulus-file counts match stad/devt counts" if verified else "family named in container log",
                  scope_def="Net Station log inside this container", review="log_literal_audio_unverified")
        elif len(fams) > 1:
            for f in fams:
                claim(cid, "task_family", f, "SCOPED", evidence="log_txt", locator="several families named in one log",
                      scope_def="Net Station log inside this container", conflict="CONFLICT", review="log_literal_audio_unverified")
        if verified:
            claim(cid, "stimulus_id[standard]", wav[0][0], "DIRECT", evidence="log_txt", locator=f"count {wav[0][1]} vs stad {std}",
                  raw=wav[0][0], review="log_literal_audio_unverified")
            claim(cid, "stimulus_id[deviant]", wav[1][0], "DIRECT", evidence="log_txt", locator=f"count {wav[1][1]} vs devt {dev}",
                  raw=wav[1][0], review="log_literal_audio_unverified")
    C = mark_conflicts(pd.DataFrame(claims))
    write_csv_atomic(C, run["private"] / "semantic_claims.csv", private=True)
    write_csv_atomic(pd.DataFrame(edges), run["private"] / "lineage_edges.csv", private=True)
    out = summarize_u1(L, C, scans, edges, scope)
    out["scans_reused_from"] = getattr(args, "reuse_scan", "") or None
    out["scans_reused"] = reused
    return out


def mark_conflicts(C: pd.DataFrame) -> pd.DataFrame:
    """Two different strong (DIRECT/LINKED) task families, or a strong family against a different SCOPED label, on one
    record -> every task_family claim of that record is CONFLICT (no majority vote)."""
    C = C.copy()
    for cid, g in C[C.claim_field == "task_family"].groupby("record_id"):
        strong = set(g[g.evidence_grade.isin(["DIRECT", "LINKED"])].claim_value) - {"other"}
        scoped = set(g[g.evidence_grade == "SCOPED"].claim_value) - {"other"}
        if len(strong) > 1 or (strong and scoped and not scoped <= strong):
            C.loc[(C.record_id == cid) & (C.claim_field == "task_family"), "conflict_status"] = "CONFLICT"
    return C


def summarize_u1(L: Ledgers, C: pd.DataFrame, scans: dict, edges: list, scope: set) -> dict:
    unknown = [c for c in L.canon.index if L.canon.loc[c, "protocol_task"] == "unknown"]

    def best(cid, field_prefix):
        g = C[(C.record_id == cid) & C.claim_field.str.startswith(field_prefix)]
        for grade in ("DIRECT", "LINKED", "SCOPED", "CANDIDATE"):
            if (g.evidence_grade == grade).any():
                return grade
        return "UNKNOWN"
    rows = []
    for cid in unknown:
        roles = sorted(set(C[(C.record_id == cid) & (C.claim_field == "presentation_role")].claim_value))
        rows.append({"task": best(cid, "task_family"), "stimulus": best(cid, "stimulus_id"),
                     "cell_definition": best(cid, "cell_definition"), "free_text": best(cid, "free_text_vocab"),
                     "roles": "+".join(roles) or "none"})
    U = pd.DataFrame(rows)
    stim = C[C.claim_field.str.startswith("stimulus_id") & C.evidence_grade.isin(["DIRECT", "LINKED"])]
    support = []
    for fam, g in C[(C.claim_field == "task_family") & C.evidence_grade.isin(["DIRECT", "LINKED"])].groupby("claim_value"):
        recs = sorted(set(g.record_id))
        cont = [r for r in recs if r in L.idx.index and L.idx.loc[r, "data_level"] == "continuous_or_discontinuous"]
        support.append({"task_family": fam, "records": len(recs), "continuous_records": len(cont),
                        "canonical_records": int(sum(r in L.canon.index for r in recs)),
                        "components": len({L.comp_of.get(r, r) for r in recs}),
                        "stimulus_pairs": sorted({" vs ".join(sorted(set(stim[stim.record_id == r].claim_value))) for r in recs
                                                  if (stim.record_id == r).any()})})
    roles_by_stim = defaultdict(set)
    for r in stim.itertuples():
        roles_by_stim[r.claim_value].add(normalise_role(r.claim_field.split("[")[1].rstrip("]")))
    cells_found = C[C.claim_field == "cell_definition"]
    ft = C[(C.claim_field == "free_text_vocab") & C.record_id.isin(unknown)]
    free_text_tokens = ft.groupby("claim_value").record_id.nunique().sort_values(ascending=False).head(40).to_dict()
    free_text_files = ft.groupby("evidence_file_id").record_id.nunique().to_dict()
    rule_records = sorted(set(C[(C.claim_field.str.startswith("stimulus_id")) & (C.evidence_file_id == "history.settings")
                                & (C.evidence_grade == "DIRECT")].record_id))
    E = pd.DataFrame(edges)
    lin = {}
    if len(E):
        er = E[E.derived.isin(rule_records)].copy()
        er["source_level"] = [L.idx.loc[x, "data_level"] if x in L.idx.index else "unknown" for x in er.source]
        lin = {"edges_from_rule_containers": int(len(er)),
               "by_source_level_and_verified": er.groupby(["source_level", "verified"]).size().rename("n").reset_index().to_dict("records"),
               "unique_basename_false": int((~er.unique_basename).sum()), "same_acq_false": int((~er.same_acquisition_id).sum())}
    return {"scope_containers": len(scope), "canonical_unknown": len(unknown), "lineage_edges": len(edges),
            "lineage_edges_verified": int(sum(e["verified"] for e in edges)),
            "lineage_edges_count_verified": int(sum(e.get("verification") == "category_counts_match_stm_cel_classes" for e in edges)),
            "unknown_canonical_task_family_by_value_and_grade": C[(C.claim_field == "task_family") & C.record_id.isin(unknown)]
                .groupby(["claim_value", "evidence_grade", "conflict_status"]).record_id.nunique().rename("records").reset_index()
                .to_dict("records"),
            "unknown_canonical_evidence": {"task_family": U.task.value_counts().to_dict(),
                                           "stimulus_id": U.stimulus.value_counts().to_dict(),
                                           "cell_definition": U.cell_definition.value_counts().to_dict(),
                                           "free_text_vocab": U.free_text.value_counts().to_dict(),
                                           "roles": U.roles.value_counts().to_dict()},
            "task_family_support_direct_or_linked": support,
            "role_reversal_candidates": {s: sorted(r) for s, r in roles_by_stim.items() if len(r - {"other"}) > 1},
            "unknown_canonical_free_text_tokens_records": free_text_tokens, "unknown_canonical_free_text_files": free_text_files,
            "rule_container_lineage": lin,
            "cell_definition_records": int(cells_found.record_id.nunique()),
            "events_parse_errors": int(sum(1 for s in scans.values() for e in s["events"].values() if "error" in e)),
            "claims": int(len(C)), "claims_by_grade": C.evidence_grade.value_counts().to_dict(),
            "conflicts": int((C.conflict_status == "CONFLICT").sum())}


# ---------------------------------------------------------------------- U3 non-canonical identity / age / exposure

def _linkage_helpers():
    spec_path = ROOT / "scripts/phase3_ci_linkage.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("phase3_ci_linkage", spec_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("phase3_ci_linkage", mod)
    spec.loader.exec_module(mod)
    return mod


def path_tokens(lk, path: str, subject: str = "") -> set:
    """phase3 ASCII source tokens plus the full pinyin of each Han-character run (paths may carry Chinese names)."""
    toks = set(lk.source_tokens({"path": path, "subject": subject, "identity_clue": ""}))
    for run_ in re.findall(r"[\u4e00-\u9fff]+", f"{path} {subject}"):
        for n in (2, 3, 4):
            for i in range(len(run_) - n + 1):
                tok = lk.pinyin_token(run_[i:i + n])[0]
                if tok:
                    toks.add(tok)
    return toks


def _months(dob, when) -> float | None:
    if dob is None or when is None:
        return None
    return (when.year - dob.year) * 12 + (when.month - dob.month) + (when.day - dob.day) / 30.4375


def cmd_recover_u3(args, config, run) -> dict:
    L = Ledgers(config)
    lk = _linkage_helpers()
    members = sorted({m for d in L.components.values() if not d["has_canonical"] for m in d["members"]})
    # clinical anchors with DOB: CI workbook candidate rows and BDF vendor identity records
    anchors = []
    for r in pd.read_csv(ROOT / cfg(config, "sources.ci_rows"), dtype=str).fillna("").itertuples():
        if r.row_status != "candidate_row" or not r.participant_id:
            continue
        tok = lk.pinyin_token(r.raw_name)[0]
        if tok:
            anchors.append({"anchor": f"ci:{r.participant_id}", "token": tok, "dob": lk.parse_date(r.raw_dob)})
    for v in json.loads((ROOT / "private/linkage_001/vendor_identity_records.json").read_text()):
        tok = lk.pinyin_token(v.get("PatientName", ""))[0] or lk.norm_text(v.get("namekey", ""))
        if tok:
            anchors.append({"anchor": f"bdf:{v.get('candidate_acquisition_id')}", "token": tok, "dob": lk.parse_date(v.get("BirthDate", ""))})
    # canonical side: which anchors are already linked to canonical MFF identity groups (accepted name links)
    canon_links = pd.read_csv(ROOT / "private/phase3_ci_linkage_005/linkage_candidates.csv", dtype=str).fillna("")
    canon_pids = set(canon_links[canon_links.accepted_name_link == "true"].participant_id)
    st = pd.read_csv(ROOT / "private/auditory_st" / cfg(config, "sources.st_scope_run") / "records.csv", dtype=str).fillna("")
    edges, rows = [], []
    for cid in members:
        r = L.reg[cid]
        toks = path_tokens(lk, r["path"], (r.get("subject_fields") or {}).get("Patient ID", ""))
        when = lk.parse_date(r.get("record_time", ""))
        hits = [a for a in anchors if a["token"] in toks]
        anchors_hit = sorted({a["anchor"] for a in hits})
        dobs = sorted({str(a["dob"]) for a in hits if a["dob"]})
        status = ("no_name_link" if not hits else ("name_link_conflict" if len({a["anchor"].split(":")[1] for a in hits
                                                                                 if a["anchor"].startswith("ci:")}) > 1 else "name_link"))
        existing = any(a["anchor"].startswith("ci:") and a["anchor"][3:] in canon_pids for a in hits)
        age = None
        if status == "name_link" and len(dobs) == 1 and when:
            age = _months(lk.parse_date(dobs[0]), when)
        for a in anchors_hit:
            edges.append({"entity_a": cid, "entity_b": a, "relation_type": "possible_identity_overlap",
                          "evidence_type": "exact_full_pinyin_path_token", "evidence_file_id": "registry.path",
                          "evidence_locator": "path tokens vs clinical name", "match_status": status,
                          "confidence_basis": "exact token, date not compared" if not when else "exact token",
                          "conflict_fields": "dob" if len(dobs) > 1 else "", "reviewed": False})
        rows.append({"container_id": cid, "component": L.comp_of.get(cid, ""),
                     "data_level": L.idx.loc[cid, "data_level"] if cid in L.idx.index else "unknown",
                     "subject_fields_empty": not any((r.get("subject_fields") or {}).values()),
                     "record_time_present": bool(r.get("record_time")), "name_link_status": status,
                     "n_anchors": len(anchors_hit), "anchors": "|".join(anchors_hit),
                     "links_existing_canonical_identity": bool(existing),
                     "dob_candidates": len(dobs), "age_months": age,
                     "age_source_status": ("dob_plus_record_time" if age is not None else
                                           ("dob_conflict" if len(dobs) > 1 else "no_dob_or_no_link"))})
    for cid in members:              # processing-version / acquisition relations inside the component
        for other in L.components[L.comp_of[cid]]["members"]:
            if other > cid:
                same_acq = L.reg[cid]["candidate_acquisition_id"] == L.reg[other]["candidate_acquisition_id"]
                edges.append({"entity_a": cid, "entity_b": other,
                              "relation_type": "same_acquisition" if same_acq else "same_container_version",
                              "evidence_type": "candidate_acquisition_id" if same_acq else "history_source_paths_component",
                              "evidence_file_id": "registry/history", "evidence_locator": "dv audit_c component",
                              "match_status": "component_member", "confidence_basis": "lineage, not identity",
                              "conflict_fields": "", "reviewed": False})
    M = pd.DataFrame(rows)
    # exposure: D1 export, GX2 SSL pool, D2 self-supervised rule candidates
    d1 = {p.stem for p in (ROOT / "private/auditory_d1" / cfg(config, "sources.d1_mff_run") / "arrays").glob("*.json")}
    with np.load(ROOT / "private/auditory_gx/GX2_ssl_mff/embeddings_MFF_s11.npz", allow_pickle=False) as z:
        gx2 = {str(c) for c in z["container_id"]}
    exp = []
    for cid in members:
        exp.append({"identity_group": "", "acquisition_id": L.reg[cid]["candidate_acquisition_id"], "container_id": cid,
                    "model_or_run": "D1_mff_001", "role_in_run": "continuous export",
                    "exposure_status": "pretraining_used" if cid in d1 else "not_found_in_checked_runs",
                    "evidence_ref": "private/auditory_d1/D1_mff_001/arrays"})
        exp.append({"identity_group": "", "acquisition_id": L.reg[cid]["candidate_acquisition_id"], "container_id": cid,
                    "model_or_run": "GX2_ssl_mff", "role_in_run": "self-supervised pretraining",
                    "exposure_status": "pretraining_used" if cid in gx2 else "not_found_in_checked_runs",
                    "evidence_ref": "private/auditory_gx/GX2_ssl_mff/embeddings_MFF_s11.npz"})
        exp.append({"identity_group": "", "acquisition_id": L.reg[cid]["candidate_acquisition_id"], "container_id": cid,
                    "model_or_run": "D2_ssl_check_001", "role_in_run": "self-supervised pretraining (pool not persisted)",
                    "exposure_status": "unknown" if cid in d1 else "not_found_in_checked_runs",
                    "evidence_ref": "auditory_d2/selfsup_probe.py:_pretraining_pool"})
    E = pd.DataFrame(exp)
    write_csv_atomic(M, run["private"] / "noncanonical_members.csv", private=True)
    write_csv_atomic(pd.DataFrame(edges), run["private"] / "identity_edges.csv", private=True)
    write_csv_atomic(M[["container_id", "age_months", "age_source_status", "dob_candidates"]], run["private"] / "age_provenance.csv", private=True)
    write_csv_atomic(E, run["private"] / "exposure_ledger.csv", private=True)
    gx_used = set(E[(E.model_or_run == "GX2_ssl_mff") & (E.exposure_status == "pretraining_used")].container_id)
    out = identity_counts(M, {c: L.reg[c]["candidate_acquisition_id"] for c in members}, gx_used)
    out.update({"components": int(sum(1 for d in L.components.values() if not d["has_canonical"])),
                "exposure": {**out["exposure"], "d1_exported": int(len(set(members) & d1))}})
    return out


def identity_counts(M: pd.DataFrame, acquisition_of: dict, pretrained: set) -> dict:
    """Section 7.5 counts, kept separate: containers, acquisitions, extra visits of known identities, net-new
    identities (DISTINCT anchors, never containers), those with an age, unresolved containers, exposure."""
    linked = M[M.name_link_status == "name_link"]
    net_new = linked[~linked.links_existing_canonical_identity]
    anchors_new = {a for s in net_new.anchors for a in str(s).split("|") if a}
    anchors_new_age = {a for s in net_new[net_new.age_months.notna()].anchors for a in str(s).split("|") if a}
    exposed = {a for s in net_new[net_new.container_id.isin(pretrained)].anchors for a in str(s).split("|") if a}
    return {"containers": int(len(M)),
            "continuous_containers": int((M.data_level == "continuous_or_discontinuous").sum()),
            "distinct_acquisition_ids": len({acquisition_of[c] for c in M.container_id}),
            "subject_fields_empty": int(M.subject_fields_empty.sum()),
            "name_link_status": M.name_link_status.value_counts().to_dict(),
            "containers_of_known_identities_extra_visits": int(linked.links_existing_canonical_identity.sum()),
            "net_new_identity_candidates": len(anchors_new),
            "net_new_identity_candidates_with_age": len(anchors_new_age),
            "unresolved_identity_containers": int((M.name_link_status != "name_link").sum()),
            "exposure": {"net_new_identities_with_pretraining_exposure": len(exposed),
                         "containers_in_gx2_ssl": int(M.container_id.isin(pretrained).sum())},
            "note": "candidates from exact name tokens only; unresolved containers are not new children"}


# ---------------------------------------------------------------------- U2 SET/FDT bridge

def cmd_recover_u2(args, config, run) -> dict:
    links = pd.read_csv(ROOT / "results/processed_link_001/processed_to_raw_candidates.csv", dtype=str).fillna("")
    sets = pd.read_csv(ROOT / "results/other_eeg_001/set_index.csv", dtype=str).fillna("")
    src = pd.read_csv(ROOT / "results/phase1_sources_001/source_manifest.csv", dtype=str).fillna("")
    by_event = {r.event_file_id: r for r in src.itertuples()}
    rows = []
    for r in links.itertuples():
        s = sets[sets.file_id == r.file_id]
        b = by_event.get(r.raw_event_file_id) if r.raw_event_file_id else None
        rows.append({"set_file_id": r.file_id, "data_level": r.data_level, "directory_group_clue": r.directory_group_clue,
                     "n_raw_candidates": r.n_raw_acquisition_candidates, "exact_sequence_match": r.exact_stimulus_code_sequence_match,
                     "subsequence_match": r.processed_code_sequence_is_raw_subsequence,
                     "bdf_recording_id": b.recording_id if b is not None else "", "bdf_participant_id": b.participant_id if b is not None else "",
                     "bdf_cohort_label": b.cohort_label if b is not None else "", "bdf_source_gate": b.source_gate if b is not None else "",
                     "set_sampling_rate_hz": s.sampling_rate_hz.iloc[0] if len(s) else "", "set_n_channels": s.n_channels.iloc[0] if len(s) else "",
                     "set_reference": s.reference.iloc[0] if len(s) else "", "set_n_epochs": s.n_epochs.iloc[0] if len(s) else "",
                     "bridge_status": ("same_acquisition_candidate" if b is not None and r.n_raw_acquisition_candidates == "1"
                                       else ("no_raw_candidate" if r.n_raw_acquisition_candidates in ("", "0") else "ambiguous"))})
    B = pd.DataFrame(rows)
    # groups without a raw candidate: exact full-pinyin name tokens of the file path vs the HA master workbook rows
    # (the only route to a net-new identity; a matched row WITHOUT a BDF recording would be new to the BDF cohort)
    lk = _linkage_helpers()
    with open(ROOT / cfg(config, "sources.file_path_map"), newline="", encoding="utf-8") as h:
        rel = {r["file_id"]: r["relative_path"] for r in csv.DictReader(h)}
    master = pd.read_csv(ROOT / cfg(config, "sources.ha_cohort"), dtype=str).fillna("")
    bdf_ids = set(src.recording_id)
    master_tok = [(lk.pinyin_token(m.name)[0], m.group, bool(m.recording and m.recording in bdf_ids)) for m in master.itertuples()]
    name_status = []
    for r in B.itertuples():
        if r.bridge_status == "same_acquisition_candidate":
            name_status.append("not_needed_linked")
            continue
        toks = path_tokens(lk, rel.get(r.set_file_id, ""))
        hits = [(g, has_bdf) for t, g, has_bdf in master_tok if t and t in toks]
        if not hits:
            name_status.append("no_name_link")
        elif len(hits) > 1:
            name_status.append("name_link_ambiguous")
        else:
            name_status.append(f"name_link_{hits[0][0]}_" + ("with_bdf_recording" if hits[0][1] else "without_bdf_recording"))
    B["name_link_status"] = name_status
    write_csv_atomic(B, run["private"] / "set_source_bridge.csv", private=True)
    linked = B[B.bridge_status == "same_acquisition_candidate"]
    return {"set_groups": int(len(B)), "by_level": B.data_level.value_counts().to_dict(),
            "bridge_status": B.bridge_status.value_counts().to_dict(),
            "linked_distinct_bdf_recordings": int(linked.bdf_recording_id.nunique()),
            "linked_distinct_bdf_participants": int(linked.bdf_participant_id.nunique()),
            "linked_by_bdf_cohort": linked.drop_duplicates("bdf_recording_id").bdf_cohort_label.value_counts().to_dict(),
            "linked_to_held_bdf": int((linked.drop_duplicates("bdf_recording_id").bdf_source_gate == "hold").sum()),
            "unlinked_groups_by_clue_and_level": B[B.bridge_status != "same_acquisition_candidate"].groupby(
                ["directory_group_clue", "data_level"]).size().rename("n").reset_index().to_dict("records"),
            "unlinked_name_link_status": B[B.bridge_status != "same_acquisition_candidate"].name_link_status.value_counts().to_dict(),
            "net_new_identity_candidates": int(B.name_link_status.str.endswith("without_bdf_recording").sum()),
            "epochs_in_linked_epoched_groups": int(pd.to_numeric(linked[linked.data_level == "epochs"].set_n_epochs, errors="coerce").fillna(0).sum())}


# ---------------------------------------------------------------------- U4 BDF clock candidates (metadata only)

def _edf_start(path: Path) -> dict:
    import pyedflib
    out = {}
    try:
        with pyedflib.EdfReader(str(path)) as f:
            dt = f.getStartdatetime()
            out["start"] = dt.isoformat()
            out["subsecond"] = float(getattr(f, "starttime_subsecond", 0) or 0) / 1e7 if hasattr(f, "starttime_subsecond") else None
            out["datarecord_duration_s"] = float(f.datarecord_duration) if hasattr(f, "datarecord_duration") else None
            out["file_duration_s"] = float(f.file_duration)
    except Exception as exc:   # noqa: BLE001  (reported, not hidden)
        out["error"] = type(exc).__name__
    return out


def cmd_recover_u4(args, config, run) -> dict:
    from datetime import datetime
    src = pd.read_csv(ROOT / "results/phase1_sources_001/source_manifest.csv", dtype=str).fillna("")
    with open(ROOT / cfg(config, "sources.file_path_map"), newline="", encoding="utf-8") as h:
        fmap = {r["file_id"]: r["absolute_path"] for r in csv.DictReader(h)}
    rows = []
    for r in src.itertuples():
        sig, evt = _edf_start(Path(fmap.get(r.signal_file_id, ""))), _edf_start(Path(fmap.get(r.event_file_id, "")))
        d = None
        if "start" in sig and "start" in evt:
            d = (datetime.fromisoformat(evt["start"]) - datetime.fromisoformat(sig["start"])).total_seconds()
            if sig.get("subsecond") is not None and evt.get("subsecond") is not None:
                d += evt["subsecond"] - sig["subsecond"]
        rows.append({"recording_id": r.recording_id, "source_gate": r.source_gate,
                     "manifest_offset_s": float(r.event_header_minus_signal_header_s or "nan"),
                     "header_offset_s": d, "signal_subsecond": sig.get("subsecond"), "event_subsecond": evt.get("subsecond"),
                     "signal_error": sig.get("error", ""), "event_error": evt.get("error", ""),
                     "event_datarecord_s": evt.get("datarecord_duration_s")})
    R = pd.DataFrame(rows)
    held = R[R.source_gate == "hold"].copy()

    def candidates(x):
        if x.header_offset_s is None or not np.isfinite(x.header_offset_s):
            return "UNRESOLVED:no_header_offset"
        sub_known = x.signal_subsecond is not None and x.event_subsecond is not None and (x.signal_subsecond or x.event_subsecond)
        if sub_known:
            return f"METADATA_DETERMINED:{x.header_offset_s:+.4f}"
        return f"UNRESOLVED:offset_in_({x.header_offset_s - 1:+.0f},{x.header_offset_s + 1:+.0f})_s_header_resolution_1s"
    held["candidate_set"] = held.apply(candidates, axis=1)
    write_csv_atomic(R, run["private"] / "bdf_header_times.csv", private=True)
    write_csv_atomic(held, run["private"] / "bdf_clock_candidates.csv", private=True)
    elig = R[R.source_gate != "hold"]
    return {"held": int(len(held)), "held_manifest_offsets": held.manifest_offset_s.value_counts().to_dict(),
            "held_header_offset_agrees_with_manifest": int((np.abs(held.header_offset_s.astype(float) - held.manifest_offset_s) < 1e-9).sum()),
            "subsecond_available_signal": int(R.signal_subsecond.notna().sum() and (R.signal_subsecond.fillna(0) != 0).sum()),
            "subsecond_available_event": int((R.event_subsecond.fillna(0) != 0).sum()),
            "eligible_header_offset_values": elig.header_offset_s.round(4).value_counts().to_dict(),
            "candidate_status": held.candidate_set.str.split(":").str[0].value_counts().to_dict(),
            "read_errors": int((R.signal_error != "").sum() + (R.event_error != "").sum()),
            "note": "no signal-based selection; acoustic delay unknown; recovered records are not new children"}


# ---------------------------------------------------------------------- dispatcher

def cmd_recover(args, config) -> dict:
    unit = args.unit.upper()
    fn = {"U1": cmd_recover_u1, "U2": cmd_recover_u2, "U3": cmd_recover_u3, "U4": cmd_recover_u4}.get(unit)
    if fn is None:
        raise ValueError(f"unknown unit {args.unit}")
    run = open_run(f"recover_{unit}", args.run, config, args=vars(args))
    out = fn(args, config, run)
    out["unit"] = unit
    write_json_atomic(run["public"] / f"summary_{unit.lower()}.json", out, private=False)
    close_run(config, f"recover_{unit}", args.run, "COMPLETED")
    return out
