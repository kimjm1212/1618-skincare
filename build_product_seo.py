"""영문몰 상세페이지 8개에 SEO/GEO 텍스트(핵심성분·사용법·전성분·주의사항) + Product JSON-LD 를 채우고
llms.txt / sitemap lastmod / 메인 가격을 갱신한다.

전성분은 공통정보 및 양식/products.json 의 ingredients_en 만 쓴다(단일 진실 출처).
문구에 적은 성분이 전성분에 없으면 assert 로 멈춘다. 몇 번 돌려도 결과가 같다.

    python build_product_seo.py
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SITE = Path(__file__).parent / "웹소스"
BASE = "https://en.1618cosmetic.com/"
PRODUCTS = json.loads((Path(__file__).parents[1] / "공통정보 및 양식" / "products.json")
                      .read_text(encoding="utf-8"))["products"]
# ponytail: 아마존 판매가를 손으로 맞춘다(2026-09-17 SP-API 기준 8종 모두 18.99). 아마존 가격 바꾸면 여기도 바꿀 것
PRICE = "18.99"

HA6 = ["Sodium Hyaluronate", "Hyaluronic Acid", "Hydrolyzed Hyaluronic Acid", "Sodium Hyaluronate Crosspolymer",
       "Hydroxypropyltrimonium Hyaluronate", "Sodium Acetylated Hyaluronate"]
AA17 = ["Glycine", "Serine", "Glutamic Acid", "Aspartic Acid", "Leucine", "Alanine", "Lysine", "Arginine", "Tyrosine",
        "Phenylalanine", "Valine", "Threonine", "Proline", "Isoleucine", "Histidine", "Methionine", "Cysteine"]
CAUTION = [
    "Stop use and talk to a dermatologist if redness, swelling, itching or other irritation appears during or after use, "
    "including after exposure to direct sunlight.",
    "Do not apply to broken or damaged skin.",
    "Keep out of reach of children. Store away from direct sunlight.",
]

# 🔴 미국 페이지: 여드름·항균·미백(스킨라이트닝)·식약처 기능성 표현 금지, 샐몬 PDRN·아침세안 금지
PAGES = [
    dict(sku="toner", path="히알토너 상세/toner.html", img="p-toner.webp", asin="B08CGM1H45",
         name="Hyaluronic Acid Ampoule Toner", category="Toner", size="200 ml / 6.7 fl oz",
         desc="A hydrating toner with six forms of hyaluronic acid, panthenol, ceramide NP and collagen. "
              "Pat it on after cleansing, or soak cotton pads for a quick toner pack on dry areas.",
         benefits=["Six forms of hyaluronic acid for layered hydration",
                   "Panthenol and ceramide NP to keep skin comfortable and moisturized",
                   "The first step after cleansing",
                   "Doubles as a cotton pad toner pack"],
         key=[("Hyaluronic acid, 6 forms", HA6),
              ("Panthenol (provitamin B5)", ["Panthenol"]),
              ("Ceramide NP", ["Ceramide NP"]),
              ("Collagen", ["Hydrolyzed Collagen", "Collagen"]),
              ("Peptides", ["Acetyl Hexapeptide-8", "Hexapeptide-9", "Tripeptide-1", "Tripeptide-3"])],
         how="After cleansing, dispense an appropriate amount onto a cotton pad or your palm and let it absorb "
             "over the whole face. For a toner pack, soak cotton pads and place them on dry areas.",
         caution=[]),
    dict(sku="cleanser", path="티트리상세/teatree.html", img="p-teatree.webp", asin="B09BTPXXLL",
         name="Tea Tree Clearing Foam Cleanser", category="Cleanser", size="150 ml / 5.07 fl oz",
         desc="A foam cleanser with tea tree leaf oil, centella asiatica and witch hazel water, built on an "
              "amino acid-based cleansing agent. Work it into a rich lather, massage gently and rinse.",
         benefits=["Amino acid-based cleansing agent (sodium lauroyl glutamate)",
                   "Tea tree leaf oil and tea tree extract",
                   "Rich lather that rinses clean",
                   "Made for oily and sensitive skin"],
         key=[("Tea tree", ["Melaleuca Alternifolia (Tea Tree) Leaf Oil", "Melaleuca Alternifolia (Tea Tree) Extract"]),
              ("Centella asiatica", ["Centella Asiatica Extract", "Madecassoside", "Asiaticoside"]),
              ("Witch hazel water", ["Hamamelis Virginiana (Witch Hazel) Water"]),
              ("Amino acid-based cleanser", ["Sodium Lauroyl Glutamate"]),
              ("Ectoin", ["Ectoin"])],
         how="Take an appropriate amount and work it into a rich lather, then gently massage over the whole face. "
             "Rinse thoroughly with lukewarm water.",
         caution=["Do not use on children aged 3 or under."]),
    dict(sku="porepack", path="화산송이_영문상세/blackhead.html", img="p-blackhead.webp", asin="B09BQWRDJN",
         name="Volcanic Clay Blackhead Mask", category="Wash-Off Mask", size="120 g / 4.23 oz",
         desc="A wash-off clay mask with volcanic ash, kaolin and bentonite. Apply a thick layer, let it dry for "
              "about 10 minutes, then rinse to clear away excess sebum and impurities from pores.",
         benefits=["Volcanic ash with kaolin and bentonite clays",
                   "Helps clear blackheads, excess sebum and impurities",
                   "Tea tree, willow bark and hinoki leaf extracts",
                   "Rinse off after about 10 minutes"],
         key=[("Volcanic ash", ["Volcanic Ash"]),
              ("Kaolin and bentonite clays", ["Kaolin", "Bentonite"]),
              ("Tea tree extract", ["Melaleuca Alternifolia (Tea Tree) Extract"]),
              ("Willow bark extract", ["Salix Alba (Willow) Bark Extract"]),
              ("Hinoki leaf extract", ["Chamaecyparis Obtusa Leaf Extract"])],
         how="After cleansing, pat your face dry. Spread a thick, even layer over the face, avoiding the eye and "
             "mouth areas. After 10 minutes, once the mask has dried, rinse off with lukewarm water.",
         caution=["Avoid the eye area."]),
    dict(sku="mask", path="샐몬상세/salmon.html", img="p-salmon.webp", asin="B08CGNKFZ3",
         name="Salmon Firming Sleeping Mask", category="Sleeping Mask", size="100 g / 3.53 oz",
         desc="An overnight mask with salmon egg extract, peptides, niacinamide, adenosine and ceramide NP. "
              "Smooth it on as the last step before bed. No need to wash it off in the morning.",
         benefits=["Leave-on overnight mask, no rinsing needed",
                   "Salmon egg extract and two peptides",
                   "Niacinamide, adenosine and ceramide NP",
                   "Helps skin look firmer and more hydrated"],
         key=[("Salmon egg extract", ["Salmon Egg Extract"]),
              ("Peptides", ["Acetyl Hexapeptide-8", "Palmitoyl Pentapeptide-4"]),
              ("Niacinamide", ["Niacinamide"]),
              ("Adenosine", ["Adenosine"]),
              ("Centella asiatica", ["Centella Asiatica Extract"]),
              ("Ceramide NP and beta-glucan", ["Ceramide NP", "Beta-Glucan"])],
         how="Before bed, take an appropriate amount and spread it evenly over the skin. Leave it on while you sleep.",
         caution=[]),
    dict(sku="cream", path="링클케어상세_영문/wrinkle.html", img="p-wrinkle.webp", asin="B076Q26SF7",
         name="Intensive Wrinkle Care Cream", category="Cream", size="100 g / 3.52 oz",
         desc="A rich face cream with adenosine, GABA, 17 amino acids and gold. Apply it to the whole face "
              "and to the areas where wrinkles concern you most.",
         benefits=["Adenosine and GABA (aminobutyric acid)",
                   "A complex of 17 amino acids",
                   "Gold (CI 77480) in a rich, moisturizing cream",
                   "Helps reduce the look of wrinkles"],
         key=[("Adenosine", ["Adenosine"]),
              ("GABA", ["Aminobutyric Acid"]),
              ("17 amino acids", AA17),
              ("Gold", ["Gold (CI 77480)"]),
              ("Witch hazel and purslane", ["Hamamelis Virginiana (Witch Hazel) Extract", "Portulaca Oleracea Extract"])],
         how="Apply an appropriate amount to the whole face and any areas with wrinkle concerns, then spread evenly.",
         caution=[]),
    dict(sku="essence", path="쑥에센스상세/essence.html", img="p-essence.webp", asin="B0DCNLN16W",
         name="Artemisia Capillaris Essence", category="Essence", size="180 ml / 6.08 fl oz",
         desc="A four-ingredient essence made with artemisia capillaris (mugwort) extract. Smooth it on after "
              "cleansing, or soak a cotton pad and leave it on for 5 to 10 minutes when skin needs quick soothing.",
         benefits=["Just four ingredients",
                   "Artemisia capillaris (mugwort) extract",
                   "Soothes and hydrates sensitive skin",
                   "No added fragrance"],
         key=[("Artemisia capillaris (mugwort) extract", ["Artemisia Capillaris Extract"])],
         how="After cleansing, spread a small amount evenly over the skin. When skin needs quick soothing, soak a "
             "cotton pad with the essence and place it on the face for 5 to 10 minutes.",
         caution=[]),
    dict(sku="mist", path="미스트상세/mist.html", img="p-mist.webp", asin="B0CYWZLTF9",
         name="Betula Calming Dual Mist", category="Mist", size="90 ml / 3.04 fl oz",
         desc="A two-layer face mist of birch sap and sunflower seed oil, with niacinamide, panthenol and centella "
              "asiatica. Shake to mix, then spray after cleansing or any time during the day.",
         benefits=["Two layers: birch sap water and sunflower seed oil",
                   "Hydrates and calms skin",
                   "Niacinamide, panthenol and centella asiatica",
                   "Use after cleansing or throughout the day"],
         key=[("Birch sap", ["Betula Platyphylla Japonica Juice"]),
              ("Sunflower seed oil", ["Helianthus Annuus (Sunflower) Seed Oil"]),
              ("Niacinamide", ["Niacinamide"]),
              ("Panthenol", ["Panthenol"]),
              ("Centella asiatica", ["Centella Asiatica Extract"]),
              ("Adenosine", ["Adenosine"])],
         how="Shake well so the two layers mix, then spray over the whole face. Use it as a step after cleansing, "
             "or any time during the day.",
         caution=["Do not use on children aged 3 or under.", "Stop use right away if irritation occurs."]),
    dict(sku="poreampoule", path="편백수모공앰플상세/hinoki.html", img="p-hinoki.webp", asin="B0GVDM7KKM",
         name="Hinoki Pore Tightening Ampoule", category="Ampoule", size="30 ml / 1.01 fl oz",
         desc="A pore care ampoule with hinoki water (98,000 ppm) and spicules, plus niacinamide, panthenol, "
              "six forms of hyaluronic acid and 17 amino acids. Spicules may cause a light tingling feeling.",
         benefits=["Hinoki (Japanese cypress) water, 98,000 ppm",
                   "Spicules (hydrolyzed sponge) for pore and texture care",
                   "Six forms of hyaluronic acid and 17 amino acids",
                   "Helps pores look tighter and skin feel smoother"],
         key=[("Hinoki water", ["Chamaecyparis Obtusa Water"]),
              ("Spicules", ["Hydrolyzed Sponge"]),
              ("Niacinamide", ["Niacinamide"]),
              ("Panthenol", ["Panthenol"]),
              ("Hyaluronic acid, 6 forms", HA6),
              ("17 amino acids", AA17),
              ("Ceramide NP", ["Ceramide NP"])],
         how="Take an appropriate amount and spread it gently along the skin's texture, avoiding the eye and mouth "
             "areas, then pat lightly until absorbed.",
         caution=["Keep away from the eyes.",
                  "If you have sensitive skin, do a patch test on a small area first.",
                  "Contains spicules, so you may feel a tingling sensation. How strong it feels varies from person to person."]),
]

# 제품별 자주 묻는 질문 — 답은 공식 사용법, 전성분, 주의사항에 있는 사실로만
FAQ = {
    "toner": [
        ("When do I use the toner?", "Right after cleansing, as the first step. Apply it with a cotton pad or your palm."),
        ("Can I use it as a toner pack?", "Yes. Soak cotton pads with the toner and place them on dry areas."),
        ("Which forms of hyaluronic acid are in it?", "Six: " + ", ".join(HA6).lower() + "."),
    ],
    "cleanser": [
        ("How do I use the cleanser?", "Work a small amount into a rich lather, massage it over the face, then rinse with lukewarm water."),
        ("What is the cleansing agent?", "Sodium lauroyl glutamate, an amino acid-based cleansing agent."),
        ("Can children use it?", "Do not use it on children aged 3 or under."),
    ],
    "porepack": [
        ("How long do I leave the mask on?", "About 10 minutes, until the mask has dried. Then rinse it off with lukewarm water."),
        ("Where should I not apply it?", "Avoid the eye and mouth areas."),
        ("Which clays are in it?", "Kaolin and bentonite, together with volcanic ash."),
    ],
    "mask": [
        ("Do I need to rinse it off?", "No. It is a leave-on overnight mask, so there is no need to wash it off in the morning."),
        ("When do I apply it?", "As the last step of your evening routine, right before bed."),
        ("What is the key ingredient?", "Salmon egg extract, together with two peptides, niacinamide, adenosine and ceramide NP."),
    ],
    "cream": [
        ("Is there real gold in the cream?", "Yes. Gold (CI 77480) is in the ingredient list."),
        ("What is GABA?", "GABA is aminobutyric acid. It appears in the ingredient list as Aminobutyric Acid."),
        ("How do I apply it?", "Apply an appropriate amount to the whole face and any areas with wrinkle concerns, then spread evenly."),
    ],
    "essence": [
        ("How many ingredients does it have?", "Four: water, pentylene glycol, artemisia capillaris extract and caprylyl glycol."),
        ("Does it contain fragrance?", "No. There is no fragrance in the ingredient list."),
        ("Can I use it as a cotton pad pack?", "Yes. Soak a cotton pad with the essence and leave it on the face for 5 to 10 minutes."),
    ],
    "mist": [
        ("Why do I need to shake it?", "It has two layers, birch sap water and sunflower seed oil. Shaking mixes them before you spray."),
        ("When can I use it?", "After cleansing as part of your routine, or any time during the day."),
        ("Can children use it?", "Do not use it on children aged 3 or under."),
    ],
    "poreampoule": [
        ("Why does it tingle?", "It contains spicules (hydrolyzed sponge), which can cause a tingling feeling. How strong it feels varies from person to person."),
        ("How much hinoki water is in it?", "98,000 ppm of Chamaecyparis obtusa (hinoki) water."),
        ("Should I do a patch test?", "If you have sensitive skin, test it on a small area first. Keep it away from the eyes."),
    ],
}
COMMON_FAQ = [
    ("Where can I buy it in the US?", "On Amazon US. The Buy on Amazon button on this page opens the product listing."),
    ("Where is it made?", "In Korea."),
    ("How long can I use it after opening?", "Use it within 12 months after opening."),
]
# 루틴 순서(묽은 것 → 진한 것). 설명은 각 제품의 공식 사용법(how)을 그대로 쓴다
ROUTINE = [("Cleanse", "cleanser"), ("Wash-off clay mask, after cleansing", "porepack"), ("Tone", "toner"),
           ("Essence", "essence"), ("Ampoule", "poreampoule"), ("Cream", "cream"),
           ("Overnight mask, last step of the evening", "mask")]


def inci(p):
    # "1,2-Hexanediol" 안의 쉼표는 구분자가 아니다 → 쉼표+공백으로만 자른다
    return re.split(r",\s+", PRODUCTS[p["sku"]]["ingredients_en"].strip())


def check(p):
    names = inci(p)
    for _, terms in p["key"]:
        for t in terms:
            assert t in names, f"{p['sku']}: '{t}' 가 전성분에 없음"
    if "No added fragrance" in p["benefits"]:
        assert "Fragrance" not in names, f"{p['sku']}: 향료가 들어있는데 무향 표기"
    text = " ".join([p["desc"], *p["benefits"], p["how"], *sum(map(list, FAQ[p["sku"]]), [])]).lower()
    if any("no fragrance" in a.lower() for _, a in FAQ[p["sku"]]):
        assert "Fragrance" not in names, f"{p['sku']}: 향료가 들어있는데 FAQ 에 무향"
    for bad in ("acne", "antibacterial", "pdrn", "whiten", "lighten", "blemish", "morning wash"):
        assert bad not in text, f"{p['sku']}: 금지 표현 '{bad}'"


e = html.escape


def url(p):
    return BASE + quote(p["path"])


def amazon(p):
    return f"https://www.amazon.com/dp/{p['asin']}"


def key_item(label, terms):
    if [label.lower()] == [x.lower() for x in terms]:
        return f"<strong>{e(label)}</strong>"
    return f"<strong>{e(label)}</strong>: {e(', '.join(terms))}"


def faqs(p):
    return FAQ[p["sku"]] + COMMON_FAQ


def info_block(p):
    lis = "\n".join(f"                            <li>{e(b)}</li>" for b in p["benefits"])
    return f'''<div class="product-detail-info">
                    <h1>{e(p["name"])}</h1>
                    <p class="product-category">{e(p["category"])}, {e(p["size"])}</p>
                    <div class="product-price">${PRICE}</div>
                    <p class="product-description">{e(p["desc"])}</p>

                    <div class="product-features">
                        <h3>Key Benefits:</h3>
                        <ul>
{lis}
                        </ul>
                    </div>

                    <a href="{amazon(p)}" target="_blank" rel="noopener" class="amazon-button-large">Buy on Amazon</a>
                </div>
            </div>

            <section class="product-facts">
                <div>
                    <h2>Key Ingredients</h2>
                    <ul>
{chr(10).join(f"                        <li>{key_item(k, t)}</li>" for k, t in p["key"])}
                    </ul>
                </div>
                <div>
                    <h2>How to Use</h2>
                    <p>{e(p["how"])}</p>
                </div>
                <div>
                    <h2>Full Ingredients</h2>
                    <p class="small">{e(", ".join(inci(p)))}</p>
                </div>
                <div>
                    <h2>FAQ</h2>
{chr(10).join(f"                    <h3>{e(q)}</h3>{chr(10)}                    <p>{e(a)}</p>" for q, a in faqs(p))}
                    <p class="small"><a href="../routine.html">See where it fits in the 1.618 routine</a></p>
                </div>
                <div>
                    <h2>Caution</h2>
                    <ul class="small">
{chr(10).join(f"                        <li>{e(c)}</li>" for c in p["caution"] + CAUTION)}
                    </ul>
                </div>
            </section>

            '''


def jsonld(p):
    product = {
        "@type": "Product",
        "name": f"1.618 {p['name']}",
        "brand": {"@type": "Brand", "name": "1.618"},
        "description": p["desc"],
        "image": BASE + "img/" + p["img"],
        "url": url(p),
        "sku": PRODUCTS[p["sku"]]["barcode"],
        "gtin13": PRODUCTS[p["sku"]]["barcode"],
        "category": p["category"],
        "size": p["size"],
        "countryOfOrigin": {"@type": "Country", "name": "KR"},
        "offers": {"@type": "Offer", "url": amazon(p), "price": PRICE, "priceCurrency": "USD",
                   "availability": "https://schema.org/InStock"},
    }
    faq = {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs(p)]}
    data = {"@context": "https://schema.org", "@graph": [product, faq]}
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\n    ")
    return f'<script type="application/ld+json">\n    {body}\n    </script>\n    '


def sub1(pattern, repl, text):
    out, n = re.subn(pattern, lambda _: repl, text, count=1, flags=re.S)
    assert n == 1, f"패턴 못 찾음: {pattern[:60]}"
    return out


def build_page(p):
    f = SITE / p["path"]
    t = f.read_text(encoding="utf-8")
    title = f"{p['name']} | 1.618 Korean Skincare"
    meta = e(f"1.618 {p['name']}, {p['size']}. {p['desc']}")
    t = sub1(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{meta}">', t)
    t = sub1(r"<title>.*?</title>", f"<title>{e(title)}</title>", t)
    t = sub1(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{e(title)}">', t)
    t = sub1(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{meta}">', t)
    t = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', "", t, flags=re.S)
    t = sub1(r'(?=<link rel="stylesheet" href="https://cdn\.jsdelivr\.net)', jsonld(p), t)
    t = sub1(r'<img src="\.\./img/[^"]+"[^>]*>',
             f'<img src="../img/{p["img"]}" alt="1.618 {e(p["name"])}" width="900" height="900">', t)
    t = sub1(r'<div class="product-detail-info">.*?(?=<div class="product-detail-description">)', info_block(p), t)
    f.write_text(t, encoding="utf-8", newline="\n")


def build_index():
    f = SITE / "index.html"
    t = re.sub(r'<div class="product-price">\$[\d.]+</div>', f'<div class="product-price">${PRICE}</div>',
               f.read_text(encoding="utf-8"))
    if 'href="routine.html"' not in t:
        contact = '<li><a href="#contact">Contact</a></li>'
        assert t.count(contact) == 1
        t = t.replace(contact, '<li><a href="routine.html">Routine</a></li>\n                ' + contact)
    f.write_text(t, encoding="utf-8", newline="\n")


def build_llms():
    lines = [
        "# 1.618 Skincare",
        "",
        "> 1.618 is a Korean skincare brand named after the golden ratio. Products are made in Korea and sold in "
        "the US on Amazon. This is the official English site. The official Korean store is https://1618cosmetic.com/.",
        "",
        "## Products",
        "",
    ]
    for p in PAGES:
        lines.append(f"- [1.618 {p['name']}]({url(p)}): {p['category']}, {p['size']}. {p['desc']} "
                     f"Buy on Amazon: {amazon(p)}")
    lines += [
        "",
        "## Guides",
        "",
        f"- [The 1.618 routine, step by step]({BASE}routine.html): which 1.618 product goes where in a skincare "
        "routine, with each product's official directions.",
        "",
        "## Where to buy",
        "",
        "- Amazon US brand store: https://www.amazon.com/stores/GoldenRatio1618Cosmetic/page/2E637E4C-FEA2-4756-B501-0C4CF772875E",
        "- Korea (official store): https://1618cosmetic.com/",
        "",
        "## Contact",
        "",
        "- Email: kim_1212@naver.com",
        "- Instagram: https://www.instagram.com/1.618_cosmetic_US",
        "- TikTok: https://www.tiktok.com/@1.618_us",
        "- YouTube: https://www.youtube.com/@1.618_US",
        "",
    ]
    (SITE / "llms.txt").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def build_sitemap():
    rows = [(BASE, "1.0"), (BASE + "routine.html", "0.8")] + [(url(p), "0.8") for p in PAGES]
    body = "".join(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{date.today()}</lastmod>\n"
                   f"    <priority>{pr}</priority>\n  </url>\n" for u, pr in rows)
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      f"{body}</urlset>\n", encoding="utf-8", newline="\n")


def build_routine():
    by = {p["sku"]: p for p in PAGES}
    steps = "\n".join(
        f'                <li>\n'
        f'                    <h2>{e(step)}</h2>\n'
        f'                    <p><a href="{quote(by[s]["path"])}"><strong>1.618 {e(by[s]["name"])}</strong></a>, {e(by[s]["size"])}</p>\n'
        f'                    <p>{e(by[s]["how"])}</p>\n'
        f'                    <p class="small"><a href="{amazon(by[s])}" target="_blank" rel="noopener">Buy on Amazon</a></p>\n'
        f'                </li>' for step, s in ROUTINE)
    mist = by["mist"]
    title = "The 1.618 Skincare Routine, Step by Step | 1.618 Korean Skincare"
    desc = ("Which 1.618 Korean skincare product goes where: cleanser, clay mask, toner, essence, ampoule, "
            "cream and overnight mask, with each product's official directions.")
    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <meta name="description" content="{e(desc)}">
    <title>{e(title)}</title>
    <link rel="canonical" href="{BASE}routine.html">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="1.618 Skincare">
    <meta property="og:title" content="{e(title)}">
    <meta property="og:description" content="{e(desc)}">
    <meta property="og:url" content="{BASE}routine.html">
    <meta property="og:image" content="{BASE}og-image.jpg">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <!-- build_product_seo.py 가 만드는 파일. 직접 고치지 말 것 -->
    <nav class="navbar">
        <div class="container">
            <a class="logo" href="index.html"><img src="1.618.png" alt="1.618" class="logo-image"></a>
            <ul class="nav-menu">
                <li><a href="index.html">Home</a></li>
                <li><a href="index.html#about">Brand</a></li>
                <li><a href="index.html#products">Products</a></li>
                <li><a href="routine.html" class="active">Routine</a></li>
                <li><a href="index.html#contact">Contact</a></li>
            </ul>
            <div class="nav-right">
                <a class="lang-switch" href="https://www.1618cosmetic.com/" title="한국어 사이트로 이동">KO</a>
                <div class="hamburger" aria-label="Menu"><span></span><span></span><span></span></div>
            </div>
        </div>
    </nav>

    <section class="product-detail">
        <div class="container">
            <div class="product-facts">
                <div>
                    <h1>The 1.618 routine, step by step</h1>
                    <p>Go from the thinnest texture to the richest. Use only the steps you need, and follow each product's own directions.</p>
                </div>
                <ol class="routine">
{steps}
                </ol>
                <div>
                    <h2>Any time: 1.618 {e(mist["name"])}</h2>
                    <p>{e(mist["how"])}</p>
                    <p class="small"><a href="{quote(mist["path"])}">Product details</a>, <a href="{amazon(mist)}" target="_blank" rel="noopener">Buy on Amazon</a></p>
                </div>
            </div>
        </div>
    </section>

    <footer id="contact" class="footer">
        <div class="footer-content">
            <div class="footer-logo">1.618</div>
            <p>Korean skincare in the golden ratio. Available on Amazon US.</p>
            <p>For inquiries: <a href="mailto:kim_1212@naver.com">kim_1212@naver.com</a></p>
            <p class="footer-lang"><a href="https://www.1618cosmetic.com/">한국어 사이트 &rarr;</a></p>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2026 1.618 Skincare. All rights reserved.</p>
        </div>
    </footer>
    <script src="script.js"></script>
</body>
</html>
'''
    (SITE / "routine.html").write_text(page, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    for p in PAGES:
        check(p)
    assert len({p["path"] for p in PAGES}) == 8
    for p in PAGES:
        build_page(p)
        print("OK", p["path"])
    build_index()
    build_routine()
    build_llms()
    build_sitemap()
    print("OK index.html / routine.html / llms.txt / sitemap.xml")
