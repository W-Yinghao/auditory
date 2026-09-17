"""Slurm-only export of already computed v2.1 aggregate results; zero fits."""
import hashlib
import json
import os
from pathlib import Path
import shutil

if not os.environ.get('SLURM_JOB_ID'):
    raise RuntimeError('SLURM_REQUIRED')
os.umask(0o077)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path('/home/infres/yinwang/EEG_auditory')
RUN = os.environ.get('AUDITORY_V21_FIGURE_RUN', 'figures_001')
if not RUN.startswith('figures_') or not RUN.replace('_','').isalnum():
    raise ValueError('INVALID_RUN_NAME')
DEST = ROOT / 'reports/auditory_v21' / RUN
PRIVATE = ROOT / 'private/auditory_v21' / RUN
DEST.mkdir(mode=0o700)
PRIVATE.mkdir(mode=0o700)
shutil.copyfile(__file__, PRIVATE / 'source.py')
hashes = {}

def read_csv(relative):
    path = ROOT / relative
    hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path)

def save(fig, name):
    fig.savefig(DEST / (name + '.pdf'), bbox_inches='tight')
    fig.savefig(DEST / (name + '.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)

plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'pdf.fonttype': 42, 'savefig.facecolor': 'white'})

a2 = read_csv('results/auditory_v21/stage0_001/a2_secondary_comparisons.csv')
fig, ax = plt.subplots(figsize=(7, 3.2))
labels = []
for i, row in a2.iterrows():
    ax.plot([row['ci_lower'],row['ci_upper']], [i,i], color='#296b8a')
    ax.plot(row['estimate'],i,'o',color='#296b8a')
    labels.append(str(row['comparison']).replace('R_SUP_minus_R_', 'SUP minus ') + ' / ' + str(row['endpoint']))
ax.axvline(0, color='0.5', lw=1)
ax.set_yticks(range(len(labels)), labels)
ax.set_xlabel('Paired difference in frozen matching statistic (95% identity bootstrap CI)')
ax.set_title('A2: retrospective comparisons on the same 49 identities')
save(fig, 'a2_paired_comparisons')

n2 = read_csv('results/auditory_v21/n2_design_001/N2_METADATA_ABLATION_METRICS.csv')
fig, axes = plt.subplots(1, 2, figsize=(8, 3), sharey=True)
views = ['all_metadata', 'history', 'gap', 'position', 'block_span']
for ax, metric, label in zip(axes, ['bacc', 'ce_bits'], ['Balanced accuracy', 'Cross-entropy (bits/bag)']):
    frame = n2.loc[n2.metric.eq(metric)].set_index('view').loc[views]
    for i, (_, row) in enumerate(frame.iterrows()):
        ax.plot([row.ci_lower,row.ci_upper],[i,i],color='#8d5c23')
        ax.plot(row.estimate,i,'o',color='#8d5c23')
    ax.set_xlabel(label)
    ax.set_yticks(range(5), [v.replace('_', ' ') for v in views])
axes[0].axvline(.5, color='0.5', lw=1)
fig.suptitle('N2: metadata-only diagnostic on original bags (57 identities)')
save(fig, 'n2_metadata_diagnostic')

lanes = ['N1_R_SIM', 'N1_L0', 'N3_R_SIM', 'N3_L0']
fig, axes = plt.subplots(2, 2, figsize=(9, 7))
for lane, ax in zip(lanes, axes.flat):
    path = ROOT / 'results/auditory_v21' / ('real_' + lane + '_001') / 'route_decision.json'
    hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = json.loads(path.read_text())
    if receipt['status'] == 'REAL_COMPARISON_COMPLETE':
        frame = read_csv('results/auditory_v21/real_' + lane + '_001/paired_effects_v2_1.csv')
        for i, row in frame.iterrows():
            ax.plot([row.ci_lower,row.ci_upper],[i,i],color='#296b8a')
            ax.plot(row.estimate,i,'o',color='#296b8a')
        ax.set_yticks(range(len(frame)), [str(r['first'])+' minus '+str(r['second']) for _, r in frame.iterrows()])
        ax.axvline(0, color='0.5', lw=1)
        ax.set_xlabel('Risk gain (bits/trial), fixed-prediction 95% CI')
        ax.locator_params(axis='x',nbins=4)
    else:
        ax.text(.5, .5, 'Conditionally stopped\n' + receipt.get('reason', ''), ha='center', va='center', transform=ax.transAxes)
    ax.set_title(lane)
fig.tight_layout()
save(fig, 'new_real_risk_comparisons')

(DEST / 'FIGURE_NOTES.md').write_text(
    '# v2.1 aggregate figures\n\n'
    'These figures export saved aggregate statistics without refitting. A2 is a retrospective paired review on the same 49 identities; its units are not information bits. '
    'N2 shows the original homogeneous-bag task, with equal identity weighting; metadata accuracy is not EEG accuracy. '
    'Real risk differences use the new finite-budget learner, with fixed-prediction identity bootstrap intervals. '
    'A zero-width interval from identical selected predictions does not prove zero population conditional information. '
    'R_SIM remains primary; L0 remains secondary. No source result or failure is overwritten.\n')
receipt = {'status': 'FIGURES_COMPLETE', 'job_id': os.environ['SLURM_JOB_ID'],
           'new_head_fits': 0, 'input_hashes': hashes,
           'source_sha256': hashlib.sha256((PRIVATE/'source.py').read_bytes()).hexdigest()}
(PRIVATE/'completion.json').write_text(json.dumps(receipt, indent=2)+'\n')
(DEST/'figure_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt))
