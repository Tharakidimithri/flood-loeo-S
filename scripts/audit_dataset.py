"""Audit official hand-labelled split membership and, when present, raster pairs."""
import csv, hashlib, itertools, json
from pathlib import Path
import numpy as np
import rasterio
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/sen1floods11/v1.1'

def main():
    splits = {}
    details = {}
    errors = []
    for name in ['train','valid','test','bolivia']:
        path = DATA/f'splits/flood_handlabeled/flood_{name}_data.csv'
        with path.open(newline='', encoding='utf-8-sig') as stream:
            rows = list(csv.reader(stream))
        if any(len(r)!=2 for r in rows): raise ValueError(f'Malformed split {name}')
        ids = [r[0].removesuffix('_S1Hand.tif') for r in rows]
        if len(ids)!=len(set(ids)): errors.append(f'Duplicate chips in {name}')
        if any(r[1] != chip+'_LabelHand.tif' for r,chip in zip(rows,ids)):
            errors.append(f'Image/label name mismatch in {name}')
        splits[name] = set(ids)
        details[name] = dict(file=path.name, count=len(rows), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                             events={event:sum(chip.split('_')[0]==event for chip in ids) for event in sorted({chip.split('_')[0] for chip in ids})})
    overlaps = {a+' vs '+b:sorted(splits[a]&splits[b]) for a,b in itertools.combinations(splits,2)}
    if any(overlaps.values()): errors.append('Overlapping official splits')
    expected = set.union(*splits.values())
    missing = []
    audited = 0
    for chip in sorted(expected):
        image = DATA/f'data/flood_events/HandLabeled/S1Hand/{chip}_S1Hand.tif'
        label = DATA/f'data/flood_events/HandLabeled/LabelHand/{chip}_LabelHand.tif'
        if not image.exists() or not label.exists():
            missing.append(chip); continue
        try:
            with rasterio.open(image) as src, rasterio.open(label) as mask:
                if src.count != 2 or mask.count != 1: errors.append(f'Band count: {chip}')
                if (src.height,src.width)!=(512,512): errors.append(f'Image dimensions: {chip}')
                if (src.height,src.width,src.crs,src.transform)!=(mask.height,mask.width,mask.crs,mask.transform):
                    errors.append(f'Georeferencing mismatch: {chip}')
                values = set(np.unique(mask.read(1)).tolist())
                if not values <= {-1,0,1}: errors.append(f'Unexpected labels: {chip}: {values}')
            audited += 1
        except Exception as exc: errors.append(f'{chip}: {exc}')
    local = {p.name.removesuffix('_S1Hand.tif') for p in (DATA/'data/flood_events/HandLabeled/S1Hand').glob('*.tif')}
    result = dict(splits=details, overlaps=overlaps, unique_chips=len(expected), raster_pairs_audited=audited,
                  missing_raster_pairs=missing, unassigned_local_chips=sorted(local-expected), errors=errors,
                  status='failed' if errors else 'awaiting_download' if missing else 'complete')
    (ROOT/'reports/dataset_audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# Official split audit','', '| Split | Chips |','|---|---:|']
    lines += [f'| {name} | {item["count"]} |' for name,item in details.items()]
    lines += ['',f'Unique chips: {len(expected)}. Pairwise overlap: {sum(map(len,overlaps.values()))}.',
              f'Raster pairs audited: {audited}. Missing pairs: {len(missing)}. Errors: {len(errors)}.',
              '', 'The Bolivia split is separate from the standard train/validation/test files.',
              'These are upstream splits, not leave-one-event-out folds. Preserve them unchanged.',
              'For LOEO, hold out complete events and build separate fold manifests. Ignore label -1 in losses and metrics.',
              '', 'See dataset_audit.json for filenames, SHA-256, event counts and detailed checks.']
    (ROOT/'reports/dataset_audit.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['splits','missing_raster_pairs']}, indent=2))
    if errors: raise SystemExit(1)

if __name__ == '__main__': main()
