#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ф2/3: верификация качества таблиц. Флагирует источники, где извлечён мусор/навигация
вместо статьи (систематический сбой парсера), пустоту, ошибки. + сводка покрытия."""
import json, glob, collections, re, os

CHROME = ["JavaScript aktiviert", "muss JavaScript", "Anmelden", "Benutzerkonto erstellen",
          "document.get", "function(", "window.", "Zum Inhalt springen", "Hauptmenü",
          "Cookie", "data-nosnippet", "Sucheingabe", "skw.toUpperCase",
          "Все языки Русский Английский", "Android версия iPhone"]

tables = sorted(glob.glob("research/tables/*.json"))
by_source = collections.defaultdict(lambda: {"ok":0,"chrome":0,"empty":0,"err":0,"nolemma":0,"samples_bad":[]})
group_cov = collections.defaultdict(lambda: {"ok":0,"total":0})

def classify(s):
    st = s.get("status",""); txt = (s.get("text") or "").strip()
    if "❌" in st:
        return "nolemma" if ("нет леммы" in st or "нет совпадений" in st or "нет статьи" in st) else "err"
    if "⚠" in st and "WebFetch" in st:
        return "ok"  # PONS — ожидаемо WebFetch
    if not txt or len(txt) < 15:
        return "empty"
    chrome_hits = sum(1 for c in CHROME if c in txt)
    # «мусорным» считаем, если много chrome-маркеров и мало «словарного»
    if chrome_hits >= 2 and len(txt) < 400:
        return "chrome"
    if chrome_hits >= 3:
        return "chrome"
    return "ok"

for tf in tables:
    t = json.load(open(tf, encoding="utf-8"))
    for s in t.get("sources", []):
        name = s["name"].split("«")[0].strip()  # объединить per-candidate имена
        cls = classify(s)
        by_source[name][cls] += 1
        if cls in ("chrome","empty") and len(by_source[name]["samples_bad"]) < 3:
            by_source[name]["samples_bad"].append(f"{t['lemma']}: {(s.get('text') or '')[:80]}")
        g = s.get("group","?")
        group_cov[g]["total"] += 1
        if cls == "ok": group_cov[g]["ok"] += 1

print(f"=== ТАБЛИЦ: {len(tables)} ===\n")
print("=== ПОКРЫТИЕ ПО ГРУППАМ (ok / всего) ===")
for g in ["A","A'","A+","B","C","D"]:
    if g in group_cov:
        c=group_cov[g]; print(f"  {g}: {c['ok']}/{c['total']}  ({100*c['ok']//max(1,c['total'])}%)")
print("\n=== ПО ИСТОЧНИКАМ (ok/chrome/empty/nolemma/err) ===")
for name, c in sorted(by_source.items()):
    flag = " ⚠ПАРСЕР?" if (c["chrome"]+c["empty"]) > 0.15*max(1,sum(c[k] for k in ("ok","chrome","empty","nolemma","err"))) and (c["chrome"]+c["empty"])>=3 else ""
    print(f"  {name:38} ok={c['ok']:3} chrome={c['chrome']:3} empty={c['empty']:3} nolemma={c['nolemma']:3} err={c['err']:3}{flag}")
    for s in c["samples_bad"][:2]:
        print(f"        bad: {s}")

# nolemma по группе A (приоритет!) — что 1820-е не нашли
print("\n=== ПРИОРИТЕТ A: леммы, НЕ найденные в Adelung И Campe (проверить орфографию) ===")
miss=[]
for tf in tables:
    t = json.load(open(tf, encoding="utf-8"))
    a=[s for s in t["sources"] if "Adelung" in s["name"]]
    c=[s for s in t["sources"] if "Campe" in s["name"]]
    a_ok = a and "❌" not in a[0]["status"]
    c_ok = c and "❌" not in c[0]["status"]
    if not a_ok and not c_ok:
        miss.append(t["lemma"])
print(f"  {len(miss)} лемм без Adelung И Campe:")
print("  ", miss)
json.dump({"miss_1820": miss}, open("research/verify_report.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
