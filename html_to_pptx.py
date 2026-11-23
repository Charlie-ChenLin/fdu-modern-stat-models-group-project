#!/usr/bin/env python3
"""Convert a 15-slide 1280x720 HTML presentation into a high-resolution 16:9 PPTX
using headless Google Chrome (via Playwright at 2x Retina scale = 2560x1440),
with strict DOM overflow & image-load auditing and automatic Speaker Notes transfer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from PIL import Image
from playwright.sync_api import sync_playwright
from pptx import Presentation
from pptx.util import Inches


def export_html_to_pptx(html_path: Path, pptx_path: Path) -> None:
    html_path = html_path.resolve()
    pptx_path = pptx_path.resolve()
    preview_dir = pptx_path.parent / "slides_preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    url = html_path.as_uri() + "?export=1"
    notes_list: List[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle")
        page.evaluate("() => document.fonts.ready")
        page.wait_for_timeout(400)

        audit = page.evaluate(
            """() => {
                const slides = Array.from(document.querySelectorAll('section.slide'));
                const imgs = Array.from(document.querySelectorAll('img'));
                const brokenImgs = imgs.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'));
                const slideStats = slides.map((s, idx) => {
                    const rect = s.getBoundingClientRect();
                    let maxBottom = 0;
                    for (const ch of s.children) {
                        const cs = getComputedStyle(ch);
                        if (cs.position === 'absolute' && (ch.classList.contains('bg-decor') || ch.classList.contains('decor'))) continue;
                        const cr = ch.getBoundingClientRect();
                        if (cr.bottom - rect.top > maxBottom) maxBottom = cr.bottom - rect.top;
                    }
                    return {
                        index: idx + 1,
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        scrollHeight: s.scrollHeight,
                        clientHeight: s.clientHeight,
                        scrollWidth: s.scrollWidth,
                        clientWidth: s.clientWidth,
                        maxChildBottom: Math.round(maxBottom),
                        notes: s.getAttribute('data-notes') || ''
                    };
                });
                let scriptNotes = null;
                const snEl = document.getElementById('speaker-notes');
                if (snEl) {
                    try { scriptNotes = JSON.parse(snEl.textContent); } catch(e) {}
                }
                return { count: slides.length, brokenImgs, slideStats, scriptNotes };
            }"""
        )

        if audit["count"] != 15:
            browser.close()
            raise RuntimeError(f"{html_path.name}: expected 15 <section class='slide'>, found {audit['count']}")
        if audit["brokenImgs"]:
            browser.close()
            raise RuntimeError(f"{html_path.name}: broken images: {audit['brokenImgs']}")

        overflows = []
        for st in audit["slideStats"]:
            if (
                abs(st["width"] - 1280) > 2
                or abs(st["height"] - 720) > 2
                or st["scrollHeight"] > st["clientHeight"] + 3
                or st["scrollWidth"] > st["clientWidth"] + 3
                or st["maxChildBottom"] > 724
            ):
                overflows.append(st)
        if overflows:
            browser.close()
            raise RuntimeError(
                f"{html_path.name}: DOM overflow/size error on slides: "
                + json.dumps(overflows, ensure_ascii=False)
            )

        slide_locators = page.locator("section.slide")
        for i in range(15):
            out_png = preview_dir / f"slide_{i + 1:02d}.png"
            slide_locators.nth(i).screenshot(path=str(out_png))
            note = audit["slideStats"][i]["notes"]
            if not note and audit["scriptNotes"] and i < len(audit["scriptNotes"]):
                note = str(audit["scriptNotes"][i])
            notes_list.append(note)

        browser.close()

    # Build 16:9 PPTX from crisp 2560x1440 PNGs + Speaker Notes
    prs = Presentation()
    prs.slide_width = Inches(13.333333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    for i in range(15):
        png_path = preview_dir / f"slide_{i + 1:02d}.png"
        with Image.open(png_path) as im:
            assert im.size == (2560, 1440), f"Unexpected PNG size {im.size} for {png_path}"
        slide = prs.slides.add_slide(blank)
        slide.shapes.add_picture(str(png_path), Inches(0), Inches(0), width=prs.slide_width, height=prs.slide_height)
        if notes_list[i].strip():
            slide.notes_slide.notes_text_frame.text = notes_list[i].strip()

    pptx_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(pptx_path))
    print(f"[OK] {html_path.name} -> {pptx_path.name} (15 slides, 2560x1440 Retina, notes attached)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert 15-slide 1280x720 HTML presentations to 16:9 PPTX.")
    parser.add_argument("--version", choices=["v1", "v2", "all"], default="all")
    args = parser.parse_args()

    group_dir = Path(__file__).resolve().parent
    targets = []
    if args.version in ("v1", "all"):
        targets.append((
            group_dir / "version1_taught_ggm" / "presentation" / "版本一_高斯图模型与跨资产风险传染网络.html",
            group_dir / "version1_taught_ggm" / "presentation" / "版本一_高斯图模型与跨资产风险传染网络.pptx",
        ))
    if args.version in ("v2", "all"):
        targets.append((
            group_dir / "version2_untaught_dml" / "presentation" / "版本二_双重机器学习与养老金因果评估.html",
            group_dir / "version2_untaught_dml" / "presentation" / "版本二_双重机器学习与养老金因果评估.pptx",
        ))

    for html_p, pptx_p in targets:
        if not html_p.exists():
            print(f"[SKIP] Missing {html_p}", file=sys.stderr)
            continue
        export_html_to_pptx(html_p, pptx_p)


if __name__ == "__main__":
    main()
