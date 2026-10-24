"""Benchmark full U-Net training steps; each case runs in a fresh process."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent

def worker(size, precision, cfg):
    import numpy as np
    import torch
    import segmentation_models_pytorch as smp
    row = dict(size=size, precision=precision, batch_size=cfg['batch_size'])
    try:
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA GPU is unavailable')
        torch.manual_seed(cfg['seed'])
        device = torch.device('cuda')
        props = torch.cuda.get_device_properties(0)
        row.update(gpu=props.name, total_gpu_mib=props.total_memory/2**20,
                   torch_version=torch.__version__, cuda_version=torch.version.cuda)
        model = smp.Unet(encoder_name='resnet18', encoder_weights=None,
                         in_channels=2, classes=1).to(device).train()
        row['total_parameters'] = sum(p.numel() for p in model.parameters())
        row['trainable_parameters'] = sum(p.numel() for p in model.parameters() if p.requires_grad)
        x = torch.randn(cfg['batch_size'], 2, size, size, device=device)
        y = torch.randint(0, 2, (cfg['batch_size'], 1, size, size), device=device).float()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        criterion = torch.nn.BCEWithLogitsLoss()
        amp = precision == 'amp_fp16'
        scaler = torch.amp.GradScaler('cuda', enabled=amp)
        def step():
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast('cuda', dtype=torch.float16, enabled=amp):
                loss = criterion(model(x), y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            return loss.detach()
        for _ in range(cfg['warmup_steps']):
            step()
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        times = []
        losses = []
        for _ in range(cfg['measured_steps']):
            torch.cuda.synchronize()
            start = time.perf_counter()
            loss = step()
            torch.cuda.synchronize()
            times.append((time.perf_counter()-start)*1000)
            losses.append(float(loss))
        row.update(peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
                   peak_reserved_mib=torch.cuda.max_memory_reserved()/2**20,
                   median_step_ms=float(np.median(times)), p95_step_ms=float(np.percentile(times,95)),
                   status='ok' if np.isfinite(losses).all() else 'nonfinite_loss')
    except torch.OutOfMemoryError as exc:
        row.update(status='out_of_memory', error=str(exc))
    except Exception as exc:
        row.update(status='error', error=str(exc))
    return row

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int)
    parser.add_argument('--precision')
    args = parser.parse_args()
    cfg = json.loads((ROOT/'configs/memory_test.json').read_text(encoding='utf-8-sig'))
    if args.size:
        print(json.dumps(worker(args.size, args.precision, cfg)))
        return
    rows = []
    for size in cfg['sizes']:
        for precision in cfg['precisions']:
            print(f'Testing {size} x {size}, {precision}', flush=True)
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                '--size', str(size), '--precision', precision], capture_output=True, text=True)
            if result.returncode:
                row = dict(size=size, precision=precision, status='process_error', error=result.stderr)
            else:
                row = json.loads(result.stdout.strip().splitlines()[-1])
            rows.append(row)
            print(json.dumps(row), flush=True)
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/memory_test.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (ROOT/'reports/memory_test.csv').open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    if any(row['status'] not in ('ok','out_of_memory') for row in rows):
        sys.exit(1)

if __name__ == '__main__':
    main()
