"""Capture real browser-demo module screenshots and assemble a 32-second GIF.

Run from the repository root with Playwright, Chromium, and Pillow installed:
    python scripts/build_demo_assets.py

Generated images are written under docs/assets/ for the GitHub Pages artifact.
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "index.html"
ASSETS = ROOT / "docs" / "assets"
SCREENSHOTS = ASSETS / "screenshots"

MODULES = [
    ("briefing", "01-leadership-briefing.png", "01 / Leadership briefing"),
    ("market", "02-market-context.png", "02 / Market context"),
    ("lab", "03-cuda-future-lab.png", "03 / CUDA Future Lab"),
    ("jacket", "04-jacket-office.png", "04 / Jacket Office"),
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def capture_screenshots() -> None:
    if not INDEX.is_file():
        raise FileNotFoundError(f"Browser demo not found: {INDEX}")

    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    html = INDEX.read_text(encoding="utf-8")

    with sync_playwright() as playwright:
        launch_options = {"headless": True}
        if os.environ.get("CHROMIUM_EXECUTABLE_PATH"):
            launch_options["executable_path"] = os.environ["CHROMIUM_EXECUTABLE_PATH"]

        browser = playwright.chromium.launch(**launch_options)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 960}, device_scale_factor=1)
            # The static demo is self-contained, so set_content avoids file:// and server setup.
            page.set_content(html, wait_until="load")
            page.emulate_media(color_scheme="dark", reduced_motion="reduce")

            required_selectors = ["#briefing", "#market", "#lab", "#jacket", "#roadmapBtn", "#generateBtn"]
            for selector in required_selectors:
                if page.locator(selector).count() != 1:
                    raise RuntimeError(f"Browser demo is missing required selector: {selector}")

            # Exercise both interactive modules before recording their actual DOM state.
            page.locator("#scenario").select_option("engineering")
            page.locator("#focus").select_option("Developer experience")
            page.locator("#roadmapBtn").click()
            page.wait_for_function("document.querySelectorAll('#roadmap .feature').length === 5")

            page.locator("#format").select_option("release")
            page.locator("#generateBtn").click()
            page.wait_for_function(
                "document.querySelector('#message').textContent.toLowerCase().includes('jacket')"
            )

            for section_id, filename, _title in MODULES:
                section = page.locator(f"#{section_id}")
                section.wait_for(state="visible")
                section.screenshot(path=str(SCREENSHOTS / filename), animations="disabled")
        finally:
            browser.close()


def build_gif() -> None:
    images: list[Image.Image] = []
    canvas_size = (960, 640)
    content_size = (912, 520)

    for _section_id, filename, title in MODULES:
        path = SCREENSHOTS / filename
        if not path.is_file():
            raise FileNotFoundError(f"Expected browser screenshot is missing: {path}")

        with Image.open(path) as source_file:
            source = source_file.convert("RGB")
        preview = ImageOps.contain(source, content_size, method=Image.Resampling.LANCZOS)

        frame = Image.new("RGB", canvas_size, "#080d0a")
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, 0, 960, 68), fill="#101a13")
        draw.text((24, 12), "OPEN TO WORK JENSEN  /  INTERACTIVE BROWSER DEMO",
                  font=_font(14, True), fill="#a5d76f")
        draw.text((24, 38), title, font=_font(13), fill="#edf5ef")
        x = (canvas_size[0] - preview.width) // 2
        y = 76 + (content_size[1] - preview.height) // 2
        frame.paste(preview, (x, y))
        draw.rectangle((0, 608, 960, 640), fill="#101a13")
        draw.text((24, 616),
                  "SOURCE-AWARE  ·  CPU-ONLY  ·  FICTIONAL CUDA IDEAS  ·  NO OUTREACH",
                  font=_font(10), fill="#9fb4a5")
        images.append(frame)

    gif_path = ASSETS / "demo-tour.gif"
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=[8000] * len(images),
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Created {gif_path} ({len(images) * 8} seconds)")
    for _section_id, filename, _title in MODULES:
        print(f"Created {SCREENSHOTS / filename}")


def main() -> None:
    capture_screenshots()
    build_gif()


if __name__ == "__main__":
    main()
