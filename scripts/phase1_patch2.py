#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Патч2: применяет ИСПРАВЛЕНИЯ фетчеров к существующим таблицам — пере-фетч ячеек в статусе
error/chrome/empty исправленными функциями (Grimm/DWDS/Pfeifer/Wiktionary вариант-перебор;
Pfeifer no-byline→нет статьи). Чистит junk-леммы. Запускать ПОСЛЕ исчерпывающего прохода."""
import json, glob, os, sys, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_check_lib as wcl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CHROME = ["Um den vollen Funktionsumfang", "muss JavaScript", "Zum Inhalt springen",
          "Benutzerkonto erstellen", "Hauptmenü Hauptmenü", "JavaScript aktiviert",
          "Sucheingabe Hilfe", "document.get", "skw.toUpperCase", "Bitte warten Sie"]
FN = {"Adelung": wcl.src_adelung, "Campe": wcl.src_campe, "Grimm": wcl.src_grimm,
      "DWDS": wcl.src_dwds, "Pfeifer": wcl.src_pfeifer, "Duden Synonyme": wcl.src_duden_syn,
      "Duden": wcl.src_duden, "Wiktionary": wcl.src_wiktionary, "Leipzig": wcl.src_leipzig,
      "Goethe": wcl.src_goethe, "Wander": wcl.src_wander, "БНРС": wcl.src_bnrs,
      "Multitran DE": wcl.src_multitran_de, "Langenscheidt": wcl.src_langenscheidt}

def bad(s):
    st = s.get("status", ""); txt = (s.get("text") or "").strip()
    if "⚠" in st: return False
    if "❌" in st:
        return not any(k in st for k in ("нет леммы", "нет совпадений", "нет статьи", "404", "нет в"))
    if not txt or len(txt) < 15: return True
    if any(m in txt for m in CHROME) and (len(txt) < 500 or sum(1 for m in CHROME if m in txt) >= 2):
        return True
    return False

def fn_for(name):
    for k, f in FN.items():
        if k in name: return f
    return None

# 1) удалить junk-леммы (пробелы/скобки/«sich »)
junk = []
for tf in glob.glob("research/tables/*.json"):
    t = json.load(open(tf, encoding="utf-8"))
    L = t["lemma"]
    if " " in L or "(" in L or L.startswith("sich "):
        junk.append(L); os.remove(tf)
print(f"Удалено junk-лемм: {len(junk)} → {junk}")

# 2) пере-фетч исправимых ячеек
t0 = time.time(); n = 0; fixed = 0
for tf in sorted(glob.glob("research/tables/*.json")):
    t = json.load(open(tf, encoding="utf-8"))
    L = t["lemma"]; raw_dir = f"research/raw/{L}"; changed = False
    for i, s in enumerate(t["sources"]):
        if s.get("group") in ("C", "D"): continue
        if bad(s):
            f = fn_for(s["name"])
            if f:
                t["sources"][i] = f(L, raw_dir); changed = True; fixed += 1
    if changed:
        json.dump(t, open(tf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n += 1
    if n % 80 == 0: print(f"{n} таблиц, исправлено ячеек {fixed}, {time.time()-t0:.0f}s", flush=True)
print(f"ИТОГО: {n} таблиц, пере-фетч ячеек {fixed}, {time.time()-t0:.0f}s", flush=True)
