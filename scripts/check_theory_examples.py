#!/usr/bin/env python3
"""Deterministic arithmetic checks of illustrative theory cases; no experiment data."""
import math

# Imperfect model example: the permitted alternative corrects the query mean.
a = (0.5, 0.5)
w = (0.6, 0.4)
h = (0.3, 0.8)
mean = lambda x: sum(xi * hi for xi, hi in zip(x, h))
size, alternative = mean(a), mean(w)
assert math.isclose(size, 0.55) and math.isclose(alternative, 0.5)
assert sum(abs(x-y) for x,y in zip(w,a)) <= 0.25
assert all(x >= 0.5*y for x,y in zip(w,a))
kl = 0.5 * math.log(0.5/size) + 0.5 * math.log(0.5/(1-size))
assert math.isclose(kl, 0.00502516792675, rel_tol=1e-10)

# A dual certificate: constant first row has irreducible error 0.2.
H = ((0.7, 0.7), (0.2, 0.8))
b = (0.5, 0.5)
s = (1.0, 0.0)
hts = tuple(sum(H[j][i]*s[j] for j in range(2)) for i in range(2))
assert hts == (0.7, 0.7)
for j in range(101):
    x = (j/100, 1-j/100)
    objective = max(abs(sum(row[i]*x[i] for i in range(2))-target)
                    for row, target in zip(H, b))
    assert objective >= 0.2 - 1e-12
assert math.isclose(max(abs(sum(row[i]*a[i] for i in range(2))-target)
                        for row,target in zip(H,b)), 0.2)

# Sharp representation example: equality for two extreme query columns.
t = 0.3
assert math.isclose(t, 0.5 * (abs((1-t)-1) + abs(t)))
print(f'OK: size mean={size:.2f}, alternative mean={alternative:.2f}, KL={kl:.9f}; dual lower bound=0.2; sharpness verified')
