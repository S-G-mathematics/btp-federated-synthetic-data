# Projected repeated-pilot development findings — 24 October 2026 UTC

## Execution and provenance

The registered `docs/PROJECTED_PILOT_SENSITIVITY_PROTOCOL_20261024.md` ran on the existing EC2 under the shared heavy-compute lease, one worker and one native thread. It used the same six Chow-Liu age/K5 and mixed-GMM label-skew/K10 development cells at split seeds101/202/303. All six saved 1,500-row/client source H matrices were **reproduced exactly** from the checkpoints and public seeds before analysis. The corrected run completed 6/6 cells with four pilot sizes (500, 1,500, 5,000 and 15,000 per client), five independent pilot seeds each, a disjoint 30,000-row/client finite synthetic H_ref and one fresh 10,000-row synthetic assessment draw per pilot fit. All constrained LP certificates succeeded; no corrected-run failure file exists. Six cell wall times ranged 125.10–169.46 seconds and summed to about 895 seconds. The suite passed 76 tests. At the final check EC2 had about 29 GiB available RAM and 121 GiB free disk.

Raw evidence: `results/projected_pilot_sensitivity_v2_20261024/<cell>/` stores fixed matrices, every fitted weight/certificate, fresh-sample metrics and config hashes. Aggregates: `reports/projected_pilot_sensitivity_v2_20261024/`; lightweight copies on the laptop: `reports/projected_pilot_sensitivity_local_20261024/`. Logs: `logs/projected_pilot_sensitivity_v2_initial_20261024.log`, `logs/projected_pilot_sensitivity_v2_remaining_20261024.log` and `logs/ec2_tests_projected_pilot_sensitivity_20261024.log`. The first attempt stopped at a tuple/list JSON workload comparison before scoring; its failure remains at `results/projected_pilot_sensitivity_20261024/<first-cell>/failure.json`, separate from this corrected root. No official Adult test or confirmation seed404/505 was used.

## Pilot size and decision sensitivity

| Fixed family, three overlapping split seeds | Pilot rows/client | Mean max H discrepancy vs finite H_ref | Mean same-target finite-H_ref LP excess | Mean fresh D_S primary query max, constrained minus size |
| --- | ---: | ---: | ---: | ---: |
| Chow-Liu age/K5 | 500 | 0.055407 | 0.003247 | +0.007153 |
| Chow-Liu age/K5 | 1,500 | 0.033276 | 0.003770 | +0.003376 |
| Chow-Liu age/K5 | 5,000 | 0.020778 | 0.001903 | +0.001183 |
| Chow-Liu age/K5 | 15,000 | 0.011480 | 0.000832 | +0.000262 |
| Mixed GMM label-skew/K10 | 500 | 0.064649 | 0.005328 | +0.002593 |
| Mixed GMM label-skew/K10 | 1,500 | 0.036260 | 0.001847 | +0.000984 |
| Mixed GMM label-skew/K10 | 5,000 | 0.021818 | 0.001316 | −0.000487 |
| Mixed GMM label-skew/K10 | 15,000 | 0.014229 | 0.000878 | +0.005894 |

The same-target excess compares each pilot-fitted constrained vector against a constrained LP on the independent finite H_ref **using the same released calibration vector b_cal**. It isolates sensitivity to the synthetic pilot conditional on that finite reference; it does not estimate population regret. Its mean decreased to below 0.001 at 15,000 rows/client for both families. Weight vectors could still shift: mean L1 distance from the original 1,500-row-pilot vector at 15,000 rows was 0.352724 Chow-Liu and 0.232146 GMM, consistent with an unstable/flat weight objective. The report also retains a fixed-H_ref **privileged validation LP** using real b_val. Its excess is not pure pilot error because the reference target and access change; it is not a deployable candidate or population oracle.

The fresh D_S assessment differences did not meet the registered practical **−0.005** three-seed mean improvement at any pilot size. At 15,000 rows/client, Chow-Liu's seed-level mean differences ranged −0.000907 to +0.001920, and GMM's ranged −0.005336 to +0.015530. The GMM 5,000-row pilot mean of −0.000487 is below the practical margin and reverses at 15,000. These fresh draws are paired by seed against size weighting, but the pilot replicates share fitted models and the three Adult split seeds share people. The real assessment is finite.

**Interpretation:** More pilot rows reduce the finite-H estimation discrepancy and same-target LP excess, but do not uncover a robust practical weighting gain in these selected development slices. Combined with the 54-cell primary matrix, subgroup/utility gate and sample-size check, tuned size weighting remains the provisional fixed-target fallback. Conditional support, repaired privacy baseline and full release/accounting limits remain open; no campaign-wide freeze, official-test result, full-pipeline DP claim or universal superiority/ineffectiveness claim follows.
