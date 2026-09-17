"""Private contact sheets and video metadata for source-evidence review."""
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

BASE = Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
os.umask(0o077)
out = BASE / 'results/visual_review_001'; out.mkdir(exist_ok=False)
priv = BASE / 'private/visual_review_001'; priv.mkdir(mode=0o700, exist_ok=False)
with (BASE / 'private/inventory_001/file_path_map.csv').open() as f:
    source = {r['file_id']: Path(r['absolute_path']) for r in csv.DictReader(f)}
with (BASE / 'results/assets_001/visual_assets.csv').open() as f:
    assets = list(csv.DictReader(f))
unique = {}; rows = []; errors = []
ffprobe = shutil.which('ffprobe'); ffmpeg = shutil.which('ffmpeg')
frames = []
for a in assets:
    p = source[a['file_id']]
    if a['format'] == 'PNG':
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        unique.setdefault(digest, (a['file_id'], p))
        rows.append({'file_id': a['file_id'], 'sha256': digest,
                     'same_bytes_representative': unique[digest][0], 'format': 'PNG'})
    else:
        r = {'file_id': a['file_id'], 'format': 'AVI', 'review_scope': 'metadata_and_sampled_frames'}
        try:
            if not ffprobe or not ffmpeg:
                raise RuntimeError('ffmpeg_or_ffprobe_not_available')
            result = subprocess.run([ffprobe, '-v', 'error', '-show_format', '-show_streams',
                                     '-of', 'json', str(p)], capture_output=True, text=True,
                                    check=True, timeout=30)
            info = json.loads(result.stdout)
            (priv / (a['file_id'] + '_metadata.json')).write_text(result.stdout)
            vs = next(s for s in info['streams'] if s['codec_type'] == 'video')
            duration = float(info['format']['duration'])
            r.update(duration_s=duration, width=vs['width'], height=vs['height'],
                     codec=vs['codec_name'], frame_rate=vs['avg_frame_rate'])
            for n, fraction in enumerate((0.1, 0.5, 0.9)):
                target = priv / f'{a["file_id"]}_frame{n}.png'
                subprocess.run([ffmpeg, '-v', 'error', '-threads', '1', '-ss',
                                str(duration * fraction), '-i', str(p), '-frames:v', '1',
                                '-threads', '1', str(target)], capture_output=True, check=True, timeout=40)
                frames.append((f'{a["file_id"][:13]} @ {fraction:.0%}', target))
            r['sampled_frames'] = 3
        except Exception as exc:
            r['review_scope'] = 'metadata_or_frame_read_failed'
            errors.append({'file_id': a['file_id'], 'error': repr(exc)})
        rows.append(r)

entries = list(unique.values()) + frames
sheetmap = []
for start in range(0, len(entries), 9):
    selected = entries[start:start + 9]
    sheet = Image.new('RGB', (1800, 440 * math.ceil(len(selected) / 3)), 'white')
    draw = ImageDraw.Draw(sheet)
    sheetname = f'contact_{start // 9 + 1:02d}.jpg'
    for n, (fid, p) in enumerate(selected):
        with Image.open(p) as im:
            tile = ImageOps.contain(im.convert('RGB'), (590, 410))
        x, y = (n % 3) * 600, (n // 3) * 440
        sheet.paste(tile, (x, y + 25))
        draw.text((x + 5, y + 4), f'{start + n + 1:02d} {fid}', fill='black')
        sheetmap.append({'sheet': sheetname, 'tile': n + 1, 'asset_or_frame': fid})
    sheet.save(priv / sheetname, quality=92)

def table(path, data):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for row in data for k in row}))
        w.writeheader(); w.writerows(data)

table(out / 'asset_index.csv', rows)
table(priv / 'contact_sheet_index.csv', sheetmap)
(priv / 'errors.json').write_text(json.dumps(errors, indent=2))
(out / 'summary.json').write_text(json.dumps({
    'job_id': os.environ['SLURM_JOB_ID'], 'png_files': sum(a['format'] == 'PNG' for a in assets),
    'unique_png_byte_hashes': len(unique), 'video_files': sum(a['format'] == 'AVI' for a in assets),
    'video_sampled_frames': len(frames), 'contact_sheets': math.ceil(len(entries) / 9),
    'errors': len(errors), 'content_interpretation': 'See docs/visual_review.md after human-readable inspection'
}, indent=2))
print((out / 'summary.json').read_text())
