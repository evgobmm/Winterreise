#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ф3.5: по-песенные досье для ревью Ф4. На каждый сегмент — DE-слова с их леммами и
СЛОВАРНЫМИ ДОКАЗАТЕЛЬСТВАМИ (реальные цитаты из таблиц, приоритет 1820-х)."""
import json, glob, re, os, collections

segments = json.load(open("research/segments.json", encoding="utf-8"))
form2lemma = json.load(open("research/lemmas.json", encoding="utf-8"))

# индекс таблиц по лемме
tables = {}
for tf in glob.glob("research/tables/*.json"):
    t = json.load(open(tf, encoding="utf-8"))
    tables[t["lemma"]] = t

# карта источник→короткий ключ
SRCKEY = [
    ("Adelung", "adelung_1820"), ("Campe", "campe_1820"), ("Grimm", "grimm"),
    ("DWDS", "dwds"), ("Pfeifer", "pfeifer"), ("Duden Synonyme","duden_syn"), ("Duden", "duden"),
    ("Wiktionary","wiktionary"), ("Leipzig","leipzig_freq"), ("Goethe","goethe"), ("Wander","wander"),
    ("БНРС", "bnrs_de_ru"), ("Multitran DE", "multitran_de_ru"), ("PONS","pons"), ("Langenscheidt","langenscheidt"),
    ("БРНС", "brns_ru_de"), ("Multitran RU", "multitran_ru_de"), ("gufo", "ru_tolk"),
]
def srckey(name):
    for pat,k in SRCKEY:
        if pat in name: return k
    return None

CHROME = ["Um den vollen Funktionsumfang", "muss JavaScript", "Zum Inhalt springen",
          "Benutzerkonto erstellen", "Hauptmenü Hauptmenü", "Diese Seite existiert nicht",
          "JavaScript aktiviert"]

def lemma_evidence(L):
    t = tables.get(L)
    if not t: return None
    ev = {"lemma":L, "pos":t.get("pos"), "tier":t.get("tier"), "ru_candidates":t.get("ru_candidates")}
    by = collections.defaultdict(list)
    for s in t.get("sources", []):
        k = srckey(s["name"])
        if not k: continue
        txt = (s.get("text") or "").strip()
        if "❌" in s.get("status","") or not txt: continue
        if any(m in txt for m in CHROME): continue  # отсев нет-статья/JS-заглушек
        by[k].append(txt)
    # СЛИМ: приоритет 1820-х + DE→RU кандидаты; остальное агент дочитает из research/tables/<лемма>.json
    KEEP = {"adelung_1820":700, "campe_1820":600, "grimm":600,
            "bnrs_de_ru":350, "langenscheidt":220, "multitran_de_ru":220}
    for k, cap in KEEP.items():
        if k in by:
            ev[k] = " || ".join(by[k])[:cap]
    return ev

CONTENT_POS = {"noun","verb","adj","adv","num","interj","sep_prefix"}
def content_tokens(de):
    toks=[]
    for raw in re.findall(r"[A-Za-zÄÖÜäöüß'’]+", (de or "").replace("/"," ")):
        tok = raw.strip("'’")
        if not tok: continue
        info = form2lemma.get(tok)
        if info and (info.get("tier") in ("content","loaded_particle")):
            toks.append((tok, info.get("lemma",tok)))
    return toks

os.makedirs("research/dossiers", exist_ok=True)
by_song = collections.defaultdict(list)
for s in segments: by_song[s["song"]].append(s)

for song, segs in sorted(by_song.items()):
    dossier = {"song":song, "title_de":segs[0]["title_de"], "segments":[]}
    seen_lemmas={}
    for s in segs:
        words=[]
        for tok,L in content_tokens(s["de"]):
            ev = lemma_evidence(L)
            if ev: seen_lemmas[L]=ev
            words.append({"form":tok,"lemma":L})
        dossier["segments"].append({
            "id":s["id"],"stanza":s["stanza"],"line":s["line"],"seg":s["seg"],
            "line_de":s["line_de"],"ru":s["ru"],"de":s["de"],
            "variant_de":s.get("variant_de"),"variant_ru":s.get("variant_ru"),
            "content_words":words,
        })
    dossier["evidence"] = seen_lemmas  # лемма→словарные цитаты
    json.dump(dossier, open(f"research/dossiers/song_{song:02d}.json","w",encoding="utf-8"),
              ensure_ascii=False, indent=1)

print(f"Досье собраны: {len(by_song)} песен в research/dossiers/")
print(f"Таблиц подключено: {len(tables)}")
sz = sum(os.path.getsize(f) for f in glob.glob('research/dossiers/*.json'))
print(f"Суммарный размер досье: {sz//1024} КБ")
