# Copyright (c) 2022 NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import warp as wp
from warp.tests.test_base import *

wp.init()


# disable stores during forward replay
# replay while loop in backwards pass

@wp.kernel
def while_loop_grad(n: int, 
                    x: wp.array(dtype=float),
                    s: wp.array(dtype=float)):

    tid = wp.tid()
    
    sum = float(0.0)
    i = int(0)

    while i < n:
        sum = sum + x[i]*2.0
        i = i + 1

    s[0] = sum

def test_while_loop_grad(test, device):

    n = 32
    x = wp.array(np.ones(n, dtype=np.float32), device=device, requires_grad=True)
    sum = wp.zeros(1, dtype=wp.float32, device=device)

    tape = wp.Tape()
    with tape:
        wp.launch(while_loop_grad, dim=1, inputs=[n, x, sum], device=device)
   
    tape.backward(loss=sum)

    assert_np_equal(sum.numpy(), 2.0*np.sum(x.numpy()))
    assert_np_equal(tape.gradients[x].numpy(), 2.0*np.ones_like(x.numpy()))



@wp.kernel
def preserve_outputs(n: int, 
                     x: wp.array(dtype=float),
                     c: wp.array(dtype=float),
                     s0: wp.array(dtype=float),
                     s1: wp.array(dtype=float)):

    tid = wp.tid()

    # plain store
    c[tid] = x[tid]*2.0
    
    # atomic stores
    wp.atomic_add(s0, 0, x[tid]*2.0)
    wp.atomic_sub(s1, 0, x[tid]*2.0)


# tests that outputs from the forward pass are
# preserved by the backward pass, i.e.: stores
# are omitted during the forward reply
def test_preserve_outputs_grad(test, device):

    n = 32

    val = np.ones(n, dtype=np.float32)

    x = wp.array(val, device=device, requires_grad=True)
    c = wp.zeros_like(x)
    
    s1 = wp.zeros(1, dtype=wp.float32, device=device)
    s2 = wp.zeros(1, dtype=wp.float32, device=device)

    tape = wp.Tape()
    with tape:
        wp.launch(preserve_outputs, dim=n, inputs=[n, x, c, s1, s2], device=device)

    # ensure forward pass results are correct
    assert_np_equal(x.numpy(), val)
    assert_np_equal(c.numpy(), val*2.0)
    assert_np_equal(s1.numpy(), np.array(2.0*n))
    assert_np_equal(s2.numpy(), np.array(-2.0*n))
    
    # run backward on first loss
    tape.backward(loss=s1)

    # ensure inputs, copy and sum are unchanged by backwards pass
    assert_np_equal(x.numpy(), val)
    assert_np_equal(c.numpy(), val*2.0)
    assert_np_equal(s1.numpy(), np.array(2.0*n))
    assert_np_equal(s2.numpy(), np.array(-2.0*n))

    # ensure gradients are correct
    assert_np_equal(tape.gradients[x].numpy(), 2.0*val)

    # run backward on second loss
    tape.zero()    
    tape.backward(loss=s2)

    assert_np_equal(x.numpy(), val)
    assert_np_equal(c.numpy(), val*2.0)
    assert_np_equal(s1.numpy(), np.array(2.0*n))
    assert_np_equal(s2.numpy(), np.array(-2.0*n))

    # ensure gradients are correct
    assert_np_equal(tape.gradients[x].numpy(), -2.0*val)


def register(parent):

    devices = wp.get_devices()

    class TestGrad(parent):
        pass

    #add_function_test(TestGrad, "test_while_loop_grad", test_while_loop_grad, devices=devices)
    add_function_test(TestGrad, "test_preserve_outputs_grad", test_preserve_outputs_grad, devices=devices)

    return TestGrad

if __name__ == '__main__':
    c = register(unittest.TestCase)
    unittest.main(verbosity=2, failfast=False)