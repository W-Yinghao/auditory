"""Read local AVI headers/chunks and three frames without external decoders."""
import csv
import io
import json
import os
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

BASE = Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
os.umask(0o077)
out = BASE / 'results/video_001'; out.mkdir(exist_ok=False)
priv = BASE / 'private/video_001'; priv.mkdir(mode=0o700, exist_ok=False)
with (BASE / 'private/inventory_001/file_path_map.csv').open() as f:
    files = [r for r in csv.DictReader(f) if Path(r['absolute_path']).suffix.lower() == '.avi']
rows = []; errors = []; previews = []
for source in files:
    p = Path(source['absolute_path']); fid = source['file_id']
    row = {'file_id': fid}; rows.append(row)
    frames = []; headers = {}; stream_headers = []
    try:
        with p.open('rb') as f:
            def walk(start, end):
                pos = start
                while pos + 8 <= end:
                    f.seek(pos); tag, length = struct.unpack('<4sI', f.read(8))
                    body = pos + 8
                    if body + length > end:
                        raise ValueError('RIFF_chunk_exceeds_parent')
                    if tag in (b'RIFF', b'LIST'):
                        kind = f.read(4)
                        walk(body + 4, body + length)
                    elif tag in (b'avih', b'strh', b'strf'):
                        payload = f.read(length)
                        if tag == b'strh':
                            stream_headers.append({'strh': payload})
                        elif tag == b'strf' and stream_headers:
                            stream_headers[-1]['strf'] = payload
                        else:
                            headers[tag] = payload
                    elif tag[2:] in (b'db', b'dc'):
                        frames.append((tag, body, length))
                    pos = body + length + (length % 2)
            walk(0, p.stat().st_size)
            avih = headers[b'avih']
            us, _, _, _, total, _, streams, _, width, height = struct.unpack('<10I', avih[:40])
            video_stream = next(i for i, h in enumerate(stream_headers) if h['strh'][:4] == b'vids')
            h = stream_headers[video_stream]
            scale, rate, start, length = struct.unpack_from('<4I', h['strh'], 20)
            fmt = h['strf']; _, bw, bh, planes, bits = struct.unpack_from('<IiiHH', fmt)
            codec = fmt[16:20]
            row.update(width=width, height=height, nominal_frames=total, stream_count=streams,
                       frame_rate=(rate / scale if scale else None),
                       duration_s=(length * scale / rate if rate else total * us / 1e6),
                       fourcc=codec.decode('ascii', errors='replace').replace('\x00', ''),
                       bits_per_pixel=bits)
            vf = [fr for fr in frames if fr[0][:2] == f'{video_stream:02d}'.encode()]
            row['observed_video_chunks'] = len(vf)
            decoded = 0
            for i, fraction in enumerate((0.1, 0.5, 0.9)):
                idx = min(len(vf) - 1, int((len(vf) - 1) * fraction))
                tag, offset, size = vf[idx]
                f.seek(offset); data = f.read(size)
                try:
                    if codec == b'\0\0\0\0' and bits in (24, 32):
                        stride = ((bw * bits + 31) // 32) * 4
                        frame = Image.frombytes('RGB', (bw, abs(bh)), data, 'raw',
                                                'BGR' if bits == 24 else 'BGRX',
                                                stride, -1 if bh > 0 else 1)
                    else:
                        frame = Image.open(io.BytesIO(data)).convert('RGB')
                    target = priv / f'{fid}_frame_{idx:06d}.png'
                    frame.save(target)
                    previews.append((f'{fid[:13]} frame {idx}', frame.copy()))
                    decoded += 1
                except Exception as exc:
                    errors.append({'file_id': fid, 'frame_index': idx, 'error': repr(exc)})
            row['sampled_frames_decoded'] = decoded
            row['scope'] = 'header_chunk_scan_and_sampled_frames_not_full_playback'
    except Exception as exc:
        row['scope'] = 'reader_failed'
        errors.append({'file_id': fid, 'error': repr(exc)})
if previews:
    sheet = Image.new('RGB', (1800, 450 * ((len(previews) + 2) // 3)), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, (name, frame) in enumerate(previews):
        x, y = i % 3 * 600, i // 3 * 450
        sheet.paste(ImageOps.contain(frame, (590, 420)), (x, y + 25))
        draw.text((x + 5, y + 5), name, fill='black')
    sheet.save(priv / 'contact.jpg', quality=92)
with (out / 'video_metadata.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
    w.writeheader(); w.writerows(rows)
(priv / 'errors.json').write_text(json.dumps(errors, indent=2))
(out / 'summary.json').write_text(json.dumps({'job_id': os.environ['SLURM_JOB_ID'],
    'files': len(rows), 'sampled_frames_decoded': len(previews), 'errors': len(errors)}, indent=2))
print((out / 'summary.json').read_text())
