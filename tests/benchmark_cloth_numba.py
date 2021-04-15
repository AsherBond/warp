from numba import jit, prange
import numpy as np

# Notes:
# 
# * Pro: Easy installation

# * Con: Pain due to random unsupported parts of numpy in JIT compiler, e.g.: np.linalg.norm with axis param,  no np.einsum spuport, have to workaround these things in weird ways
# * Con: No unified way to write CPU/CUDA kernels
# * Con: Fragile support for parallel reductions, e.g.: y[i] += x from multiple threads may/may result in a race depending on compiler, no explicit atomics support
# * Con: Incorrect type promotions from f32->f64 that differ from numpy semantics, e.g. 1.0 / tensor_f32 -> tensor_f64
# * Con: Doesn't correctly handle bool * float conversions like numpy, see gravity computation
# * Con: Bad performance out of the box

@jit(nopython=True, parallel=True)
def eval_springs(num_springs,
    x,
    v,
    indices,
    rest,
    ke,
    kd,
    f):

    i = indices[:,0]
    j = indices[:,1]

    xi = x[i]
    xj = x[j]

    vi = v[i]
    vj = v[j]

    xij = xi - xj
    vij = vi - vj

    # no support for norm on a axis so have to run a custom parallel loop
    l = np.empty(num_springs, dtype=np.float32)
    for r in prange(num_springs):
        l[r] = np.linalg.norm(xij[r])

    l_inv = (1.0 / l).astype(np.float32)

    # normalized spring direction
    dir = (xij.T * l_inv).T

    c = l - rest

    # no support for sum over an axis so have to run custom parallel loop
    dcdt = np.empty(num_springs, dtype=np.float32)
    for r in prange(num_springs):
        dcdt[r] = np.dot(dir[r], vij[r])

    # damping based on relative velocity.
    fs = dir.T*(ke * c + kd * dcdt)

    # no atomic add support so have to run serial reduce
    for r in range(num_springs):
        dcdt[r] = np.dot(dir[r], vij[r])

        f[i[r]] -= (fs.T)[r]
        f[j[r]] += (fs.T)[r]


@jit(nopython=True, parallel=True)
def integrate_particles(x,
                        v,
                        f,
                        w,
                        dt):

    g = np.array((0.0, 0.0 - 9.8, 0.0))
    s = w > 0.0

    # todo: how to express this in Numba?
    a_ext = g#*s[:,None]

    # simple semi-implicit Euler. v1 = v0 + a dt, x1 = x0 + v1 dt
    v += ((f.T * w).T + a_ext) * dt
    x += (v * dt)

    # clear forces
    f *= 0.0


class NbIntegrator:

    def __init__(self, cloth):

        self.cloth = cloth

        self.positions = np.array(self.cloth.positions)
        self.velocities = np.array(self.cloth.velocities)
        self.inv_mass = np.array(self.cloth.inv_masses)

        self.spring_indices = np.array(self.cloth.spring_indices)
        self.spring_lengths = np.array(self.cloth.spring_lengths)
        self.spring_stiffness = np.array(self.cloth.spring_stiffness)
        self.spring_damping = np.array(self.cloth.spring_damping)
        
        self.forces = np.zeros((self.cloth.num_particles, 3), dtype=np.float32)

    def simulate(self, dt, substeps):

        sim_dt = dt/substeps
        
        for s in range(substeps):

            eval_springs(self.cloth.num_springs,
                        self.positions, 
                        self.velocities,
                        self.spring_indices.reshape((self.cloth.num_springs, 2)),
                        self.spring_lengths,
                        self.spring_stiffness,
                        self.spring_damping,
                        self.forces)

            # integrate 
            integrate_particles(
                self.positions,
                self.velocities,
                self.forces,
                self.inv_mass,
                sim_dt)

        return self.positions