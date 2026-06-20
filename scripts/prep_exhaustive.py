#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Подготовка ИСЧЕРПЫВАЮЩЕГО прохода: индекс вхождений по лемме + чанки для ревью.
По каждой лемме — ВСЕ вхождения (сегмент, RU, строка) + путь к полной таблице."""
import json, glob, re, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

segs = json.load(open("research/segments.json", encoding="utf-8"))
f2l = json.load(open("research/lemmas.json", encoding="utf-8"))

# значимые служебные, которые включаем дополнительно
EXTRA_FUNC = {"über", "mancher", "ander", "selbst", "selber", "wann", "sonder", "beide", "all", "jeder"}

def safe(lemma):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in lemma)

def content_tokens(de):
    out = []
    for raw in re.findall(r"[A-Za-zÄÖÜäöüß'’]+", (de or "").replace("/", " ")):
        t = raw.strip("'’")
        if not t:
            continue
        info = f2l.get(t)
        if not info:
            continue
        L = info.get("lemma", t)
        tier = info.get("tier")
        if tier in ("content", "loaded_particle") or t in EXTRA_FUNC or L in EXTRA_FUNC:
            out.append((t, L, info.get("pos", "")))
    return out

occ = {}
for s in segs:
    for tok, L, pos in content_tokens(s["de"]):
        rec = occ.setdefault(L, {"lemma": L, "pos": set(), "occurrences": []})
        rec["pos"].add(pos)
        rec["occurrences"].append({
            "song": s["song"], "seg_id": s["id"], "de": s["de"],
            "ru": s["ru"], "line_de": s["line_de"],
            "variant_ru": s.get("variant_ru"),
        })

# финализация + наличие таблицы
items = []
for L, rec in occ.items():
    rec["pos"] = sorted(p for p in rec["pos"] if p)
    tf = f"research/tables/{safe(L)}.json"
    rec["table_file"] = tf if os.path.exists(tf) else None
    rec["n_occ"] = len(rec["occurrences"])
    rec["distinct_ru"] = sorted(set(o["ru"] for o in rec["occurrences"] if o["ru"]))
    rec["multi_render"] = len(set(re.sub(r"[^а-яёА-ЯЁ-]", "", (o["ru"] or "").lower()) for o in rec["occurrences"]) - {""}) >= 2
    items.append(rec)

json.dump({i["lemma"]: i for i in items}, open("research/occurrences.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# сортировка: мульти-рендеринг и многократные — вперёд (важнее); затем по алфавиту
items.sort(key=lambda r: (not r["multi_render"], -r["n_occ"], r["lemma"].lower()))

# чанки по ~6 лемм
os.makedirs("research/review_chunks", exist_ok=True)
for f in glob.glob("research/review_chunks/*.json"):
    os.remove(f)
PER = 6
N = math.ceil(len(items) / PER)
no_table = [r["lemma"] for r in items if not r["table_file"]]
for i in range(N):
    chunk = items[i*PER:(i+1)*PER]
    json.dump(chunk, open(f"research/review_chunks/chunk_{i:03d}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"Лемм на исчерпывающий ревью: {len(items)} (контент+значимые служебные)")
print(f"  мульти-рендеринг (>=2 разных RU): {sum(1 for r in items if r['multi_render'])}")
print(f"  без таблицы: {len(no_table)} → {no_table}")
print(f"Чанков по {PER}: {N} в research/review_chunks/")
