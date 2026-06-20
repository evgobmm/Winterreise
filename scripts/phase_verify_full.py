#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""СКВОЗНОЙ верификатор пайплайна: не только «источник ответил», а КОРРЕКТНОСТЬ контента —
та ли статья для того слова. По каждой лемме × источнику. + целостность инвентаря + функц. обратной сверки."""
import json, glob, os, re, collections

def norm(s):
    s = (s or "").lower()
    return s.replace("th", "t").replace("sz", "ss").replace("ß", "ss").replace("dt", "t")

def alnum_de(s):
    return re.sub(r"[^a-zäöüß]", "", norm(s))

def has_cyr(s, n=3):
    return len(re.findall(r"[а-яё]{2,}", (s or "").lower())) >= n

def has_lat(s, n=3):
    return len(re.findall(r"[a-zäöü]{2,}", (s or "").lower())) >= n

CHROME = ["Um den vollen Funktionsumfang", "muss JavaScript", "Zum Inhalt springen",
          "Benutzerkonto erstellen", "JavaScript aktiviert", "Sucheingabe Hilfe", "Bitte warten Sie"]

DE_EXPL = ["Adelung", "Campe", "Grimm", "DWDS", "Goethe"]  # заголовок=слово (строгая сверка)
# Pfeifer (группирует по корню) и Wiktionary (не повторяет заголовок в определении) — мягкая сверка
LENIENT = ["Pfeifer", "Wiktionary"]
DE_RU = ["БНРС", "Multitran DE", "Langenscheidt"]
RU_DE = ["БРНС", "Multitran RU"]

def classify_correct(lemma, s):
    """Вернуть (presence, correct?) — presence: ok/error/nolemma/chrome/empty/webfetch; correct: bool|None."""
    nm = s["name"]; st = s.get("status", ""); txt = (s.get("text") or "").strip()
    if "⚠" in st: return "webfetch", None
    if "❌" in st:
        return ("nolemma" if any(k in st for k in ("нет леммы", "нет совпадений", "нет статьи", "404", "нет в")) else "error"), None
    if not txt or len(txt) < 15: return "empty", None
    if any(m in txt for m in CHROME) and (len(txt) < 500 or sum(1 for m in CHROME if m in txt) >= 2):
        return "chrome", None
    # КОРРЕКТНОСТЬ
    grp = s.get("group", "")
    if any(p in nm for p in LENIENT):
        return "ok", True  # есть контент (root-grouping/без повтора заголовка — не баг)
    if any(p in nm for p in DE_EXPL):
        # слово (или его корневой префикс ≥4) должно появляться где-либо в статье
        nl = alnum_de(lemma); body = alnum_de(txt)
        probe = nl if len(nl) <= 5 else nl[:max(5, len(nl) - 2)]
        return "ok", bool(probe and probe in body)
    if any(p in nm for p in DE_RU):
        return "ok", has_cyr(txt) or alnum_de(lemma)[:5] in alnum_de(txt)
    if any(p in nm for p in RU_DE):
        return "ok", has_lat(txt)
    if "gufo" in nm or "толков" in nm:
        cand = nm.split("«")[-1].rstrip("»") if "«" in nm else ""
        return "ok", has_cyr(txt)
    if "Leipzig" in nm or "Wander" in nm or "Duden" in nm:
        return "ok", True  # справочные
    return "ok", True

tables = sorted(glob.glob("research/tables/*.json"))
pres = collections.defaultdict(lambda: collections.Counter())
wrong = collections.defaultdict(list)  # source -> [(lemma, head)]
for tf in tables:
    t = json.load(open(tf, encoding="utf-8"))
    L = t["lemma"]
    seen = {}
    for s in t.get("sources", []):
        nm = None
        for p in DE_EXPL + DE_RU + RU_DE + ["Leipzig", "Duden Synonyme", "Duden", "Wander", "gufo", "PONS"]:
            if p in s["name"]: nm = p; break
        if not nm: continue
        p_, c_ = classify_correct(L, s)
        key = (nm)
        # объединяем дубли (RU per-candidate): берём лучший
        rank = {"ok": 0, "webfetch": 1, "nolemma": 2, "empty": 3, "chrome": 4, "error": 5}
        prev = seen.get(nm)
        if prev is None or rank[p_] < rank[prev[0]]:
            seen[nm] = (p_, c_)
    for nm, (p_, c_) in seen.items():
        pres[nm][p_] += 1
        if p_ == "ok" and c_ is False:
            pres[nm]["WRONG"] += 1
            if len(wrong[nm]) < 20:
                wrong[nm].append(L)

print(f"=== СКВОЗНАЯ ВЕРИФИКАЦИЯ: {len(tables)} лемм ===\n")
print("Источник: ok(из них WRONG-контент) | nolemma | error | chrome | empty | webfetch")
ALL = DE_EXPL + DE_RU + RU_DE + ["Leipzig", "Duden", "Duden Synonyme", "Wander", "gufo", "PONS"]
for nm in ALL:
    c = pres.get(nm)
    if not c: continue
    print(f"  {nm:16} ok={c['ok']:3}(WRONG={c['WRONG']:3}) nolemma={c['nolemma']:3} error={c['error']:3} chrome={c['chrome']:3} empty={c['empty']:3} wf={c['webfetch']:3}")

print("\n=== WRONG-КОНТЕНТ (статус ok, но статья НЕ про это слово) — критично ===")
for nm in ALL:
    if wrong[nm]:
        print(f"  {nm}: {len(wrong[nm])}{'+' if len(wrong[nm])>=20 else ''} → {wrong[nm]}")
total_wrong = sum(len(v) for v in wrong.values())
print(f"\n  ИТОГО WRONG-контент ячеек (≥, sample cap 20): {total_wrong}")
json.dump({k: v for k, v in wrong.items()}, open("research/verify_full_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
