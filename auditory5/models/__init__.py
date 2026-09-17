"""Small, auditable models used by the auditory5 v1 routes."""

from .small_cnn import SmallEEGCNN_v1
from .simclr import (
    ProjectionHead,
    add_independent_gaussian_noise,
    make_noise_views,
    nt_xent_loss,
)

__all__ = [
    "SmallEEGCNN_v1",
    "ProjectionHead",
    "add_independent_gaussian_noise",
    "make_noise_views",
    "nt_xent_loss",
]
