#!/usr/bin/env python3
"""THROWAWAY: builds the mechanics-lab review page (index.html + play/ + linux zip) for gh-pages.

usage: build_site.py LAB_DIR EXPORT_OUT_DIR SITE_OUT_DIR --issue N --commit SHA
  LAB_DIR         prototypes/mechanics-lab (reads experiments.json)
  EXPORT_OUT_DIR  export.sh output (has web/ and linux/)
  SITE_OUT_DIR    directory to publish (index.html, play/, violet-mechanics-lab-linux.zip)
"""
import argparse, html, json, shutil, zipfile
from pathlib import Path

CONTROLS = [
    ("Move", "A / D or arrow keys", "Left stick or d-pad"),
    ("Jump (again in the air: double jump)", "Space or K", "A"),
    ("Dash", "Shift or J", "X"),
    ("Blue ability (blink or swing)", "L or C", "B"),
    ("Stomp (yellow)", "S or down arrow, in the air", "Down, in the air"),
    ("Switch color", "Q or I", "Y"),
    ("Hold to resonate", "E or O", "RB"),
    ("Restart room", "R", "Back"),
    ("Menu", "Esc", "Start"),
    ("Compare with bake-off movement", "Tab", "LB"),
    ("Tuning sliders", "F1", ""),
    ("Show controls", "H", ""),
    ("Mute", "M", ""),
]

# Mirrors lab/ui/menu.gd's GROUP_LABELS: experiments.json entries may carry an
# optional "group" key; the first entry of a new group gets a heading above
# it (the first group in the list -- the round-2 chapter/wall-jump trial --
# gets none, since it's already first), so the review page's experiment list
# matches the in-game menu's grouping instead of running all eleven
# experiments together as one undifferentiated list.
GROUP_LABELS = {
    "round1": "Round 1 experiments",
}


def _render_experiments(experiments: list[dict]) -> str:
    parts = ["<ol>"]
    last_group = ""
    number = 0
    for e in experiments:
        group = e.get("group", "")
        if group != "" and group != last_group:
            number += 1
            parts.append(f'</ol>\n<h3>{html.escape(GROUP_LABELS.get(group, group))}</h3>\n<ol start="{number}">')
            number -= 1
        last_group = group
        number += 1
        parts.append(f"<li><b>{html.escape(e['title'])}</b><br><span>{html.escape(e['question'])}</span></li>")
    parts.append("</ol>")
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lab"); ap.add_argument("export"); ap.add_argument("out")
    ap.add_argument("--issue", required=True, type=int)
    ap.add_argument("--commit", required=True)
    a = ap.parse_args()
    lab, export, out = Path(a.lab), Path(a.export), Path(a.out)
    experiments = json.loads((lab / "experiments.json").read_text())
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(export / "web", out / "play")
    linux = sorted((export / "linux").iterdir())
    if not linux:
        raise SystemExit(f"no Linux export in {export / 'linux'}")
    with zipfile.ZipFile(out / "violet-mechanics-lab-linux.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in linux:
            z.write(f, f"violet-mechanics-lab/{f.name}")
    experiment_list_html = _render_experiments(experiments)
    controls = "\n".join(
        f"<tr><td>{html.escape(a_)}</td><td>{html.escape(k)}</td><td>{html.escape(g)}</td></tr>" for a_, k, g in CONTROLS
    )
    issue = f"https://github.com/sjawhar/project-violet/issues/{a.issue}"
    src = f"https://github.com/sjawhar/project-violet/tree/{a.commit}/prototypes/mechanics-lab"
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Violet mechanics lab (throwaway)</title>
<style>
body{{font:17px/1.5 system-ui,sans-serif;background:#1f2430;color:#e8e3d8;max-width:860px;margin:2rem auto;padding:0 1rem}}
a{{color:#7fb2f0}} h1{{margin-bottom:.2rem}} .sub{{color:#9aa0a6;margin-top:0}}
.play{{display:inline-block;background:#4cc27a;color:#1f2430;font-weight:700;padding:.8rem 1.4rem;border-radius:8px;text-decoration:none;font-size:1.2rem;margin:.6rem .6rem .6rem 0}}
.dl{{background:#3a4150;color:#e8e3d8}}
ol li{{margin:.6rem 0}} ol li span{{color:#c9c4b8}}
table{{border-collapse:collapse;width:100%}} td{{border-top:1px solid #3a4150;padding:.3rem .5rem}}
.note{{color:#9aa0a6;font-size:.9rem}}
</style></head><body>
<h1>Violet mechanics lab</h1>
<p class="sub">Throwaway greybox. Each experiment asks one question for the mechanics brainstorm; nothing here is canon.</p>
<a class="play" href="play/index.html">Play in the browser</a>
<a class="play dl" href="violet-mechanics-lab-linux.zip">Linux build (zip)</a>
<p>Answer the questions in <a href="{issue}">issue #{a.issue}</a>. A gamepad works in both builds; the browser needs a click on the game before sound starts.</p>
<h2>Experiments</h2>
{experiment_list_html}
<h2>Controls</h2>
<table><tr><td><b>Action</b></td><td><b>Keyboard</b></td><td><b>Gamepad</b></td></tr>
{controls}
</table>
<p class="note">Built from <a href="{src}">prototypes/mechanics-lab at {a.commit[:8]}</a> on branch proto/mechanics-lab.</p>
</body></html>
"""
    (out / "index.html").write_text(page)
    print(f"site: {out} ({len(experiments)} experiments, linux zip {(out / 'violet-mechanics-lab-linux.zip').stat().st_size} bytes)")


if __name__ == "__main__":
    main()
