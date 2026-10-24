"""Create or verify a SHA-256 manifest for an existing data directory."""
import argparse
import csv
import hashlib
from pathlib import Path

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest.resolve()
    if not root.is_dir():
        parser.error('Dataset directory does not exist')
    if manifest.is_relative_to(root):
        parser.error('Save the manifest outside the dataset directory')
    actual = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    if not actual:
        parser.error('Dataset directory is empty')
    if args.verify:
        with manifest.open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        expected = {r['path']: r for r in rows}
        problems = []
        for name, row in expected.items():
            if name not in actual:
                problems.append('Missing: '+name)
            elif actual[name].stat().st_size != int(row['bytes']) or digest(actual[name]) != row['sha256']:
                problems.append('Changed: '+name)
        problems.extend('Unexpected: '+name for name in actual.keys()-expected.keys())
        print('\n'.join(problems) if problems else f'Verified {len(rows)} files')
        raise SystemExit(bool(problems))
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['path','bytes','sha256'])
        writer.writeheader()
        for name, path in sorted(actual.items()):
            writer.writerow(dict(path=name, bytes=path.stat().st_size, sha256=digest(path)))
    print(f'Hashed {len(actual)} files')

if __name__ == '__main__':
    main()
