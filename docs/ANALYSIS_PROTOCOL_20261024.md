# BTP development analysis protocol

**Fixed on:** 24 October 2026 UTC, after the seed101/202/303 copula and age-only Chow-Liu/GMM exploratory results, before the next age+education/label-skew replication. This is a dated **development protocol**, not a claim of prospective registration for earlier cells. Any change must receive a dated amendment before its affected results are inspected.

## Research question and estimand

Under a fixed client-population target and an explicit statistical release contract, when can weighting released non-neural generators improve empirical synthetic-data fidelity over sample-size weighting, and when should sample-size weighting be retained?

The primary real reference is **standardized to the training client masses** alpha_i = n_i / sum_j n_j. For a bounded query q and held-out client partitions D_{R,i}, the reference answer is

    q_R,alpha = sum_i alpha_i (1 / |D_{R,i}|) sum_{z in D_{R,i}} q(z).

The synthetic answer is the ordinary mean over exactly m generated rows. Primary loss is max_q |q_S - q_R,alpha| over the frozen public calibration workload in btp.evaluation.public_workloads. This is an empirical dataset comparison; it does not estimate population TV. The ordinary unweighted pooled held-out answer, whose client coefficients are their held-out counts, is a separately labeled **secondary estimand**. It must never silently replace the alpha-standardized primary reference. Adult fnlwgt is a modeled feature, not a survey analysis weight. A survey-weighted estimand would require a separate protocol.

For a method and size weighting evaluated in the same cell with matched synthetic seeds, define Delta = L_Q(method) - L_Q(size). Negative Delta favors the method. The unseen-interaction workload is a **predeclared development audit**: it is not fed into fitting, per-cell validation winner selection or posthoc workload revision. Its registered global guardrail may reject a candidate; after that decision it is no longer independent confirmation. Only the locked official test can serve as the later Adult confirmation reference. All methods use the same training, tune, calibration, selection-validation and development-assessment partitions within a cell. Model checkpoints and pilot matrices stay fixed across methods.

## Access and comparison contract

- Primary deployable research track: released local checkpoints, declared client counts/public schema, synthetic pilots, and permitted aggregate calibration query/covariance/kernel means. These unnoised releases are **nonprivate**. Size and uniform need less access; access differences remain visible.
- Privileged score track: F1/F2/F3 use per-record real calibration candidate scores inside the evaluator. Report separately. They cannot establish an equal-access server advantage until an aggregate objective/gradient protocol and release ledger exist.
- Operator track: finite-support logpool and entropic barycenter are different aggregation operators. Compare against same-support best-found references, and never use the linear-mixture LP as a global operator oracle.
- Diagnostic reference: a pooled real-data non-neural model, if implemented, remains evaluator-privileged and outside the deployable ranking.
- Preserve every failed fit/timeout in the manifest. A failed method does not receive a fabricated fallback score. No invalid tiny client is rebalanced.

## Frozen development workload and candidate policy

The primary query workload, unseen audit workload, public schema and pilot/full profile settings are the current committed definitions in btp.evaluation, btp.privacy and configs/campaign.yaml. A change to them requires a new comparable run root or an explicit bridge analysis. The current pilot comparison has m=10,000 and three independent synthetic draws per assessment cell. **Final development comparisons require at least five draws** from the same frozen model checkpoints and exact largest-remainder counts. Synthetic draws measure Monte Carlo variation, not independent data cohorts.

Size weighting is the mandatory primary baseline. Unconstrained moment, query, entropy, GLS, KMM and robust methods remain diagnostic candidates. The prospective fixed-target candidate for the next representation analysis is a query-minimax mixture constrained to

    w >= 0, sum_i w_i = 1,
    sum_i |w_i - alpha_i| <= 0.25,
    w_i >= 0.5 alpha_i for every client i.

These numerical bounds are **provisional application tolerances fixed before the next skew replication is analyzed**. They allow limited correction while guaranteeing at least half of each declared client contribution. They are not theorem-derived privacy or subgroup guarantees. The already explored delta grid was postpilot development work. The unconstrained fit and the delta frontier remain comparators, not automatic selection choices. If the constrained rule cannot produce a practical gain, retain size weighting. Pure client-weight bounds do not guarantee observable subgroup coverage; measure that separately.

For any fixed empirical H whose entries lie in [0,1], the elementary bound ||H(w-alpha)||_infinity <= 0.5 ||w-alpha||_1 quantifies the largest query change attributable solely to reweighting. It does **not** bound generator error or prove subgroup fidelity.

## Development decision rules

The practical improvement margin is an **absolute 0.005** reduction in primary query maximum relative to tuned size weighting. This is a decision margin to be checked against observed sampling variation, not a p-value or a universal standard. Report the paired Delta for every generator × partition × K × split seed, plus fixed-pilot oracle headroom and the calibration-to-audit gap. Aggregate cells by declared slice and split seed; do not treat three/five synthetic draws or overlapping Adult split seeds as independent cohorts. Report the mean and the full per-seed range. A conclusion that depends on one split seed is inconclusive.

A candidate may advance only if:

1. Its declared alpha-shift and per-client floor satisfy the fixed constraints above; also report effective client count, min w_i/alpha_i and near-zero client weights.
2. Its registered unseen-audit query maximum does not worsen by more than 0.005 versus size in the same cell on average across the three development split seeds, and no slice is hidden. This is a guardrail, not a target for fitting.
3. Its schema validity is complete and structural zero atoms/education relationships have no unexplained dominant defect.
4. Where downstream utility is evaluated with matched synthetic sample and same learner, target-weighted AUROC is no more than 0.01 below the size-weighted synthetic baseline; TRTR is a separate privileged reference. Rare-client intervals remain explicit.
5. Conditional requests use the teacher-only registered support gate and abstain when unsupported. The current seed101 revision requires evaluation on later seeds.
6. Its release ledger accurately labels all fitted models, summaries, scores and repeated settings. No whole-pipeline DP claim is permitted for the current unnoised releases.

The main global development comparison will consider tuned size, the fixed constrained calibration rule, and at most one additional viable release-only candidate chosen by a dated rule before final confirmation. A campaign-wide choice must use development validation across registered cells and the above guardrails. Existing development-assessment results have already influenced research design; they are exploratory and cannot be relabeled as independent confirmation. No per-cell validation winner is automatically a global method.

## Matrix, replication and freeze gate

The core matched matrix is copula, Chow-Liu and mixed GMM × age, age+education and label skew × K=5/10 × development seeds101/202/303 = 54 cells. Reuse requires matching dataset/split, generator tuning grid, preprocessing, workload, solver/evaluation code and profile; audit the corresponding hashes and selected tuning parameters. The immediate missing age+education/label-skew Chow-Liu/GMM seeds202/303 batch has 16 cells. A resource-limited reduction must be documented before inspecting those outcomes. The six latent-class and six independent seed202 cells are challenger/negative-control screens, not a substitute for the matched core.

After the complete viable development comparison, freeze generator, preprocessing, local tuning rule, weighting rule, representation budget, workload, m, sample seeds, conditional support policy and registered baselines in campaign-wide SELECTION_FROZEN.json, including code/config hashes, all alternatives considered, timestamp and test_used_for_selection:false. Official Adult test and confirmation seeds404/505 remain locked until then. Those seeds reuse Adult people and are not external-dataset replication. If no constrained method meets the practical/guardrail requirements, record “no improved weighting method established” and keep size weighting as the final procedure.

## Evidence required for each reported claim

Every cell must point to configuration.json (reference role and code hash), partition_manifest.csv, workload and profile, selected local tuning/checkpoint, weight_fits.json with solver status, synthetic seed/count, primary/audit query-answer files, model/summary bytes and execution log. Paired analyses must retain failed and null rows. Claims about exact scores, oracle optimality, conditional generalization, formal privacy and novelty require their separate stated assumptions and evidence.

## Postpilot structural-diagnostic amendment (24 October 2026, after inspecting the 54-cell core)

A subsequent TRAIN-based evaluator audit found that the official Adult education category and education-number field have a deterministic mapping in the real training split, while current generators often emit mismatched pairs. The registered primary and unseen audit workloads do not directly query that relation. A new education-number mapping projection is therefore a **postpilot ablation**, not part of the earlier prospective core rule. Its first cell changed the relation mismatch dramatically but did not change the primary or audit query maximum. This is a workload blind spot, not evidence that the defect is unimportant.

The mapping is fixed in scripts/education_projection_ablation.py and verified against development TRAIN only; synthetic education='?' is left unprojected and counted unsupported. Raw and projected samples use identical model checkpoints, weights, row counts and sampling seeds. The projected output has no exact joint log-score claim even when its underlying unprojected model had one. The first trial that failed on unmapped '?' rows remains in the original failure directory. Full projection outcomes must be reported as exploratory, then a revised structural support policy and workload must be fixed before any future confirmation run. No historical primary result is silently relabeled.
