"""
Slide images as SVG, using only Python's standard library (no installs).

    python make_slide_visuals.py      (from astraterra-kit/docs/slides/)
    -> pipeline.svg     slide 6: NASA data -> harmonize -> model -> decision
    -> validation.svg   slide 5: real USDA corn yields vs our model (from data/validation/validation_vernon_wi.json)

To put them in Google Slides: open the .svg in Chrome, take a screenshot (Windows: Win+Shift+S), paste.
Colours match the slides: dark green background, yellow accents, white text.
"""

import json
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATION = HERE.parent.parent / "data" / "validation" / "validation_vernon_wi.json"

BG, YELLOW, WHITE, SOFT, GREEN, RED, AMBER = "#06392f", "#f6c61a", "#ffffff", "#bcd3c8", "#3f9b6b", "#e0533f", "#f0a23a"
FONT = "font-family='Segoe UI, Arial, sans-serif'"


def text(x, y, s, size=20, color=WHITE, weight="normal", anchor="start"):
    return (f"<text x='{x}' y='{y}' {FONT} font-size='{size}' fill='{color}' font-weight='{weight}' "
            f"text-anchor='{anchor}'>{escape(str(s))}</text>")


def pipeline():
    W, H = 1600, 760
    boxes = [
        ("1  DATA", [("NASA POWER", True), ("21 years of daily weather", False), ("rain · heat · sun · soil moisture", False), ("", False),
                     ("NASA SRTM", True), ("30 m elevation: slopes", False), ("", False),
                     ("+ SoilGrids soil", False), ("+ USDA crop maps", False), ("+ FAO-56 crop water", False)]),
        ("2  HARMONIZE", [("Different resolutions,", True), ("one field", True), ("", False),
                          ("weather   50 km", False), ("soil        250 m", False), ("elevation   30 m", False), ("crop maps   30 m", False), ("", False),
                          ("daily → monthly, per field", True)]),
        ("3  MODEL", [("Water balance", True), ("FAO-56 crop demand", False), ("+ soil water bucket", False), ("", False),
                      ("21-year replay", True), ("every rotation, 2005-2025", False), ("", False),
                      ("Rule-based scores", True), ("water · erosion · nitrogen", False), ("soil · pests · forage", False), ("", False),
                      ("Year types + trends", True), ("k-means: hot/dry, normal, wet", False), ("Mann-Kendall trend tests", False)]),
        ("4  DECISION", [("Ranked recommendation", True), ("for the farmer's priorities", False), ("", False),
                         ("Reasons with numbers", True), ("Evidence + sources", True), ("Risks for local review", True),
                         ("Data gaps", True), ("", False), ("Farm Journal clues", True)]),
    ]
    bw, gap, top, bh = 360, 40, 30, 640
    x0 = (W - (4 * bw + 3 * gap)) / 2
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
           f"<rect width='{W}' height='{H}' fill='{BG}'/>",
           "<defs><marker id='a' markerWidth='10' markerHeight='10' refX='8' refY='5' orient='auto'>"
           f"<path d='M0,0 L10,5 L0,10 z' fill='{YELLOW}'/></marker></defs>"]
    for i, (title, lines) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        highlight = i == 1                      # the challenge asks about harmonizing resolutions
        out.append(f"<rect x='{x}' y='{top}' width='{bw}' height='{bh}' rx='18' fill='none' "
                   f"stroke='{YELLOW if highlight else WHITE}' stroke-width='{4 if highlight else 2}'/>")
        out.append(f"<rect x='{x}' y='{top}' width='{bw}' height='64' rx='18' fill='{YELLOW}'/>")
        out.append(f"<rect x='{x}' y='{top + 40}' width='{bw}' height='24' fill='{YELLOW}'/>")
        out.append(text(x + bw / 2, top + 44, title, 32, BG, "bold", "middle"))
        y = top + 112
        for line, bold in lines:
            if line:
                out.append(text(x + 22, y, line, 26 if bold else 22, WHITE if bold else SOFT, "bold" if bold else "normal"))
            y += 40 if line else 16
        if i < 3:
            ax = x + bw + 6
            out.append(f"<line x1='{ax}' y1='{top + bh / 2}' x2='{ax + gap - 14}' y2='{top + bh / 2}' "
                       f"stroke='{YELLOW}' stroke-width='5' marker-end='url(#a)'/>")
    out.append(text(W / 2, H - 40, "Every score traces back to a real number: no AI decides the scores.", 28, YELLOW, "bold", "middle"))
    out.append("</svg>")
    return "\n".join(out)


def validation():
    corn = json.loads(VALIDATION.read_text())["crops"]["corn"]["years"]
    W, H = 1600, 860
    left, right, top, mid, bottom = 150, 60, 100, 300, 720
    n = len(corn)
    step = (W - left - right) / n
    bar = step * 0.62
    max_pct = 20                                   # axis: -20% .. +20% (bars end by y=500)
    def y_of(pct):
        return mid - pct / max_pct * (mid - top)

    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
           f"<rect width='{W}' height='{H}' fill='{BG}'/>",
           text(left, 58, "Real corn yield vs trend, Vernon County WI (USDA NASS)  ·  model water stress below", 26, WHITE, "bold")]
    for pct in (-20, -10, 0, 10, 20):
        y = y_of(pct)
        out.append(f"<line x1='{left}' y1='{y}' x2='{W - right}' y2='{y}' stroke='{SOFT}' stroke-opacity='{0.6 if pct == 0 else 0.18}'/>")
        out.append(text(left - 14, y + 6, f"{pct:+d}%" if pct else "trend", 17, SOFT, anchor="end"))
    for i, yr in enumerate(corn):
        cx = left + step * i + step / 2
        key = yr["year"] in (2012, 2023)
        pct = yr["yield_vs_trend_pct"]
        y1, y2 = sorted((y_of(0), y_of(pct)))
        color = RED if key else (GREEN if pct >= 0 else SOFT)
        out.append(f"<rect x='{cx - bar / 2}' y='{y1}' width='{bar}' height='{max(y2 - y1, 1)}' rx='3' fill='{color}'/>")
        if key:
            out.append(text(cx + bar / 2 + 6, y_of(pct) - 4, f"{pct:+.0f}%", 24, WHITE, "bold"))
        # model stress dots row
        s = yr["model_stress_pct"]
        r = 4 + s * 0.75
        out.append(f"<circle cx='{cx}' cy='{bottom - 70}' r='{r}' fill='{RED if s >= 15 else (AMBER if s > 0 else SOFT)}' "
                   f"fill-opacity='{1 if s else 0.35}'/>")
        if s >= 15:
            out.append(text(cx, bottom - 70 - r - 8, f"{s}%", 22, WHITE, "bold", "middle"))
        out.append(text(cx, bottom - 10, yr["year"] if yr["year"] % 5 == 0 or key else "", 18,
                        YELLOW if key else SOFT, "bold" if key else "normal", "middle"))
    out.append(f"<line x1='{left}' y1='{bottom - 185}' x2='{W - right}' y2='{bottom - 185}' stroke='{SOFT}' stroke-opacity='0.3'/>")
    out.append(text(left, bottom - 158, "Model water stress (NASA weather only): bigger, redder dot = more stress", 20, SOFT))
    out.append(text(left - 14, bottom - 64, "model", 18, SOFT, anchor="end"))
    out.append(text(W / 2, H - 50, "Using only NASA weather, the model's 2 worst years (2012, 2023) are the 2 lowest yields on record.",
                    24, YELLOW, "bold", "middle"))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    (HERE / "pipeline.svg").write_text(pipeline(), encoding="utf-8")
    (HERE / "validation.svg").write_text(validation(), encoding="utf-8")
    print("written pipeline.svg and validation.svg in", HERE)
