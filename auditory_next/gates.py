"""Require tested code and a fixed, internally consistent task catalog."""
import json
from pathlib import Path
from .provenance import ROOT,digest


PACKET_MODULES={
    'A2':['a2_execution','a2_overlap','a2_residual_audit'],
    'A2_RESIDUAL':['a2_residual_execution','a2_execution','a2_overlap','a2_residual_audit'],
    'N1':['context_execution','context_inputs','n1_controls','n3_summary','features','history','fitting','readouts'],
    'N3':['context_execution','context_inputs','n1_controls','n3_summary','features','history','fitting','readouts'],
    'N2':['n2_execution','n2_bags','n2_features','features','fitting','readouts'],
    'C2_R':['repair','readouts'], 'E0_R':['repair','readouts'],
    'C2_S':['spatial_execution','c2_spatial'],
    'G0':['g0_execution','features','fitting','readouts','context_execution'],
    'INTEGRATION':['integration','features','context_inputs','fitting','readouts','context_execution'],
    'SYNTHETIC':['synthetic_execution','synthetic_worlds','fitting','readouts','a2_residual_audit'],
}


def check(task_plan,packet,*,real=False):
    root=ROOT/'private/auditory_next_v2'
    tested=root/task_plan['contract_run']
    if json.loads((tested/'completion.json').read_text())['status']!='PASS':raise ValueError('CONTRACT_TEST_GATE')
    task_csv=Path(task_plan['task_csv'])
    if not task_csv.resolve().is_relative_to(root) or digest(task_csv)!=task_plan['task_csv_hash']:
        raise ValueError('FROZEN_TASK_CATALOG_GATE')
    source=Path(__file__).resolve().parent
    for module in PACKET_MODULES[packet]:
        old=tested/'source/auditory_next'/(module+'.py')
        if not old.exists() or digest(source/(module+'.py'))!=digest(old):
            raise ValueError('CODE_MATCHED_CONTRACT_GATE:'+module)
    if real and packet not in ('INTEGRATION','SYNTHETIC'):
        done=root/'integration_001/completion.json'
        if not done.exists() or json.loads(done.read_text())['status']!='PASS':
            raise ValueError('REAL_INTEGRATION_GATE')
