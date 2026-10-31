# Achieved client partitions, seed 101 (development only)

All clients retain the same 15 Adult columns. The TRAIN-fitted assignment
rule is unchanged on local tune, calibration, selection validation and
independent development assessment. The official Adult test was not scored.
The tables below summarize one split seed; complete row IDs, client counts,
category coverage, per-client prevalence and marginal differences are in
`reports/partition_audit_20261024/`, `reports/partition_skew_20261024/` and
`reports/partition_k10_20261024/`.

| K | Assignment | TRAIN rows/client range | High-income prevalence/client range | Smallest assessment client | Smallest assessment positive count |
|---:|---|---:|---:|---:|---:|
| 5 | age | 3,556?4,781 | 9.1%?33.1% | 264 | 26 |
| 5 | age + education | 2,605?5,563 | 8.4%?38.4% | 222 | 23 |
| 5 | label skew | 1,031?7,090 | 1.5%?66.5% | 70 | 2 |
| 10 | age | 1,122?3,482 | 13.1%?30.0% | 97 | 13 |
| 10 | age + education | 1,234?2,668 | 8.3%?39.1% | 98 | 8 |
| 10 | label skew | 227?5,364 | 1.1%?60.8% | 18 | 3 |

The smallest K=10 label-skew assessment client is only 18 rows. Client-level
probability metrics and rare conjunctions in that cell have high sampling
uncertainty. We did not rebalance it or fabricate examples. Across K=10
label-skew training clients, 17?41 of the 43 declared native-country
categories occur; absent categories remain in the fixed public vocabulary.
The CSV audits report category coverage and categorical TV from each pooled
split for every client, rather than assuming the requested skew was achieved.
