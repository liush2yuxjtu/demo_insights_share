# Topic Walkthrough Log
Date: 2026-04-15

## Steps
1. Server started on port 7821 (tree mode)
2. Topic created: postgres-pool-exhaustion
3. Alice (good) + Bob (bad) examples published
4. Read verification: topics, good examples, bad examples
5. Relabel: bob changed from bad to good by admin
6. topic-show after relabel
7. raw_log files preserved (alice: jsonl, bob: txt)

## effective_label summary
...

## Notes
- alice-pgpool-2026-04-10: good, raw_log preserved as jsonl
- bob-pgpool-bad-2026-04-12: initially bad, relabeled to good by admin
- topic postgres-pool-exhaustion with tags: postgres, connection-pool
