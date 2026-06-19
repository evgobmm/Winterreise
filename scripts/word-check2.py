#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
word-check2 — полный словарный аудит одного DE-слова (новый пайплайн).
Usage: python3 scripts/word-check2.py <DE-WORD> [RU-CANDIDATE...] [--raw DIR]

Приоритет: ТОЛКОВЫЕ СЛОВАРИ НАЧАЛА XIX в. (значения слова в эпоху Мюллера — решающее).
Сырьё сохраняется (--raw) для последующей детерминированной сверки цитат.
"""
import sys
from word_check_lib import check_word

GROUP_TITLES = {
    "A":  "ГРУППА A — ТОЛКОВЫЕ 1820-х (ПРИОРИТЕТ: основные значения эпохи Мюллера)",
    "A'": "Группа A′ — современные толковые/этимологические (вторичные)",
    "A+": "Группа A+ — доп. историч. (Goethe-WB, пословицы)",
    "B":  "Группа B — НЕМ→РУС (DE→RU)",
    "C":  "Группа C — РУС→НЕМ обратная сверка (RU→DE)",
    "D":  "Группа D — RU-толковые (проверка русской стороны)",
}
ORDER = ["A", "A'", "A+", "B", "C", "D"]


def main():
    args = [a for a in sys.argv[1:]]
    raw_root = None
    if "--raw" in args:
        i = args.index("--raw"); raw_root = args[i + 1]; del args[i:i + 2]
    if not args:
        print("Usage: python3 scripts/word-check2.py <DE-WORD> [RU-CANDIDATE...] [--raw DIR]")
        sys.exit(1)
    de_word, ru_cands = args[0], args[1:]
    print(f"=== Полный словарный аудит: «{de_word}» ===")
    if ru_cands:
        print("RU-кандидаты:", ", ".join(f"«{r}»" for r in ru_cands))
    print()
    results = check_word(de_word, ru_cands, raw_root)
    by = {}
    for r in results:
        by.setdefault(r["group"], []).append(r)
    miss = []
    for g in ORDER:
        if g not in by:
            continue
        print("#" * 4, GROUP_TITLES[g])
        for r in by[g]:
            print(f"  ### {r['name']}  [{r['status']}]")
            print(f"      URL: {r['url']}")
            if r.get("text"):
                print(f"      {r['text']}")
            if "❌" in r["status"] or "⚠" in r["status"]:
                miss.append(r["name"])
            print()
        print()
    print("=== СВОДКА ===")
    print(f"Источников отработано: {len(results)}; проблемных: {len(miss)}")
    if miss:
        print("Проблемные/ручные:", "; ".join(miss))


if __name__ == "__main__":
    main()
