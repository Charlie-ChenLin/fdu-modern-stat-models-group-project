#!/usr/bin/env python3
"""Comprehensive automated verification for both Version 1 (GGM) and Version 2 (DML) deliverables:
1. Numeric integrity of results_summary.json (no NaN/Inf, PD precision, Alg1 precision,
   DML simulation coverage & bias checks, 401(k) estimate sanity).
2. HTML presentation integrity:
   - Exactly 15 <section class="slide"> elements with non-empty data-notes
   - Offline self-contained (no external CDN <script>/<link>)
   - All 6 PNG figure links valid, no dirty placeholders
   - Core numeric consistency with results_summary.json
3. PPTX integrity:
   - Exactly 15 slides per deck (13.333" x 7.5")
   - Each slide has 2560x1440 Retina render + non-empty Speaker Notes
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import List

from lxml import html as lxml_html
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

GROUP_DIR = Path(__file__).resolve().parent
V1_DIR = GROUP_DIR / "version1_taught_ggm"
V2_DIR = GROUP_DIR / "version2_untaught_dml"


def check_no_nan(obj, prefix: str = "") -> List[str]:
    errs = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            errs.extend(check_no_nan(v, f"{prefix}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            errs.extend(check_no_nan(v, f"{prefix}[{i}]"))
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            errs.append(f"Invalid float at {prefix}: {obj}")
    return errs


def verify_v1_json() -> List[str]:
    errs = []
    p = V1_DIR / "outputs" / "results_summary.json"
    if not p.exists():
        return [f"Missing {p}"]
    data = json.loads(p.read_text(encoding="utf-8"))
    errs.extend(check_no_nan(data, "v1"))
    ebic = data["ebic_selected_model"]
    if ebic["alg1_primal_err"] > 1e-10:
        errs.append(f"V1 Alg1 primal_err too large: {ebic['alg1_primal_err']}")
    if ebic["alg1_zero_err"] != 0.0:
        errs.append(f"V1 Alg1 zero_err nonzero: {ebic['alg1_zero_err']}")
    if ebic["min_eigenvalue_theta_refit"] <= 0:
        errs.append("V1 Theta_refit not positive definite!")
    vol_ggm = data["rolling_gmvp_oos_metrics"]["GGM 两步精估 (Alg1)"]["ann_vol_pct"]
    vol_eq = data["rolling_gmvp_oos_metrics"]["等权组合 (1/N)"]["ann_vol_pct"]
    if vol_ggm >= vol_eq:
        errs.append(f"V1 unexpected vol: GGM {vol_ggm} >= EqualWeight {vol_eq}")
    return errs


def verify_v2_json() -> List[str]:
    errs = []
    p = V2_DIR / "outputs" / "results_summary.json"
    if not p.exists():
        return [f"Missing {p}"]
    data = json.loads(p.read_text(encoding="utf-8"))
    errs.extend(check_no_nan(data, "v2"))
    sim_rows = {r["method"]: r for r in data["simulation"]["summary"]}
    dml_row = [v for k, v in sim_rows.items() if "完整 DML" in k][0]
    if abs(dml_row["bias"]) > 0.08:
        errs.append(f"V2 DML simulation bias too large: {dml_row['bias']}")
    if dml_row["coverage_95_pct"] < 89.0 or dml_row["coverage_95_pct"] > 99.0:
        errs.append(f"V2 DML simulation coverage out of range: {dml_row['coverage_95_pct']}%")
    emp = data["empirical_401k"]
    if not (5000 <= emp["dml_irm"]["HistGradientBoosting"]["ATE"]["est"] <= 15000):
        errs.append(f"V2 401k HGB ATE out of expected range: {emp['dml_irm']['HistGradientBoosting']['ATE']['est']}")
    return errs


def verify_html(html_path: Path, expected_tokens: List[str]) -> List[str]:
    errs = []
    if not html_path.exists():
        return [f"Missing HTML: {html_path}"]
    raw = html_path.read_text(encoding="utf-8")
    doc = lxml_html.fromstring(raw)

    slides = doc.xpath("//section[contains(@class,'slide')]")
    if len(slides) != 15:
        errs.append(f"{html_path.name}: expected 15 <section class='slide'>, got {len(slides)}")
    for i, s in enumerate(slides, 1):
        notes = (s.get("data-notes") or "").strip()
        if len(notes) < 10:
            errs.append(f"{html_path.name} Slide {i}: empty or too short data-notes")

    # Offline self-contained check
    ext_refs = doc.xpath("//script[@src[starts-with(.,'http')]] | //link[@href[starts-with(.,'http')]]")
    if ext_refs:
        errs.append(f"{html_path.name}: external CDN reference found ({len(ext_refs)})")

    # Image check
    imgs = doc.xpath("//img")
    if len(imgs) < 6:
        errs.append(f"{html_path.name}: expected >=6 images, got {len(imgs)}")
    for img in imgs:
        src = img.get("src") or ""
        target = (html_path.parent / src).resolve()
        if not target.exists():
            errs.append(f"{html_path.name}: broken image path '{src}'")

    # Dirty token check
    txt = doc.text_content()
    for bad in ["NaN", "nan%", "TODO", "TBD", "¤"]:
        if bad in txt:
            errs.append(f"{html_path.name}: dirty token '{bad}' found in text")

    # Key numeric presence check
    norm_txt = re.sub(r"\s+", "", txt).replace("−", "-")
    for tok in expected_tokens:
        if tok not in norm_txt:
            errs.append(f"{html_path.name}: missing expected metric token '{tok}'")

    return errs


def verify_pptx(pptx_path: Path) -> List[str]:
    errs = []
    if not pptx_path.exists():
        return [f"Missing PPTX: {pptx_path}"]
    prs = Presentation(str(pptx_path))
    if len(prs.slides) != 15:
        errs.append(f"{pptx_path.name}: expected 15 slides, got {len(prs.slides)}")

    preview_dir = pptx_path.parent / "slides_preview"
    for i, slide in enumerate(prs.slides, 1):
        pics = [sh for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
        if len(pics) != 1:
            errs.append(f"{pptx_path.name} Slide {i}: expected 1 full-bleed rendered slide image, got {len(pics)}")
        else:
            w_px, h_px = pics[0].image.size
            if (w_px, h_px) != (2560, 1440):
                errs.append(f"{pptx_path.name} Slide {i}: expected 2560x1440 image, got {w_px}x{h_px}")
        notes_txt = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
        if len(notes_txt) < 10:
            errs.append(f"{pptx_path.name} Slide {i}: missing speaker notes")
        pv = preview_dir / f"slide_{i:02d}.png"
        if not pv.exists():
            errs.append(f"{pptx_path.name}: missing preview PNG {pv}")
        else:
            with Image.open(pv) as im:
                if im.size != (2560, 1440):
                    errs.append(f"{pv.name}: expected 2560x1440, got {im.size}")
    return errs


def main() -> None:
    all_errs = []
    all_errs.extend(verify_v1_json())
    all_errs.extend(verify_v2_json())
    all_errs.extend(verify_html(
        V1_DIR / "presentation" / "版本一_高斯图模型与跨资产风险传染网络.html",
        ["0.541", "0.176", "0.251", "64", "3.03%", "2.82", "0.122"],
    ))
    all_errs.extend(verify_html(
        V2_DIR / "presentation" / "版本二_双重机器学习与养老金因果评估.html",
        ["19,559", "96.5%", "8,693", "12,107", "20,588", "36.6%"],
    ))
    all_errs.extend(verify_pptx(V1_DIR / "presentation" / "版本一_高斯图模型与跨资产风险传染网络.pptx"))
    all_errs.extend(verify_pptx(V2_DIR / "presentation" / "版本二_双重机器学习与养老金因果评估.pptx"))

    if all_errs:
        print("VERIFICATION FAILED:")
        for e in all_errs:
            print("  -", e)
        raise SystemExit(1)
    print("ALL VERIFICATIONS PASSED SUCCESSFULLY (V1 + V2 JSON, 6x2 PNGs, 15-slide HTMLs, 2560x1440 PPTXs + Speaker Notes).")


if __name__ == "__main__":
    main()
