"""Small stimulus-conditioned response-profile model.

This prototype consumes preprocessed tensor batches. It does not read EEG files,
fit cohort transformations, train clinical heads, or provide clinical uncertainty.
The normalization follows 03_METHOD_SPEC.md; clinical labels are not accepted.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import torch
from torch import Tensor, nn

@dataclass
class ProfileOutput:
    mean: Tensor
    logvar: Tensor
    latent_mean: Tensor
    latent_logvar: Tensor
    latent: Tensor

class PopulationResponse(nn.Module):
    """Frozen conditional mean coefficients [K,H+1,D] and log variance [K,D]."""
    def __init__(self, coefficients: Tensor, logvar: Tensor) -> None:
        super().__init__()
        if coefficients.ndim != 3 or logvar.shape != (coefficients.shape[0], coefficients.shape[2]):
            raise ValueError("Population shapes must be [K,H+1,D] and [K,D].")
        if not torch.isfinite(coefficients).all() or not torch.isfinite(logvar).all():
            raise ValueError("Nonfinite population parameters.")
        self.register_buffer("coefficients", coefficients.detach().clone())
        self.register_buffer("base_logvar", logvar.detach().clone().clamp(-4.0,3.0))
        self.n_conditions, h1, self.feature_dim = coefficients.shape
        self.history_dim = h1 - 1

    def forward(self, conditions: Tensor, history: Tensor) -> tuple[Tensor, Tensor]:
        if conditions.dtype != torch.long or conditions.ndim != 2:
            raise ValueError("conditions must be int64 [B,Q].")
        if history.shape != (*conditions.shape, self.history_dim):
            raise ValueError("history must be [B,Q,H].")
        if conditions.numel() == 0 or (conditions < 0).any() or (conditions >= self.n_conditions).any():
            raise ValueError("Invalid or empty condition indices.")
        if not torch.isfinite(history).all():
            raise ValueError("History must be imputed on the training pool first.")
        ones = torch.ones_like(history[..., :1]) if self.history_dim else history.new_ones((*conditions.shape, 1))
        design = torch.cat((ones, history), dim=-1)
        mean = torch.einsum("bqh,bqhd->bqd", design, self.coefficients[conditions])
        return mean, self.base_logvar[conditions]

class ResponseProfile(nn.Module):
    """Conditioned vs pooled support summaries, with the same decoder capacity."""
    def __init__(self, population: PopulationResponse, *, latent_dim: int = 8,
                 hidden: int = 32, phi_dim: int = 16, conditioned: bool = True) -> None:
        super().__init__()
        if latent_dim < 1 or hidden < 1 or phi_dim < 1:
            raise ValueError("Dimensions must be positive.")
        self.population = population
        self.conditioned = conditioned
        self.latent_dim = latent_dim
        d, k = population.feature_dim, population.n_conditions
        self.phi = nn.Sequential(nn.Linear(d, hidden), nn.Tanh(), nn.Linear(hidden, phi_dim), nn.Tanh())
        self.posterior = nn.Linear(k * phi_dim, 2 * latent_dim)
        self.mean_map = nn.Parameter(torch.randn(k, d, latent_dim) * 0.01)
        self.logvar_map = nn.Parameter(torch.zeros(k, d, latent_dim))

    def encode(self, support: Tensor, support_mask: Tensor) -> tuple[Tensor, Tensor]:
        if support.ndim != 4:
            raise ValueError("support must be [B,K,T,D].")
        b, k, t, d = support.shape
        if k != self.population.n_conditions or d != self.population.feature_dim or t == 0:
            raise ValueError("Support dimensions do not match the population model.")
        if support_mask.shape != (b,k,t) or support_mask.dtype != torch.bool:
            raise ValueError("support_mask must be bool [B,K,T].")
        counts = support_mask.sum(-1)
        if (counts == 0).any():
            raise ValueError("Every child must have support for each declared condition.")
        if not torch.isfinite(support[support_mask]).all():
            raise ValueError("Nonfinite accepted support features.")
        clean = torch.where(support_mask[...,None], support, torch.zeros_like(support))
        features = self.phi(clean)
        means = (features * support_mask[...,None]).sum(-2) / counts[...,None]
        if not self.conditioned:
            means = means.mean(1, keepdim=True).expand(-1,k,-1)
        mu, logvar = self.posterior(means.reshape(b,-1)).chunk(2,dim=-1)
        return mu, logvar.clamp(-6.0,2.0)

    def decode(self, latent: Tensor, query_conditions: Tensor, query_history: Tensor) -> tuple[Tensor, Tensor]:
        pop_mean, pop_logvar = self.population(query_conditions,query_history)
        if latent.shape != (query_conditions.shape[0], self.latent_dim):
            raise ValueError("latent must be [B,U].")
        mean = pop_mean + torch.einsum("bqdu,bu->bqd", self.mean_map[query_conditions], latent)
        lv = pop_logvar + torch.einsum("bqdu,bu->bqd", self.logvar_map[query_conditions], latent)
        return mean, lv.clamp(-4.0,3.0)

    def forward(self, support: Tensor, support_mask: Tensor, query_conditions: Tensor,
                query_history: Tensor, *, sample_latent: bool | None = None) -> ProfileOutput:
        mu, lv = self.encode(support,support_mask)
        sample = self.training if sample_latent is None else sample_latent
        latent = mu + torch.exp(0.5*lv)*torch.randn_like(mu) if sample else mu
        mean, logvar = self.decode(latent,query_conditions,query_history)
        return ProfileOutput(mean,logvar,mu,lv,latent)


def balanced_profile_loss(target: Tensor, out: ProfileOutput, query_conditions: Tensor,
                          n_conditions: int, *, beta: float = 0.01,
                          query_mask: Tensor | None = None) -> dict[str, Tensor]:
    """Per-child/per-condition mean NLL per dimension plus KL per latent dimension."""
    if beta < 0 or target.shape != out.mean.shape or target.shape != out.logvar.shape:
        raise ValueError("Invalid loss shape or beta.")
    if query_conditions.shape != target.shape[:2]:
        raise ValueError("Query index shape mismatch.")
    if query_mask is None:
        query_mask = torch.ones_like(query_conditions,dtype=torch.bool)
    if query_mask.shape != query_conditions.shape or query_mask.dtype != torch.bool:
        raise ValueError("query_mask must be bool [B,Q].")
    if not torch.isfinite(target[query_mask]).all():
        raise ValueError("Nonfinite valid targets.")
    target = torch.where(query_mask[...,None], target, out.mean.detach())
    nll_trial = 0.5*(math.log(2*math.pi)+out.logvar+(target-out.mean).square()*torch.exp(-out.logvar))
    nll_trial = nll_trial.mean(-1)
    child_cond = []
    for c in range(n_conditions):
        m = query_mask & (query_conditions == c)
        counts = m.sum(1)
        if (counts == 0).any():
            raise ValueError("Every query child must have each declared condition.")
        child_cond.append((nll_trial*m).sum(1)/counts)
    nll = torch.stack(child_cond,1).mean()
    kl = 0.5*(torch.exp(out.latent_logvar)+out.latent_mean.square()-1-out.latent_logvar)
    kl = kl.mean(-1).mean()
    return {"loss":nll+beta*kl,"nll_per_dimension":nll,"kl_per_latent_dimension":kl}
