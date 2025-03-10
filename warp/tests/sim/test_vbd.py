# Copyright (c) 2024 NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import contextlib
import io
import unittest

import warp as wp
import warp.optim
import warp.sim
from warp.sim.model import PARTICLE_FLAG_ACTIVE
from warp.tests.unittest_utils import *

# fmt: off
CLOTH_POINTS = [
    (-50.0000000, 0.0000000, -50.0000000),
    (-38.8888893, 11.1111107, -50.0000000),
    (-27.7777786, 22.2222214, -50.0000000),
    (-16.6666679, 33.3333321, -50.0000000),
    (-5.5555558, 44.4444427, -50.0000000),
    (5.5555558, 55.5555573, -50.0000000),
    (16.6666679, 66.6666641, -50.0000000),
    (27.7777786, 77.7777786, -50.0000000),
    (38.8888893, 88.8888855, -50.0000000),
    (50.0000000, 100.0000000, -50.0000000),
    (-50.0000000, 0.0000000, -38.8888893),
    (-38.8888893, 11.1111107, -38.8888893),
    (-27.7777786, 22.2222214, -38.8888893),
    (-16.6666679, 33.3333321, -38.8888893),
    (-5.5555558, 44.4444427, -38.8888893),
    (5.5555558, 55.5555573, -38.8888893),
    (16.6666679, 66.6666641, -38.8888893),
    (27.7777786, 77.7777786, -38.8888893),
    (38.8888893, 88.8888855, -38.8888893),
    (50.0000000, 100.0000000, -38.8888893),
    (-50.0000000, 0.0000000, -27.7777786),
    (-38.8888893, 11.1111107, -27.7777786),
    (-27.7777786, 22.2222214, -27.7777786),
    (-16.6666679, 33.3333321, -27.7777786),
    (-5.5555558, 44.4444427, -27.7777786),
    (5.5555558, 55.5555573, -27.7777786),
    (16.6666679, 66.6666641, -27.7777786),
    (27.7777786, 77.7777786, -27.7777786),
    (38.8888893, 88.8888855, -27.7777786),
    (50.0000000, 100.0000000, -27.7777786),
    (-50.0000000, 0.0000000, -16.6666679),
    (-38.8888893, 11.1111107, -16.6666679),
    (-27.7777786, 22.2222214, -16.6666679),
    (-16.6666679, 33.3333321, -16.6666679),
    (-5.5555558, 44.4444427, -16.6666679),
    (5.5555558, 55.5555573, -16.6666679),
    (16.6666679, 66.6666641, -16.6666679),
    (27.7777786, 77.7777786, -16.6666679),
    (38.8888893, 88.8888855, -16.6666679),
    (50.0000000, 100.0000000, -16.6666679),
    (-50.0000000, 0.0000000, -5.5555558),
    (-38.8888893, 11.1111107, -5.5555558),
    (-27.7777786, 22.2222214, -5.5555558),
    (-16.6666679, 33.3333321, -5.5555558),
    (-5.5555558, 44.4444427, -5.5555558),
    (5.5555558, 55.5555573, -5.5555558),
    (16.6666679, 66.6666641, -5.5555558),
    (27.7777786, 77.7777786, -5.5555558),
    (38.8888893, 88.8888855, -5.5555558),
    (50.0000000, 100.0000000, -5.5555558),
    (-50.0000000, 0.0000000, 5.5555558),
    (-38.8888893, 11.1111107, 5.5555558),
    (-27.7777786, 22.2222214, 5.5555558),
    (-16.6666679, 33.3333321, 5.5555558),
    (-5.5555558, 44.4444427, 5.5555558),
    (5.5555558, 55.5555573, 5.5555558),
    (16.6666679, 66.6666641, 5.5555558),
    (27.7777786, 77.7777786, 5.5555558),
    (38.8888893, 88.8888855, 5.5555558),
    (50.0000000, 100.0000000, 5.5555558),
    (-50.0000000, 0.0000000, 16.6666679),
    (-38.8888893, 11.1111107, 16.6666679),
    (-27.7777786, 22.2222214, 16.6666679),
    (-16.6666679, 33.3333321, 16.6666679),
    (-5.5555558, 44.4444427, 16.6666679),
    (5.5555558, 55.5555573, 16.6666679),
    (16.6666679, 66.6666641, 16.6666679),
    (27.7777786, 77.7777786, 16.6666679),
    (38.8888893, 88.8888855, 16.6666679),
    (50.0000000, 100.0000000, 16.6666679),
    (-50.0000000, 0.0000000, 27.7777786),
    (-38.8888893, 11.1111107, 27.7777786),
    (-27.7777786, 22.2222214, 27.7777786),
    (-16.6666679, 33.3333321, 27.7777786),
    (-5.5555558, 44.4444427, 27.7777786),
    (5.5555558, 55.5555573, 27.7777786),
    (16.6666679, 66.6666641, 27.7777786),
    (27.7777786, 77.7777786, 27.7777786),
    (38.8888893, 88.8888855, 27.7777786),
    (50.0000000, 100.0000000, 27.7777786),
    (-50.0000000, 0.0000000, 38.8888893),
    (-38.8888893, 11.1111107, 38.8888893),
    (-27.7777786, 22.2222214, 38.8888893),
    (-16.6666679, 33.3333321, 38.8888893),
    (-5.5555558, 44.4444427, 38.8888893),
    (5.5555558, 55.5555573, 38.8888893),
    (16.6666679, 66.6666641, 38.8888893),
    (27.7777786, 77.7777786, 38.8888893),
    (38.8888893, 88.8888855, 38.8888893),
    (50.0000000, 100.0000000, 38.8888893),
    (-50.0000000, 0.0000000, 50.0000000),
    (-38.8888893, 11.1111107, 50.0000000),
    (-27.7777786, 22.2222214, 50.0000000),
    (-16.6666679, 33.3333321, 50.0000000),
    (-5.5555558, 44.4444427, 50.0000000),
    (5.5555558, 55.5555573, 50.0000000),
    (16.6666679, 66.6666641, 50.0000000),
    (27.7777786, 77.7777786, 50.0000000),
    (38.8888893, 88.8888855, 50.0000000),
    (50.0000000, 100.0000000, 50.0000000),
]

CLOTH_FACES = [
    1, 12, 2,
    1, 11, 12,
    2, 12, 3,
    12, 13, 3,
    3, 14, 4,
    3, 13, 14,
    4, 14, 5,
    14, 15, 5,
    5, 16, 6,
    5, 15, 16,
    6, 16, 7,
    16, 17, 7,
    7, 18, 8,
    7, 17, 18,
    8, 18, 9,
    18, 19, 9,
    9, 20, 10,
    9, 19, 20,
    11, 21, 12,
    21, 22, 12,
    12, 23, 13,
    12, 22, 23,
    13, 23, 14,
    23, 24, 14,
    14, 25, 15,
    14, 24, 25,
    15, 25, 16,
    25, 26, 16,
    16, 27, 17,
    16, 26, 27,
    17, 27, 18,
    27, 28, 18,
    18, 29, 19,
    18, 28, 29,
    19, 29, 20,
    29, 30, 20,
    21, 32, 22,
    21, 31, 32,
    22, 32, 23,
    32, 33, 23,
    23, 34, 24,
    23, 33, 34,
    24, 34, 25,
    34, 35, 25,
    25, 36, 26,
    25, 35, 36,
    26, 36, 27,
    36, 37, 27,
    27, 38, 28,
    27, 37, 38,
    28, 38, 29,
    38, 39, 29,
    29, 40, 30,
    29, 39, 40,
    31, 41, 32,
    41, 42, 32,
    32, 43, 33,
    32, 42, 43,
    33, 43, 34,
    43, 44, 34,
    34, 45, 35,
    34, 44, 45,
    35, 45, 36,
    45, 46, 36,
    36, 47, 37,
    36, 46, 47,
    37, 47, 38,
    47, 48, 38,
    38, 49, 39,
    38, 48, 49,
    39, 49, 40,
    49, 50, 40,
    41, 52, 42,
    41, 51, 52,
    42, 52, 43,
    52, 53, 43,
    43, 54, 44,
    43, 53, 54,
    44, 54, 45,
    54, 55, 45,
    45, 56, 46,
    45, 55, 56,
    46, 56, 47,
    56, 57, 47,
    47, 58, 48,
    47, 57, 58,
    48, 58, 49,
    58, 59, 49,
    49, 60, 50,
    49, 59, 60,
    51, 61, 52,
    61, 62, 52,
    52, 63, 53,
    52, 62, 63,
    53, 63, 54,
    63, 64, 54,
    54, 65, 55,
    54, 64, 65,
    55, 65, 56,
    65, 66, 56,
    56, 67, 57,
    56, 66, 67,
    57, 67, 58,
    67, 68, 58,
    58, 69, 59,
    58, 68, 69,
    59, 69, 60,
    69, 70, 60,
    61, 72, 62,
    61, 71, 72,
    62, 72, 63,
    72, 73, 63,
    63, 74, 64,
    63, 73, 74,
    64, 74, 65,
    74, 75, 65,
    65, 76, 66,
    65, 75, 76,
    66, 76, 67,
    76, 77, 67,
    67, 78, 68,
    67, 77, 78,
    68, 78, 69,
    78, 79, 69,
    69, 80, 70,
    69, 79, 80,
    71, 81, 72,
    81, 82, 72,
    72, 83, 73,
    72, 82, 83,
    73, 83, 74,
    83, 84, 74,
    74, 85, 75,
    74, 84, 85,
    75, 85, 76,
    85, 86, 76,
    76, 87, 77,
    76, 86, 87,
    77, 87, 78,
    87, 88, 78,
    78, 89, 79,
    78, 88, 89,
    79, 89, 80,
    89, 90, 80,
    81, 92, 82,
    81, 91, 92,
    82, 92, 83,
    92, 93, 83,
    83, 94, 84,
    83, 93, 94,
    84, 94, 85,
    94, 95, 85,
    85, 96, 86,
    85, 95, 96,
    86, 96, 87,
    96, 97, 87,
    87, 98, 88,
    87, 97, 98,
    88, 98, 89,
    98, 99, 89,
    89, 100, 90,
    89, 99, 100
]

# fmt: on
class VBDClothSim:
    def __init__(self, device, use_cuda_graph=False):
        self.frame_dt = 1 / 60
        self.num_test_frames = 100
        self.num_substeps = 10
        self.iterations = 10
        self.dt = self.frame_dt / self.num_substeps

        stiffness = 1e5
        kd = 1.0e-7

        self.input_scale_factor = 1.0
        self.renderer_scale_factor = 0.01
        vertices = [wp.vec3(v) * self.input_scale_factor for v in CLOTH_POINTS]
        faces_flatten = [fv - 1 for fv in CLOTH_FACES]

        builder = wp.sim.ModelBuilder()
        builder.add_cloth_mesh(
            pos=wp.vec3(0.0, 200.0, 0.0),
            rot=wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), 0.0),
            scale=1.0,
            vertices=vertices,
            indices=faces_flatten,
            vel=wp.vec3(0.0, 0.0, 0.0),
            density=0.02,
            tri_ke=stiffness,
            tri_ka=stiffness,
            tri_kd=kd,
        )
        builder.color()

        self.model = builder.finalize(device=device)
        self.model.ground = True
        self.model.gravity = wp.vec3(0, -1000.0, 0)
        self.model.soft_contact_ke = 1.0e4
        self.model.soft_contact_kd = 1.0e2

        self.fixed_particles = [0, 9]

        self.set_points_fixed(self.model, self.fixed_particles)

        self.integrator = wp.sim.VBDIntegrator(self.model, self.iterations)
        self.state0 = self.model.state()
        self.state1 = self.model.state()

        self.init_pos = np.array(self.state0.particle_q.numpy(), copy=True)

        self.use_cuda_graph = device.is_cuda and use_cuda_graph
        self.graph = None
        if self.use_cuda_graph:
            with wp.ScopedCapture(device=device) as capture:
                self.simulate()
            self.graph = capture.graph

    def simulate(self):
        for _step in range(self.num_substeps * self.num_test_frames):
            self.integrator.simulate(self.model, self.state0, self.state1, self.dt, None)
            (self.state0, self.state1) = (self.state1, self.state0)

    def run(self):
        if self.graph:
            wp.capture_launch(self.graph)
        else:
            self.simulate()

    def set_points_fixed(self, model, fixed_particles):
        if len(fixed_particles):
            flags = model.particle_flags.numpy()
            for fixed_v_id in fixed_particles:
                flags[fixed_v_id] = wp.uint32(int(flags[fixed_v_id]) & ~int(PARTICLE_FLAG_ACTIVE))

            model.particle_flags = wp.array(flags, device=model.device)


def test_vbd_cloth(test, device):
    with contextlib.redirect_stdout(io.StringIO()) as f:
        example = VBDClothSim(device)

    test.assertRegex(
        f.getvalue(),
        r"Warp UserWarning: The graph is not optimizable anymore, terminated with a max/min ratio: 2.0 without reaching the target ratio: 1.1",
    )

    example.run()

    # examine that the simulation does not explode
    final_pos = example.state0.particle_q.numpy()
    test.assertTrue((final_pos < 1e5).all())
    # examine that the simulation have moved
    test.assertTrue((example.init_pos != final_pos).any())


def test_vbd_cloth_cuda_graph(test, device):
    with contextlib.redirect_stdout(io.StringIO()) as f:
        example = VBDClothSim(device, use_cuda_graph=True)
    test.assertRegex(
        f.getvalue(),
        r"Warp UserWarning: The graph is not optimizable anymore, terminated with a max/min ratio: 2.0 without reaching the target ratio: 1.1",
    )

    example.run()

    # examine that the simulation does not explode
    final_pos = example.state0.particle_q.numpy()
    test.assertTrue((final_pos < 1e5).all())
    # examine that the simulation have moved
    test.assertTrue((example.init_pos != final_pos).any())


devices = get_test_devices()
cuda_devices = get_selected_cuda_test_devices()


class TestVbd(unittest.TestCase):
    pass


add_function_test(TestVbd, "test_vbd_cloth", test_vbd_cloth, devices=devices)
add_function_test(TestVbd, "test_vbd_cloth_cuda_graph", test_vbd_cloth_cuda_graph, devices=cuda_devices)


if __name__ == "__main__":
    wp.clear_kernel_cache()
    unittest.main(verbosity=2)
