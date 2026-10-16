"""Pinterest 핀 게시 — 자동화 크롬(9222, Pinterest 로그인됨)의 핀 만들기 화면을 그대로 조작한다.

    python post_pin.py mask          # 그 핀 하나
    python post_pin.py --next        # 아직 안 올린 것 중 ORDER 순서로 1개
    python post_pin.py --schedule 2026.10.17 [A]   # 그 시안의 남은 것 전부 그날부터 하루 1개씩 Pinterest 예약

이미지 = pins/{시안}_{sku}.png, 제목·설명·링크 = CSV[시안]. 올린 기록 posted.json(같은 핀 두 번 안 올림).
게시 성공 판정 = 내 프로필 '생성됨' 목록에 새 핀 id 가 생겼는지(버튼 클릭만으로 성공 처리하지 않음).
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
LOG = HERE / "posted.json"
CSV = {"B": "pins.csv", "A": "pins_A.csv"}  # 시안별 문구표. 기록 키 = B는 sku, A는 "A_sku"
PROFILE = "https://kr.pinterest.com/1618cosmetic/_created/"
BOARD = {"routine": "Korean Skincare Routine", "toner": "Korean Skincare Routine",
         "essence": "Korean Skincare Routine", "poreampoule": "Korean Skincare Routine",
         "mask": "K-Beauty Masks & Cleansers", "porepack": "K-Beauty Masks & Cleansers",
         "cleanser": "K-Beauty Masks & Cleansers",
         "cream": "Anti-Aging Skincare", "mist": "Anti-Aging Skincare"}
ORDER = {"B": ["routine", "mask", "toner", "porepack", "cream", "essence", "cleanser", "poreampoule", "mist"],
         "A": ["mask", "toner", "routine", "cream", "porepack", "essence", "cleanser", "poreampoule", "mist"]}
TOPICS = ["Korean skincare", "Skincare routine"]
SCHEDULE_TIME = "11:00 AM"  # 한국시간 = 미국 동부 전날 밤 10시. 목록이 30분 단위라 11:11 은 없음


def _pin_ids(pg):
    pg.goto(PROFILE, wait_until="commit")
    pg.wait_for_timeout(5000)
    return {h.split("/")[2] for h in pg.eval_on_selector_all('a[href^="/pin/"]', "as => as.map(a => a.getAttribute('href'))")}


def key(sku, variant):
    return sku if variant == "B" else f"{variant}_{sku}"


def post(sku, at=None, variant="B"):
    """at='2026.10.18' 이면 그 날 SCHEDULE_TIME 에 Pinterest 예약 게시(PC 꺼져 있어도 올라감)."""
    from playwright.sync_api import sync_playwright
    row = {r["image"]: r for r in csv.DictReader(open(HERE / CSV[variant], encoding="utf-8-sig"))}[sku]
    with sync_playwright() as pw:
        ctx = pw.chromium.connect_over_cdp("http://127.0.0.1:9222").contexts[0]
        pg = ctx.new_page()
        pg.set_default_navigation_timeout(90000)
        try:
            before = _pin_ids(pg)
            pg.goto("https://kr.pinterest.com/pin-creation-tool/", wait_until="commit")
            pg.wait_for_selector("#storyboard-upload-input", state="attached", timeout=30000)
            pg.set_input_files("#storyboard-upload-input", str(HERE / "pins" / f"{variant}_{sku}.png"))
            pg.wait_for_timeout(5000)
            pg.fill("#storyboard-selector-title", row["title"])
            pg.locator("div[contenteditable=true]").first.click()
            pg.keyboard.insert_text(row["description"])
            pg.fill("#WebsiteField", row["link"])
            # 보드: 있으면 고르고 없으면 만든다
            pg.click("[data-test-id=board-dropdown-select-button]")
            pg.wait_for_timeout(1500)
            item = pg.get_by_text(BOARD[sku], exact=True)
            if item.count():
                item.first.click()
            else:
                pg.get_by_text("보드 만들기", exact=True).click()
                pg.fill("#boardEditName", BOARD[sku])
                pg.locator("[role=dialog] button[type=submit]").click()
            pg.wait_for_timeout(2000)
            assert BOARD[sku] in pg.locator("[data-test-id=board-dropdown-select-button]").inner_text(), "보드 선택 실패"
            for t in TOPICS:
                pg.fill("#combobox-storyboard-interest-tags", t)
                pg.wait_for_timeout(2500)
                if pg.locator("[role=option]").count():
                    pg.locator("[role=option]").first.click()
                    pg.wait_for_timeout(800)
            pg.click("[data-test-id=storyboard-show-more-options-button]")
            pg.wait_for_timeout(1000)
            if pg.is_checked("#stelaSwitch"):  # '비슷한 상품 표시' = 남의 상품을 옆에 띄움 → 끈다
                pg.locator("#stelaSwitch").click(force=True)
            assert pg.input_value("#WebsiteField").startswith("https://en.1618cosmetic.com/"), "링크 입력 실패"
            if at:
                pg.bring_to_front()  # 창이 뒤에 있으면 시간 목록이 안 열린다
                pg.locator("#pin-draft-switch-group").click(force=True)
                pg.wait_for_timeout(1500)
                d = pg.locator("input[id^=pin-draft-schedule-date-field]")
                t = pg.locator("input[id^=pin-draft-schedule-time-field]")
                d.click(); pg.keyboard.press("Control+A"); pg.keyboard.type(at); pg.keyboard.press("Escape")
                t.click(); pg.wait_for_timeout(1500)
                pg.locator("[role=menuitem]", has_text=SCHEDULE_TIME).first.click()
                pg.wait_for_timeout(800)
                assert (d.input_value(), t.input_value()) == (at, SCHEDULE_TIME), f"예약시각 입력 실패 {d.input_value()} {t.input_value()}"
                pg.get_by_role("button", name="예약", exact=True).locator("visible=true").first.click()
                dlg = pg.locator("[role=dialog]").filter(has_text="예약 일정")  # "예약한 후에는 변경할 수 없습니다" 확인창
                dlg.wait_for(timeout=20000)
                dlg.get_by_role("button", name="예약", exact=True).click()
                y, m, dd = at.split(".")
                pg.get_by_text(f"예약 시간: {int(m)}월 {int(dd)}일").first.wait_for(timeout=30000)
                pin = f"scheduled {at} {SCHEDULE_TIME}"
            else:
                pg.get_by_role("button", name="게시").first.click()
                pg.wait_for_timeout(8000)
                new = _pin_ids(pg) - before
                if not new:
                    raise RuntimeError("게시 버튼은 눌렀지만 프로필에 새 핀이 안 보임")
                pin = sorted(new)[-1]
        finally:
            pg.close()
    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {}
    log[key(sku, variant)] = {"pin": pin, "at": datetime.now().isoformat(timespec="seconds"), "variant": variant}
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK {variant}_{sku} → {pin}")
    return pin


if __name__ == "__main__":
    done = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {}
    if sys.argv[1:] == ["--next"]:
        left = [s for s in ORDER["B"] if s not in done]
        if not left:
            print("모두 게시됨")
            sys.exit(0)
        post(left[0])
    elif sys.argv[1] == "--schedule":  # --schedule 2026.10.17 [A] → 그 시안의 남은 것 전부 그날부터 하루 1개씩 예약
        from datetime import timedelta
        day = datetime.strptime(sys.argv[2], "%Y.%m.%d")
        v = sys.argv[3] if len(sys.argv) > 3 else "B"
        for i, s in enumerate(x for x in ORDER[v] if key(x, v) not in done):
            post(s, (day + timedelta(days=i)).strftime("%Y.%m.%d"), v)
    else:
        for s in sys.argv[1:]:
            print(f"SKIP {s} (이미 게시: {done[s]['pin']})") if s in done else post(s)
