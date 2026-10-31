# Proof supplement: weighted federated synthetic data

**Post-experiment supplement · 31 October 2026**

This post-experiment supplement preserves the report’s theoretical framework. It does not claim originality for standard results, modify the frozen method, or certify its empirical outcomes. The fallback in Statement [8](#thm:fallback) is a theoretical proposal, not the frozen selection method.

Let $K$ be the number of clients and $\Delta_K=\{w\ge0:\sum_i w_i=1\}$. Let $\alpha\in\Delta_K$ denote target size weights and $\mathcal W\subseteq\Delta_K$ a nonempty closed feasible set containing $\alpha$ unless stated otherwise. Let $Q_i$ be fixed fitted distributions, $q_1,\dots,q_L$ fixed measurable queries taking values in $[0,1]$, $H_{\ell i}=\mathbb E_{Q_i}q_\ell$, and $Q_w=\sum_i w_i Q_i$. Let $B_{\ell i}$ denote the empirical answer on reference client $i$ and $b_R=B\alpha$. For a generated table $D_S$, let $b_S$ be its query vector, $\mathcal L_\mathcal Q(D_S,D_R;\alpha)=\left\lVert b_S-b_R\right\rVert_\infty$, and $L_R(w)=\left\lVert Hw-b_R\right\rVert_\infty$. The latter compares *model expectations* to a fixed finite real reference, whereas $\mathcal L_\mathcal Q$ compares a realized finite synthetic table to that reference. Sampling and allocation error connect them; neither objective is automatically population loss.

For measures $A,B$, $d_\mathcal Q(A,B)=\max_{q\in\mathcal Q}|\mathbb E_Aq-\mathbb E_Bq|$ and $\operatorname{TV}(A,B)=\sup_E|A(E)-B(E)|$. Write $\rho_m(w)=\frac12\left\lVert\bar w-w\right\rVert_1$ for realized allocation proportions $\bar w$. For a pilot matrix $\widehat H$ and target summary $\widehat b$, assume the error event

$$
\max_i\left\lVert\widehat H_{\cdot i}-H_{\cdot i}\right\rVert_\infty\le r_H,\qquad \left\lVert\widehat b-b_R\right\rVert_\infty\le r_b,\quad r=r_H+r_b.
$$

Set $\widehat L(w)=\left\lVert\widehat Hw-\widehat b\right\rVert_\infty$. For prediction, $R_A(g)=\mathbb E_A\ell(g(X),Y)$ with $0\le\ell\le1$, and $d_{\ell,\mathcal G}(A,B)=\sup_{g\in\mathcal G}|R_A(g)-R_B(g)|$. In the Brier statement, $R_A$ specifically uses squared loss. Conditional notation $R_C,T_C$ means conditioning on $C$ with positive mass. All optimization tolerances are nonnegative; all logarithms are natural, $\lambda\ge0$ where used as a penalty, and $\varepsilon\ge0$ in the transport statement.

For hypothetical population laws $P_i$, define $e_i=\operatorname{TV}(P_i,Q_i)$, $D_Q=\max_{i,j}\operatorname{TV}(Q_i,Q_j)$, and $a_A=\operatorname{TV}(Q_w,A_w)$. Inserting $Q_\alpha$ and $Q_w$ and using mixture convexity and the positive/negative weight decomposition yields $\operatorname{TV}(\sum_i\alpha_iP_i,A_w)\le\sum_i\alpha_i e_i+(D_Q/2)\left\lVert w-\alpha\right\rVert_1+a_A$. These population quantities were not certified by the finite-query experiment.

The achievable model-answer set is $H\Delta_K=\operatorname{conv}\{H_{\cdot i}\}$, so $\inf_{w\in\Delta_K}L_R(w)=\operatorname{dist}_\infty(b_R,H\Delta_K)$. For $Q_w(C)>0$, conditioning routes via weights $w_iQ_i(C)/Q_w(C)$; zero-mass components contribute zero. A finite exact joint model has posterior $\eta_{Q_w}(x)=\sum_iw_iq_i(x,1)/\sum_iw_iq_i^X(x)$ when the denominator is positive. These identities do not imply a learned adaptive gate.

<a id="thm:representation"></a>

### Statement 1: Sharp representation bound; thm:representation

For $H\in[0,1]^{L\times K}$ and $w,\alpha\in\Delta_K$, let $D_H=\max_{i,j}\left\lVert H_{\cdot i}-H_{\cdot j}\right\rVert_\infty$. Then

$$
\left\lVert H(w-\alpha)\right\rVert_\infty
\le\frac{D_H}{2}\left\lVert w-\alpha\right\rVert_1
\le\frac12\left\lVert w-\alpha\right\rVert_1.
$$

The constant $1/2$ is attained by some two-client query matrices.

*Proof.* Let $v=w-\alpha$ and $s=\sum_{v_i>0}v_i=\frac12\left\lVert v\right\rVert_1$. For $s>0$, its positive and negative parts, divided by $s$, are probability vectors. A row $h$ therefore satisfies $|hv|\le s(\max_i h_i-\min_i h_i)$. Maximize over rows. For sharpness, take $K=2$, $h=(0,1)$, $\alpha=(1,0)$, and $w=(1-t,t)$. Both sides of the last inequality equal $t$. For a fixed row, equality requires its extrema on the respective positive and negative supports of $v$. ◻

<a id="thm:decomp"></a>

### Statement 2: Observable error decomposition; thm:decomp

Let $B_{\ell i}$ be the empirical query mean in $D_i^R$, so $b_R=B\alpha$. Then

$$
\begin{split}
\left\lVert b_S-B\alpha\right\rVert_\infty\le{}&\left\lVert b_S-Hw\right\rVert_\infty\\
&+\sum_i\alpha_i\left\lVert H_{\cdot i}-B_{\cdot i}\right\rVert_\infty
+\frac{D_H}{2}\left\lVert w-\alpha\right\rVert_1.
\end{split}
$$

For an additional aggregation operator or compressed model, add the discrepancy between its query-answer vector and $Hw$.

*Proof.* The exact vector identity is $b_S-B\alpha=(b_S-Hw)+(H-B)\alpha+H(w-\alpha)$. Apply the triangle inequality, convexity, and Statement [1](#thm:representation). An operator approximation is another inserted vector. The components need not be independent, positive contributions: errors may cancel before norms are taken. ◻

<a id="thm:subsets"></a>

### Statement 3: Subset collapse and identifiability; thm:subsets

If a subset generator is $Q_B=\sum_{i\in B}w_i^{(B)}Q_i$ and subsets are mixed with weights $\rho_B$, then

$$
\sum_B\rho_B Q_B=\sum_i\omega_iQ_i,\qquad
\omega_i=\sum_{B\ni i}\rho_Bw_i^{(B)}.
$$

Regrouping introduces no new mixture distributions. Query answers identify all simplex weights uniquely if $\ker H\cap\{v:\mathbf 1^\top v=0\}=\{0\}$; otherwise feasible null directions can make different weights observationally indistinguishable.

*Proof.* Exchange the finite sums; nonnegativity and normalization give $\omega\in\Delta_K$. Equality of two answer vectors implies $H(w-w')=0$ and $\mathbf 1^\top(w-w')=0$. The kernel condition is sufficient and necessary for injectivity on the whole simplex because any nonzero zero-sum direction can be scaled around an interior point. Boundary constraints can yield uniqueness at a particular point without global injectivity. ◻

<a id="ex:ident"></a>

### Statement 4: Model-only information is insufficient; ex:ident

Suppose identical releases in two possible worlds are $Q_1=\mathrm{Bernoulli}(1/4)$ and $Q_2=\mathrm{Bernoulli}(3/4)$. No assumption connects model error to the real reference. For $q(z)=z$, a real empirical target with fraction $1/4$ of ones has oracle $w=(1,0)$, while fraction $3/4$ has oracle $w=(0,1)$. A release-only rule returns the same answer $x$ in both worlds. At least one error is $\max\{|x-1/4|,|x-3/4|\}\ge1/4$. Randomization cannot remove this worst-world expected lower bound, since the two absolute errors sum to at least $1/2$ pointwise. Informative summaries or modelling assumptions are necessary.

<a id="thm:oracle"></a>

### Statement 5: Uniform perturbation and oracle inequality; thm:oracle

Uniformly over every $w\in\Delta_K$,

$$
|\widehat L(w)-L_R(w)|\le r.
$$

Let $\Omega(w)=\frac12\left\lVert w-\alpha\right\rVert_2^2$ and let $\widehat w_\lambda\in\mathcal W$ minimize $\widehat L(w)+\lambda\Omega(w)$ to tolerance $\zeta\ge0$. If $w^*\in\operatorname*{arg\,min}_{w\in\mathcal W}L_R(w)$, then

$$
L_R(\widehat w_\lambda)-L_R(w^*)
\le2r+\lambda\Omega(w^*)+\zeta\le2r+\lambda+\zeta.
$$

This is valid for data-adaptive weights chosen from the same finite pilot.

*Proof.* For simplex $w$, $\left\lVert(\widehat H-H)w\right\rVert_\infty\le r_H$. The reverse triangle inequality gives <a href="#eq:uniform" data-reference-type="eqref" data-reference="eq:uniform">[eq:uniform]</a>. Compare the approximate regularized minimizer with $w^*$, use <a href="#eq:uniform" data-reference-type="eqref" data-reference="eq:uniform">[eq:uniform]</a> twice, and drop $-\lambda\Omega(\widehat w_\lambda)\le0$. Since two simplex points have squared distance at most two, $\Omega\le1$. The argument is uniform in $w$ and therefore covers selection of weights from $\widehat H,\widehat b$; it does not cover arbitrary data-adaptive query discovery without an additional uniform event. ◻

<a id="thm:stability"></a>

### Statement 6: Regularization stability; thm:stability

For two objectives $F,F'$ that share the term $\lambda\Omega$, $\lambda>0$, suppose their remaining terms are convex on the same convex feasible set and $\sup_w|F(w)-F'(w)|\le\eta$. Their unique exact minimizers $w,w'$ obey

$$
\left\lVert w-w'\right\rVert_2\le2\sqrt{\eta/\lambda}.$$

*Proof.* Strong convexity and constrained optimality give $\frac\lambda2\left\lVert w-w'\right\rVert_2^2\le F(w')-F(w)$. Adding and subtracting $F'$ and using optimality of $w'$ bounds the right side by $2\eta$. Strong convexity also gives uniqueness. Stability increases with $\lambda$, at the cost of the comparator term in <a href="#eq:oracle" data-reference-type="eqref" data-reference="eq:oracle">[eq:oracle]</a>. ◻

<a id="thm:sampling"></a>

### Statement 7: Finite-workload stratified sampling; thm:sampling

Condition on fitted models and selected weights. Generate $m_i$ independent rows from $Q_i$, with $\sum_i m_i=m$, and write $\bar w_i=m_i/m$. For fixed $L$ bounded queries, with probability at least $1-\gamma$,

$$
\left\lVert b_S-Hw\right\rVert_\infty
\le u_m(\gamma)+\rho_m(w),\quad
u_m(\gamma)=\sqrt{\frac{\log(2L/\gamma)}{2m}},
$$

where $\rho_m(w)=\frac12\left\lVert\bar w-w\right\rVert_1$. Largest-remainder allocation gives $\rho_m(w)<K/(2m)$. The same $u_m$ applies to IID mixture sampling with $\rho_m=0$.

*Proof.* Each query average is a mean of $m$ independent variables in $[0,1]$, not necessarily identically distributed. Its expectation is $H\bar w$. Hoeffding’s exponential argument yields tail probability at most $2e^{-2mu^2}$ per query. A union bound gives the displayed $u_m$. Statement [1](#thm:representation) bounds $\left\lVert H(\bar w-w)\right\rVert_\infty$ by $\rho_m$. Each rounded count differs from $mw_i$ by less than one. Shuffling does not change query averages. ◻

<a id="thm:fallback"></a>

### Statement 8: Sufficient fallback certificate; thm:fallback

On the error event <a href="#eq:errors" data-reference-type="eqref" data-reference="eq:errors">[eq:errors]</a>, choose any candidate $\widehat w\in\mathcal W$ using the released pilot and summaries. Let $\kappa>0$ be a desired gain. Accept only when

$$
\widehat L(\alpha)-\widehat L(\widehat w)
\ge\kappa+2r+2u_m(\gamma_S/2)
+\rho_m(\alpha)+\rho_m(\widehat w).
$$

Generate fresh candidate and size tables independently of selection. With conditional probability at least $1-\gamma_S$, acceptance guarantees

$$
\mathcal L_\mathcal Q(D_S^{\widehat w},D_R;\alpha)
\le\mathcal L_\mathcal Q(D_S^{\alpha},D_R;\alpha)-\kappa.
$$

On rejection, returning the already generated size table has exactly its loss. If the error event <a href="#eq:errors" data-reference-type="eqref" data-reference="eq:errors">[eq:errors]</a> holds with probability $1-\gamma_0$, the joint guarantee is at least $1-\gamma_0-\gamma_S$.

*Proof.* Uniform perturbation gives $L_R(\widehat w)-L_R(\alpha)\le\widehat L(\widehat w)-\widehat L(\alpha)+2r$. Apply Statement [7](#thm:sampling) to the two fresh tables and use a union bound. The sum of their deviations is the last three terms in <a href="#eq:certificate" data-reference-type="eqref" data-reference="eq:certificate">[eq:certificate]</a>. Returning the same baseline table on rejection avoids falsely promising equality between two independent baseline draws. ◻

<a id="thm:conditional"></a>

### Statement 9: Empirical conditional transfer; thm:conditional

For two fixed measures $R,S$ with $r=R(C)>0$, $s=S(C)>0$, let $e_C=\max_{q\in\mathcal Q_C}|\mathbb E_S[\mathbf 1_Cq]-\mathbb E_R[\mathbf 1_Cq]|$ and $e_0=|s-r|$. Then

$$
d_{\mathcal Q_C}(S(\cdot\mid C),R(\cdot\mid C))
\le\min\{1,(e_C+e_0)/r\}.$$

*Proof.* For $a=\mathbb E_R[\mathbf 1_Cq]$ and $c=\mathbb E_S[\mathbf 1_Cq]$, add and subtract $c/r$ in $|c/s-a/r|$. The result is at most $|c-a|/r+c|r-s|/(rs)\le(|c-a|+|r-s|)/r$, since $c\le s$. Take the maximum and cap by one. If $s=0$, the synthetic conditional is undefined and must abstain. ◻

<a id="ex:parity"></a>

### Statement 10: Matching marginals can reverse a conditional; ex:parity

Let $R$ put mass $1/2$ at $(X,Y)=(0,0),(1,1)$ and $S$ at $(0,1),(1,0)$. Their one-way means agree exactly. Nevertheless $R(Y=1\mid X=1)=1$ and $S(Y=1\mid X=1)=0$. A perfect synthetic predictor $g(x)=1-x$ has real squared loss one. Thus neither conditional fidelity nor predictive utility follows from these marginal matches. Higher-order parity distributions give analogous failures for workloads omitting the relevant interaction.

<a id="thm:pilot"></a>

### Statement 11: Simultaneous pilot accuracy; thm:pilot

Conditional on fitted models and a fixed workload, suppose each column of $\widehat H$ averages $p_i$ independent draws from $Q_i$. With probability at least $1-\gamma_H$,

$$
\left\lVert\widehat H_{\cdot i}-H_{\cdot i}\right\rVert_\infty
\le\sqrt{\frac{\log(2KL/\gamma_H)}{2p_i}}
\quad\text{for every }i.
$$

The maximum of these client-specific radii is a valid $r_H$ in Statement [5](#thm:oracle).

*Proof.* For each client/query pair Hoeffding’s bound is $2\exp(-2p_i u_i^2)$. Set each to $\gamma_H/(KL)$ and sum over $KL$ events. Independence between different queries is unnecessary. Fresh within-client sampling is sufficient; data-derived models and queries can be conditioned upon if pilot draws are independent of their construction. ◻

<a id="thm:summary"></a>

### Statement 12: A sufficient target-summary radius; thm:summary

Fix $\alpha$ and $\mathcal Q$. For each $i$, suppose calibration and reference observations are independent, bounded-query evaluations of sizes $c_i,t_i>0$, drawn from the same client law; observations are independent within and across these samples. Let $b_{\mathrm{cal}}$ and $b_R$ use the same $\alpha$. Then with probability at least $1-\gamma_b$,

$$
\left\lVert b_{\mathrm{cal}}-b_R\right\rVert_\infty
\le r_{\mathrm{data}}=
\sqrt{\frac{\log(2L/\gamma_b)}{2}
\sum_i\alpha_i^2\left(\frac1{c_i}+\frac1{t_i}\right)}.
$$

If $\widehat b=b_{\mathrm{cal}}+e$ and $\left\lVert e\right\rVert_\infty\le r_{\mathrm{noise}}$, then $r_b=r_{\mathrm{data}}+r_{\mathrm{noise}}$ is valid. For exact released summaries and a calibration target itself, $r_b=0$; this does not make that target identical to a held-out reference.

*Proof.* For each query, the calibration-minus-reference mean is a sum of independent mean-zero bounded variables. Their interval lengths are $\alpha_i/c_i$ repeated $c_i$ times and $\alpha_i/t_i$ repeated $t_i$ times. The sum of squared lengths is $V=\sum_i\alpha_i^2(1/c_i+1/t_i)$. Hoeffding gives $2\exp(-2r^2/V)$; a union bound yields <a href="#eq:realradius" data-reference-type="eqref" data-reference="eq:realradius">[eq:realradius]</a>. Add the release error by the triangle inequality. ◻

<a id="thm:val"></a>

### Statement 13: Validation-to-reference comparison; thm:val

For the same model-answer map $H$, suppose $\left\lVert b_{\mathrm{val}}-b_R\right\rVert_\infty\le r_V$. If $w_V$ minimizes $\left\lVert Hw-b_{\mathrm{val}}\right\rVert_\infty$ over $\mathcal W$ to tolerance $\zeta$, then

$$
L_R(w_V)\le\inf_{w\in\mathcal W}L_R(w)+2r_V+\zeta.
$$

If $H$ is replaced by a pilot matrix, add $2r_H$.

*Proof.* The reverse triangle inequality bounds the difference of the two objectives by $r_V$ for every $w$. Apply this at $w_V$ and at a comparator minimizing $L_R$, with the optimization inequality between them. The pilot statement follows from Statement [5](#thm:oracle). ◻

<a id="thm:projection"></a>

### Statement 14: Projected probability and information loss; thm:projection

Let $T:\mathcal Z\to\mathcal Z$ be deterministic. On a finite or countable support,

$$
(T_\#Q)(z)=\sum_{u:T(u)=z}Q(u).
$$

This is normalized and satisfies $\mathbb E_{T_\#Q}q=\mathbb E_Q(q\circ T)$. For arbitrary measures $A,B$, $\operatorname{TV}(T_\#A,T_\#B)\le\operatorname{TV}(A,B)$.

*Proof.* The preimages partition the original support, so their masses sum to one. The expectation identity follows by grouping terms by image. For any event $E$, $(T_\#A)(E)-(T_\#B)(E)=A(T^{-1}E)-B(T^{-1}E)$, bounded by the original TV. Take the supremum. ◻

<a id="thm:support"></a>

### Statement 15: Support-pilot statement and rejection cost; thm:support

For a fixed condition $C$ and $p$ independent IID proposals from a model $Q$, let $\widehat c$ be the matching fraction and $c=Q(C)$. With probability $1-\gamma$,

$$
c\ge\widehat c-\sqrt{\log(1/\gamma)/(2p)}.
$$

For a largest-remainder pilot from mixture $Q_w$, subtract an additional $\rho_p(w)$ to obtain a bound on $Q_w(C)$. For $J$ predeclared conditions, replace $\gamma$ by $\gamma/J$. Under IID rejection with $c>0$, the expected proposals for $a$ accepted rows is $a/c$, and the probability of failing a cap $B$ is $\mathbb P\{\mathrm{Binomial}(B,c)<a\}$.

*Proof.* Apply the one-sided Hoeffding inequality to indicators. With fixed client counts, indicators are independent but may have different means; their average expectation is $Q_{\bar w}(C)$, within $\rho_p(w)$ of $Q_w(C)$. For IID proposals, waiting times between accepts are geometric with mean $1/c$; their sum has mean $a/c$, and accepted counts before the cap are binomial. ◻

<a id="thm:student"></a>

### Statement 16: Student filtering and transfer; thm:student

Let $M$ be a raw per-condition student distribution with $a=M(C)>0$, and let $M_C=M(\cdot\mid C)$. Then $\operatorname{TV}(M,M_C)=1-a$. For any fixed conditional workload and teacher conditional $T_C$,

$$
d_{\mathcal Q_C}(M_C,R_C)\le
d_{\mathcal Q_C}(M_C,T_C)+d_{\mathcal Q_C}(T_C,R_C).
$$

An average error over conditions does not bound a worst-case error without further support or complexity restrictions.

*Proof.* Write $M=aM_C+(1-a)M_{C^c}$, with disjoint conditional supports; the event $C^c$ attains TV $1-a$. The transfer inequality is the querywise triangle inequality followed by a maximum. For the last statement, place an error of one on a condition of evaluation probability $\eta$ and zero elsewhere. The average is $\eta$ while the maximum is one, for any positive $\eta$. ◻

<a id="thm:tvconditional"></a>

### Statement 17: Abstract TV conditional implication; thm:tvconditional

For arbitrary measures $A,B$, suppose $\operatorname{TV}(A,B)\le e$ and $A(C)\ge\tau>e$. Then $B(C)>0$ and

$$
\operatorname{TV}(A(\cdot\mid C),B(\cdot\mid C))\le\min\{1,2e/\tau\}.
$$

A separate conditional student with TV error $a_C$ from $B(\cdot\mid C)$ adds $a_C$ to this upper bound, capped at one.

*Proof.* $B(C)\ge A(C)-e>0$. Apply the proof of Statement [9](#thm:conditional) to every indicator of an event inside $C$: both joint-event and mass discrepancies are at most $e$. Take the event supremum and then the triangle inequality for the student. ◻

<a id="thm:risk"></a>

### Statement 18: Risk transfer and approximate empirical learning; thm:risk

Suppose $d_{\ell,\mathcal G}(R_\alpha,Q_w)\le e_\ell$ and a synthetic sample satisfies $\sup_{g\in\mathcal G}|\widehat R_{D_S}(g)-R_{Q_w}(g)|\le\xi_m$. If $g_S$ is an approximate synthetic empirical-risk minimizer with tolerance $\zeta$, then

$$
R_{R_\alpha}(g_S)-\inf_{g\in\mathcal G}R_{R_\alpha}(g)
\le2e_\ell+2\xi_m+\zeta.
$$

For arbitrary measures $A,B$, $d_{\ell,\mathcal G}(A,B)\le\operatorname{TV}(A,B)$. For finite fixed $|\mathcal G|=M$ and IID synthetic draws, one sufficient radius is $\xi_m=\sqrt{\log(2M/\gamma)/(2m)}$ with probability $1-\gamma$.

*Proof.* For any comparator $g$, move from real risk of $g_S$ to model risk, then empirical synthetic risk, use approximate empirical optimality, and reverse the two comparisons for $g$. This incurs two copies of $e_\ell$ and $\xi_m$, plus $\zeta$; take the infimum. The TV implication follows by integrating the layer-cake indicators of a $[0,1]$-valued loss. The finite-class statement is Hoeffding plus a union bound. Stratified generation adds the allocation correction as in Statement [7](#thm:sampling). ◻

<a id="thm:brier"></a>

### Statement 19: Brier decomposition and teacher consistency; thm:brier

For binary $Y$, let $\eta_A(x)=A(Y=1\mid X=x)$. For any $g:\mathcal X\to[0,1]$,

$$
R_A(g)-R_A(\eta_A)=\mathbb E_{A^X}(g-\eta_A)^2.
$$

If $\operatorname{TV}(A,B)\le e$ and $a_g=\mathbb E_{B^X}(g-\eta_B)^2$, then

$$
\mathbb E_{A^X}(g-\eta_A)^2\le a_g+2e.$$

*Proof.* Condition on $X$: $\mathbb E[(g-Y)^2\mid X]=(g-\eta_A)^2+\eta_A(1-\eta_A)$. Subtract the Bayes risk and integrate. For transfer, $R_A(g)\le R_B(g)+e=R_B(\eta_B)+a_g+e\le R_B(\eta_A)+a_g+e\le R_A(\eta_A)+a_g+2e$. ◻

<a id="thm:finite"></a>

### Statement 20: Restriction and smoothing on a finite support; thm:finite

Let a discrete target model $Q$ assign positive mass to finite candidate support $\mathcal S$, and let $Q_{\mathcal S}=Q(\cdot\mid\mathcal S)$. Then

$$
\operatorname{TV}(Q,Q_{\mathcal S})=Q(\mathcal S^c).
$$

If $\widehat Q_{\mathcal S}$ has normalized mass-vector error at most $\eta$ in $\ell_1$, and smoothing forms $Q'=(1-\beta)\widehat Q_{\mathcal S}+\beta U$, then

$$
d_\mathcal Q(Q,Q')\le\min\{1,Q(\mathcal S^c)+\eta/2+\beta\}.
$$

Applying the same deterministic projection to both sides does not enlarge the TV version of this bound.

*Proof.* Restriction is the filtering identity of Statement [16](#thm:student). On a discrete support TV is half the $\ell_1$ mass difference. Mixing in $\beta U$ changes TV by at most $\beta$. Sum these quantities, use $d_\mathcal Q\le\operatorname{TV}$, and apply Statement [14](#thm:projection). ◻

<a id="thm:logpool"></a>

### Statement 21: Geometric-score perturbation; thm:logpool

On common finite support, let positive unnormalized masses be $g(z)=\exp h(z)$ and $g'(z)=\exp h'(z)$, with $\max_z|h'(z)-h(z)|\le\eta$. Normalize them to $G,G'$. Then

$$
\begin{gathered}
e^{-2\eta}\le G'(z)/G(z)\le e^{2\eta},\\
d_\mathcal Q(G,G')\le\min\{1,(e^{2\eta}-1)/2\}.
\end{gathered}
$$

For a fixed geometric weight vector, client log-score perturbations $\eta_i$ give $\eta\le\sum_iw_i\eta_i$.

*Proof.* The pointwise unnormalized ratio lies in $[e^{-\eta},e^\eta]$, as does the ratio of normalizing constants. Dividing gives the first bound. Sum $\frac12G(z)|G'(z)/G(z)-1|$ and bound the absolute ratio deviation by $e^{2\eta}-1$. The weighted score statement is the triangle inequality. ◻

<a id="thm:ot"></a>

### Statement 22: Finite entropic transport objective boundary; thm:ot

On finite probability supports with at most $B$ points each, define

$$
T_\varepsilon(a,b)=\min_{\pi\in\Pi(a,b)}
\langle C,\pi\rangle+\varepsilon\operatorname{KL}(\pi\|a\otimes b),
$$

and $T_0$ without the penalty. Then $T_0\le T_\varepsilon\le T_0+\varepsilon\log B$. For fixed client weights, if $a_\varepsilon$ minimizes $F_\varepsilon(a)=\sum_iw_iT_\varepsilon(a,b_i)$ to tolerance $\zeta$ over a common allowed set $\mathcal A$, then

$$
F_0(a_\varepsilon)-\inf_{a\in\mathcal A}F_0(a)
\le\varepsilon\log B+\zeta.
$$

A cost perturbation bounded entrywise by $\kappa$ adds $2\kappa$ when comparing the perturbed minimizer to the original objective. Restricting $\mathcal A$ further adds its approximation gap relative to a larger decision set.

*Proof.* For a coupling, $\operatorname{KL}(\pi\|a\otimes b)$ is mutual information and lies between zero and $\min\{H(a),H(b)\}\le\log B$. Evaluate the penalized objective at an unpenalized optimal coupling for the upper bound; nonnegativity gives the lower bound. Hence $F_0\le F_\varepsilon\le F_0+\varepsilon\log B$ uniformly, which yields <a href="#eq:ot" data-reference-type="eqref" data-reference="eq:ot">[eq:ot]</a> by comparison at its minimizer. A unit-mass coupling changes its cost by at most $\kappa$, giving two copies through a minimizer comparison. A restricted minimum differs from the larger-set minimum by exactly the stated nonnegative approximation gap. ◻

<a id="thm:privacy"></a>

### Statement 23: Scope of composed release guarantees; thm:privacy

Suppose each full client mechanism is $(\varepsilon_i,\delta_i)$-DP, each client mechanism depends only on its own dataset and uses randomness independent across clients (conditional on the fixed input datasets), membership is fixed and disjoint, and record replacement affects only one client. Joint release is $(\max_i\varepsilon_i,\max_i\delta_i)$-DP. Subsequent server operations using only that release and independent randomness preserve the guarantee. If multiple mechanisms access overlapping records with the required conditional DP guarantees, basic sequential composition instead sums their $\varepsilon$ and $\delta$ budgets. These conclusions are conditional on valid guarantees for every released mechanism; reusing hidden random noise is not justified by marginal per-fit guarantees alone.

*Proof.* Under fixed disjoint membership, a neighboring record replacement changes only one client output law. Condition on the unaffected outputs and apply that client’s DP inequality; integrate and take the largest budgets. Server postprocessing replaces an event by a randomized event probability in $[0,1]$ and integrates the same inequality. For overlapping accesses, the standard adaptive composition theorem supplies the sum of budgets; disjoint parallel reasoning is inapplicable. The displayed theorem is an application of these established rules, not a new composition result. ◻

<a id="thm:sizeexact"></a>

### Statement 24: Exact-model size-weight optimality; thm:sizeexact

Let $\alpha\in\Delta_K$, let $P_R=\sum_i\alpha_iP_i$ be the declared target and suppose the released generators satisfy $Q_i=P_i$ for every client. Then $w=\alpha$ globally minimizes both $\operatorname{KL}(P_R\|Q_w)$ and $d_\mathcal Q(P_R,Q_w)$, with minimum zero, where $Q_w=\sum_iw_iQ_i$. The KL minimizer is unique if the fixed component measures are affinely independent. Query-loss uniqueness requires affine independence of their query-answer vectors.

*Proof.* By the assumptions, $Q_\alpha=\sum_i\alpha_iQ_i=P_R$. Both discrepancies are nonnegative and vanish at equality. For KL, a second zero-loss mixture must equal $P_R$ as a measure. If the only coefficients $v$ satisfying $\sum_i v_i=0$ and $\sum_i v_iP_i=0$ are $v=0$, its weights must be $\alpha$. For a query matrix $B$, the corresponding condition is $\ker(B)\cap\{v:\mathbf 1^\top v=0\}=\{0\}$. ◻

For finite discrete models, expected negative log likelihood equals $H(P_R)+\operatorname{KL}(P_R\|Q_w)$ when well-defined, so the exact-model result is a population likelihood statement. A separate multinomial likelihood for independently sampled client labels is maximized by their empirical proportions; counts fixed by design do not establish that sampling model. Neither result asserts that $\alpha$ maximizes the observed-data mixture likelihood in a finite sample: for example, with exact Bernoulli components $Q_1=\mathrm{Bernoulli}(0.2)$, $Q_2=\mathrm{Bernoulli}(0.8)$ and $\alpha=(1/2,1/2)$, a single observed one has mixture likelihood $0.2w_1+0.8w_2$, maximized at $w=(0,1)$.

<a id="ex:sizefails"></a>

### Statement 25: Small local error can favour different weights; ex:sizefails

Let $P_1=\operatorname{Bernoulli}(0.2)$, $P_2=\operatorname{Bernoulli}(0.8)$ and $\alpha=(0.5,0.5)$. Their target is $\operatorname{Bernoulli}(0.5)$. Suppose $Q_1=\operatorname{Bernoulli}(0.3)$ and $Q_2=P_2$. Size weighting gives probability 0.55 of one and error 0.05 for $q(z)=z$. Weights $w=(0.6,0.4)$ give probability 0.5 and zero error. They satisfy $\left\lVert w-\alpha\right\rVert_1=0.2\le0.25$ and $w_i\ge0.5\alpha_i$. The same alternative achieves zero KL, while size weighting gives approximately 0.005025. Hence unrestricted optimality of size weights for imperfect models is false, even within the retained constraints.

<a id="thm:sizenear"></a>

### Statement 26: Approximate size optimality and weight localization; thm:sizenear

Define $e_i=\left\lVert H_{\cdot i}-B_{\cdot i}\right\rVert_\infty$, $e_\alpha=\sum_i\alpha_i e_i$, and $e_{\max}=\max_i e_i$. Let $\mathcal W$ be a closed subset of the simplex containing $\alpha$, and let $w^*$ minimize $L_R(w)=\left\lVert Hw-B\alpha\right\rVert_\infty$ over $\mathcal W$. Then

$$
0\le L_R(\alpha)-L_R(w^*)\le e_\alpha.
$$

If, additionally, a constant $c>0$ satisfies

$$
\left\lVert Bv\right\rVert_\infty\ge c\left\lVert v\right\rVert_1\quad\text{whenever }\mathbf 1^\top v=0,
$$

then

$$
\left\lVert w^*-\alpha\right\rVert_1\le\frac{e_\alpha+e_{\max}}{c}.$$

*Proof.* Since $b_R=B\alpha$, convexity of the norm gives $L_R(\alpha)=\left\lVert(H-B)\alpha\right\rVert_\infty\le e_\alpha$. The first bound follows from optimality and nonnegativity. For any simplex $w$,

$$
\begin{aligned}
L_R(w)&=\left\lVert B(w-\alpha)+(H-B)w\right\rVert_\infty\\
&\ge c\left\lVert w-\alpha\right\rVert_1-e_{\max}.
\end{aligned}
$$

Use $L_R(w^*)\le L_R(\alpha)\le e_\alpha$ and rearrange. ◻

<a id="thm:sizedual"></a>

### Statement 27: A sufficient query-loss certificate; thm:sizedual

Let $r=H\alpha-b_R$ and $t=\left\lVert r\right\rVert_\infty>0$. Let $\mathcal A=\{\ell:|r_\ell|=t\}$. Suppose there are $\lambda_\ell\ge0$ summing to one over $\mathcal A$ such that $s_\ell=\lambda_\ell\operatorname{sign}(r_\ell)$ for $\ell\in\mathcal A$, $s_\ell=0$ otherwise, and $H^\top s=\nu\mathbf 1$ for a scalar $\nu$. Then $\alpha$ is a global minimizer of $\left\lVert Hw-b_R\right\rVert_\infty$ over the entire simplex, and therefore over any feasible subset containing it. If $t=0$, optimality already follows from nonnegativity.

*Proof.* We have $\left\lVert s\right\rVert_1=1$ and $s^\top r=t$. For any simplex vector $w$, norm duality and the zero-sum constraint give

$$
\begin{aligned}
\left\lVert Hw-b_R\right\rVert_\infty
&\ge s^\top(Hw-b_R)\\
&=s^\top r+\nu\mathbf 1^\top(w-\alpha)=t.
\end{aligned}
$$

Size weights attain this lower bound. ◻

