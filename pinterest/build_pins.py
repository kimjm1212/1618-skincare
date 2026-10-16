"""Pinterest 핀 이미지(1000x1500, 2:3) — 영문몰 제품사진 + 브랜드 그래픽 표준(#ffbf00 / #3a2e2b / Paperlogy / 실제 로고).

    python build_pins.py          # 시안 A·B 둘 다 → pins/A_*.png, pins/B_*.png + 비교판 compare.png
    python build_pins.py A        # 한 시안만

문구는 build_product_seo.PAGES(영문몰 상세와 같은 출처)에서 가져온다 → 미국 금지 표현 규칙도 같이 따른다.
"""
import base64
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from build_product_seo import PAGES, ROUTINE  # noqa: E402

IMG = HERE.parent / "웹소스" / "img"
OUT = HERE / "pins"
FONT = "file:///C:/Users/user/AppData/Local/Microsoft/Windows/Fonts/Paperlogy-{}.ttf"
_d = re.search(r' d="([^"]+)"', Path(r"d:/Desktop/클로드/1.618 로고.svg").read_text(encoding="utf-8")).group(1)
LOGO = ('<svg class="logo" viewBox="138 200 228 100" xmlns="http://www.w3.org/2000/svg">'
        f'<path fill="currentColor" d="{_d}"/></svg>')

# 핀 제목(사진 위 큰 글씨) — 상세페이지 benefits 에 있는 사실만 짧게 바꿔 쓴 것
HOOK = {
    "toner": "6 forms of hyaluronic acid in one toner",
    "cleanser": "An amino acid foam cleanser with tea tree",
    "porepack": "A 10-minute volcanic clay mask for blackheads",
    "mask": "Sleep in it. No rinsing in the morning.",
    "cream": "Adenosine, 17 amino acids and gold",
    "essence": "Just 4 ingredients. Mugwort essence.",
    "mist": "Shake, spray, calm. A two-layer birch mist.",
    "poreampoule": "Hinoki water 98,000 ppm pore ampoule",
}

CSS = "".join(f"@font-face{{font-family:'PL';font-weight:{w};src:url('{FONT.format(f)}')}}"
              for w, f in [(500, "5Medium"), (600, "6SemiBold"), (800, "8ExtraBold")]) + """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1000px;height:1500px;font-family:'PL',sans-serif;-webkit-font-smoothing:antialiased;overflow:hidden}
.logo{display:block;height:44px;width:auto}
.photo{width:1000px;height:1000px;object-fit:cover;display:block}
h1{font-weight:800;font-size:66px;line-height:1.14;letter-spacing:-2px}
.name{font-weight:600;font-size:30px;letter-spacing:-.4px}
ul{list-style:none}
li{font-weight:500;font-size:27px;line-height:1.35;padding-left:26px;position:relative;margin-top:8px}
li:before{content:"";position:absolute;left:0;top:15px;width:11px;height:11px;border-radius:50%;background:currentColor}
.url{font-weight:600;font-size:24px;letter-spacing:.5px}
/* A: 사진 위 · 진한 띠 아래 */
.A{background:#3a2e2b;color:#ffbf00}
.A .band{height:500px;padding:46px 60px 0;position:relative}
.A h1{font-size:64px;color:#fff}
.A ul{margin-top:26px;color:#e9dccb}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:10px 40px;list-style:none}
.steps li{padding:0;margin:0;font-size:38px;font-weight:600}.steps li:before{display:none}
.A .name{margin-top:18px;color:#ffbf00}
.A .foot{position:absolute;left:60px;right:60px;bottom:44px;display:flex;justify-content:space-between;align-items:center}
.A .logo{color:#ffbf00;height:40px}.A .url{color:#ffbf00}
/* B: 노란 면 글씨 위 · 사진 아래 */
.B{background:#ffbf00;color:#3a2e2b}
.B .top{height:500px;padding:50px 60px 0;position:relative}
.B .logo{color:#3a2e2b}
.B h1{margin-top:34px}
.B .name{margin-top:18px}
.B .url{position:absolute;right:60px;top:58px}
/* 루틴 */
.grid{display:grid;grid-template-columns:repeat(4,250px)}
.grid div{position:relative}.grid img{width:250px;height:250px;object-fit:cover;display:block}
.grid span{position:absolute;left:12px;top:10px;font-weight:800;font-size:26px;color:#3a2e2b;
  background:#fff;border-radius:50%;width:44px;height:44px;text-align:center;line-height:44px}
"""


def b64(name):
    return "data:image/webp;base64," + base64.b64encode((IMG / name).read_bytes()).decode()


def product(v, p):
    name = f'1.618 {p["name"]}'
    lis = "".join(f"<li>{b}</li>" for b in p["benefits"][:2])
    if v == "A":
        return (f'<body class="A"><img class="photo" src="{b64(p["img"])}">'
                f'<div class="band"><h1>{HOOK[p["sku"]]}</h1><div class="name">{name}</div><ul>{lis}</ul>'
                f'<div class="foot">{LOGO}<span class="url">en.1618cosmetic.com</span></div></div></body>')
    return (f'<body class="B"><div class="top">{LOGO}<span class="url">en.1618cosmetic.com</span>'
            f'<h1>{HOOK[p["sku"]]}</h1><div class="name">{name}</div></div>'
            f'<img class="photo" src="{b64(p["img"])}"></body>')


def routine(v):
    by = {p["sku"]: p for p in PAGES}
    order = [s for _, s in ROUTINE] + ["mist"]
    cells = "".join(f'<div><img src="{b64(by[s]["img"])}"><span>{i}</span></div>' for i, s in enumerate(order, 1))
    cells = cells.replace("<span>8</span>", "<span>+</span>")  # 미스트 = 아무 때나
    steps = ["Cleanse", "Clay mask", "Tone", "Essence", "Ampoule", "Cream", "Overnight mask", "Mist, any time"]
    lis = "".join(f"<li>{i}. {s}</li>" for i, s in enumerate(steps[:7], 1))
    if v == "A":
        return (f'<body class="A"><div class="grid" style="height:500px">{cells}</div>'
                f'<div class="band" style="height:1000px;padding-top:70px">'
                f'<h1 style="font-size:72px">The Korean skincare routine, step by step</h1>'
                f'<ul class="steps" style="margin-top:44px;color:#fff">{lis}<li>+ Mist, any time</li></ul>'
                f'<div class="foot">{LOGO}<span class="url">en.1618cosmetic.com</span></div></div></body>')
    return (f'<body class="B"><div class="top" style="height:1000px">{LOGO}'
            f'<h1 style="font-size:96px;margin-top:90px">The Korean skincare routine, step by step</h1>'
            f'<ul class="steps" style="margin-top:70px;gap:22px 40px">{lis}<li>+ Mist, any time</li></ul>'
            f'<span class="url" style="top:auto;bottom:40px">en.1618cosmetic.com</span></div>'
            f'<div class="grid">{cells}</div></body>')


def build(variants):
    from playwright.sync_api import sync_playwright
    OUT.mkdir(exist_ok=True)
    files = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1000, "height": 1500})
        for v in variants:
            jobs = [(p["sku"], product(v, p)) for p in PAGES] + [("routine", routine(v))]
            for key, body in jobs:
                pg.set_content(f"<html><head><style>{CSS}</style></head>{body}</html>")
                pg.evaluate("document.fonts.ready")
                f = OUT / f"{v}_{key}.png"
                pg.screenshot(path=str(f))
                files.append(f)
        b.close()
    return files


def compare(files):
    """실제 피드 크기(폭 236px)로 줄인 비교판 — 줄 위 A, 아래 B."""
    from PIL import Image
    rows = {}
    for f in files:
        rows.setdefault(f.stem[0], []).append(Image.open(f).resize((236, 354)))
    w = max(len(r) for r in rows.values())
    sheet = Image.new("RGB", (w * 246 + 10, len(rows) * 364 + 10), "white")
    for y, r in enumerate(rows.values()):
        for x, im in enumerate(r):
            sheet.paste(im, (10 + x * 246, 10 + y * 364))
    sheet.save(HERE / "compare.png")


def sheet():
    """업로드용 문구표 pins.csv — 제목·설명·링크(utm=pinterest). 이미지는 pins/ 에서 고른 시안."""
    import csv
    from urllib.parse import quote
    base = "https://en.1618cosmetic.com/"
    utm = "?utm_source=pinterest&utm_medium=social&utm_campaign=organic_pin"
    rows = [(p["sku"], f'{HOOK[p["sku"]]} | 1.618 {p["name"]}'[:100],
             f'{p["desc"]} Korean skincare by 1.618, available on Amazon US.'[:500],
             base + quote(p["path"]) + utm) for p in PAGES]
    rows.append(("routine", "The Korean skincare routine, step by step | 1.618",
                 "Cleanse, clay mask, tone, essence, ampoule, cream, overnight mask, plus a mist any time. "
                 "Which 1.618 product goes where in a Korean skincare routine.", base + "routine.html" + utm))
    with open(HERE / "pins.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["image", "title", "description", "link"])
        w.writerows(rows)


if __name__ == "__main__":
    fs = build(sys.argv[1:] or ["A", "B"])
    compare(fs)
    sheet()
    print(len(fs), "pins →", OUT)
