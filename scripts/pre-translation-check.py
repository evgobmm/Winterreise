#!/usr/bin/env python3
"""
Pre-translation check для новой песни Winterreise.
Usage: python3 scripts/pre-translation-check.py <song-number>

Делает автоматически:
1. Извлекает значимые DE-слова из новой песни.
2. Grep по всем уже переведённым песням — таблица «слово | прошлый RU | где».
3. Выделяет «новые» слова (впервые в цикле).
4. Печатает lines_de для ручной сверки пунктуации по источникам.
5. Печатает чеклист дальнейших ручных шагов.

Применять ОБЯЗАТЕЛЬНО до первой записи перевода новой песни в JSON
(см. протокол в начале CLAUDE.md).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SONGS = ROOT / "src" / "data" / "songs"

# Служебные DE-слова: артикли, предлоги, союзы, местоимения, формы auxiliary.
# Если значимое слово сюда случайно попало — это исказит фильтр; пересматривать.
STOP_WORDS = {
    # артикли
    "der", "die", "das", "den", "dem", "des",
    "ein", "eine", "einen", "einem", "einer", "eines",
    # предлоги
    "in", "auf", "an", "zu", "mit", "von", "für", "durch",
    "hinter", "vor", "über", "unter", "neben", "zwischen",
    "bei", "nach", "aus", "um", "ohne", "gegen", "bis",
    "ab", "seit",
    # союзы и частицы
    "und", "oder", "aber", "denn", "doch", "sondern",
    "dass", "daß", "wenn", "weil", "ob", "als", "während",
    "wie", "wer", "was", "wo", "wann",
    # личные местоимения
    "ich", "du", "er", "sie", "es", "wir", "ihr",
    "mich", "dich", "ihn", "uns", "euch",
    "mir", "dir", "ihm", "ihnen",
    # притяжательные
    "mein", "meine", "meinen", "meinem", "meiner", "meines",
    "dein", "deine", "deinen", "deinem", "deiner", "deines",
    "sein", "seine", "seinen", "seinem", "seiner", "seines",
    "unser", "unsre", "unsere", "unsren", "unsrem",
    "euer", "eure", "euren",
    # указательные
    "dieser", "diese", "dieses", "diesen", "diesem",
    "jener", "jene", "jenes", "jenen", "jenem",
    # частые наречия / частицы (не знаменательные)
    "auch", "schon", "nur", "so", "nicht", "kein",
    "keine", "keinen", "keinem", "keiner", "keines",
    "ja", "nein",
    # формы auxiliary (часто связки/Perfekt-aux)
    "ist", "sind", "war", "waren", "sei", "wäre", "wären",
    "hat", "haben", "habe", "hatte", "hatten",
    "wird", "werden", "wurde", "wurden", "ward",
    "muss", "musst", "mußt", "kann", "kannst", "mag",
}


def normalize(word):
    """Очистить слово от пунктуации, кроме апострофа внутри."""
    return re.sub(r"[^A-Za-zÄÖÜäöüß']", "", word).strip("'")


def extract_de_words(song):
    """Извлечь все знаменательные DE-слова из lines_de песни."""
    words = set()
    for stanza in song.get("stanzas", []):
        for line in stanza.get("lines_de", []):
            for w in re.split(r"[\s\.,;:!?—–\-/]+", line):
                w = normalize(w)
                if not w or len(w) <= 1:
                    continue
                if w.lower() in STOP_WORDS:
                    continue
                words.add(w)
    return sorted(words, key=lambda x: x.lower())


def grep_word(word, song_data):
    """Найти вхождения слова в lines_ru[*].segments[*].de текущей песни."""
    hits = []
    for stanza in song_data.get("stanzas", []):
        for line_idx, line_ru in enumerate(stanza.get("lines_ru", [])):
            for seg_idx, seg in enumerate(line_ru.get("segments", [])):
                de_field = seg.get("de", "")
                ru_field = seg.get("ru", "")
                if re.search(rf"\b{re.escape(word)}\b", de_field, re.IGNORECASE):
                    hits.append((line_idx + 1, seg_idx, ru_field, de_field))
    return hits


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/pre-translation-check.py <song-number>")
        sys.exit(1)
    try:
        target = int(sys.argv[1])
    except ValueError:
        print(f"Invalid song number: {sys.argv[1]}")
        sys.exit(1)

    target_files = list(SONGS.glob(f"{target:02d}-*.json"))
    if not target_files:
        print(f"Song {target:02d} not found in {SONGS}")
        sys.exit(1)
    target_data = json.loads(target_files[0].read_text(encoding="utf-8"))

    print(f"=== Pre-translation check: Song {target:02d} «{target_data['title_de']}» ===\n")

    de_words = extract_de_words(target_data)
    print(f"Significant DE words extracted: {len(de_words)}\n")

    # Собрать все другие песни
    other_songs = []
    for f in sorted(SONGS.glob("*.json")):
        m = re.match(r"(\d+)-", f.name)
        if not m:
            continue
        n = int(m.group(1))
        if n == target:
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        other_songs.append((n, data))

    # Grep results
    print("=== GREP: prior usage of each DE word in already-translated songs ===\n")
    new_words = []
    for word in de_words:
        hits_all = []
        for n, data in other_songs:
            for ln, sg, ru, de in grep_word(word, data):
                hits_all.append((n, ln, sg, ru, de))
        if hits_all:
            print(f"• {word}:")
            for n, ln, sg, ru, de in hits_all:
                print(f"    Song {n:02d} L{ln} sec[{sg}]: ru=«{ru}» de=«{de}»")
            print()
        else:
            new_words.append(word)

    # Новые слова (впервые в цикле) — но возможно есть семья
    print("=== NEW WORDS (first appearance in cycle) — check family by root ===")
    if new_words:
        for word in new_words:
            # Корневой grep: первые 4 буквы (находит спряжённые формы).
            # 4 буквы — компромисс: ловит семьи (weist↔weisen) ценой
            # ложных срабатываний (weis* также «weiß»). Их фильтрует человек.
            root_len = min(len(word), 4)
            root = word[:root_len].lower()
            if len(root) < 4:
                print(f"• {word} (root too short for family search)")
                continue
            family_hits = []
            for n, data in other_songs:
                for stanza in data.get("stanzas", []):
                    for line_idx, line_ru in enumerate(stanza.get("lines_ru", [])):
                        for seg_idx, seg in enumerate(line_ru.get("segments", [])):
                            de_field = seg.get("de", "")
                            # ищем все DE-слова в сегменте, начинающиеся с этого корня
                            # (case-insensitive)
                            matches = re.findall(
                                rf"\b{re.escape(root)}\w*\b", de_field, re.IGNORECASE
                            )
                            if matches:
                                family_hits.append(
                                    (n, line_idx + 1, seg_idx,
                                     seg.get("ru", ""), de_field, matches)
                                )
            if family_hits:
                print(f"• {word} — FAMILY MATCHES (root «{root}-»):")
                for n, ln, sg, ru, de, ms in family_hits:
                    print(f"    Song {n:02d} L{ln} sec[{sg}]: «{ms}» ru=«{ru}» de=«{de}»")
                print("  ⚠ verify if same family (rule 32: verbal prefixes); apply convention")
            else:
                print(f"• {word} — truly new (no family match)")
            print()
    else:
        print("(none)")
    print()

    # lines_de для ручной сверки пунктуации
    print("=== LINES_DE — manual punctuation cross-check ===")
    print("Compare each against minimum 3 independent sources:")
    print("- Wikisource Müller Waldhornist 1824")
    print("- LiederNet")
    print("- schubertsong.uk")
    print()
    for stanza_idx, stanza in enumerate(target_data.get("stanzas", [])):
        for line_idx, line in enumerate(stanza.get("lines_de", [])):
            print(f"  L{line_idx + 1}: {line}")
    print()

    # Чеклист дальнейших шагов
    print("=== MANUAL CHECKLIST (perform & report each before JSON write) ===")
    print("[ ] 1. Punctuation cross-check: every line above verified against ≥3 sources")
    print("[ ] 2. Schubert vs Müller textual differences flagged")
    print("[ ] 3. For each significant word: convention applied OR deliberate departure signalled")
    print("[ ] 4. Disputed translation choices listed with concrete alternatives (rule 6)")
    print("[ ] 5. User-approved each disputed point")
    print("[ ] 6. Rule 7: no JSON write without explicit user approval")
    print()
    print("If ANY box is unchecked — JSON write is FORBIDDEN.")


if __name__ == "__main__":
    main()
