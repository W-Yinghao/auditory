"""Render ALN3.6 summary.json / ALN4.1 contrasts.json families as Markdown tables (no computation, CPU only).

usage: python render_family_tables.py <summary-or-contrasts.json> <out.md>
"""
import json
import sys


def fmt(x, nd=5):
    return 'NA' if x is None else f'{x:+.{nd}f}'


def interval(iv, nd=5):
    return 'not issued' if not iv else f'[{iv[0]:+.{nd}f}, {iv[1]:+.{nd}f}]'


def main(src, out):
    d = json.load(open(src))
    lines = []
    for f in d['families']:
        lines.append(f"### {f['family_id']} ({f.get('unit', '')})\n")
        cov = f.get('coverage')
        if cov:
            lines.append('Coverage: ' + '; '.join(f"{g} {c['complete_n']}/{c['expected_n']}" for g, c in cov.items()))
        else:
            lines.append(f"Coverage: {f.get('complete_n')}/{f.get('expected_n')}")
        crit = f.get('critical'); ref = f.get('secondary_reference_fixed_se_max_z') or {}
        lines.append(f"Status {f['status']}; bootstrap-t critical {crit if crit is None else round(crit, 3)}"
                     + (f"; fixed-SE max-|z| reference critical {round(ref['critical'], 3)}" if ref.get('critical') else '') + '\n')
        has_ref = bool(ref.get('intervals'))
        lines.append('| member | n | estimate | simultaneous 95% (bootstrap-t) |' + (' fixed-SE reference 95% |' if has_ref else ''))
        lines.append('|---|---:|---:|---|' + ('---|' if has_ref else ''))
        for m in f['members']:
            row = f"| {m['name']} | {m['n']} | {fmt(m.get('estimate'))} | {interval(m.get('simultaneous_95'))} |"
            if has_ref:
                row += f" {interval(ref['intervals'].get(m['name']))} |"
            lines.append(row)
        lines.append('')
    open(out, 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main(*sys.argv[1:3])
