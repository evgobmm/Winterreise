#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Патч3: пере-фетч RU-стороны (C: БРНС/Multitran-RU; D: gufo) на ЛЕММАТИЗИРОВАННЫХ кандидатах.
Сначала мержит research/ru_lemmas_out/*.json → ru_lemma_map. Запускать ПОСЛЕ патч2 + лемматизации."""
import json, glob, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_check_lib as wcl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# 1) мерж карты лемматизации
ru_map = {}
for cf in sorted(glob.glob("research/ru_lemmas_out/ru_*.json")):
    try:
        for it in json.load(open(cf, encoding="utf-8")):
            ru_map[it["orig"]] = [l for l in it.get("lemmas", []) if l]
    except Exception as e:
        print(f"⚠ {cf}: {e}", file=sys.stderr)
json.dump(ru_map, open("research/ru_lemma_map.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Карта лемматизации: {len(ru_map)} кандидатов")

def lemmas_for(orig):
    ls = ru_map.get(orig)
    if ls:
        return ls
    c = wcl._clean_ru(orig)
    return [c] if c else []

# 2) пере-фетч C/D по таблицам
t0 = time.time(); n = 0; rf = 0
for tf in sorted(glob.glob("research/tables/*.json")):
    t = json.load(open(tf, encoding="utf-8"))
    L = t["lemma"]; raw_dir = f"research/raw/{L}"
    cands = t.get("ru_candidates", [])
    if not cands:
        n += 1; continue
    # выкинуть старые C/D, собрать новые на леммах
    t["sources"] = [s for s in t["sources"] if s.get("group") not in ("C", "D")]
    for orig in cands[:4]:
        lem = (lemmas_for(orig) or [None])[0]
        if not lem:
            continue
        for fn, grp in ((wcl.src_brns, "C"), (wcl.src_multitran_ru, "C"), (wcl.src_gufo, "D")):
            s = fn(lem, os.path.join(raw_dir, "ru", lem))
            s["name"] = s["name"].replace(f"«{lem}»", f"«{orig}→{lem}»")
            t["sources"].append(s); rf += 1
    json.dump(t, open(tf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n += 1
    if n % 80 == 0:
        print(f"{n} таблиц, RU-ячеек пере-фетч {rf}, {time.time()-t0:.0f}s", flush=True)
print(f"ИТОГО: {n} таблиц, RU пере-фетч {rf}, {time.time()-t0:.0f}s", flush=True)
