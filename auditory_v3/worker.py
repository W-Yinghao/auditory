import json
from pathlib import Path
import sys
import traceback
from .runtime import ROOT,require_slurm,write_json,finish

def main():
    require_slurm();private,public,report=map(Path,sys.argv[1:])
    args=json.loads((private/'args.json').read_text());config=json.loads((private/'config.json').read_text())
    try:
        command=args['command']
        if command=='inspect':
            from .registry import inspect
            result=inspect(ROOT,private,public,report,config,args)
        elif command=='freeze-support':
            from .splits import freeze_support
            result=freeze_support(ROOT,private,public,report,config,args)
        elif command=='make-plan':
            from .planning import make_plan
            result=make_plan(ROOT,private,public,report,config,args)
        elif command=='test':
            from .test_runner import run_tests
            result=run_tests(ROOT,private,public,report,config,args)
        elif command=='test-scoring':
            from .r3_scoring import tests
            result=tests(ROOT,private,public,report,config,args)
        elif command=='repair-selection':
            from .r3_scoring import repair_selection
            result=repair_selection(ROOT,private,public,report,config,args)
        elif command=='capability' and args['packet']=='P0':
            from .gates import require_tests
            from .data import load_support
            from .runtime import Ledger
            from .p0_capability import run_p0_capability
            require_tests(ROOT,private,args['gate_run'],'P0')
            *_,support=load_support(ROOT,args['split_run'])
            if support['P0_support']!='SUFFICIENT':raise ValueError('P0_SUPPORT_LIMITED')
            output=run_p0_capability(ledger=Ledger(private))
            output['world_results'].to_csv(public/'world_results.csv',index=False)
            output['fit_diagnostics'].to_pickle(private/'fit_diagnostics.pkl')
            result=dict(output['receipt'],test_run=args['gate_run'],split_run=args['split_run'])
            write_json(public/'capability_receipt.json',result)
        elif command=='run-pca':
            import pickle
            import pandas as pd
            from .gates import require_capability
            from .data import load_support,feature_loader
            from .runtime import Ledger
            from .pca_packet import run_pca
            gate=require_capability(ROOT,private,args['gate_run'],'P0',args['split_run'])
            members,splits,history,registry,support=load_support(ROOT,args['split_run'])
            if support['P0_support']!='SUFFICIENT':raise ValueError('P0_SUPPORT_LIMITED')
            output=run_pca(members,feature_loader(members,registry),capability_receipt=gate,ledger=Ledger(private))
            for name in ('predictions','identity_risks'):output[name].to_parquet(private/(name+'.parquet'),index=False)
            for name in ('fit_diagnostics','transforms','models'):
                if name in output:
                    with (private/(name+'.pkl')).open('wb') as f:pickle.dump(output[name],f)
            result=dict(output['summary'],status='P0_RECORDED',capability_run=args['gate_run'],split_run=args['split_run'])
            pd.DataFrame([dict(model=k,**v) for k,v in result['metrics'].items()]).to_csv(public/'P0_metrics.csv',index=False)
            pd.DataFrame([dict(contrast=k,**v) for k,v in result['contrasts'].items()]).to_csv(public/'P0_paired_effects.csv',index=False)
        elif command=='develop-n2r' or command=='capability' and args['packet']=='N2R':
            from .gates import require_tests
            from .data import load_support
            from .runtime import Ledger,safe_run
            from .n2r_capability import run_worlds
            require_tests(ROOT,private,args['gate_run'],'N2R')
            members,splits,history,registry,support=load_support(ROOT,args['split_run'])
            if support['N2R_support']!='SUFFICIENT':raise ValueError('N2R_SUPPORT_LIMITED')
            development=command=='develop-n2r';receipt=None
            if not development:
                folder=ROOT/'private/auditory_v3'/safe_run(args['development_run'])
                receipt=json.loads((folder/'completion.json').read_text())
                if receipt['split_run']!=args['split_run'] or receipt['test_run']!=args['gate_run']:raise ValueError('DEVELOPMENT_SCOPE_MISMATCH')
            table,result=run_worlds(members,history,splits,private,Ledger(private),development=development,development_receipt=receipt)
            table.to_csv(public/'world_results.csv',index=False)
            result.update(test_run=args['gate_run'],split_run=args['split_run'],development_run=args.get('development_run'))
            write_json(public/'capability_receipt.json',result)
        elif command=='run-bags':
            import pickle
            import pandas as pd
            from .gates import require_capability
            from .data import load_support,load_epochs,l0
            from .runtime import Ledger
            from .n2r_execution import run_packet
            require_capability(ROOT,private,args['gate_run'],'N2R',args['split_run'])
            members,splits,history,registry,support=load_support(ROOT,args['split_run'])
            if support['N2R_support']!='SUFFICIENT':raise ValueError('N2R_SUPPORT_LIMITED')
            post,pre=l0(*load_epochs(members,registry))
            output=run_packet(members,post,pre,history,splits,ledger=Ledger(private))
            for name in ('predictions','identity_risks'):output[name].to_parquet(private/(name+'.parquet'),index=False)
            for name in ('models','transforms','fit_diagnostics','selections'):
                with (private/(name+'.pkl')).open('wb') as f:pickle.dump(output[name],f)
            result=dict(output['summary'],status='N2R_RECORDED',capability_run=args['gate_run'],split_run=args['split_run'])
            pd.DataFrame([dict(model=k,**v) for k,v in result['metrics'].items()]).to_csv(public/'N2R_metrics.csv',index=False)
            pd.DataFrame([dict(contrast=k,**v) for k,v in result['contrasts'].items()]).to_csv(public/'N2R_paired_effects.csv',index=False)
        elif command in ('prepare-exposures','join-r3-capability','train-representation') or command=='capability' and args['packet']=='R3':
            from .r3_training import run
            result=run(ROOT,private,public,report,config,args)
        elif command in ('select-probes','evaluate-representations'):
            if args.get('stable_scoring'):
                from .r3_scoring import require_scoring_test
                require_scoring_test(ROOT,private,args['scoring_test_run'])
            from .r3_execution import probe_packet
            result=probe_packet(ROOT,private,public,report,config,args)
            if args.get('stable_scoring'):
                from .r3_scoring import repair_final
                result=repair_final(ROOT,private,public,report,config,args,result)
        elif command=='finalize':
            from .reporting import finalize
            result=finalize(ROOT,private,public,report,config,args)
        else:raise NotImplementedError('ENTRYPOINT_IMPLEMENTATION_NOT_READY')
        finish(private,public,result)
        if command in ('test','test-scoring') and result['status']!='PASS':raise SystemExit(1)
    except Exception as exc:
        (private/'traceback.txt').write_text(traceback.format_exc())
        write_json(private/'failure.json',dict(status='FAILED',type=type(exc).__name__,message=str(exc)))
        write_json(public/'failure.json',dict(status='FAILED',type=type(exc).__name__,details='private'))
        print(json.dumps(dict(status='FAILED',type=type(exc).__name__,details='private')))
        raise SystemExit(1)
if __name__=='__main__':main()
