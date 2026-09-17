"""All numerical entry points are Slurm-only and refuse existing run folders."""
import argparse
import traceback
import json
import os
import sys
from pathlib import Path
from .provenance import ROOT, digest, config_load, create_run, write_json, require_slurm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/auditory_next_v2.yaml')
    parser.add_argument('command', choices=['preflight', 'freeze-support', 'test-contracts', 'diagnostics','refine-metadata','run-packet','make-plan','smoke-packet','integration','finalize-a2','postflight','metrics','resources','report','progress','check-module','audit-public','fit-accounting'])
    parser.add_argument('--run', required=True)
    parser.add_argument('--source-run')
    parser.add_argument('--packet',choices=['G0','A2','A2_RESIDUAL','N1','N2','N3','C2_R','C2_S','E0_R','SYNTHETIC'])
    parser.add_argument('--plan')
    parser.add_argument('--support-run')
    parser.add_argument('--tests-run')
    args = parser.parse_args()
    require_slurm()
    config, registry, site = config_load(args.config)
    existing=os.environ.get('AUDITORY_NEXT_SNAPSHOT_RUN')
    if existing:
        if existing!=args.run: raise ValueError('SNAPSHOT_RUN_MISMATCH')
        dest=ROOT/'private/auditory_next_v2'/args.run
        public=ROOT/'results/auditory_next_v2'/args.run
        report=ROOT/'reports/auditory_next_v2'/args.run
        source=dest/'source'
        start=json.loads((dest/'start.json').read_text())
        if Path(__file__).resolve()!=source/'auditory_next/cli.py': raise ValueError('SNAPSHOT_EXECUTION_REQUIRED')
        for rel,h in start['source_hashes'].items():
            if digest(source/rel)!=h: raise ValueError('SNAPSHOT_MUTATION')
        if digest(ROOT/args.config)!=start['config_hash']: raise ValueError('CONFIG_CHANGED_AFTER_SUBMISSION')
    else:
        dest, public, report = create_run(args.run, args.config)
        env=os.environ.copy();env['AUDITORY_NEXT_SNAPSHOT_RUN']=args.run
        env['PYTHONPATH']=str(dest/'source')
        os.chdir(dest/'source')
        os.execve(sys.executable,[sys.executable,'-m','auditory_next.cli',*sys.argv[1:]],env)
    try:
        if args.command == 'fit-accounting':
            from .fit_accounting import run
            run(config,registry,site,dest,public,report)
        elif args.command == 'audit-public':
            from .public_audit import run
            run(config,registry,site,dest,public,report,args.source_run)
        elif args.command == 'check-module':
            from .verification import run_module
            run_module(config,registry,site,dest,public,report,args.source_run)
        elif args.command == 'progress':
            from .progress import run
            run(config,registry,site,dest,public,report)
        elif args.command == 'finalize-a2':
            from .a2_residual_finalize import run
            run(config,registry,site,dest,public,report,source_run=args.source_run or 'A2_residual_001')
        elif args.command == 'postflight':
            from .postflight import run
            run(config,registry,site,dest,public,report,args.source_run)
        elif args.command == 'metrics':
            from .metrics_supplement import run
            run(config,registry,site,dest,public,report)
        elif args.command == 'resources':
            from .resource_accounting import run
            run(config,registry,site,dest,public,report,json.loads((ROOT/args.plan).read_text()) if args.plan else None)
        elif args.command == 'report':
            from .reporting import run
            run(config,registry,site,dest,public,report)
        elif args.command == 'preflight':
            from .preflight import run
            run(config, registry, site, dest, public, report)
        elif args.command == 'freeze-support':
            from .support import run
            run(config, registry, site, dest, public, report, args.source_run)
        elif args.command == 'test-contracts':
            from .verification import run
            run(config, registry, site, dest, public, report, args.source_run)
        elif args.command == 'diagnostics':
            from .diagnostics import run
            run(config, registry, site, dest, public, report, args.source_run)
        elif args.command == 'refine-metadata':
            from .metadata_refinement import run
            run(config,registry,site,dest,public,report,args.source_run)
        elif args.command in ('run-packet','smoke-packet','integration'):
            if not args.plan:raise ValueError('FROZEN_TASK_PLAN_REQUIRED')
            task_plan=json.loads((ROOT/args.plan).read_text())
            smoke=args.command=='smoke-packet'
            from .gates import check
            check(task_plan,'INTEGRATION' if args.command=='integration' else args.packet,real=not smoke)
            if args.command=='integration':
                from .integration import run
                run(config,registry,site,dest,public,report,task_plan)
            elif args.packet=='A2':
                from .a2_execution import run
                run(config,registry,site,dest,public,report,task_plan['support_run'])
            elif args.packet=='A2_RESIDUAL':
                from .a2_residual_execution import run
                run(config,registry,site,dest,public,report,task_plan,smoke=smoke)
            elif args.packet in ('C2_R','E0_R'):
                from .repair import run
                run(config,registry,site,dest,public,report,args.packet,source_run=task_plan['preflight_run'],contract_run=task_plan['contract_run'],smoke=smoke)
            elif args.packet in ('N1','N3'):
                from .context_execution import run
                run(config,registry,site,dest,public,report,args.packet,task_plan,smoke=smoke)
            elif args.packet=='N2':
                from .n2_execution import run
                run(config,registry,site,dest,public,report,task_plan,smoke=smoke)
            elif args.packet=='C2_S':
                from .spatial_execution import run
                run(config,registry,site,dest,public,report,task_plan,smoke=smoke)
            elif args.packet=='G0':
                from .g0_execution import run
                run(config,registry,site,dest,public,report,task_plan,smoke=smoke)
            elif args.packet=='SYNTHETIC':
                from .synthetic_execution import run
                run(config,registry,site,dest,public,report,task_plan,smoke=smoke)
            else:
                raise ValueError('PACKET_DISPATCHER_NOT_YET_IMPLEMENTED')
        elif args.command=='make-plan':
            from .planning import run
            run(config,registry,site,dest,public,report,args.support_run,args.tests_run)
    except BaseException:
        write_json(dest / 'failure.json', dict(status='FAILED', command=args.command, traceback=traceback.format_exc()))
        raise


if __name__ == '__main__':
    main()
