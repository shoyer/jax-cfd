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

"""Tests for jax_cfd.base.resize."""

from absl.testing import absltest
from absl.testing import parameterized

from jax_cfd.base import grids
from jax_cfd.base import resize
from jax_cfd.base import test_util
import numpy as np


class ResizeTest(test_util.TestCase):

  @parameterized.parameters(
      dict(u=np.array([[0, 1, 2, 3],
                       [4, 5, 6, 7],
                       [8, 9, 10, 11],
                       [12, 13, 14, 15]]),
           direction=0,
           factor=2,
           expected=np.array([[4.5, 6.5],
                              [12.5, 14.5]])),
      dict(u=np.array([[0, 1, 2, 3],
                       [4, 5, 6, 7],
                       [8, 9, 10, 11],
                       [12, 13, 14, 15]]),
           direction=1,
           factor=2,
           expected=np.array([[3., 5.],
                              [11., 13.]])),
  )
  def testDownsampleVelocityComponent(self, u, direction, factor, expected):
    """Test `downsample_array` produces the expected results."""
    actual = resize.downsample_staggered_velocity_component(
        u, direction, factor)
    self.assertAllClose(expected, actual)

  def testDownsampleVelocity(self):
    source_grid = grids.Grid((4, 4), domain=[(0, 1), (0, 1)])
    destination_grid = grids.Grid((2, 2), domain=[(0, 1), (0, 1)])
    u = np.array([
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11],
        [12, 13, 14, 15],
    ])
    expected = (np.array([[4.5, 6.5],
                          [12.5, 14.5]]), np.array([[3., 5.], [11., 13.]]))

    with self.subTest('ArrayField'):
      velocity = (u, u)
      actual = resize.downsample_staggered_velocity(source_grid,
                                                    destination_grid, velocity)
      self.assertAllClose(expected, actual)

    with self.subTest('AlignedField'):
      velocity = (grids.AlignedArray(u, offset=(1, 0)),
                  grids.AlignedArray(u, offset=(0, 1)))
      actual = resize.downsample_staggered_velocity(source_grid,
                                                    destination_grid, velocity)
      expected_aligned = (grids.AlignedArray(expected[0], offset=(1, 0)),
                          grids.AlignedArray(expected[1], offset=(0, 1)))
      self.assertAllClose(expected_aligned[0], actual[0])
      self.assertAllClose(expected_aligned[1], actual[1])

if __name__ == '__main__':
  absltest.main()
