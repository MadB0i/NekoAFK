import os
import shutil
import subprocess
import pathlib
import time
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRAMES_DIR = ROOT / 'temp_nova_frames'
OUTPUT_GIF = ROOT / 'assets/nova-showcase.gif'

if FRAMES_DIR.exists():
    shutil.rmtree(FRAMES_DIR)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

html_file = ROOT / 'scratch_stage.html'
file_url = html_file.resolve().as_uri()

fps = 20
duration = 14.0
total_frames = int(fps * duration)
dt = 1.0 / fps

print(f"Rendering {total_frames} frames ({duration}s @ {fps}fps)...")
start_time = time.time()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 440, 'height': 440})
    page.goto(file_url)
    page.wait_for_timeout(300)
    page.evaluate("window.stage.setup('writing')")
    
    for i in range(total_frames):
        t = i * dt
        page.evaluate(f"window.stage.render({t})")
        frame_path = FRAMES_DIR / f"frame_{i:04d}.png"
        page.screenshot(path=str(frame_path))
        if i % 40 == 0 or i == total_frames - 1:
            print(f"Rendered frame {i+1}/{total_frames} (t={t:.2f}s)")
            
    browser.close()

render_duration = time.time() - start_time
print(f"All {total_frames} frames rendered in {render_duration:.2f}s!")

# Now encode to high-quality palette-optimized GIF with ffmpeg
print("Encoding GIF with ffmpeg palettegen + paletteuse...")
cmd = [
    'ffmpeg', '-y',
    '-framerate', str(fps),
    '-i', str(FRAMES_DIR / 'frame_%04d.png'),
    '-vf', 'scale=440:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer',
    str(OUTPUT_GIF)
]

res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    print("FFmpeg error:", res.stderr)
    exit(1)

gif_size = OUTPUT_GIF.stat().st_size
print(f"Successfully generated {OUTPUT_GIF.name} ({gif_size / (1024*1024):.2f} MB)")

# Clean up frame directory
shutil.rmtree(FRAMES_DIR)
print("Temp frames cleaned up.")
