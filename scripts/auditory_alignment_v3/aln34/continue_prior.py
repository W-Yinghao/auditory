"""Versioned donor continuations under the existing §2.10 rule; no gate changes.

Uses the frozen plan maker with an externally tracked exact-byte append guard.
The original 4,479-line deployed plan is the trust anchor. A write-ahead intent
makes an interruption after append recoverable without duplicate registration.
"""
import argparse
from datetime import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

from auditory_alignment_v3 import core
from auditory_alignment_v3.aln34 import learning_budget as B

OUT = Path(core.OUT); BASE = OUT/'aln34/prior_continuations'
ORIGINAL = {'lines': 4479, 'sha256': 'ed0b16da2ec2ad902a4b102520b8a8fea596d5f44c2db87792e7a88cccd295e8'}


def digest(raw): return hashlib.sha256(raw).hexdigest()
def read(p): return json.loads(p.read_text())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); args = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    BASE.mkdir(parents=True, exist_ok=True)
    with (BASE/'lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        statep = BASE/'state.json'; state = read(statep) if statep.exists() else dict(ORIGINAL)
        plan = OUT/'plan_ext.jsonl'; raw = plan.read_bytes()
        pending = BASE/'intent.json'
        if pending.exists():
            intent = read(pending)
            if digest(raw) == intent['after']['sha256']:
                # The exact planned bytes were appended before an interruption.
                state = intent['after']; B.write(statep, state)
                receipt = {**intent, 'reconciled_exact_bytes': True, 'time': datetime.now().astimezone().isoformat()}
                B.write(BASE/(intent['parent']+'.json'), receipt)
                pending.rename(BASE/(intent['parent']+'.intent.done.json'))
            elif digest(raw) != intent['before']['sha256']:
                raise ValueError('unrecognized live plan after an interrupted continuation')
        if len(raw.splitlines()) != state['lines'] or digest(raw) != state['sha256']:
            raise ValueError('plan changed outside the tracked continuation chain; review before rebasing')
        prefix = b''.join(raw.splitlines(keepends=True)[:ORIGINAL['lines']])
        assert digest(prefix) == ORIGINAL['sha256'], 'deployed original plan prefix changed'
        path = OUT/'make_plan_ext_prior33.py'
        spec = importlib.util.spec_from_file_location('prior33_frozen_maker', path)
        maker = importlib.util.module_from_spec(spec); spec.loader.exec_module(maker)
        ext = [json.loads(x) for x in raw.splitlines()]; rows = core.load_rows() + ext
        already = {r['spec'].get('continuation_of') for r in rows if r['family_id'] == maker.S.DONOR}
        eligible = []
        for r in rows:
            if r['family_id'] != maker.S.DONOR or r['experiment_id'] in already: continue
            p = OUT/'units'/f'{r["experiment_id"]}.json'
            if p.exists():
                rec = read(p)
                if rec.get('status') == 'complete' and not rec.get('truncated') and rec.get('ceiling_reached_while_improving') is True:
                    eligible.append(r['experiment_id'])
        print('Eligible uncontinued donors:', eligible, flush=True)
        for gid in eligible:
            argv = ['--continuation', gid, '--manifest-sha', 'b751976b9238590026f26a6fbe6c84177b69802ef9e55e687425af210b627426']
            guard = (state['lines'], state['sha256'])
            proposed = maker.main(argv, guard=guard)
            added = ''.join(json.dumps(r)+'\n' for r in proposed['rows']).encode()
            expected = {'lines': state['lines']+len(proposed['rows']), 'sha256': digest(raw+added)}
            if not args.apply: continue
            intent = {'parent': gid, 'before': state, 'after': expected, 'rows': proposed['rows'],
                      'job': os.environ['SLURM_JOB_ID'], 'maker_sha256': B.sha(path), 'operator_sha256': B.sha(__file__),
                      'time': datetime.now().astimezone().isoformat()}
            B.write(pending, intent)
            applied = maker.main(['--apply', *argv], guard=guard)
            raw = plan.read_bytes()
            assert digest(raw) == expected['sha256'] == applied['new_sha256'] and len(raw.splitlines()) == expected['lines']
            state = expected; B.write(statep, state)
            B.write(BASE/(gid+'.json'), {**intent, 'backup': applied['backup'], 'applied': True})
            pending.rename(BASE/(gid+'.intent.done.json'))
            with (OUT/'logs/operations.log').open('a') as log:
                log.write(f'{datetime.now().astimezone().isoformat()} prior continuation {gid}: {len(proposed["rows"])} new IDs; plan={state["sha256"]}; job={os.environ["SLURM_JOB_ID"]}\n')
        if args.apply and eligible:
            subprocess.run([sys.executable, '-B', str(OUT/'make_queue.py')], check=True)


if __name__ == '__main__': main()
