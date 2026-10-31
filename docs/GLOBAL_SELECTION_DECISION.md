# Global Adult generator selection decision

**25 October 2026, 04:30:39 UTC. Development validation only; official Adult test and seeds404/505 remain unscored.** The registered rule is in `docs/GLOBAL_SELECTION_RULE.md`. It selected **copula**, with size weights `w=alpha` exactly. The external challenger family is **Chow-Liu**, the lowest mean validation-loss alternative.

| Family | Mean of 18 cell means, five m=10,000 validation draws/cell | Median saved client-model bytes | Median sum of selected local-fit seconds | Selected |
| --- | ---: | ---: | ---: | --- |
| Copula | 0.029974733312622057 | 2,124,004 | 8.316761 | Yes |
| Chow-Liu | 0.031455472569221765 | 227,170 | 1.260895 | No |
| Mixed GMM | 0.051445647137699654 | 188,828 | 4.517454 | No |

Each saved first validation draw was regenerated and matched to `1e-10` before four new independent validation draws were scored. The 54 current projected checkpoint cells yielded 270 draw rows; three independent controls stayed outside the candidate set. The CSV SHA-256 is `df29cd7628a30ffb4809b77db2f82ece0200416bf6031411563ecdbe2351a29f`. Source checkpoint code hash is `25c89ff4971fa79be992e93f4c92d2ce51ab7d3368a569389a3118bd07b47868`. The selector took 213.2704 seconds on the verified EC2 in one native thread under the shared lease. Its first attempt failed after encountering the separate independent controls; that log is retained, and the corrected retry completed without omitting any registered core cell.

Evidence: `reports/completion_selection_20261025/global_generator_validation_draws.csv`, `global_generator_validation_cells.csv`, `global_generator_validation_selection.csv`, `decision.json`, and `logs/completion_selection_retry1_20261025.log`. The file `exp01_validation.csv` supplied only one original validation draw; this new table is the first five-draw global selection table. Assessment, viewed audit queries and test records were not selection inputs. Assessment-informed design choices preceding this rule remain disclosed; this is not a prospectively pure study from project inception.

Copula's score is approximate; it was not compared as a raw likelihood against Chow-Liu or GMM. This choice fixes a procedure for the remaining bounded studies; it does not assert absolute data quality, utility superiority or privacy. The main pipeline remains nonprivate. A full campaign-wide freeze still requires the external, mechanism, release and policy gates, and legacy official-test scoring is disabled until a dedicated confirmation path is validated.
