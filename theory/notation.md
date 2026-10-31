# Notation

- `D_R`: observed real reference, partitioned into clients `D_R,i`; `D_S`: a generated finite table.
- `alpha_i=n_i/sum_j n_j`: declared client-mass target; `w` is a simplex vector of generator weights; `W` is the declared feasible subset.
- `Q_i`: fixed fitted generator for client i; `Q_w=sum_i w_i Q_i`: its mixture. `q_l` is a fixed [0,1]-valued query.
- `B_li=mean_{D_R,i} q_l`, `b_R=B alpha`, and `H_li=E_{Q_i} q_l`. `b_S` contains the same query means on `D_S`.
- `L_R(w)=||H w-b_R||_infinity` compares model expectations with the finite real reference. The measured finite-table loss is `||b_S-b_R||_infinity`; sampling and allocation add uncertainty between them.
- `H_hat` is a finite pilot answer matrix, `b_hat` a permitted target summary, and `r_H,r_b` are simultaneous error radii. These need justification before use in a certificate.
- `TV(A,B)=sup_E |A(E)-B(E)|`; finite-query discrepancy takes the maximum only over the declared workload. Unknown population TV is not measured.

See [PROOFS.md](PROOFS.md) for all theorem-specific definitions and [the historical framework](BTP_Theoretical_Framework.tex) for its original notation.
