"""Short actual optimization and information-boundary checks, Slurm only."""
import numpy as np
import pytest
import torch
from auditory5.contracts import FitScope
from auditory5.training import _batch_indices,fit_random,fit_simclr,fit_supervised,FittedEncoder


def toy():
    rng=np.random.default_rng(74);g=np.repeat(np.array(['a','b','c','d','e']),8)
    x=rng.normal(size=(len(g),2,25)).astype('float32');y=np.tile([0,1],20)
    x+=np.repeat(np.arange(5),8)[:,None,None]*3
    return x,y,g,g.copy(),np.tile(np.arange(8)*1.5,5)


def test_sampler_uniform_candidates_and_classes_with_unequal_counts():
    g=np.array(['a']*40+['b']*400);y=np.array([0]*30+[1]*10+[0]*80+[1]*320)
    batches,v=_batch_indices(g,y,batch_size=16,seed=3,class_balanced=True)
    draw=np.concatenate(batches)
    assert v==0 and all(len(b)==len(set(b)) for b in batches)
    assert .35<np.mean(g[draw]=='a')<.65
    for k in ['a','b']:assert .3<np.mean(y[draw][g[draw]==k])<.7
    again,_=_batch_indices(g,y,batch_size=16,seed=3,class_balanced=True)
    assert all(np.array_equal(a,b) for a,b in zip(batches,again))


def test_sampler_no_raw_overlap():
    x,y,g,r,t=toy();t=t*.1
    batches,v=_batch_indices(g,y,r,t,batch_size=12,seed=2,class_balanced=True)
    for b in batches:
        for i in b:
            for j in b:
                if i!=j and r[i]==r[j]:assert abs(t[i]-t[j])>=.7
    assert v==0


def test_heldout_eeg_is_rejected():
    x,y,g,r,t=toy();scope=FitScope(('a','b','c'),('d',),('e',))
    for mode in [fit_random,fit_simclr]:
        with pytest.raises(ValueError,match='LEAKAGE'):mode(x,g,scope)


def test_short_supervised_monitor_and_refit_scalers_checkpoint(tmp_path):
    x,y,g,r,t=toy();scope=FitScope(tuple(np.unique(g)))
    fit=fit_supervised(x,y,g,scope,record_ids=r,onset_seconds=t,max_epochs=2,batch_size=16,device='cpu')
    m=fit.metadata
    assert set(m['monitor_train_groups']).isdisjoint(m['monitor_validation_groups'])
    assert set(m['monitor_scaler_fit_groups'])==set(m['monitor_train_groups'])
    assert set(fit.scaler.fit_groups)==set(g)
    expected=np.mean([x[g==k].mean(axis=(0,2)) for k in np.unique(g)],axis=0)
    np.testing.assert_allclose(fit.scaler.center,expected,atol=1e-6)
    mask=np.isin(g,m['monitor_train_groups'])
    expected_monitor=np.mean([x[g==k].mean(axis=(0,2)) for k in np.unique(g[mask])],axis=0)
    np.testing.assert_allclose(m['monitor_scaler_center'],expected_monitor,atol=1e-6)
    assert m['history'][0]['learning_rate']==pytest.approx(.0002)
    assert 1<=m['selected_epochs']<=2
    path=tmp_path/'model.pt';fit.save(path);restored=FittedEncoder.load(path)
    np.testing.assert_array_equal(fit.transform(x),restored.transform(x))
    with pytest.raises(FileExistsError):fit.save(path)


def test_sim_short_training_labels_hidden_clip_before_step(monkeypatch,tmp_path):
    x,y,g,r,t=toy();scope=FitScope(tuple(np.unique(g)))
    steps=[];original=torch.optim.AdamW.step
    def checked(opt,*a,**kw):
        norms=[p.grad.detach().norm()**2 for group in opt.param_groups for p in group['params'] if p.grad is not None]
        norm=float(torch.sqrt(torch.stack(norms).sum()));assert norm<=5.0001;steps.append(norm)
        return original(opt,*a,**kw)
    monkeypatch.setattr(torch.optim.AdamW,'step',checked)
    with pytest.raises(TypeError):fit_simclr(x,g,scope,y=y)
    fit=fit_simclr(x,g,scope,record_ids=r,onset_seconds=t,epochs=2,batch_size=16,device='cpu')
    assert len(steps)==6 and len(fit.metadata['history'])==2
    assert fit.metadata['history'][0]['learning_rate']==pytest.approx(.00006)
    p=tmp_path/'sim.pt';fit.save(p);restored=FittedEncoder.load(p)
    np.testing.assert_array_equal(fit.transform(x),restored.transform(x))
    assert fit.metadata['encoder_effective_rank']>0


def test_random_fixed_seed_and_sup_missing_class():
    x,y,g,r,t=toy();scope=FitScope(tuple(np.unique(g)))
    a=fit_random(x,g,scope,device='cpu');b=fit_random(x,g,scope,device='cpu')
    np.testing.assert_array_equal(a.transform(x),b.transform(x))
    y[g=='a']=0
    with pytest.raises(ValueError,match='both classes'):fit_supervised(x,y,g,scope)
