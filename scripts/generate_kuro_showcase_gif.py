import os
import shutil
import subprocess
import pathlib
import time
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRAMES_DIR = ROOT / 'temp_kuro_frames'
OUTPUT_GIF = ROOT / 'assets/kuro-showcase.gif'
URL = "http://127.0.0.1:1425/tests/kuro-stage.html"

if FRAMES_DIR.exists():
    shutil.rmtree(FRAMES_DIR)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# Sequence of showcase acting beats
# Total duration: ~10 seconds @ 20 fps = 200 frames
BEATS = [
    # 0.0 - 2.5s: Idle Phone Scrolling (t = 2.0 to 4.5)
    {"dur": 2.2, "state": "editing", "time_fn": lambda s: 2.0 + s, "badge": "Idle: Phone Scrolling"},
    # 2.2 - 4.4s: Curious Glance Up at User (t = 8.5 to 10.7)
    {"dur": 2.2, "state": "editing", "time_fn": lambda s: 8.5 + s, "badge": "Idle: Curious Glance Up"},
    # 4.4 - 6.0s: Testing (Coding on laptop)
    {"dur": 1.6, "state": "testing", "time_fn": lambda s: s, "badge": "Agent: Testing Code"},
    # 6.0 - 7.6s: Verifying (Inspection hover)
    {"dur": 1.6, "state": "verifying", "time_fn": lambda s: s, "badge": "Agent: Verifying Output"},
    # 7.6 - 9.6s: Success (Victory bounce celebration)
    {"dur": 2.0, "state": "verified", "time_fn": lambda s: s, "badge": "Agent: Verified Victory!"},
    # 9.6 - 11.2s: Petting Reaction (Joyful ear flutter & tail wag)
    {"dur": 1.6, "state": "editing", "pet": True, "time_fn": lambda s: 2.0 + s * 0.5, "badge": "Interactive: Petting Reaction"}
]

fps = 20
total_dur = sum(b["dur"] for b in BEATS)
total_frames = int(fps * total_dur)
dt = 1.0 / fps

print(f"Rendering {total_frames} frames ({total_dur:.1f}s @ {fps}fps)...")
start_time = time.time()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 440, "height": 480})
    page.goto(URL)
    page.wait_for_function("() => window.kuro !== undefined")
    page.wait_for_timeout(500)

    frame_idx = 0
    for beat in BEATS:
        beat_frames = int(beat["dur"] * fps)
        state = beat["state"]
        badge = beat["badge"]
        is_pet = beat.get("pet", False)

        page.evaluate(f"window.kuro.observe('{state}', 0, '', 'playful', false, true); window.setBadge('{badge}');")
        if is_pet:
            page.evaluate("window.kuro.pet();")

        for f in range(beat_frames):
            s = f * dt
            t = beat["time_fn"](s)
            page.evaluate(f"window.kuro.setTimeForTest({t});")
            frame_path = FRAMES_DIR / f"frame_{frame_idx:04d}.png"
            page.screenshot(path=str(frame_path))
            frame_idx += 1

    browser.close()

render_duration = time.time() - start_time
print(f"Rendered {frame_idx} frames in {render_duration:.2f}s!")

print("Encoding GIF with ffmpeg...")
cmd = [
    'ffmpeg', '-y',
    '-framerate', str(fps),
    '-i', str(FRAMES_DIR / 'frame_%04d.png'),
    '-vf', 'scale=360:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer',
    str(OUTPUT_GIF)
]

res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    print("FFmpeg error:", res.stderr)
    exit(1)

gif_size = OUTPUT_GIF.stat().st_size
print(f"Successfully generated {OUTPUT_GIF.name} ({gif_size / (1024*1024):.2f} MB)")

# Also copy to artifacts directory for user viewing
shutil.copy(OUTPUT_GIF, ARTIFACT_DIR / "kuro_multi_animation_demo.gif")
print("Copied to artifacts directory.")

shutil.rmtree(FRAMES_DIR)
print("Temp frames cleaned up.")
