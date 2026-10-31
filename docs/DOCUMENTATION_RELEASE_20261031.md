# Documentation and theory release — 31 October 2026

This update makes the completed bounded study easier to inspect. Its base is repository commit `7e139abadb6aea3f44feba9e68869d9ee5887ea8`. It adds no fitted model, synthetic draw, test evaluation or selection decision.

## Changes

- The root README now states the finite-table objective, target masses, three evidence stages, headline paired differences and contribution boundaries.
- Every experiment guide states its research question, actual bounded setup, observed result, limitations and paths to saved evidence.
- A standalone proof supplement gives 27 labeled statements (24 proofs and three counterexamples). It preserves the report's statement IDs and clarifies sampling, conditioning, loss and privacy assumptions. It distinguishes exact-model size optimality, client-label MLE, finite observed-data mixture MLE, approximate optimality and a sufficient dual certificate.
- The 29-item historical theory index maps later conditional proofs without rewriting their earlier chronology or claiming empirical verification of their premises.
- The dated MA4998P and IEEE drafts are imported with editable source archives. They remain drafts; the latest proof qualifications are separately documented for reconciliation during editing.
- The lightweight CI additionally checks theory-example arithmetic and the writing-release manifest. It continues to check original source hashes, immutable selection, saved evidence, regenerated figures/tables and the scientific test suite.

## Protected experimental record

The selection SHA-256 remains `2420f737b6af732925f9cce3fbb82c8a9a7a30e1988dde5e68900d1404bb3a23`. The original full archive remains identified by SHA-256 `b184b0b07d3185ca7bd95322fd7bf432b28293b1041f5cae5cc9153ead25b2bf` and 537,318,039 bytes. Original source-map entries, protocols and results retain their content. The new writing artifacts have their own [manifest](../provenance/documentation_release_20261031.json).

## Verification scope

The proof source compiles with two LaTeX passes; the compiled pages were reviewed for layout. Python arithmetic checks cover the numerical size-weight counterexample, a dual-certificate instance and sharpness of the representation bound. The documentation check validates artifact hashes, statement IDs, historical mappings and local link targets. These checks do not constitute automated theorem proving.

CI validation is reported by the workflow on the final commit. Earlier packaging logs remain historical evidence. No training campaign is rerun for this documentation release. Current scientific claims remain tied to the original saved experimental records; the additional theory is post-experiment analysis.

## Remaining human review

Author/supervisor details, signatures and institutional declarations require confirmation. A supervisor must review the mathematical assumptions and writing; an authorized similarity check has not been performed here. Neither publication readiness nor Turnitin scores follow from passing repository CI.
