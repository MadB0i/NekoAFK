import os
import pathlib
import time
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACT_DIR = pathlib.Path(r"C:\Users\rupjy\.gemini\antigravity\brain\efb58a8b-050f-446b-bb11-16cd534d5e2a")
URL = "http://127.0.0.1:1425/tests/kuro-stage.html"

STATES = [
    {
        "id": "idle_scroll",
        "title": "Idle: Phone Scrolling & Foot Swing",
        "action": lambda page: page.evaluate("window.kuro.observe('editing',0,'','playful',false,true); window.kuro.setTimeForTest(3.0); window.setBadge('Idle: Phone Scrolling & Foot Swing');")
    },
    {
        "id": "idle_glance",
        "title": "Idle: Curious Glance Up & Perked Ears",
        "action": lambda page: page.evaluate("window.kuro.observe('editing',0,'','playful',false,true); window.kuro.setTimeForTest(10.5); window.setBadge('Idle: Curious Glance Up (Looking at User)');")
    },
    {
        "id": "idle_sigh",
        "title": "Idle: Deep Relaxed Breath & Resting Foot",
        "action": lambda page: page.evaluate("window.kuro.observe('editing',0,'','playful',false,true); window.kuro.setTimeForTest(18.0); window.setBadge('Idle: Deep Relaxed Breath / Sigh');")
    },
    {
        "id": "idle_tilt",
        "title": "Idle: Playful Head Tilt & Ear Flick",
        "action": lambda page: page.evaluate("window.kuro.observe('editing',0,'','playful',false,true); window.kuro.setTimeForTest(26.0); window.setBadge('Idle: Playful Head Tilt & Ear Flick');")
    },
    {
        "id": "pet_reaction",
        "title": "Interaction: Joyful Pet Reaction",
        "action": lambda page: page.evaluate("window.kuro.observe('editing',0,'','playful',false,true); window.kuro.setTimeForTest(2.0); window.kuro.pet(); window.kuro.setTimeForTest(2.2); window.setBadge('Interaction: Joyful Ear Flutter & Tail Wag');")
    },
    {
        "id": "testing",
        "title": "Agent State: Testing & Laptop Coding",
        "action": lambda page: page.evaluate("window.kuro.observe('testing',0,'','playful',false,true); window.kuro.setTimeForTest(1.5); window.setBadge('Agent State: Testing (Laptop Coding Focus)');")
    },
    {
        "id": "verifying",
        "title": "Agent State: Local Verification Inspection",
        "action": lambda page: page.evaluate("window.kuro.observe('verifying',0,'','playful',false,true); window.kuro.setTimeForTest(2.0); window.setBadge('Agent State: Verifying (Inspection Hover)');")
    },
    {
        "id": "success",
        "title": "Agent State: Verified Celebration",
        "action": lambda page: page.evaluate("window.kuro.observe('verified',0,'','playful',false,true); window.kuro.setTimeForTest(2.4); window.setBadge('Agent State: Verified Success (Victory Bounce)');")
    },
    {
        "id": "failed",
        "title": "Agent State: Failed Check Pout",
        "action": lambda page: page.evaluate("window.kuro.observe('failed',1,'','playful',false,true); window.kuro.setTimeForTest(2.0); window.setBadge('Agent State: Failed (Pout Huff & Droop)');")
    },
    {
        "id": "frustrated",
        "title": "Agent State: Inconclusive Slump",
        "action": lambda page: page.evaluate("window.kuro.observe('inconclusive',0,'','playful',false,true); window.kuro.setTimeForTest(2.0); window.setBadge('Agent State: Inconclusive (Head-shake Slump)');")
    }
]

print("Launching Playwright...")
screenshots = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 460, "height": 520})
    page.goto(URL)
    page.wait_for_function("() => window.kuro !== undefined")
    page.wait_for_timeout(600)

    for item in STATES:
        print(f"Capturing: {item['title']}...")
        item["action"](page)
        page.wait_for_timeout(100)
        out_path = ARTIFACT_DIR / f"kuro_{item['id']}.png"
        page.screenshot(path=str(out_path))
        screenshots.append(out_path)
        print(f"  -> Saved {out_path.name}")

    browser.close()

# Create a composite showcase image grid (2 rows x 5 columns)
print("Creating composite showcase image grid...")
imgs = [Image.open(p) for p in screenshots]
w, h = imgs[0].size
cols = 5
rows = 2
grid_w = w * cols
grid_h = h * rows

grid = Image.new("RGBA", (grid_w, grid_h), (13, 12, 19, 255))
for idx, img in enumerate(imgs):
    r = idx // cols
    c = idx % cols
    grid.paste(img, (c * w, r * h))

grid_path = ARTIFACT_DIR / "kuro_animation_showcase_grid.png"
grid.save(grid_path)
print(f"Showcase grid saved to {grid_path.name} ({grid_w}x{grid_h})")
