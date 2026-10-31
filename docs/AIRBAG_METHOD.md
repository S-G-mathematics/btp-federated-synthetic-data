# Airbag Method for this BTP

Source skill: `/home/ubuntu/research-problem-1/rp1-cfo-harbor/.agents/skills/airbag-method/SKILL.md` and its project policy. This is the BTP-specific application, without importing RP1 benchmark rules.

- PAST: inspect actual commands, hashes, tests, logs, access boundaries, and scientific claims.
- PRESENT: run one bounded EC2 compute lane, checkpoint and inspect failures before scaling.
- FUTURE: prepare the next experiment requirements and scientific gates from `docs/EXPERIMENTS_12.md`.
- All substantive work and any worker run on the verified EC2 host. At most three focused workers, only confirmed Luna or Terra models; independent file ownership for edits. If a worker sandbox cannot run, record the failure and continue verified coordinator work.
- Preserve official test until the campaign-wide development selection is frozen. Never treat smoke completion as scientific completion or infer a result from a worker self-report.
- Record verified evidence in `STATUS.md`, `TASK_BOARD.md`, `DECISIONS.md`, `docs/WORKER_ASSIGNMENTS.md`, and `docs/AIRBAG_MONITOR.md`.
