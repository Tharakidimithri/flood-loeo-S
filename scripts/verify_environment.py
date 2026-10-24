import importlib
import json
import platform
from pathlib import Path

packages = ['torch','torchvision','segmentation_models_pytorch','rasterio','numpy','pandas','skimage','pytest']
report = {'python':platform.python_version(), 'packages':{}}
failed = False
for name in packages:
    try:
        module = importlib.import_module(name)
        report['packages'][name] = getattr(module, '__version__', 'unknown')
    except Exception as exc:
        report['packages'][name] = {'error':str(exc)}
        failed = True
if isinstance(report['packages']['torch'], str):
    import torch
    report['cuda_available'] = torch.cuda.is_available()
    if report['cuda_available']:
        report['gpu'] = torch.cuda.get_device_name(0)
        report['cuda_smoke_test'] = float((torch.ones(4, device='cuda') * 2).sum())
    else:
        failed = True
root = Path(__file__).resolve().parents[1]
(root/'reports/environment.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
raise SystemExit(failed)
