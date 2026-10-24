# flood-loeo

Python 3.11 project for Sentinel-1 flood segmentation.

The Python environment is `.venv`. VS Code is configured to use it.

## Environment setup

GPU PyTorch was installed from the official CUDA 12.8 wheel index:

```powershell
.\.venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Memory benchmark

```powershell
.\.venv\Scripts\python.exe memory_test.py
```

Tests batch size 1, two input channels, U-Net ResNet-18, AdamW, and binary cross entropy. Each configuration uses a fresh process, five warmup training steps and twenty timed steps. AMP is float16 with gradient scaling. Timings exclude disk loading and transfers. Results appear in reports/memory_test.csv and reports/memory_test.json. Allocated/reserved memory describes the PyTorch allocator, not all memory used by Windows and the GPU driver.

Dataset download and licence confirmation are separate steps; data/ is ignored by Git.

## Dataset download and audit

The full v1.1 data assets, official splits, event metadata and catalog archive total 36,314,158,380 bytes across 21,405 objects in the inventory retrieved on 2026-10-22. Pretrained checkpoints and redundant unpacked STAC objects are excluded.

The current download runs in the background. Open reports/download-status.json for progress. Do not launch another downloader concurrently.

After interruption, resume with:

```powershell
.\.venv\Scripts\python.exe -u scripts/download_sen1floods11.py
```

Per-file GCS MD5 verification and SHA-256 recording occur during download. Download completion automatically triggers the raster/split audit. The manifest is complete only when the status reports complete with zero failures. See metadata/dataset_status.md for provenance and verification commands, reports/dataset_audit.md for the official split audit, and metadata/LICENSE_DATASET.md for licence evidence.

The official source and annotation collections declare proprietary; specific usage permissions have not been confirmed. Do not describe this dataset as CC BY based on third-party mirrors.

See reports/compute_plan.md for the measured baseline and initial compute choice.
