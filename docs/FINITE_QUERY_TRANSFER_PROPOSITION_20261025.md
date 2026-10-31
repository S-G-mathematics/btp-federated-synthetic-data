# Finite-query conditional transfer: proposition and limits

**25 October 2026 local time.** This is an elementary deterministic fact about two fixed empirical measures. It is not a new population theorem or an estimate of continuous total variation.

Let R and S be probability measures (for this application, the alpha-standardized real development-assessment empirical measure and one generated dataset's empirical measure). Let A be a registered condition with `r=R(A)>0`, `s=S(A)>0`. For any declared query `q: Z -> [0,1]`, set `a=E_R[1_A q]` and `c=E_S[1_A q]`. Then

`|E_S[q|A] - E_R[q|A]| <= (|c-a| + |s-r|)/r`.

For a finite query list Q, if `epsilon_joint=max_q |E_S[1_A q]-E_R[1_A q]|` and `epsilon_mass=|s-r|`, then

`max_q |E_S[q|A]-E_R[q|A]| <= min(1,(epsilon_joint+epsilon_mass)/r)`.

**Proof.** Add and subtract `c/r` in `|c/s-a/r|`. The first term is `|c-a|/r`. The second is `c|r-s|/(rs)`, which is at most `|r-s|/r` because `0<=c<=s`. Both conditional expectations lie in `[0,1]`, giving the optional cap at one. This also proves the bound for bounded query functions, not only event indicators. If `s=0`, S's conditional is undefined and the route must abstain. A small positive `r` amplifies the joint and mass errors; no useful bound follows merely from support existing.

For the separately trained conditional student M, let T be a direct teacher conditional sample and R_A the real conditional reference on the **same query list**. Per query, `|M(q)-R_A(q)| <= |T(q)-R_A(q)| + |M(q)-T(q)|`. The second term is student approximation plus both routes' finite sampling noise, not a pure training error when T and M are independent samples. If a raw student produces condition A with probability `a>0` and only accepted rows are used, `|E_M q-E_M[q|A]| <= 1-a` for bounded q; this violation statement does not bound the accepted within-condition fidelity. Expected raw draws per accepted row are `1/a` under independent requests. A support gate must be reported separately.

**Counterexample to universal transfer.** Let X,Y be binary. Under R, put half the mass at `(X,Y)=(0,0)` and half at `(1,1)`. Under S, put half at `(0,1)` and half at `(1,0)`. The one-way query answers `P(X=1)` and `P(Y=1)` match exactly at 1/2, yet `P_R(Y=1|X=1)=1` and `P_S(Y=1|X=1)=0`. Thus matching one-way marginals cannot ensure the conditional query, and a predictor trained from S need not have small real predictive loss. More generally, a finite workload cannot certify every unlisted condition/query without additional structural assumptions.

The registered six-cell empirical audit in `docs/PROJECTED_TRANSFER_PROTOCOL_20261025.md` checks the ratio and student/direct triangle on observed development answers. Their truth as algebra does not imply that unknown population conditional errors are bounded by the observed numbers. No adaptive query search, privacy noise or official-test uncertainty is accounted for by this proposition.
