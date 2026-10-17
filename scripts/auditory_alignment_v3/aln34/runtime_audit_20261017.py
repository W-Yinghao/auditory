"""Read-only runtime inventory for an operational ETA; run on a Slurm CPU node."""
import json
import os
from pathlib import Path
from collections import defaultdict
from statistics import mean, median
from datetime import datetime

assert os.environ.get('SLURM_JOB_ID')
from auditory_alignment_v3 import core
from private.auditory_alignment_v3.aln34.milestone_monitor_v9 import LANES

OUT = Path(core.OUT)
BASE = OUT / 'aln34'

def read(p):
    return json.loads(p.read_text())

def source(r):
    if 'spec' in r:
        return r
    for key in ('source', 'outer', 'row', 'inner'):
        v = r.get(key)
        if isinstance(v, dict):
            return source(v)
    return r

def seconds(rec):
    t = rec.get('total_seconds', rec.get('seconds'))
    return float(t) if isinstance(t, (int, float)) else None

def classify(r):
    s = source(r); spec = s.get('spec', {})
    return '|'.join(map(str, (s.get('dataset', r.get('dataset', '?')),
        spec.get('architecture', r.get('architecture', '?')),
        r.get('kind', spec.get('stage', '')),
        spec.get('axis', ''), spec.get('fraction', ''))))

def summary(v):
    return {'n': len(v), 'mean_s': round(mean(v), 1), 'median_s': round(median(v), 1),
            'min_s': round(min(v), 1), 'max_s': round(max(v), 1)} if v else {'n': 0}

def inventory(rows, unitdir):
    groups = defaultdict(lambda: {'total': 0, 'complete': 0, 'times': [], 'train': [], 'eval': []})
    examples = {}
    for r in rows:
        k = classify(r); g = groups[k]; g['total'] += 1
        eid = r.get('experiment_id', r.get('id')); p = unitdir / f'{eid}.json'
        if not p.exists():
            continue
        rec = read(p)
        if rec.get('status') != 'complete':
            continue
        g['complete'] += 1
        t = seconds(rec)
        if t is not None: g['times'].append(t)
        for name in ('train', 'eval'):
            v = rec.get(name + '_seconds')
            if isinstance(v, (int, float)): g[name].append(v)
        if k not in examples:
            examples[k] = {key: rec[key] for key in ('experiment_id','id','total_seconds','seconds',
                'train_seconds','eval_seconds','epochs_completed','optimizer_steps','steps_per_epoch','device') if key in rec}
            examples[k]['path'] = str(p)
    result = {}
    for k, g in groups.items():
        result[k] = {'total':g['total'], 'complete':g['complete'], 'remaining':g['total']-g['complete'],
                     **{name:summary(g[name]) for name in ('times','train','eval')}}
    return {'groups':result,'examples':examples}

result = {'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'], 'lanes':{}}
for lane in LANES:
    p = read(BASE/lane/'plan.json')
    inv = inventory(p['rows'], BASE/lane/'units')
    probes = []
    for path in (BASE/lane/'probes').glob('**/*.json'):
        try: r = read(path)
        except (ValueError,OSError): continue
        if isinstance(r,dict) and seconds(r) is not None:
            probes.append({'path':str(path),'seconds':seconds(r),'train_seconds':r.get('train_seconds'),
                'eval_seconds':r.get('eval_seconds'),'epochs':r.get('epochs_completed'),
                'class':classify(r.get('row',r.get('unit',r)))})
    inv['probes'] = probes
    result['lanes'][lane] = inv
    print(lane, json.dumps(inv['groups']), flush=True)

rows = core.load_rows()+[json.loads(x) for x in (OUT/'plan_ext.jsonl').read_text().splitlines()]
tf = [r for r in rows if r['family_id']=='ALN32_TRUE_FULL']
result['true_full'] = inventory(tf,OUT/'units')
prior = [r for r in rows if r['spec'].get('execution_contract')=='aln33_env64_125ms_v1']
result['prior'] = inventory(prior,OUT/'units')
for name in ('true_full','prior'):
    print(name,json.dumps(result[name]['groups']),flush=True)

# Historical same-method timings inform lanes without complete production yet.
ids = set()
for lane in LANES:
    plan = read(BASE/lane/'plan.json')
    for r in plan['rows']:
        s = source(r); spec=s.get('spec',{})
        if spec.get('baseline_id'): ids.add(spec['baseline_id'])
        if s.get('experiment_id') and (OUT/'units'/f"{s['experiment_id']}.json").exists(): ids.add(s['experiment_id'])
    ids.update(plan.get('baselines',{}))
base_rows = [r for r in rows if r['experiment_id'] in ids]
result['historical_sources'] = inventory(base_rows,OUT/'units')
print('historical_sources',json.dumps(result['historical_sources']['groups']),flush=True)
dest = BASE/'runtime_audit_20261017.json'
dest.write_text(json.dumps(result,indent=2)+'\n')
print('saved',str(dest),flush=True)
