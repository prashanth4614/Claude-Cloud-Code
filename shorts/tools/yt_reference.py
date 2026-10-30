#!/usr/bin/env python3
"""Study a reference YouTube Short in a real, visible browser (Playwright + Google Chrome).

  python3 shorts/tools/yt_reference.py search "zack d films ear"      # list Shorts links from a search
  python3 shorts/tools/yt_reference.py study URL_OR_ID [--every 0.5]  # play it once, frames + tab audio
  python3 shorts/tools/yt_reference.py grid URL NAME [--pages 3]      # screenshots of a channel grid

`study` plays the Short from 0 to its end in the page, takes a screenshot of the player every
`--every` s and records ONLY that <video> element's own playback (MediaRecorder on captureStream()).
Everything goes to out/reference/<id>/ (gitignored): frames/NNNN.png, frames.json (video time per
frame), audio.webm. No downloader is used. Never commit or upload these files; delete them when done.
The browser profile lives in out/reference/profile, so a cookie/consent click is needed only once.
"""
import base64
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2] / "out" / "reference"


def vid_id(s):
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", s)
    return m.group(1) if m else s


def browser(p):
    ROOT.mkdir(parents=True, exist_ok=True)
    return p.chromium.launch_persistent_context(
        str(ROOT / "profile"), channel="chrome", headless=False, viewport={"width": 1100, "height": 900},
        args=["--autoplay-policy=no-user-gesture-required"])


def consent(page):
    for label in ("Accept all", "Reject all"):
        b = page.get_by_role("button", name=label)
        if b.count():
            b.first.click()
            page.wait_for_timeout(1500)
            return


def search(q):
    with sync_playwright() as p:
        ctx = browser(p)
        page = ctx.new_page()
        page.goto("https://www.youtube.com/results?search_query=" + q.replace(" ", "+") + "&sp=EgIYAQ%3D%3D")
        consent(page)
        page.wait_for_timeout(4000)
        for _ in range(3):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(1200)
        rows = page.evaluate("""() => [...document.querySelectorAll('a[href*="/shorts/"]')].map(a => [
            a.getAttribute('href'), (a.getAttribute('title') || a.innerText || '').trim().slice(0, 90),
            (a.closest('ytd-video-renderer,ytm-shorts-lockup-view-model,ytd-reel-item-renderer') || a)
              .innerText.replace(/\\s+/g, ' ').slice(0, 160)])""")
        seen = set()
        for href, title, ctx_text in rows:
            i = vid_id(href)
            if i not in seen:
                seen.add(i)
                print(i, "|", title, "|", ctx_text)
        ctx.close()


def grid(url, name, pages=3):
    """Screenshot a channel's Shorts/Videos grid, one viewport per scroll, into out/reference/grid_<name>/."""
    out = ROOT / f"grid_{name}"
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        ctx = browser(p)
        page = ctx.new_page()
        page.set_viewport_size({"width": 1400, "height": 1000})
        page.goto(url)
        consent(page)
        page.wait_for_timeout(4000)
        for k in range(pages):
            page.screenshot(path=str(out / f"{k:02d}.png"))
            page.mouse.wheel(0, 850)
            page.wait_for_timeout(2500)
        titles = page.evaluate("""() => [...document.querySelectorAll('a#video-title-link, a#video-title,'
            + ' h3 a[href*="/shorts/"], a[href*="/shorts/"][title]')].map(a => [a.getAttribute('href'),
            (a.getAttribute('title') || a.innerText || '').trim()]).filter(x => x[1])""")
        (out / "titles.json").write_text(json.dumps(titles, indent=1))
        print(f"[ref] {pages} screenshots + {len(titles)} titles -> {out}")
        ctx.close()


REC_START = """async () => {
  const v = document.querySelector('#shorts-player video, ytd-reel-video-renderer[is-active] video, video');
  v.loop = false; v.muted = false; v.volume = 1.0; v.pause(); v.currentTime = 0;
  await new Promise(r => setTimeout(r, 800));
  const tracks = v.captureStream().getAudioTracks();
  const rec = new MediaRecorder(new MediaStream(tracks), {mimeType: 'audio/webm;codecs=opus', audioBitsPerSecond: 256000});
  window.__chunks = []; window.__done = false;
  rec.ondataavailable = e => window.__chunks.push(e.data);
  rec.onstop = () => { window.__done = true; };
  window.__rec = rec; window.__v = v;
  rec.start(250); await v.play();
  return {duration: v.duration, tracks: tracks.length};
}"""

REC_BLOB = """async () => {
  const b = new Blob(window.__chunks, {type: 'audio/webm'});
  const buf = new Uint8Array(await b.arrayBuffer()); let s = '';
  for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
  return btoa(s);
}"""


def study(url, every=0.5):
    i = vid_id(url)
    out = ROOT / i
    (out / "frames").mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        ctx = browser(p)
        page = ctx.new_page()
        page.goto(f"https://www.youtube.com/shorts/{i}")
        consent(page)
        page.wait_for_selector("video", timeout=30000)
        page.wait_for_timeout(3000)
        title = page.title()
        channel = page.evaluate("""() => { const a = document.querySelector(
            'ytd-reel-video-renderer[is-active] a[href^="/@"], #shorts-player ~ * a[href^="/@"], a[href^="/@"]');
            return a ? a.getAttribute('href') : ''; }""")
        info = page.evaluate(REC_START)
        print(f"[ref] {i}: {title} | {channel} | {info}")
        player = page.locator("#shorts-player, ytd-reel-video-renderer[is-active] #player-container").first
        frames, k, t0, last = [], 0, time.time(), 0.0
        while True:   # YouTube re-enables looping: stop at the end or when time jumps back to the start
            vt, ended, dur = page.evaluate("() => [window.__v.currentTime, window.__v.ended, window.__v.duration]")
            if ended or vt >= dur - 0.05 or vt < last - 1 or time.time() - t0 > dur + 30:
                break
            last = vt
            f = out / "frames" / f"{k:04d}.png"
            (player if player.count() else page).screenshot(path=str(f))
            frames.append({"frame": f.name, "t": round(vt, 3)})
            k += 1
            time.sleep(max(0.0, t0 + k * every - time.time()))
        page.evaluate("() => { window.__v.pause(); window.__rec.stop(); }")
        page.wait_for_function("() => window.__done", timeout=10000)
        (out / "audio.webm").write_bytes(base64.b64decode(page.evaluate(REC_BLOB)))
        (out / "frames.json").write_text(json.dumps({"id": i, "title": title, "channel": channel, "duration": info["duration"],
                                                     "frames": frames}, indent=1))
        print(f"[ref] {len(frames)} frames + audio.webm -> {out}")
        ctx.close()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["search"]:
        search(" ".join(a[1:]))
    elif a[:1] == ["study"]:
        study(a[1], float(a[a.index("--every") + 1]) if "--every" in a else 0.5)
    elif a[:1] == ["grid"]:
        grid(a[1], a[2], int(a[a.index("--pages") + 1]) if "--pages" in a else 3)
    else:
        print(__doc__)
