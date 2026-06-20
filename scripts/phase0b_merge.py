#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ф0b-merge: lemmas_out/*.json → research/lemmas.json (form→инфо) + research/unique_lemmas.json (лемма→инфо+RU-кандидаты)."""
import json, glob, collections, sys, os

forms_info = json.load(open("research/forms.json", encoding="utf-8"))
segments = json.load(open("research/segments.json", encoding="utf-8"))
seg_by_id = {s["id"]: s for s in segments}

form2lemma = {}
chunks = sorted(glob.glob("research/lemmas_out/lemmas_*.json"))
missing_forms = []
for cf in chunks:
    try:
        arr = json.load(open(cf, encoding="utf-8"))
    except Exception as e:
        print(f"⚠ битый JSON {cf}: {e}", file=sys.stderr); continue
    for it in arr:
        form2lemma[it["form"]] = it

# проверка покрытия
content_forms = [k for k,v in forms_info.items() if not v.get("is_function")]
for f in content_forms:
    if f not in form2lemma:
        missing_forms.append(f)

json.dump(form2lemma, open("research/lemmas.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

# уникальные леммы → RU-кандидаты (наши текущие глоссы из сегментов)
lemmas = collections.defaultdict(lambda: {"pos":set(),"gender":set(),"tier":set(),"forms":set(),"ru":[],"segs":set(),"songs":set()})
def add_seg_ru(L, sid):
    s = seg_by_id.get(sid)
    if not s: return
    ru = (s.get("ru") or "").strip()
    if ru and ru not in lemmas[L]["ru"]:
        lemmas[L]["ru"].append(ru)
    lemmas[L]["segs"].add(sid); lemmas[L]["songs"].add(s["song"])

for form, info in form2lemma.items():
    L = info.get("lemma") or form
    rec = lemmas[L]
    rec["pos"].add(info.get("pos","")); rec["tier"].add(info.get("tier",""))
    if info.get("gender"): rec["gender"].add(info["gender"])
    rec["forms"].add(form)
    for sid in forms_info.get(form,{}).get("occ", []):
        add_seg_ru(L, sid)
    # sep_prefix: добавить базовые глаголы как отдельные леммы
    if info.get("pos")=="sep_prefix":
        for bv in info.get("variants",[]):
            if bv:
                br = lemmas[bv]; br["pos"].add("verb"); br["tier"].add("content"); br["forms"].add(form+"→"+bv)
                for sid in forms_info.get(form,{}).get("occ", []): add_seg_ru(bv, sid)

out = {}
for L, rec in lemmas.items():
    out[L] = {
        "pos": sorted(p for p in rec["pos"] if p),
        "gender": sorted(rec["gender"]),
        "tier": sorted(t for t in rec["tier"] if t),
        "forms": sorted(rec["forms"]),
        "ru_candidates": rec["ru"][:5],
        "n_occ": len(rec["segs"]),
        "songs": sorted(rec["songs"]),
    }
json.dump(out, open("research/unique_lemmas.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

content_lemmas = {k:v for k,v in out.items() if any(t in ("content","loaded_particle") for t in v["tier"]) or not v["tier"]}
print(f"Форм размечено: {len(form2lemma)} / {len(content_forms)} контентных")
if missing_forms:
    print(f"⚠ НЕ размечено форм: {len(missing_forms)} → {missing_forms[:20]}")
print(f"Уникальных лемм всего: {len(out)}")
print(f"  на полные таблицы (content+loaded): {len(content_lemmas)}")
