#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ф0a: детерминированная выгрузка сегментов и немецких словоформ из всех песен."""
import json, glob, re, collections, os

FUNCTION = set("""
der die das den dem des ein eine einen einem einer eines
ich du er sie es wir ihr mich dich sich uns euch mir dir ihm ihn ihnen wir
mein meine meinen meinem meiner meines dein deine deinen deinem deiner sein seine seinen seinem seiner
ihre ihren ihrem ihrer unser unsre unsern euer
und oder aber sondern wie als ob weil da damit dass daß denn doch
in an auf aus bei mit nach von vor zu zur zum im am vom beim ans
durch um über unter ohne gegen gen wider zwischen hinter neben seit
nicht kein keine keinen keiner keines nichts
ist sind bin bist war wars waren sei seid wäre wären
hat habe hast haben hatte hatt hab
so noch nur auch schon nun dann jetzt sehr je
ja nein man sich des ne
""".split())
# нагруженные частицы — НЕ исключаем (нужна переверка против правил)
LOADED = set("denn doch wohl nun so erst je nimmer da schon noch".split())

files = sorted(glob.glob("src/data/songs/*.json"))
segments = []
forms = collections.defaultdict(lambda: {"count":0,"occ":[],"songs":set(),"samples":[]})
seg_id = 0

def add_form_tokens(de, sid, line_de, song):
    if not de: return
    for raw in re.findall(r"[A-Za-zÄÖÜäöüß'’]+", de.replace("/"," ")):
        tok = raw.strip("'’")
        if not tok: continue
        low = tok.lower()
        is_fn = low in FUNCTION and low not in LOADED
        f = forms[tok]
        f["count"] += 1
        f["occ"].append(sid)
        f["songs"].add(song)
        if len(f["samples"]) < 3 and line_de not in f["samples"]:
            f["samples"].append(line_de)
        f["is_function"] = is_fn

for fp in files:
    d = json.load(open(fp, encoding="utf-8"))
    song = d["number"]
    for si, st in enumerate(d["stanzas"]):
        lines_de = st["lines_de"]
        for li, lru in enumerate(st["lines_ru"]):
            line_de = lines_de[li] if li < len(lines_de) else ""
            line_ru = " ".join(s.get("ru","") for s in lru["segments"])
            ann_ranges = []
            for a in lru.get("annotations", []):
                sr = a.get("segment_range")
                if sr: ann_ranges.append((a.get("type"), sr))
            for gi, seg in enumerate(lru["segments"]):
                global_seg = {
                    "id": seg_id, "song": song, "title_de": d["title_de"],
                    "stanza": si, "line": li, "seg": gi,
                    "ru": seg.get("ru",""), "de": seg.get("de",""),
                    "variant_de": seg.get("variant_de"), "variant_ru": seg.get("variant_ru"),
                    "line_de": line_de, "line_ru": line_ru,
                }
                segments.append(global_seg)
                add_form_tokens(seg.get("de",""), seg_id, line_de, song)
                if seg.get("variant_de"):
                    add_form_tokens(seg.get("variant_de"), seg_id, line_de, song)
                seg_id += 1

# финализация forms
forms_out = {}
for k,v in forms.items():
    v["songs"] = sorted(v["songs"])
    v.setdefault("is_function", False)
    forms_out[k] = v

content = {k:v for k,v in forms_out.items() if not v["is_function"]}
os.makedirs("research", exist_ok=True)
json.dump(segments, open("research/segments.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(forms_out, open("research/forms.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"Сегментов: {len(segments)}")
print(f"Уникальных словоформ (из de-полей): {len(forms_out)}")
print(f"  служебных (отсев): {sum(1 for v in forms_out.values() if v['is_function'])}")
print(f"  контентных+нагруженных (на лемматизацию+таблицы): {len(content)}")
print(f"Файлы: research/segments.json, research/forms.json")
