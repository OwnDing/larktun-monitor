# -*- coding: utf-8 -*-
import os, sys, pathlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenes_a as SA, scenes_b as SB

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/vision/out")
(OUT/"svg").mkdir(parents=True, exist_ok=True); (OUT/"png").mkdir(parents=True, exist_ok=True)

SCENES = [("01",SA.s01),("02",SA.s02),("03",SA.s03),("04",SA.s04),("05",SA.s05),("06",SA.s06),
          ("07",SA.s07),("08",SB.s08),("09",SB.s09),("10",SB.s10),("11",SB.s11),("12",SB.s12),
          ("13",SB.s13),("14",SB.s14)]

files=[]
for n, fn in SCENES:
    p = OUT/"svg"/f"S{n}.svg"; p.write_text(fn(), encoding="utf-8"); files.append((n,p))
print("svg:", len(files))

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--force-color-profile=srgb","--font-render-hinting=none"])
    pg = br.new_page(viewport={"width":1080,"height":1920}, device_scale_factor=1)
    for n, p in files:
        pg.goto("file://"+str(p)); pg.wait_for_timeout(320)
        pg.screenshot(path=str(OUT/"png"/f"S{n}.png"))
        print("png S"+n)
    br.close()
