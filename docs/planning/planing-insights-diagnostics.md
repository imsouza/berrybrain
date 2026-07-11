# BerryBrain Insights vs Diagnostics Plan

## Goal

Keep BerryBrain Knowledge Insights focused on learning and cognition, while moving operational/system information to diagnostics surfaces.

## Separation Rules

| Area | Goes to | Must contain | Must not contain |
|---|---|---|---|
| Knowledge Insights | Home, `/insights`, note panel, graph | concepts, gaps, context, conclusions, hypotheses, connections, study actions, graph impact | jobs, queues, providers, workers, backlog, pipeline status, raw JSON, internal keys |
| System Diagnostics | Monitor, Activity, Needs attention | jobs, queue, worker, provider, errors, backlog, pipeline health | learning conclusions or graph knowledge claims |

## Implemented

- Prompt now explicitly separates Knowledge Insights from System Diagnostics.
- Worker now sends only knowledge evidence to the insight prompt.
- API rejects system diagnostics and internal technical terms from `/insights/sync`.
- Existing technical insights are hidden from Home and `/insights`.
- Technical insights are blocked from becoming graph insight nodes.
- Graph evidence is humanized in the details panel.
- `/insights` shows raw evidence only inside collapsed `Technical details`.
- Graph connection copy now says `Connection reason` unless the edge is an actual insight edge.
- Note side panel evidence is humanized and action labels stay in English.

## Remaining Follow-up

- Add a dedicated diagnostics feed/table if Monitor needs persistent diagnostic cards.
- Add migration/cleanup command to archive old technical insights already stored in the database.
- Add tests for diagnostic rejection and evidence humanization.
