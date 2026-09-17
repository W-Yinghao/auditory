"""Explicit weighted objectives and a bounded full-batch Adam repair solver.

Legacy alpha penalizes W by alpha/(2*sum(weights)); new lambda penalizes W
by lambda/2. Biases are never penalized. These objectives must not be mixed.
Family extension decisions belong to the caller, before any test evaluation.
"""
from dataclasses import dataclass
import math
import hashlib
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import expit, logsumexp
import torch
from torch import nn


def population_weights(y, groups, population):
    y, groups = np.asarray(y), np.asarray(groups, str)
    if y.ndim != 1 or groups.shape != y.shape or not len(y) or not np.isin(y, [0, 1]).all():
        raise ValueError('BINARY_WEIGHT_SCHEMA')
    if population not in ('P_nat','P_bal'):
        raise ValueError('UNKNOWN_POPULATION')
    w = np.empty(len(y), float)
    for group in np.unique(groups):
        own = groups == group
        if population == 'P_nat':
            w[own] = 1 / own.sum()
        else:
            if set(y[own]) != {0,1}: raise ValueError('MISSING_CANDIDATE_CLASS')
            for label in (0,1):
                select = own & (y == label)
                w[select] = 1 / (2 * select.sum())
    return w


def ce_bits(logits, y, weights):
    logits, y, weights = np.asarray(logits, float), np.asarray(y), np.asarray(weights, float)
    if (logits.ndim!=1 or logits.shape != y.shape or weights.shape != y.shape or not np.isfinite(logits).all()
            or not np.isin(y,[0,1]).all() or not np.isfinite(weights).all() or np.any(weights<0) or weights.sum() <= 0):
        raise ValueError('LOGIT_LOSS_SCHEMA')
    return float(np.dot(weights, np.logaddexp(0., logits) - y*logits) / weights.sum() / np.log(2.))


def calibrate(logits, y, weights, bounds=(.25,16.),training_prior=None):
    # Inputs must already be scope-certified OOF predictions; never features
    # stacked across different encoder coordinate systems.
    result = minimize_scalar(lambda lt: ce_bits(np.asarray(logits)/np.exp(lt), y, weights),
                             bounds=tuple(np.log(bounds)), method='bounded', options={'xatol':1e-10})
    if not result.success: raise ValueError('CALIBRATION_NUMERICAL_FAILURE')
    t = float(np.exp(result.x))
    prior = float(np.average(y, weights=weights)) if training_prior is None else float(training_prior)
    if not 0 < prior < 1: raise ValueError('CALIBRATION_PRIOR_SUPPORT')
    probabilities = expit(np.asarray(logits)/t)
    choices = []
    for eta in (0., .25, .5, .75, 1.):
        # Stable log-space mixture, including eta=0 and saturated scores.
        z = np.asarray(logits)/t
        l0, l1 = -np.logaddexp(0., z), -np.logaddexp(0., -z)
        if eta > 0:
            l0 = np.logaddexp(l0 + (math.log1p(-eta) if eta < 1 else -np.inf), math.log(eta*(1-prior)))
            l1 = np.logaddexp(l1 + (math.log1p(-eta) if eta < 1 else -np.inf), math.log(eta*prior))
        choices.append((ce_bits(l1-l0, y, weights), eta))
    return dict(temperature=t, eta=min(choices)[1], training_prior=prior, status='TRAINING_OOF_ONLY')


class BinaryMLP(nn.Module):
    def __init__(self, features, width=32, seed=11):
        super().__init__()
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(seed)
            self.first = nn.Linear(features, width, dtype=torch.float64)
            self.last = nn.Linear(width, 1, dtype=torch.float64)

    def forward(self, x):
        return self.last(torch.relu(self.first(x))).flatten()


def objective(model, x, y, weights, *, alpha=None, lam=None):
    if (alpha is None) == (lam is None): raise ValueError('ONE_REGULARIZATION_SEMANTIC_REQUIRED')
    logits = model(x)
    bce = ((torch.nn.functional.softplus(logits) - y*logits)*weights).sum()/weights.sum()
    coefficient = alpha / weights.sum() if alpha is not None else lam
    penalty = coefficient * (model.first.weight.square().sum() + model.last.weight.square().sum()) / 2
    return bce + penalty, bce, penalty


@dataclass
class AdamState:
    model: object
    optimizer: object
    history: list
    steps: int
    alpha: float | None
    lam: float | None
    initial_objective: float
    fit_input_hash: str
    fit_scope_hash: str
    final_objective: float | None = None


def _fit_input_hash(x,y,weights):
    x,y,w=[np.asarray(a,dtype=np.float64) for a in (x,y,weights)]
    if x.ndim!=2 or min(x.shape)<1 or y.shape!=(len(x),) or w.shape!=y.shape:
        raise ValueError('FIT_SHAPE')
    if not all(np.isfinite(a).all() for a in (x,y,w)) or not np.isin(y,[0,1]).all() or not (w>0).all():
        raise ValueError('FIT_NONFINITE_OR_LABEL_WEIGHT')
    h=hashlib.sha256()
    for a in (x,y,w): h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()


def start_fit(x, y, weights, *, width=32, alpha=None, lam=None, seed=11, device='cpu',fit_scope_hash='synthetic_only'):
    if (alpha is None) == (lam is None): raise ValueError('ONE_REGULARIZATION_SEMANTIC_REQUIRED')
    input_hash=_fit_input_hash(x,y,weights)
    model = BinaryMLP(np.shape(x)[1], width, seed).to(device)
    tensors = tuple(torch.as_tensor(a, dtype=torch.float64, device=device) for a in (x,y,weights))
    if not all(torch.isfinite(a).all() for a in tensors) or not (tensors[2] > 0).all():
        raise ValueError('FIT_NONFINITE_OR_NONPOSITIVE_WEIGHT')
    optimizer = torch.optim.Adam(model.parameters(), lr=.001, weight_decay=0.)
    initial = float(objective(model, *tensors, alpha=alpha, lam=lam)[0].detach())
    return AdamState(model, optimizer, [], 0, alpha, lam, initial,input_hash,fit_scope_hash)


def advance_fit(state, x, y, weights, *, target_steps=1000, microbatch=8192,fit_scope_hash='synthetic_only'):
    if (state.steps,target_steps) not in ((0,1000),(1000,2000)):
        raise ValueError('ONLY_ONE_PRESPECIFIED_EXTENSION')
    if _fit_input_hash(x,y,weights)!=state.fit_input_hash or fit_scope_hash!=state.fit_scope_hash:
        raise ValueError('FIT_DATA_OR_SCOPE_CHANGED_ON_EXTENSION')
    if not isinstance(microbatch,int) or microbatch<1: raise ValueError('MICROBATCH_SIZE')
    device = next(state.model.parameters()).device
    x,y,w = [torch.as_tensor(a,dtype=torch.float64,device=device) for a in (x,y,weights)]
    sw = w.sum()
    for step in range(state.steps, target_steps):
        lr = .001 * .5 * (1 + math.cos(math.pi*step/2000))
        for group in state.optimizer.param_groups: group['lr'] = lr
        state.optimizer.zero_grad(set_to_none=True)
        loss_value = 0.
        for first in range(0,len(y),microbatch):
            z = state.model(x[first:first+microbatch]); yi=y[first:first+microbatch]; wi=w[first:first+microbatch]
            # Normalize by the FULL fit's weight sum, not each microbatch.
            loss = ((torch.nn.functional.softplus(z)-yi*z)*wi).sum()/sw
            loss.backward(); loss_value += float(loss.detach())
        coefficient = state.alpha/sw if state.alpha is not None else state.lam
        penalty = coefficient*(state.model.first.weight.square().sum()+state.model.last.weight.square().sum())/2
        penalty.backward(); loss_value += float(penalty.detach())
        grad = torch.nn.utils.clip_grad_norm_(state.model.parameters(),5.,error_if_nonfinite=True)
        norm = torch.sqrt(sum(p.square().sum() for p in state.model.parameters()))
        if not np.isfinite(loss_value) or not torch.isfinite(norm): raise ValueError('OPTIMIZATION_NONFINITE')
        state.history.append(dict(step=step, objective=loss_value, gradient_norm_unclipped=float(grad), parameter_norm=float(norm.detach()), learning_rate=lr))
        state.optimizer.step()
    state.steps = target_steps
    with torch.no_grad():
        final=objective(state.model,x,y,w,alpha=state.alpha,lam=state.lam)[0]
        if not torch.isfinite(final) or any(not torch.isfinite(p).all() for p in state.model.parameters()):
            raise ValueError('FINAL_OPTIMIZATION_NONFINITE')
        state.final_objective=float(final)
    return stability(state)


def stability(state):
    values = np.array([r['objective'] for r in state.history])
    final=state.final_objective
    tail=np.r_[values[-99:],final] if final is not None else values[-100:]
    change = None if len(values) < 100 else float(np.ptp(tail)/max(abs(tail[0]),1e-12))
    stable = (change is not None and change <= 1e-4 and np.isfinite(values).all()
              and final is not None and final <= state.initial_objective
              and max(r['parameter_norm'] for r in state.history) < 1e6)
    return dict(status='OPTIMIZATION_STABLE' if stable else 'OPTIMIZATION_UNRESOLVED',
                steps=state.steps, initial_objective=state.initial_objective,
                final_objective=final, last100_relative_change=change,
                global_optimum_claim=False)


def objective_parity():
    """Check installed sklearn's actual _backprop at identical parameters."""
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import LabelBinarizer
    rng=np.random.default_rng(11); x=rng.normal(size=(17,5)); y=np.arange(17)%2
    w=np.linspace(.05,.35,17); alpha=.3
    head=MLPClassifier(hidden_layer_sizes=(4,),activation='relu',alpha=alpha,random_state=11)
    head._label_binarizer=LabelBinarizer().fit([0,1]); head._random_state=np.random.RandomState(11)
    head._initialize(y[:,None],[5,4,1],np.dtype('float64'))
    model=BinaryMLP(5,4)
    with torch.no_grad():
        for layer,coef,bias in zip((model.first,model.last),head.coefs_,head.intercepts_):
            layer.weight.copy_(torch.as_tensor(coef.T)); layer.bias.copy_(torch.as_tensor(bias))
    acts=[x,np.empty((17,4)),np.empty((17,1))]
    loss,cg,bg=head._backprop(x,y[:,None],w,acts,[np.empty((17,4)),np.empty((17,1))],
                            [np.empty_like(a) for a in head.coefs_],[np.empty_like(a) for a in head.intercepts_])
    tensors=[torch.as_tensor(a,dtype=torch.float64) for a in (x,y,w)]
    total,bce,penalty=objective(model,*tensors,alpha=alpha); total.backward()
    errors=[abs(float(total.detach())-loss)]
    for layer,g,b in zip((model.first,model.last),cg,bg):
        errors.extend([float(np.max(abs(layer.weight.grad.numpy().T-g))),float(np.max(abs(layer.bias.grad.numpy()-b)))])
    expected_logits=(np.maximum(0,x@head.coefs_[0]+head.intercepts_[0])@head.coefs_[1]+head.intercepts_[1]).ravel()
    errors.append(float(np.max(abs(model(tensors[0]).detach().numpy()-expected_logits))))
    errors.append(abs(float(penalty.detach())-alpha/2/w.sum()*sum(np.square(a).sum() for a in head.coefs_)))
    finite_difference=[]
    for parameter in model.parameters():
        grad=parameter.grad.detach().clone()
        for index in range(parameter.numel()):
            with torch.no_grad():
                value=float(parameter.flatten()[index]); parameter.flatten()[index]=value+1e-6
            plus=float(objective(model,*tensors,alpha=alpha)[0].detach())
            with torch.no_grad(): parameter.flatten()[index]=value-1e-6
            minus=float(objective(model,*tensors,alpha=alpha)[0].detach())
            with torch.no_grad(): parameter.flatten()[index]=value
            expected=float(grad.flatten()[index]); got=(plus-minus)/2e-6
            finite_difference.append(abs(got-expected)/max(1.,abs(got),abs(expected)))
    if max(errors)>1e-7 or max(finite_difference)>1e-5: raise ValueError('LEGACY_OBJECTIVE_PARITY_FAILURE')
    return dict(status='PASS', maximum_loss_logit_penalty_gradient_error=max(errors),
                maximum_normalized_finite_difference_error=max(finite_difference), tolerance=1e-7,
                objective='weighted_mean_BCE + alpha/(2*sum_weights) * sum_weight_matrices_squared',
                new_objective='weighted_mean_BCE + lambda/2 * sum_weight_matrices_squared', weight_decay=0.,
                head_fits=0, parameters_checked=sum(p.numel() for p in model.parameters()))
