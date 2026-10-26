# Official split audit

| Split | Chips |
|---|---:|
| train | 252 |
| valid | 89 |
| test | 90 |
| bolivia | 15 |

Unique chips: 446. Pairwise overlap: 0.
Raster pairs audited: 446. Missing pairs: 0. Errors: 0.

The Bolivia split is separate from the standard train/validation/test files.
These are upstream splits, not leave-one-event-out folds. Preserve them unchanged.
For LOEO, hold out complete events and build separate fold manifests. Ignore label -1 in losses and metrics.

See dataset_audit.json for filenames, SHA-256, event counts and detailed checks.
