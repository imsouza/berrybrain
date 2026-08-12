# External Evidence Register

This register lists work that repository code cannot truthfully complete by itself. These items are
not software defects and must not be marked complete without the named artifact.

| ID | Requirement | Completion artifact | Owner/dependency | Current state |
| --- | --- | --- | --- | --- |
| EXT-001 | Final thesis theme and primary outcome | Supervisor-approved research proposal | Student and supervisor | Open |
| EXT-002 | Confirmatory preregistration | Timestamped protocol with frozen hypotheses, exclusions, and analysis | Research team | Open |
| EXT-003 | Ethics/LGPD approval or exemption | Institutional decision and approved consent/privacy materials | Institution | Open |
| EXT-004 | BEIR payload | Verified files, per-subset license, split, and SHA-256 | Upstream dataset/operator | Not installed |
| EXT-005 | HotpotQA payload | Verified official data and sampled-subset manifest | Upstream dataset/operator | Not installed |
| EXT-006 | MuSiQue payload | Verified official data and sampled-subset manifest | Upstream dataset/operator | Not installed |
| EXT-007 | Curated personal-knowledge set | Consented, de-identified corpus with qrels and gold graph | Reviewers and participants | Open |
| EXT-008 | Dual human annotation | Blinded labels, adjudication ledger, and agreement report | Two reviewers plus adjudicator | Open |
| EXT-009 | Participant power analysis | Frozen smallest effect of interest and sample-size calculation | Research team/statistical review | Open |
| EXT-010 | Participant task study | Consented anonymized observations and preregistered analysis | Participants and researchers | Open |
| EXT-011 | Longitudinal field evidence | Approved opt-in protocol and retained aggregate outcomes | Participants/operator | Open |
| EXT-012 | Independent replication | Third-party environment manifest, deviations, raw bundle, and report | Independent evaluator | Open |
| EXT-013 | Clean confirmatory revision | Clean git revision with immutable dataset/model/image digests | Release owner | Open until publication approval |
| EXT-014 | Publication authorization | Explicit owner approval for commit, tag, push, and main release | Repository owner | Withheld |

## Rules

- Missing external data remains missing; synthetic fixtures cannot replace it.
- No private-vault or participant collection begins before EXT-003.
- Pilot outcomes cannot enter confirmatory analysis.
- A clean confirmatory rerun must use frozen thresholds and retain failures.
- Commit, tag, push, and main publication remain prohibited until EXT-014 is explicitly granted.
