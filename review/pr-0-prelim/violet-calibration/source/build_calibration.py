#!/usr/bin/env python3
"""Build local PR 36 media and calibration page; never publish or change source."""
import argparse
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(os.environ.get('VIOLET_REPO', Path.cwd())).resolve()
SCRATCH = Path(__file__).resolve().parent
OUT = ROOT / 'out/review/pr-36'
ART = ROOT / 'assets/bakeoff/protagonist/glow-up'
ANIMS = ['idle', 'run', 'jump', 'fall', 'double_jump', 'dash', 'land']
LABELS = {a: a.replace('_', ' ').capitalize() for a in ANIMS}
BASE = 'https://github.com/sjawhar/project-violet'
SUMMARY = [
    'Original cutout rig. The air poses look similar, and the small face is hard to read.',
    'A larger eye lost its catchlight. Character appeal fell, so the change was reverted.',
    'The catchlight returned. The critic found no clear difference at review size.',
    'Darker robe folds and a closer match between the skirt and thigh wraps improved separation.',
    'Painted frames replaced cutout motion in all seven animations, giving the action poses more range.',
    'Darker body values and a more opaque scarf separated the figure from the gray background.',
    'Run and idle placement were steadied; the final fall pose was repainted. The calmer idle also lost some appeal.',
    'Dash and land grew from three to six drawings. Two faint double-jump scarf frames were repainted.',
    'Idle reused one painting per layer with a small procedural breath and scarf sway, removing much of the frame-to-frame flicker.',
    'Nine scarf layers were repainted for fabric texture and a consistent trailing side during landing.',
    'Idle gained a small chest rise, weight shift, head tilt and arm sway. The feet stay anchored. The six action animations are unchanged from round 9.',
]

def esc(value):
    return html.escape(str(value), quote=True)

def plain(value):
    return value.replace('**', '').replace('`', '')

def duration(seconds):
    minutes = round(seconds / 60)
    return f'{minutes // 60} h {minutes % 60:02d} min'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--page-only', action='store_true', help='Reuse existing preview media after metadata-only updates')
    parser.add_argument('--metadata', type=Path, default=SCRATCH / 'metadata.json')
    args = parser.parse_args()
    meta = json.loads(args.metadata.read_text())
    inputs = [ART / f'round-{r:02d}' / name for r in range(11)
              for name in ['contact-sheet.png', 'contact-sheet-ingame.png', *[a + '.gif' for a in ANIMS]]]
    inputs += [ART / 'trial-b' / name for name in ['run.gif', 'run-row.png', 'run-row-ingame.png']]
    inputs += [ART / 'attachment-fix' / name
               for name in ['contact-sheet.png', 'contact-sheet-ingame.png', *[a + '.gif' for a in ANIMS]]]
    if not args.page_only:
        if SCRATCH == OUT or OUT in SCRATCH.parents:
            parser.error('Copy this source directory outside out/review/pr-36 before rebuilding media; --page-only is safe in place.')
        env = {k: v for k, v in os.environ.items() if k not in ('UV_PROJECT_ENVIRONMENT', 'PYTHONPATH', 'VIRTUAL_ENV')}
        env.update(UV_PROJECT_ENVIRONMENT=str(SCRATCH / 'venv'), UV_CACHE_DIR=str(SCRATCH / 'uv-cache'), TMPDIR=str(SCRATCH), PYTHONDONTWRITEBYTECODE='1')
        command = ['mise', 'exec', '--', 'uv', 'run', '--frozen', '--project', str(ROOT / 'tools/preview'), 'preview', 'build', '36', *map(str, inputs)]
        subprocess.run(command, cwd=ROOT, env=env, check=True)
    manifest = json.loads((OUT / 'preview.json').read_text())
    assert len(manifest['items']) == len(inputs), 'Preview manifest does not match the requested calibration and correction inputs'
    media = {}
    for source, item in zip(inputs, manifest['items'], strict=True):
        assert item['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest(), f'Outdated preview: {source}'
        assert item['provenance']['status'] == 'ok', f'Provenance problem: {source}: {item["provenance"]}'
        item['source'] = str(source.relative_to(ROOT))
        if source.suffix == '.png':
            relative = Path('originals') / source.relative_to(ART)
            (OUT / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, OUT / relative)
            item['media']['original'] = relative.as_posix()
        media[str(source.relative_to(ART))] = item['media']
    (OUT / 'preview.json').write_text(json.dumps(manifest, indent=2) + '\n')
    rows = {}
    for line in (ART / 'rounds.md').read_text().splitlines():
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) == 10 and cells[0].isdigit():
            rows[int(cells[0])] = cells
    assert set(rows) == set(range(11)), 'All 11 round records are required'
    ref = meta['source_ref']
    source_root = f'{BASE}/blob/{ref}/assets/bakeoff/protagonist/glow-up'
    def source_link(path, label):
        return f'<a href="{esc(source_root + "/" + path)}">{esc(label)}</a>'
    def player(path, label, extra='', preload='none'):
        m = media[path]
        return f'<video src="{esc(m["video"])}" poster="{esc(m["poster"])}" aria-label="{esc(label)}" controls loop muted playsinline preload="{preload}" {extra}></video>'
    def sheet(round_number):
        full = media[f'round-{round_number:02d}/contact-sheet.png']
        game = media[f'round-{round_number:02d}/contact-sheet-ingame.png']
        return f'<a class="sheet" href="{esc(full["original"])}"><img src="{esc(full["image"])}" width="1840" height="2224" loading="lazy" alt="Round {round_number}: idle, run, jump, fall, double jump, dash and land contact sheet"></a><p class="links"><a href="{esc(full["original"])}">Full-resolution sheet</a><a href="{esc(game["original"])}">Game-size sheet</a></p>'
    final_status = meta['round10_status']
    final_verdict = meta['round10_verdict']
    cards = []
    score_rows = []
    for r, row in rows.items():
        start, end = (dt.datetime.fromisoformat(row[i].replace('Z', '+00:00')) for i in (1, 2))
        elapsed = (end - start).total_seconds()
        status = 'Original · kept' if r == 0 else 'Reverted' if r == 1 else final_status if r == 10 else 'Kept'
        scores = plain(row[7])
        verdict = final_verdict if r == 10 else plain(row[6])
        critic = source_link(f'round-{r:02d}/critic.md', 'Historical critic report') if r >= 3 else source_link('rounds.md', 'Historical critique in round record')
        if r == 10:
            critic = source_link('round-10/critic.md', 'Final critic report') if meta.get('round10_critic_ready') else '<span>Final critic report pending</span>'
        badge = 'reverted' if r == 1 else 'pending' if 'pending' in status.lower() else ''
        motions = ''.join(f'<figure><figcaption>{LABELS[a]}</figcaption>{player(f"round-{r:02d}/{a}.gif", f"Round {r} {LABELS[a]}")}<a href="{esc(media[f"round-{r:02d}/{a}.gif"]["gif"])}">GIF</a></figure>' for a in ANIMS)
        cards.append(f'''<article class="round" id="round-{r}"><header><h3>Round {r:02d}</h3><span class="badge {badge}">{esc(status)}</span></header><p class="round-description">{esc(SUMMARY[r])}</p>{sheet(r)}<details><summary>Motion, scores and critique</summary><div class="round-data"><p><strong>Per-comparison scores:</strong> {esc(scores)}</p><p><strong>Within-round verdict:</strong> {esc(verdict)}</p><p>{critic}</p><p class="muted">Scores are visual quality / character appeal / color readability. Letter mappings belong to that round only.</p><p><strong>Letter map:</strong> {esc(plain(row[5]))}</p><p><strong>Worker-reported window:</strong> {esc(row[1])} to {esc(row[2])} ({duration(elapsed)}). Not verified agent-hours.</p></div><div class="motion-grid">{motions}</div></details></article>''')
        score_rows.append(f'<tr><th scope="row">{r:02d}</th><td>{esc(status)}</td><td>{esc(scores)}</td><td>{esc(row[1])}<br>{esc(row[2])}</td><td>{duration(elapsed)}</td></tr>')
    pair_data = {a: [media[f'round-00/{a}.gif'], media[f'attachment-fix/{a}.gif']] for a in ANIMS}
    buttons = ''.join(f'<button type="button" class="animation-choice" data-animation="{a}" aria-pressed="{str(a == "idle").lower()}">{LABELS[a]}</button>' for a in ANIMS)
    initial = ''.join(
        f'<figure><figcaption>{label}</figcaption>{player(f"{prefix}/idle.gif", f"{label} idle", f"id=\"compare-{slot}\"", preload="metadata")}<p class="links"><a class="gif-link" href="{esc(media[f"{prefix}/idle.gif"]["gif"])}">Idle GIF</a><a href="{esc(media[f"{prefix}/contact-sheet.png"]["original"])}">Full-resolution sheet</a></p></figure>'
        for slot, prefix, label in [
            (0, 'round-00', 'Original · round 0'),
            (10, 'attachment-fix', 'Candidate · scarf attachment corrected'),
        ]
    )
    attachment_pairs = ''.join(
        f'<h3>{LABELS[a]}</h3><div class="comparison-grid"><figure><figcaption>Before · round 10</figcaption>{player(f"round-10/{a}.gif", f"Before attachment fix: {a}")}</figure><figure><figcaption>After · attached at the neck</figcaption>{player(f"attachment-fix/{a}.gif", f"After attachment fix: {a}")}</figure></div>'
        for a in ANIMS
    )
    environment = ''
    if meta.get('environment_url'):
        environment = f'''<section id="environments"><h2>The environment studies</h2><p>The world-art lanes are a separate comparison. Each completed ten rounds.</p><p><a class="primary-link" href="{esc(meta['environment_url'])}">Open environment progression</a></p><details><summary>Historical environment scores and generation costs</summary><p>These endpoint scores came from different historical critic sessions, not one calibrated comparison. The fresh Codex comparisons are listed separately below.</p><div class="table-wrap"><table><thead><tr><th>Lane</th><th>Original record</th><th>Final record</th><th>Image-generation cost</th></tr></thead><tbody><tr><th>Painted · G-A</th><td>2 / 3 / 3</td><td>3 / 3 / 4</td><td>$1.02 provider usage</td></tr><tr><th>3D · G-D</th><td>2 / 2 / 2</td><td>3 / 3 / 4</td><td>About $0.22 estimated</td></tr><tr><th>Vector · G-C</th><td>2 / 2 / 3</td><td>3 / 2 / 4</td><td>$0</td></tr></tbody></table></div><p>Scores are visual quality / character appeal / color readability, not human approval. The source records remain on the bake-off branches.</p></details></section>'''
    audits = ''
    if meta.get('endpoint_audits'):
        audit_rows = ''.join(
            f'<tr><th scope="row">{esc(a["comparison"])}</th><td>{esc(a["verdict"])}</td><td><a href="{esc(a["url"])}">Report</a></td></tr>'
            for a in meta['endpoint_audits']
        )
        audits = f'<details><summary>Fresh Codex endpoint checks</summary><p>These six checks revisit selected comparisons on verified openai-codex/gpt-6-astra. Scores are visual quality / character appeal / color readability, and each row is a separate comparison, not a calibrated trend. These checks do not replace or relabel the historical Claude sequence, and they are not human art approval.</p><div class="table-wrap"><table><thead><tr><th>Comparison</th><th>Finding</th><th>Source</th></tr></thead><tbody>{audit_rows}</tbody></table></div></details>'
    experiment_start = dt.datetime.fromisoformat(meta['experiment_start'].replace('Z', '+00:00'))
    experiment_end = dt.datetime.fromisoformat(meta['experiment_end'].replace('Z', '+00:00'))
    page = (SCRATCH / 'calibration-template.html').read_text()
    replacements = {
        'BUTTONS': buttons, 'INITIAL': initial, 'FINAL_STATUS': esc(final_status), 'FINAL_VERDICT': esc(final_verdict),
        'FINAL_MODEL': esc(meta['final_critic_model_note']), 'ROUND_CARDS': '\n'.join(cards), 'SCORE_ROWS': '\n'.join(score_rows),
        'ENVIRONMENT': environment, 'SOURCE_NOTE': esc(meta['source_note']),
        'ENDPOINT_AUDITS': audits,
        'ATTACHMENT_PAIRS': attachment_pairs,
        'ROUND_RECORD': source_link('rounds.md', 'Full round record'), 'TRIAL_RECORD': source_link('technique-trial.md', 'Technique-trial record'),
        'EXPERIMENT_TIME': duration((experiment_end - experiment_start).total_seconds()),
        'EXPERIMENT_START': esc(meta['experiment_start']), 'EXPERIMENT_END': esc(meta['experiment_end']),
        'TRIAL_CUTOUT': player('round-02/run.gif', 'Trial cutout run'), 'TRIAL_PAINTED': player('trial-b/run.gif', 'Trial painted run'),
        'TRIAL_SHEET': esc(media['trial-b/run-row.png']['original']), 'PAIR_DATA': json.dumps(pair_data).replace('</', '<\\/'),
    }
    for key, value in replacements.items():
        page = page.replace('@@' + key + '@@', value)
    assert '@@' not in page, 'Unfilled template field'
    (OUT / 'calibration.html').write_text(page)
    report = {'output': str(OUT / 'calibration.html'), 'media_items': len(inputs), 'animations': sum(i['kind'] == 'animation' for i in manifest['items']), 'images': sum(i['kind'] == 'image' for i in manifest['items']), 'provenance_ok': sum(i['provenance']['status'] == 'ok' for i in manifest['items']), 'directory_bytes': sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()), 'final_status': final_status, 'environment_url': meta.get('environment_url')}
    (SCRATCH / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
