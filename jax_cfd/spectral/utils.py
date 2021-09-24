# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper functions for building pseudospectral methods."""

from typing import Callable, Tuple

import jax.numpy as jnp
from jax_cfd.base import grids
from jax_cfd.spectral import types as spectral_types


def circular_filter_2d(grid: grids.Grid) -> spectral_types.Array:
  """Circular filter which roughly matches the 2/3 rule but is smoother.

  Follows the technique described in Equation 1 of [1]. We use a different value
  for alpha as used by pyqg [2].

  Args:
    grid: the grid to filter over

  Returns:
    Filter mask

  Reference:
    [1] Arbic, Brian K., and Glenn R. Flierl. "Coherent vortices and kinetic
    energy ribbons in asymptotic, quasi two-dimensional f-plane turbulence."
    Physics of Fluids 15, no. 8 (2003): 2177-2189.
    https://doi.org/10.1063/1.1582183

    [2] Ryan Abernathey, rochanotes, Malte Jansen, Francis J. Poulin, Navid C.
    Constantinou, Dhruv Balwada, Anirban Sinha, Mike Bueti, James Penn,
    Christopher L. Pitt Wolfe, & Bia Villas Boas. (2019). pyqg/pyqg: v0.3.0
    (v0.3.0). Zenodo. https://doi.org/10.5281/zenodo.3551326.
    See:
    https://github.com/pyqg/pyqg/blob/02e8e713660d6b2043410f2fef6a186a7cb225a6/pyqg/model.py#L136
  """
  kx, ky = grid.rfft_mesh()
  max_k = ky[-1, -1]

  circle = jnp.sqrt(kx**2 + ky**2)
  cphi = 0.65 * max_k
  filterfac = 23.6
  filter_ = jnp.exp(-filterfac * (circle - cphi)**4.)
  filter_ = jnp.where(circle <= cphi, jnp.ones_like(filter_), filter_)
  return filter_


def vorticity_to_velocity(
    grid: grids.Grid
) -> Callable[[spectral_types.Array], Tuple[spectral_types.Array,
                                            spectral_types.Array]]:
  """Constructs a function for converting vorticity to velocity, both in Fourier domain.

  Solves for the stream function and then uses the stream function to compute
  the velocity. This is the standard approach. A quick sketch can be found in
  [1].

  Args:
    grid: the grid underlying the vorticity field.

  Returns:
    A function that takes a vorticity (rfftn) and returns a velocity vector
    field.

  Reference:
    [1] Z. Yin, H.J.H. Clercx, D.C. Montgomery, An easily implemented task-based
    parallel scheme for the Fourier pseudospectral solver applied to 2D
    Navier–Stokes turbulence, Computers & Fluids, Volume 33, Issue 4, 2004,
    Pages 509-520, ISSN 0045-7930,
    https://doi.org/10.1016/j.compfluid.2003.06.003.
  """
  kx, ky = grid.rfft_mesh()
  two_pi_i = 2 * jnp.pi * 1j
  laplace = two_pi_i ** 2 * (abs(kx)**2 + abs(ky)**2)
  laplace = laplace.at[0, 0].set(1)

  def ret(vorticity_hat):
    psi_hat = -1 / laplace * vorticity_hat
    vxhat = two_pi_i * ky * psi_hat
    vyhat = -two_pi_i * kx * psi_hat
    return vxhat, vyhat

  return ret


def filter_step(step_fn: spectral_types.StepFn, filter_: spectral_types.Array):
  """Returns a filtered version of the step_fn."""
  def new_step_fn(state):
    return filter_ * step_fn(state)
  return new_step_fn