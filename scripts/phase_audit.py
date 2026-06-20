#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""По-словный аудит целостности: для КАЖДОЙ леммы × КАЖДОГО словаря — реально ли прочитан
контент (ok), нет-статьи (legit), ошибка фетча (fixable), мусор-парсер (fixable), пусто, webfetch."""
import json, glob, collections, re, os

CHROME = ["Um den vollen Funktionsumfang", "muss JavaScript", "Zum Inhalt springen",
          "Benutzerkonto erstellen", "Hauptmenü Hauptmenü", "JavaScript aktiviert",
          "Diese Seite existiert nicht", "Sucheingabe Hilfe", "document.get", "skw.toUpperCase",
          "Все языки Русский Английский", "Android версия iPhone", "Bitte warten Sie"]

# ожидаемые DE-side источники (на каждое слово); C/D — на кандидат, аудируем отдельно
DE_SOURCES = ["Adelung", "Campe", "Grimm", "DWDS", "Pfeifer", "Duden Synonyme", "Duden",
              "Wiktionary", "Leipzig", "Goethe", "Wander", "БНРС", "Multitran DE", "PONS", "Langenscheidt"]
PRIORITY = ["Adelung", "Campe", "Grimm"]

def classify(s):
    st = s.get("status", ""); txt = (s.get("text") or "").strip()
    if "⚠" in st and "WebFetch" in st: return "webfetch"
    if "❌" in st:
        if any(k in st for k in ("нет леммы", "нет совпадений", "нет статьи", "404")): return "nolemma"
        return "error"
    if not txt or len(txt) < 15: return "empty"
    if any(m in txt for m in CHROME):
        # мусор, если коротко или много маркеров
        if len(txt) < 500 or sum(1 for m in CHROME if m in txt) >= 2: return "chrome"
    return "ok"

def srcname(name):
    for p in DE_SOURCES:
        if p in name: return p
    return None

tables = sorted(glob.glob("research/tables/*.json"))
percell = collections.defaultdict(lambda: collections.Counter())
lemma_health = {}
a_fail = []        # леммы с провалом приоритетного источника
fixable = collections.defaultdict(list)  # source -> [lemma] для ошибок/chrome
webfetch_needed = collections.defaultdict(list)

for tf in tables:
    t = json.load(open(tf, encoding="utf-8"))
    L = t["lemma"]
    cells = {}
    for s in t.get("sources", []):
        nm = srcname(s["name"])
        if not nm: continue
        cls = classify(s)
        # объединяем по источнику (берём лучший статус среди дублей)
        prev = cells.get(nm)
        rank = {"ok":0,"webfetch":1,"nolemma":2,"empty":3,"chrome":4,"error":5}
        if prev is None or rank[cls] < rank[prev]:
            cells[nm] = cls
    for nm, cls in cells.items():
        percell[nm][cls] += 1
        if cls in ("error", "chrome", "empty"):
            fixable[nm].append(L)
        if cls == "webfetch":
            webfetch_needed[nm].append(L)
    # здоровье приоритета
    prio_ok = [p for p in PRIORITY if cells.get(p) == "ok"]
    lemma_health[L] = {"prio_ok": len(prio_ok), "cells": cells}
    if len(prio_ok) == 0:
        a_fail.append((L, {p: cells.get(p, "—") for p in PRIORITY}))

print(f"=== ТАБЛИЦ (лемм): {len(tables)} ===\n")
print("=== ПО ИСТОЧНИКАМ: ok / nolemma(нет статьи) / error(фетч) / chrome(парсер) / empty / webfetch ===")
for nm in DE_SOURCES:
    c = percell[nm]
    tot = sum(c.values())
    print(f"  {nm:16} ok={c['ok']:3} nolemma={c['nolemma']:3} error={c['error']:3} chrome={c['chrome']:3} empty={c['empty']:3} webfetch={c['webfetch']:3}  (Σ{tot})")

print("\n=== ЗДОРОВЬЕ ПРИОРИТЕТА (Adelung/Campe/Grimm) ===")
hist = collections.Counter(h["prio_ok"] for h in lemma_health.values())
for k in (3,2,1,0):
    print(f"  {k}/3 приоритетных прочитаны: {hist[k]} лемм")
print(f"\n  Лемм с 0/3 приоритетными ({len(a_fail)}):")
for L, st in a_fail:
    print(f"    {L:18} {st}")

print("\n=== ИСПРАВИМЫЕ (error/chrome/empty) — пере-фетч/пере-разбор ===")
total_fix = 0
for nm in DE_SOURCES:
    if fixable[nm]:
        total_fix += len(fixable[nm])
        print(f"  {nm}: {len(fixable[nm])} → {fixable[nm][:12]}{'…' if len(fixable[nm])>12 else ''}")
print(f"  ИТОГО исправимых ячеек: {total_fix}")

print("\n=== WEBFETCH-НЕОБХОДИМЫЕ (SPA, python не читает) ===")
for nm in DE_SOURCES:
    if webfetch_needed[nm]:
        print(f"  {nm}: {len(webfetch_needed[nm])} лемм")

json.dump({"a_fail":[L for L,_ in a_fail], "fixable":{k:v for k,v in fixable.items()},
           "webfetch":{k:v for k,v in webfetch_needed.items()}},
          open("research/audit_report.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nОтчёт: research/audit_report.json")
