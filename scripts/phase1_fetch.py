#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ф1: батч словарной проверки по уникальным леммам. Резюмируемо (пропуск готовых). check_word сохраняет сырьё + мы пишем таблицу."""
import json, os, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from word_check_lib import check_word

uni = json.load(open("research/unique_lemmas.json", encoding="utf-8"))
# леммы на полные таблицы: content + loaded_particle (служебные/артикли — мимо)
def needs_table(v):
    t = v["tier"]
    if not t: return True
    return any(x in ("content","loaded_particle") for x in t)

lemmas = [(L,v) for L,v in uni.items() if needs_table(v)]
lemmas.sort()
os.makedirs("research/tables", exist_ok=True)
RAW_ROOT = "research/raw"

only = sys.argv[1:] if len(sys.argv)>1 else None
done=0; skip=0; err=0
t0=time.time()
for i,(L,v) in enumerate(lemmas):
    if only and L not in only: continue
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in L)
    out_path = f"research/tables/{safe}.json"
    if os.path.exists(out_path):
        skip+=1; continue
    ru_cands = v.get("ru_candidates", [])[:4]
    try:
        results = check_word(L, ru_cands, RAW_ROOT)
        table = {"lemma":L, "pos":v["pos"], "gender":v["gender"], "tier":v["tier"],
                 "ru_candidates":ru_cands, "n_occ":v["n_occ"], "songs":v["songs"],
                 "sources":results}
        json.dump(table, open(out_path,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
        done+=1
    except Exception as e:
        err+=1
        print(f"ERR {L}: {e}", flush=True)
        traceback.print_exc()
    if (done+skip)%20==0:
        el=time.time()-t0
        print(f"[{i+1}/{len(lemmas)}] done={done} skip={skip} err={err} elapsed={el:.0f}s", flush=True)
print(f"ИТОГО: done={done} skip={skip} err={err} из {len(lemmas)} лемм, {time.time()-t0:.0f}s", flush=True)
