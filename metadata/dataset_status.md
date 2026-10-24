# Dataset acquisition

Source: gs://sen1floods11/v1.1
Started: 2026-10-22 (Asia/Colombo).

Command: .\.venv\Scripts\python.exe -u scripts/download_sen1floods11.py

Scope: all objects under v1.1/data/ and v1.1/splits/, plus Sen1Floods11_Metadata.geojson and catalog.zip. This includes hand-labelled, weakly-labelled and permanent-water data. The catalog is retained as its published archive. Pretrained checkpoints and redundant unpacked catalog objects are excluded.

The downloader snapshots GCS object names, sizes, generations, upstream MD5 and update times in metadata/download_inventory.json. Requests pin object generation. Each completed file is checked against GCS MD5, then its SHA-256 is recorded in metadata/sen1floods11_sha256.csv. Manifest paths are relative to data/sen1floods11 (including v1.1/).

Progress: reports/download-status.json. Logs: reports/download.log and reports/download-errors.log. An incomplete manifest is not evidence of a complete dataset; require state=complete and zero failed files. The full raster audit runs after download completion, with its own status in reports/dataset_audit.json.

To resume after interruption, rerun the command after confirming no downloader is already running. Completed files are rechecked, partial files resume, and the manifest is rebuilt.

After completion, independently verify local SHA-256:

    .\.venv\Scripts\python.exe scripts/checksums.py data/sen1floods11 metadata/sen1floods11_sha256.csv --verify

Official hand-labelled CSVs are preserved unchanged under data/sen1floods11/v1.1/splits/flood_handlabeled/. They contain 252 train, 89 validation, 90 test and 15 Bolivia chips, with no overlaps. See reports/dataset_audit.json for their SHA-256 and event counts. They are not LOEO folds.

Licence declaration: proprietary in both official hand-labelled collections. Detailed usage permissions remain unresolved. See LICENSE_DATASET.md.
