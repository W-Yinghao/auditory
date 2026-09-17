"""Persist each attempted fit before execution; failures consume their budget."""
import json
import time


class FitLedger:
    def __init__(self,path,limits):
        self.path=path
        self.limits=dict(limits)
        self.counts={kind:{'attempts':0,'completed':0,'failed':0} for kind in limits}
        self.pending=set()
        self.world=None
        self.world_limits={}
        self.world_counts={}

    def begin_world(self,number,limits):
        if self.pending:raise ValueError('FIT_LEDGER_UNFINISHED_CALL')
        self.world=number
        self.world_limits=dict(limits)
        self.world_counts={kind:{'attempts':0,'completed':0,'failed':0} for kind in limits}

    def __call__(self,event,kind,name,details):
        key=(kind,name)
        if kind not in self.limits or self.world is None:raise ValueError('FIT_LEDGER_SCHEMA')
        if event=='start':
            if key in self.pending:raise ValueError('FIT_LEDGER_DUPLICATE_START')
            if self.counts[kind]['attempts']>=self.limits[kind] or self.world_counts[kind]['attempts']>=self.world_limits[kind]:
                raise RuntimeError('FROZEN_FIT_BUDGET_EXCEEDED')
            self.counts[kind]['attempts']+=1;self.world_counts[kind]['attempts']+=1
            self.pending.add(key)
        elif event in ('completed','failed'):
            if key not in self.pending:raise ValueError('FIT_LEDGER_NO_STARTED_CALL')
            self.counts[kind][event]+=1;self.world_counts[kind][event]+=1
            self.pending.remove(key)
        else:raise ValueError('FIT_LEDGER_EVENT')
        with self.path.open('a') as handle:
            handle.write(json.dumps(dict(world=self.world,event=event,kind=kind,name=name,
                time_unix=time.time(),details=details),allow_nan=False)+'\n')
            handle.flush()

    def complete_world(self):
        if self.pending or any(self.world_counts[k]['completed']!=v for k,v in self.world_limits.items()):
            raise ValueError('EXACT_WORLD_FIT_CATALOG_INCOMPLETE')

    def summary(self):
        return {kind:dict(counts) for kind,counts in self.counts.items()}
