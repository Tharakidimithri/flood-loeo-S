"""Download official v1.1 data, splits and catalog archive; verify GCS MD5 and record SHA-256."""
import base64, csv, hashlib, json, time, urllib.request, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'data/sen1floods11'
META = ROOT/'metadata'
STATUS = ROOT/'reports/download-status.json'
API = 'https://storage.googleapis.com/storage/v1/b/sen1floods11/o'

def status(**values):
    values['updated_utc'] = datetime.now(timezone.utc).isoformat()
    temp = STATUS.with_suffix('.tmp')
    for attempt in range(10):
        try:
            temp.write_text(json.dumps(values, indent=2), encoding='utf-8')
            temp.replace(STATUS)
            return
        except PermissionError:
            time.sleep(0.2 * (attempt + 1))
    print('Warning: progress file locked; continuing download', flush=True)

def fetch_json(url):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if attempt == 5: raise
            time.sleep(min(2**attempt, 15))

def inventory():
    objects = []
    for prefix in ['v1.1/data/', 'v1.1/splits/', 'v1.1/Sen1Floods11_Metadata.geojson', 'v1.1/catalog.zip']:
        token = None
        while True:
            params = dict(prefix=prefix, maxResults=1000, fields='nextPageToken,items(name,size,md5Hash,generation,updated)')
            if token: params['pageToken'] = token
            page = fetch_json(API+'?'+urllib.parse.urlencode(params))
            objects.extend(o for o in page.get('items',[]) if not o['name'].endswith('/'))
            token = page.get('nextPageToken')
            if not token: break
    return objects

def hashes(path):
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            sha.update(chunk); md5.update(chunk)
    return sha.hexdigest(), base64.b64encode(md5.digest()).decode()

def download(obj):
    name = obj['name']
    target = (DEST/name).resolve()
    if not target.is_relative_to(DEST.resolve()): raise ValueError('Unsafe object path')
    target.parent.mkdir(parents=True, exist_ok=True)
    size = int(obj['size'])
    if target.exists() and target.stat().st_size == size:
        sha, md5 = hashes(target)
        if md5 == obj.get('md5Hash'):
            return dict(path=name, bytes=size, sha256=sha, gcs_md5=md5, generation=obj['generation'])
    partial = target.with_suffix(target.suffix+'.part')
    url = 'https://storage.googleapis.com/sen1floods11/'+urllib.parse.quote(name, safe='/')+'?generation='+obj['generation']
    for attempt in range(8):
        try:
            offset = partial.stat().st_size if partial.exists() else 0
            if offset > size: partial.write_bytes(b''); offset=0
            if offset < size:
                request = urllib.request.Request(url, headers={'Range':f'bytes={offset}-'} if offset else {})
                with urllib.request.urlopen(request, timeout=90) as response:
                    append = offset > 0 and response.status == 206
                    if append and not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                        raise ValueError('Unexpected range response')
                    with partial.open('ab' if append else 'wb') as out:
                        while True:
                            chunk = response.read(1024*1024)
                            if not chunk: break
                            out.write(chunk)
            if partial.stat().st_size != size: raise ValueError('Incomplete download')
            sha, md5 = hashes(partial)
            if md5 != obj.get('md5Hash'):
                partial.write_bytes(b'')
                raise ValueError('GCS MD5 mismatch')
            partial.replace(target)
            return dict(path=name, bytes=size, sha256=sha, gcs_md5=md5, generation=obj['generation'])
        except Exception:
            if attempt == 7: raise
            time.sleep(min(2**attempt, 20))

def main():
    META.mkdir(exist_ok=True)
    status(state='inventory')
    saved = META/'download_inventory.json'
    objects = json.loads(saved.read_text(encoding='utf-8')) if saved.exists() else inventory()
    (META/'download_inventory.json').write_text(json.dumps(objects, indent=2), encoding='utf-8')
    # Fetch the small split and event metadata files first, then the hand-labelled benchmark.
    objects.sort(key=lambda o: (0 if '/splits/' in o['name'] or o['name'].endswith('.geojson') else 1 if '/HandLabeled/' in o['name'] else 2, o['name']))
    total_bytes = sum(int(o['size']) for o in objects)
    complete = completed_bytes = 0
    errors = []
    fields = ['path','bytes','sha256','gcs_md5','generation']
    with (META/'sen1floods11_sha256.csv').open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader(); out.flush()
        with ThreadPoolExecutor(max_workers=6) as pool:
            tasks = {pool.submit(download,o):o for o in objects}
            for future in as_completed(tasks):
                obj = tasks[future]
                try:
                    row = future.result(); writer.writerow(row); out.flush()
                    complete += 1; completed_bytes += row['bytes']
                except Exception as exc:
                    errors.append(dict(path=obj['name'], error=str(exc)))
                status(state='downloading', complete_files=complete, total_files=len(objects),
                       verified_bytes=completed_bytes, total_bytes=total_bytes, failed_files=len(errors))
                if complete % 100 == 0: print(f'{complete}/{len(objects)} files verified', flush=True)
    (META/'download_errors.json').write_text(json.dumps(errors, indent=2), encoding='utf-8')
    status(state='failed' if errors else 'complete', complete_files=complete, total_files=len(objects),
           verified_bytes=completed_bytes, total_bytes=total_bytes, failed_files=len(errors))
    if errors: raise SystemExit(1)
    import subprocess, sys
    audit = subprocess.run([sys.executable, str(ROOT/'scripts/audit_dataset.py')], check=False)
    status(state='complete', complete_files=complete, total_files=len(objects),
           verified_bytes=completed_bytes, total_bytes=total_bytes, failed_files=0,
           audit_status='complete' if audit.returncode == 0 else 'failed')
    if audit.returncode: raise SystemExit(audit.returncode)

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        status(state='failed', error=str(exc))
        raise
