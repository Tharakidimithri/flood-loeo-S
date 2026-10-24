# Compute plan

Measured on the NVIDIA GeForce RTX 3050 Laptop GPU (4095.5 MiB), Python 3.11.9, PyTorch 2.11.0+cu128. Model: U-Net with ResNet-18, two input channels, one output logit, no pretrained weights. Total/trainable parameters: 14,325,073. Batch size: 1. AdamW with BCEWithLogitsLoss. Each case runs in a fresh process with 5 warmup and 20 timed full training steps.

| Size | Precision | Peak allocated MiB | Peak reserved MiB | Median step ms | p95 step ms |
|---|---|---:|---:|---:|---:|
| 512 | FP32 | 523.6 | 596.0 | 66.4 | 99.2 |
| 512 | AMP FP16 | 394.1 | 418.0 | 121.8 | 173.5 |
| 256 | FP32 | 281.5 | 316.0 | 50.4 | 58.2 |
| 256 | AMP FP16 | 278.8 | 318.0 | 99.3 | 249.1 |

Initial choice: 512 x 512, batch size 1, FP32. It retains native chip dimensions, fits the measured memory budget and was faster than AMP in this small benchmark. AMP at 512 reduced peak allocated memory by about 25% but did not improve latency. Keep AMP as an option if larger batches require it; do not assume it is faster on this machine.

These are synthetic repeated-batch measurements, not end-to-end training estimates. GPU allocator peaks exclude driver and other application memory. Test a real-data training/validation epoch with invalid pixels masked, then increase batch size gradually while leaving 20-30% total GPU headroom. Do not estimate the entire LOEO experiment from this one-batch benchmark. Confirm gradient finiteness and AMP update behaviour before adopting AMP for training.
