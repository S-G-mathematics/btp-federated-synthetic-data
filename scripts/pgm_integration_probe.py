"""Pinned maintained-MBI API smoke for released scalar query measurements."""
from dataclasses import dataclass

import jax.numpy as jnp
import numpy as np
from mbi import Domain, LinearMeasurement, estimation


@dataclass(frozen=True, eq=False)
class MaskSumQuery:
    mask: tuple[float, ...]

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def __call__(self, factor):
        return jnp.dot(factor.datavector(), jnp.asarray(self.mask))

    def op_norm_sq(self):
        return float(np.dot(self.mask, self.mask))


def main():
    domain = Domain(["a", "b"], [2, 2])
    measurements = [
        LinearMeasurement(.7, ("a",), 1.0, MaskSumQuery((0., 1.))),
        LinearMeasurement(.4, ("b",), 1.0, MaskSumQuery((0., 1.))),
    ]
    model = estimation.UniversalAcceleratedMethod().estimate(
        domain, measurements, known_total=1.0, iters=50, tol=None)
    np.random.seed(123)
    data = model.synthetic_data(rows=1000, method="sample")
    assert set(data.data) == {"a", "b"}
    assert len(data.data["a"]) == 1000
    print({"a_mean": float(np.mean(data.data["a"])),
           "b_mean": float(np.mean(data.data["b"]))})


if __name__ == "__main__":
    main()
