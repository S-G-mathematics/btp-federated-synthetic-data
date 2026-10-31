# Projected sample-size development findings — 24 October 2026 UTC

## Execution and evidence

The registered `docs/PROJECTED_SAMPLE_SIZE_PROTOCOL_20261024.md` ran on the existing EC2 under the shared heavy-compute lease, one worker and one native thread. It used the same six fixed-model cells and the same size/constrained weights as the secondary gate. Each method/cell had five draws at exactly 2,500 and 40,000 rows; the five compatible 10,000-row draws were reused from the existing constrained audit with source code, manifest, workload, row count and seed checks. All 6/6 cells completed, 30 observations per cell, zero failure files and zero invalid income labels. Per-cell evaluation wall times were 42.85–48.93 seconds; the six summed to about 275 seconds. At the final check, EC2 had about 29 GiB available RAM and 121 GiB free disk. The test suite remained at 76 passing tests.

Raw cell tables and config hashes: `results/projected_sample_size_20261024/`. Aggregate/paired tables: `reports/projected_sample_size_20261024/`; lightweight copies on the laptop under `reports/projected_sample_size_local_20261024/`. Execution logs: `logs/projected_sample_size_initial_20261024.log`, `logs/projected_sample_size_remaining_20261024.log`; tests: `logs/ec2_tests_projected_sample_size_20261024.log`. All real reference records are development assessment; official Adult test and seeds404/505 remain locked.

## Query error versus generated row count

| Fixed family (three overlapping split seeds) | Synthetic rows m | Size mean primary query max | Mean five-draw range for size primary max | Constrained mean primary query max | Paired constrained minus size primary max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Chow-Liu / age / K5 | 2,500 | 0.030461 | 0.009476 | 0.037755 | +0.007294 |
| Chow-Liu / age / K5 | 10,000 | 0.028363 | 0.004746 | 0.032989 | +0.004626 |
| Chow-Liu / age / K5 | 40,000 | 0.027961 | 0.002542 | 0.034673 | +0.006713 |
| Mixed GMM / label skew / K10 | 2,500 | 0.051413 | 0.015467 | 0.055364 | +0.003952 |
| Mixed GMM / label skew / K10 | 10,000 | 0.055305 | 0.011305 | 0.053559 | −0.001746 |
| Mixed GMM / label skew / K10 | 40,000 | 0.051658 | 0.003472 | 0.053149 | +0.001492 |

Positive paired differences are adverse for constrained weighting. The provisional −0.005 practical primary margin is unmet for both families at every reported m. At m=40,000, Chow-Liu's seed-level mean differences ranged +0.000510 to +0.010788; GMM's ranged −0.007119 to +0.013830. Mean within-seed five-draw range for size fell about 73% (Chow-Liu) and 78% (GMM) from m=2,500 to 40,000. The remaining mean error at 40,000 is empirical evidence of a finite-sample/model/workload floor over these tested sizes, not an estimated population lower bound. The same public seeds across m can yield overlapping random-stream prefixes; m levels and overlapping Adult split seeds are not independent cohorts.

The constrained rule's small GMM advantage at m=10,000 did not persist at m=40,000. This strengthens the **provisional fallback to tuned size weighting** for the fixed-alpha target. The six selected development cells do not prove size weighting always wins. Conditional support, repeated-pilot sensitivity and complete release/privacy/resource gates remain before a campaign-wide decision. No official-test evaluation, global freeze, full-pipeline DP or general superiority claim follows.
