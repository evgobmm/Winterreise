#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Патч таблиц Ф1: Pfeifer — переразбор сохранённого сырья (баг парсинга); Adelung/Campe —
дофетч провалившихся (новые морфо-варианты). Обновляет таблицы на месте. Запускать из корня репо."""
import json, glob, os, sys, re, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import word_check_lib as wcl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

tables = sorted(glob.glob("research/tables/*.json"))
t0 = time.time(); n = 0; pf = 0; ad = 0; ca = 0
for tf in tables:
    t = json.load(open(tf, encoding="utf-8"))
    L = t["lemma"]; raw_dir = f"research/raw/{L}"
    changed = False
    praw = f"{raw_dir}/Am_pfeifer.html"
    if os.path.exists(praw):
        body = open(praw, encoding="utf-8", errors="ignore").read()
        m = re.search(r"\(Wolfgang Pfeifer\)", body)
        chunk = body[m.end():] if m else body
        txt = wcl._strip(chunk, 1100)
        for s in t["sources"]:
            if "Pfeifer" in s["name"]:
                s["text"] = txt
                if txt:
                    s["status"] = "✓"
                changed = True; pf += 1; break
    for s in t["sources"]:
        if "Adelung" in s["name"] and "❌" in s["status"]:
            s.update(wcl.src_adelung(L, raw_dir)); changed = True; ad += 1
        if "Campe" in s["name"] and "❌" in s["status"]:
            s.update(wcl.src_campe(L, raw_dir)); changed = True; ca += 1
    if changed:
        json.dump(t, open(tf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n += 1
    if n % 80 == 0:
        print(f"{n}/{len(tables)} pf={pf} ad={ad} ca={ca} {time.time()-t0:.0f}s", flush=True)
print(f"ИТОГО: {n} таблиц; Pfeifer={pf}, Adelung-дофетч={ad}, Campe-дофетч={ca}, {time.time()-t0:.0f}s", flush=True)
