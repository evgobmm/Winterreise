#!/usr/bin/env python3
"""
Word check — обязательная сверка одного DE-слова по всем 14 источникам из CLAUDE.md.
Usage: python3 scripts/word-check.py <DE-WORD> [RU-CANDIDATE...]

В параллель опрашивает все источники списка («Словари» в CLAUDE.md):
DE→RU: Adelung 1811 BSB, Grimm DWB, DWDS, Pfeifer (DWDS etymwb), Duden, Duden Synonyme,
       Wiktionary DE, Wortschatz Leipzig, БНРС (translate.academic.ru), Multitran DE→RU,
       PONS DE-RU, Langenscheidt DE-RU.
RU→DE (по каждому RU-кандидату): Multitran RU→DE, БРНС (translate.academic.ru).

Статусы:
  ✓  HTML загружен, извлечение получилось.
  ⚠  SPA / partial HTML — извлечение неполное, обязателен WebFetch URL вручную.
  ❌  Ошибка / 404 / нет статьи.

ПРИМЕНЕНИЕ. При любом запросе «проверь точность», «полное исследование», «исследуй
слово» — обязательно запускать и приводить полный вывод в чат до анализа.
Без вывода скрипта заявлять «исследование проведено» ЗАПРЕЩЕНО.
"""
import concurrent.futures
import re
import sys
import urllib.parse
import urllib.request
from html import unescape

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
TIMEOUT = 25


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"__ERROR__: {e}"


def strip_html(h, n=600):
    if not h or h.startswith("__ERROR__"):
        return ""
    t = re.sub(r"<script[^>]*>.*?</script>", " ", h, flags=re.S)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n]


def find_block(h, *needles, before=200, after=600):
    """Найти первое вхождение одного из needles в HTML, вернуть кусок вокруг (после очистки тегов)."""
    if not h or h.startswith("__ERROR__"):
        return ""
    for ndl in needles:
        m = re.search(re.escape(ndl), h, re.I)
        if m:
            chunk = h[max(0, m.start() - before): m.start() + after]
            return strip_html(chunk, after)
    return ""


def adelung_alt_forms(word):
    forms = [word]
    # 1820-е: Tot- часто как Todt-
    if word[:3].lower() == "tot":
        forms.append(word[0] + "od" + word[2:])
    # Th- вместо T- в начале (Thron, Theil, Thier)
    if word[:1] == "T" and word[:2] != "Th":
        forms.append("Th" + word[1:])
    # rts → rths (Wirtshaus → Wirthshaus)
    if "rts" in word:
        forms.append(word.replace("rts", "rths", 1))
    # ödl → ödtl (tödlich → tödtlich)
    if "ödl" in word:
        forms.append(word.replace("ödl", "ödtl", 1))
    # ss → ß для строгих архаизмов
    if "ss" in word:
        forms.append(word.replace("ss", "ß", 1))
    return forms


def adelung(word):
    name = "Adelung 1811 BSB"
    last_url = ""
    for form in adelung_alt_forms(word):
        url = f"https://lexika.digitale-sammlungen.de/adelung/suche/abfrage?lemma={urllib.parse.quote(form)}"
        last_url = url
        h = fetch(url)
        if h.startswith("__ERROR__"):
            return (name, url, "❌", h)
        ids = re.findall(r'href="\.\./lemma/(bsb\d+_\d+_\d+_\d+)"[^>]*>([^<]+)', h)
        if ids:
            bsb_id, lemma_name = ids[0]
            lemma_url = f"https://lexika.digitale-sammlungen.de/adelung/lemma/{bsb_id}"
            lh = fetch(lemma_url)
            text = strip_html(lh, 700)
            return (name, lemma_url, "✓", f"[{lemma_name.strip()}] {text}")
    return (name, last_url, "❌ нет совпадений", f"пробовано: {adelung_alt_forms(word)}")


def grimm(word):
    name = "Grimm DWB"
    url = f"https://www.dwds.de/wb/dwb/{urllib.parse.quote(word.lower())}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    if "Diese Seite existiert nicht" in h or "Anmelden" in h and len(h) < 5000:
        return (name, url, "⚠ SPA / возможно нет статьи — WebFetch", strip_html(h, 200))
    text = find_block(h, "DWB", "Bedeutung", "wörterbuch", after=800) or strip_html(h, 500)
    return (name, url, "⚠ SPA — WebFetch для полноты", text)


def dwds(word):
    name = "DWDS"
    url = f"https://www.dwds.de/wb/{urllib.parse.quote(word.lower())}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    text = find_block(h, "dwdswb-lemma", "Bedeutung", "Definition", after=600) or strip_html(h, 400)
    return (name, url, "⚠ SPA — WebFetch для полноты", text)


def pfeifer(word):
    name = "Pfeifer (DWDS etymwb)"
    url = f"https://www.dwds.de/wb/etymwb/{urllib.parse.quote(word.lower())}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    text = find_block(h, "etymwb", "Etymologie", "Herkunft", after=600) or strip_html(h, 400)
    return (name, url, "⚠ SPA — WebFetch", text)


def duden(word):
    name = "Duden"
    url = f"https://www.duden.de/rechtschreibung/{urllib.parse.quote(word)}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    if "Seite nicht gefunden" in h or "Sorry, no result" in h:
        return (name, url, "❌ 404", "")
    text = find_block(h, "Bedeutung", "Bedeutungen", "Wortart", after=500) or strip_html(h, 400)
    return (name, url, "⚠ JS-load — WebFetch", text)


def duden_syn(word):
    name = "Duden Synonyme"
    url = f"https://www.duden.de/synonyme/{urllib.parse.quote(word)}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    if "Seite nicht gefunden" in h or "Sorry, no result" in h:
        return (name, url, "❌ 404", "")
    text = find_block(h, "Bedeutung", "Synonyme", after=600) or strip_html(h, 400)
    return (name, url, "⚠ JS-load — WebFetch", text)


def wiktionary(word):
    name = "Wiktionary DE"
    url = f"https://de.wiktionary.org/wiki/{urllib.parse.quote(word)}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    if "Diese Seite existiert nicht" in h or "Es existiert noch kein Eintrag" in h:
        return (name, url, "❌ нет статьи", "")
    text = find_block(h, "Bedeutung", "Wortart", "Herkunft", after=600) or strip_html(h, 400)
    return (name, url, "✓", text)


def leipzig(word):
    name = "Wortschatz Leipzig"
    url = f"https://corpora.uni-leipzig.de/de/res?corpusId=deu_news_2024&word={urllib.parse.quote(word)}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    text = find_block(h, "Häufigkeitsklasse", "Anzahl", "Frequenz", "Nachbarn", after=400) or strip_html(h, 300)
    return (name, url, "⚠ SPA — WebFetch для частот.", text)


def bnrs(word):
    name = "БНРС translate.academic.ru DE→RU"
    url = f"https://translate.academic.ru/{urllib.parse.quote(word)}/de/ru/"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    text = find_block(h, "Большой немецко-русский", "Универсальный", word, after=700) or strip_html(h, 500)
    return (name, url, "✓", text)


def multitran_de_ru(word):
    name = "Multitran DE→RU"
    url = f"https://www.multitran.com/m.exe?l1=3&l2=2&s={urllib.parse.quote(word)}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    text = find_block(h, "subject", "translit", "общ.", "поэт.", after=700) or strip_html(h, 500)
    return (name, url, "✓", text)


def pons(word):
    name = "PONS DE-RU"
    url = f"https://de.pons.com/%C3%BCbersetzung/deutsch-russisch/{urllib.parse.quote(word)}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    text = find_block(h, "translation", "Übersetzung", "russisch", after=500) or strip_html(h, 400)
    return (name, url, "⚠ SPA — WebFetch", text)


def langenscheidt(word):
    name = "Langenscheidt DE-RU"
    url = f"https://de.langenscheidt.com/deutsch-russisch/{urllib.parse.quote(word.lower())}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    text = find_block(h, "translation", "Übersetzung", "lemma", after=500) or strip_html(h, 400)
    return (name, url, "⚠ SPA — WebFetch", text)


def multitran_ru_de(ru_word):
    name = f"Multitran RU→DE «{ru_word}»"
    url = f"https://www.multitran.com/m.exe?l1=2&l2=3&s={urllib.parse.quote(ru_word)}"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    text = find_block(h, "subject", "Übersetzung", "общ.", after=700) or strip_html(h, 500)
    return (name, url, "✓", text)


def brns(ru_word):
    name = f"БРНС translate.academic.ru RU→DE «{ru_word}»"
    url = f"https://translate.academic.ru/{urllib.parse.quote(ru_word)}/ru/de/"
    h = fetch(url)
    if h.startswith("__ERROR__"):
        return (name, url, "❌", h)
    text = find_block(h, "Большой русско-немецкий", "Универсальный", ru_word, after=700) or strip_html(h, 500)
    return (name, url, "✓", text)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/word-check.py <DE-WORD> [RU-CANDIDATE...]")
        sys.exit(1)
    de_word = sys.argv[1]
    ru_candidates = sys.argv[2:]

    print(f"=== Word check: «{de_word}» ===")
    if ru_candidates:
        print(f"RU кандидаты для обратной сверки: {', '.join('«' + r + '»' for r in ru_candidates)}")
    print()

    de_tasks = [
        adelung, grimm, dwds, pfeifer, duden, duden_syn,
        wiktionary, leipzig, bnrs, multitran_de_ru, pons, langenscheidt,
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        de_futures = [ex.submit(task, de_word) for task in de_tasks]
        ru_futures = []
        for ru in ru_candidates:
            ru_futures.append(ex.submit(multitran_ru_de, ru))
            ru_futures.append(ex.submit(brns, ru))

        print(f"=== DE→RU словари ({len(de_tasks)} источников) ===\n")
        for fut in de_futures:
            name, url, status, text = fut.result()
            print(f"### {name}  [{status}]")
            print(f"  URL: {url}")
            if text:
                print(f"  {text[:700]}")
            print()

        if ru_candidates:
            print(f"\n=== RU→DE обратная сверка ({len(ru_candidates)} кандидатов × 2 источника) ===\n")
            for fut in ru_futures:
                name, url, status, text = fut.result()
                print(f"### {name}  [{status}]")
                print(f"  URL: {url}")
                if text:
                    print(f"  {text[:700]}")
                print()

    print("\n=== ПРАВИЛО ===")
    print("Без вывода ВСЕХ источников в чате — заявлять «исследование проведено» ЗАПРЕЩЕНО.")
    print("⚠ источники (SPA / partial HTML) — обязательны к WebFetch вручную; вывод привести в чат.")


if __name__ == "__main__":
    main()
