#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
word_check_lib — слой загрузки словарей для полного словарного аудита Winterreise.

Цель: по одному немецкому слову собрать ПОЛНУЮ таблицу-доказательство по всем
источникам, разложенную по группам, с приоритетом ТОЛКОВЫХ СЛОВАРЕЙ НАЧАЛА XIX в.
(основные значения слова в эпоху Мюллера — это решающее).

Группы:
  A.  Толковые 1820-х (ПРИОРИТЕТ): Adelung Wien 1811 (BSB), Campe 1807-11 (woerterbuchnetz API), Grimm DWB.
  A'. Современные толковые/этимол. (вторичные): DWDS, Pfeifer (EtymWb), Duden, Duden Synonyme, Wiktionary, Leipzig (частоты).
  A+. Доп. историч. (опц., woerterbuchnetz API): Goethe-WB (GWB), Wander (пословицы).
  B.  Нем→рус (DE→RU): БНРС, Multitran DE→RU, PONS, Langenscheidt.
  C.  Рус→нем (RU→DE, на каждый RU-кандидат): БРНС, Multitran RU→DE.
  D.  RU-толковые (на каждый RU-кандидат): gufo.me (Ушаков/Ожегов/Ефремова/Даль/Кузнецов).

Сырьё каждого источника сохраняется на диск (raw_dir) — citation-цитаты потом
детерминированно сверяются подстрокой (анти-галлюцинация, Фаза 3).

Статусы: ✓ извлечено; ⚠ нужен ручной WebFetch (истинный SPA — PONS); ❌ ошибка/нет статьи.
"""
import concurrent.futures
import html
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
TIMEOUT = 30
WBNET_API = "https://api.woerterbuchnetz.de"

# academic.ru (БНРС/БРНС) 429-ит при параллели → отдельный троттлинг-замок.
_academic_lock = threading.Lock()
_academic_last = [0.0]
_ACADEMIC_MIN_INTERVAL = 1.2  # сек между запросами к academic.ru


# ---------- HTTP ----------

def _raw_fetch(url, tries=3, host_throttle=False):
    """GET с ретраями/бэкоффом. Возвращает (ok, status_code, text)."""
    last_err = ""
    for attempt in range(tries):
        if host_throttle:
            with _academic_lock:
                dt = time.monotonic() - _academic_last[0]
                if dt < _ACADEMIC_MIN_INTERVAL:
                    time.sleep(_ACADEMIC_MIN_INTERVAL - dt)
                _academic_last[0] = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                        "Accept-Language": "de,ru;q=0.8,en;q=0.5"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return True, resp.getcode(), resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}"
            if e.code in (429, 500, 502, 503):
                time.sleep(1.5 * (attempt + 1))
                continue
            return False, e.code, last_err
        except Exception as e:
            last_err = str(e)
            time.sleep(1.0 * (attempt + 1))
    return False, 0, last_err


def _save_raw(raw_dir, source, ext, content):
    if not raw_dir:
        return ""
    os.makedirs(raw_dir, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", source)
    path = os.path.join(raw_dir, f"{safe}.{ext}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _strip(h, limit=1200):
    t = re.sub(r"<script[^>]*>.*?</script>", " ", h, flags=re.S)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:limit]


def _entity_decode_path(word):
    """ü→ue, ö→oe, ä→ae, ß→ss (для Duden-URL)."""
    return (word.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
                .replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
                .replace("ß", "ss"))


def _latin1_quote(word):
    """Latin-1 percent-encoding (Adelung BSB ждёт %FC, не UTF-8 %C3%BC)."""
    try:
        return urllib.parse.quote(word.encode("latin-1"))
    except UnicodeEncodeError:
        return urllib.parse.quote(word)


# ---------- A. Толковые 1820-х ----------

def src_adelung(word, raw_dir):
    name, group = "Adelung Wien 1811 (BSB)", "A"
    # поиск с Latin-1 + орфографич. альтернативы 1820-х
    alts = [word]
    if word[:1] in "Tt" and word[:2].lower() != "th":
        alts.append(word[0] + "h" + word[1:])
    if word[:3].lower() == "tot":
        alts.append(word[0] + "od" + word[2:])
    search_url = ""
    for form in alts:
        search_url = f"https://lexika.digitale-sammlungen.de/adelung/suche/abfrage?lemma={_latin1_quote(form)}"
        ok, code, body = _raw_fetch(search_url)
        if not ok:
            continue
        hits = re.findall(r'href="\.\./lemma/(bsb\d+_\d+_\d+_\d+)"[^>]*>([^<]+)', body)
        if hits:
            # выбрать лемму, ближе к искомой (по нормализованной метке)
            def norm(s): return html.unescape(s).strip().lower()
            best = None
            for lid, label in hits:
                if norm(label) == word.lower():
                    best = (lid, label); break
            if best is None:
                best = (hits[0][0], hits[0][1])
            lid, label = best
            lemma_url = f"https://lexika.digitale-sammlungen.de/adelung/lemma/{lid}"
            ok2, c2, page = _raw_fetch(lemma_url)
            path = _save_raw(raw_dir, "A_adelung", "html", page if ok2 else body)
            if ok2:
                # извлечь содержимое статьи (div.content), схлопнуть переносы
                m = re.search(r'class="content"[^>]*>(.*?)</div>\s*</div>', page, flags=re.S)
                chunk = m.group(1) if m else page
                text = _strip(chunk, 3200)
                # отрезать ведущую навигацию: начать с заголовка-леммы
                hw = html.unescape(label).strip()
                i = text.find(hw)
                if 0 <= i < 400:
                    text = text[i:]
                others = "" if len(hits) == 1 else f" [ещё леммы: {', '.join(html.unescape(l).strip() for _,l in hits[1:4])}]"
                return dict(name=name, group=group, url=lemma_url, status="✓",
                           text=text[:2800] + others, raw=path)
            return dict(name=name, group=group, url=lemma_url, status="❌ статья не открылась", text=c2 and str(c2), raw=path)
    _save_raw(raw_dir, "A_adelung", "html", "no match")
    return dict(name=name, group=group, url=search_url, status="❌ нет совпадений",
                text=f"пробовано: {alts}", raw="")


def _wbnetz_article(sigle, word, prefer_gram=None):
    """woerterbuchnetz API: lemma→lemid→article tokens. Возвращает (url, lemmas, text)."""
    q = urllib.parse.quote(word)
    lem_url = f"{WBNET_API}/dictionaries/{sigle}/lemmata/lemma/{q}/20/json"
    ok, code, body = _raw_fetch(lem_url)
    if not ok:
        return lem_url, [], f"❌ поиск леммы: {body}"
    try:
        lemmas = json.loads(body)
    except Exception as e:
        return lem_url, [], f"❌ JSON: {e}"
    if not isinstance(lemmas, list) or not lemmas:
        return lem_url, [], "❌ нет леммы"
    # выбрать lemid: предпочесть нужную часть речи, иначе первую
    chosen = lemmas[0]
    if prefer_gram:
        for L in lemmas:
            if prefer_gram in (L.get("gram") or "").lower():
                chosen = L; break
    lemid = chosen.get("value")
    art_url = f"{WBNET_API}/dictionaries/{sigle}/articles/{lemid}/formid"
    ok2, c2, abody = _raw_fetch(art_url)
    if not ok2:
        return art_url, lemmas, f"❌ статья: {abody}"
    try:
        toks = json.loads(abody)
        text = "".join(html.unescape(t.get("word", "")) for t in toks)
        text = re.sub(r"\s+", " ", text).strip()
    except Exception as e:
        text = f"❌ парс статьи: {e}"
    label = html.unescape(chosen.get("label", "")).strip()
    gram = chosen.get("gram", "")
    variants = "; ".join(f"{html.unescape(L.get('label','')).strip()}({L.get('gram','')})" for L in lemmas[:4])
    return art_url, lemmas, f"[{label} · {gram}] {text}  «леммы: {variants}»"


def src_campe(word, raw_dir):
    name, group = "Campe 1807-11 (woerterbuchnetz)", "A"
    # prefer_gram=None → первая (основная) лемма; точный выбор по POS придёт из Фазы 0.
    url, lemmas, text = _wbnetz_article("Campe", word, prefer_gram=None)
    _save_raw(raw_dir, "A_campe", "txt", text)
    status = "✓" if not text.startswith("❌") else "❌"
    return dict(name=name, group=group, url=url, status=status, text=text[:2800], raw="")


def src_grimm(word, raw_dir):
    name, group = "Grimm DWB", "A"
    url = f"https://www.dwds.de/wb/dwb/{urllib.parse.quote(word.lower())}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "A_grimm", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status="❌", text=str(body), raw=path)
    if "Diese Seite existiert nicht" in body:
        return dict(name=name, group=group, url=url, status="❌ нет статьи", text="", raw=path)
    m = re.search(r'class="dwb-entry"', body)
    start = m.start() if m else 0
    # некоторые статьи лидируют огромным списком вложенных композитов
    # («eingebettete Stichwörter») — пропустить его до первого значения dwb-sense.
    head_end = body.find("eingebettete Stichw", start)
    sense = re.search(r'class="dwb-sense"', body)
    if head_end != -1 and sense and sense.start() > head_end:
        head = _strip(body[start:head_end], 700)
        senses = _strip(body[sense.start():], 2200)
        text = head + " […значения:] " + senses
    else:
        text = _strip(body[start:], 2800)
    return dict(name=name, group=group, url=url, status="✓", text=text, raw=path)


# ---------- A'. Современные толковые/этимол. ----------

def src_dwds(word, raw_dir):
    name, group = "DWDS", "A'"
    url = f"https://www.dwds.de/wb/{urllib.parse.quote(word.lower())}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "Am_dwds", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status="❌", text=str(body), raw=path)
    m = re.search(r'class="dwdswb-lesart-def"|class="dwdswb-definitionen?"|class="dwdswb-lesarten?"', body)
    chunk = body[m.start():] if m else body
    return dict(name=name, group=group, url=url, status="✓", text=_strip(chunk, 1300), raw=path)


def src_pfeifer(word, raw_dir):
    name, group = "Pfeifer EtymWb", "A'"
    url = f"https://www.dwds.de/wb/etymwb/{urllib.parse.quote(word.lower())}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "Am_pfeifer", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status="❌", text=str(body), raw=path)
    if "Diese Seite existiert nicht" in body:
        return dict(name=name, group=group, url=url, status="❌ нет статьи", text="", raw=path)
    m = re.search(r'class="dwdswb-ft-blocktext"|Etymolog|class="dwdswb-etymwb', body)
    chunk = body[m.start():] if m else body
    return dict(name=name, group=group, url=url, status="✓", text=_strip(chunk, 1000), raw=path)


def src_duden(word, raw_dir):
    name, group = "Duden", "A'"
    url = f"https://www.duden.de/rechtschreibung/{_entity_decode_path(word)}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "Am_duden", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status=f"❌ {body}", text="", raw=path)
    b = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    m = re.search(r'id="bedeutungen?"', b)
    chunk = b[m.start():] if m else b
    return dict(name=name, group=group, url=url, status="✓", text=_strip(chunk, 1200), raw=path)


def src_duden_syn(word, raw_dir):
    name, group = "Duden Synonyme", "A'"
    url = f"https://www.duden.de/synonyme/{_entity_decode_path(word)}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "Am_dudensyn", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status=f"❌ {body}", text="", raw=path)
    b = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    m = re.search(r'class="enumeration"', b) or re.search(r'Vorhandene Synonyme', b)
    chunk = b[m.start():] if m else b
    return dict(name=name, group=group, url=url, status="✓", text=_strip(chunk, 1000), raw=path)


def src_wiktionary(word, raw_dir):
    name, group = "Wiktionary DE", "A'"
    url = f"https://de.wiktionary.org/wiki/{urllib.parse.quote(word)}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "Am_wiktionary", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status="❌", text=str(body), raw=path)
    if "Es existiert noch kein Eintrag" in body or "Diese Seite existiert nicht" in body:
        return dict(name=name, group=group, url=url, status="❌ нет статьи", text="", raw=path)
    m = re.search(r'Bedeutungen', body)
    chunk = body[m.start():] if m else body
    return dict(name=name, group=group, url=url, status="✓", text=_strip(chunk, 900), raw=path)


def src_leipzig(word, raw_dir):
    name, group = "Wortschatz Leipzig (частоты)", "A'"
    url = f"https://corpora.uni-leipzig.de/de/res?corpusId=deu_news_2024&word={urllib.parse.quote(word)}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "Am_leipzig", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status="❌", text=str(body), raw=path)
    m = re.search(r'Häufigkeitsklasse|Rang:', body)
    chunk = body[m.start()-50:] if m else body
    return dict(name=name, group=group, url=url, status="✓", text=_strip(chunk, 400), raw=path)


# ---------- A+. Доп. историч. (woerterbuchnetz) ----------

def src_goethe(word, raw_dir):
    name, group = "Goethe-Wörterbuch (GWB)", "A+"
    url, lemmas, text = _wbnetz_article("GWB", word)
    _save_raw(raw_dir, "Ap_goethe", "txt", text)
    status = "✓" if not text.startswith("❌") else "❌ нет статьи"
    return dict(name=name, group=group, url=url, status=status, text=text[:900], raw="")


def src_wander(word, raw_dir):
    name, group = "Wander Sprichwörter", "A+"
    url, lemmas, text = _wbnetz_article("Wander", word)
    _save_raw(raw_dir, "Ap_wander", "txt", text)
    status = "✓" if not text.startswith("❌") else "❌ нет статьи"
    return dict(name=name, group=group, url=url, status=status, text=text[:700], raw="")


# ---------- B. Нем→рус ----------

def src_bnrs(word, raw_dir):
    name, group = "БНРС (academic.ru) DE→RU", "B"
    url = f"https://translate.academic.ru/{urllib.parse.quote(word)}/de/ru/"
    ok, code, body = _raw_fetch(url, host_throttle=True)
    path = _save_raw(raw_dir, "B_bnrs", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status=f"❌ {body}", text="", raw=path)
    m = re.search(r'class="translate_definition"', body) or re.search(r'class="dictionary"', body)
    chunk = body[m.start():] if m else body
    return dict(name=name, group=group, url=url, status="✓", text=_strip(chunk, 1100), raw=path)


def src_multitran_de(word, raw_dir):
    name, group = "Multitran DE→RU", "B"
    url = f"https://www.multitran.com/m.exe?l1=3&l2=2&s={urllib.parse.quote(word)}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "B_multitran", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status="❌", text=str(body), raw=path)
    # переводы в ячейках с классом trans / ссылки на статьи
    cells = re.findall(r'<td[^>]*class="trans"[^>]*>(.*?)</td>', body, flags=re.S)
    text = " | ".join(_strip(c, 120) for c in cells[:12]) if cells else _strip(body, 700)
    return dict(name=name, group=group, url=url, status="✓", text=text[:900], raw=path)


def src_pons(word, raw_dir):
    name, group = "PONS DE-RU", "B"
    url = f"https://de.pons.com/übersetzung/deutsch-russisch/{urllib.parse.quote(word)}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "B_pons", "html", body if ok else str(body))
    # PONS — истинный SPA: переводы грузятся JS, в сыром HTML их нет → нужен WebFetch.
    has_ru = bool(re.search(r"[А-Яа-яёЁ]{3,}", body)) if ok else False
    if ok and has_ru:
        m = re.search(r'class="target"', body)
        chunk = body[m.start():] if m else body
        return dict(name=name, group=group, url=url, status="✓", text=_strip(chunk, 800), raw=path)
    return dict(name=name, group=group, url=url, status="⚠ SPA → WebFetch", text="(русские переводы грузятся JS; забрать вручную WebFetch)", raw=path)


def src_langenscheidt(word, raw_dir):
    name, group = "Langenscheidt DE-RU", "B"
    url = f"https://de.langenscheidt.com/deutsch-russisch/{urllib.parse.quote(word.lower())}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, "B_langenscheidt", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status="❌", text=str(body), raw=path)
    ru = re.findall(r'[А-Яа-яёЁ][А-Яа-яёЁ \-,]{2,60}', _strip(body, 4000))
    text = " | ".join(dict.fromkeys(r.strip() for r in ru))[:600] if ru else _strip(body, 600)
    status = "✓" if ru else "⚠ нет RU в HTML → WebFetch"
    return dict(name=name, group=group, url=url, status=status, text=text, raw=path)


# ---------- C. Рус→нем (на RU-кандидат) ----------

def src_brns(ru, raw_dir):
    name, group = f"БРНС (academic.ru) RU→DE «{ru}»", "C"
    url = f"https://translate.academic.ru/{urllib.parse.quote(ru)}/ru/de/"
    ok, code, body = _raw_fetch(url, host_throttle=True)
    path = _save_raw(raw_dir, f"C_brns_{ru}", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status=f"❌ {body}", text="", raw=path)
    m = re.search(r'class="translate_definition"', body) or re.search(r'class="dictionary"', body)
    chunk = body[m.start():] if m else body
    return dict(name=name, group=group, url=url, status="✓", text=_strip(chunk, 900), raw=path)


def src_multitran_ru(ru, raw_dir):
    name, group = f"Multitran RU→DE «{ru}»", "C"
    url = f"https://www.multitran.com/m.exe?l1=2&l2=3&s={urllib.parse.quote(ru)}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, f"C_multitran_{ru}", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status="❌", text=str(body), raw=path)
    cells = re.findall(r'<td[^>]*class="trans"[^>]*>(.*?)</td>', body, flags=re.S)
    text = " | ".join(_strip(c, 120) for c in cells[:12]) if cells else _strip(body, 600)
    return dict(name=name, group=group, url=url, status="✓", text=text[:800], raw=path)


# ---------- D. RU-толковые (на RU-кандидат) ----------

def src_gufo(ru, raw_dir):
    name, group = f"RU-толковые gufo.me «{ru}»", "D"
    url = f"https://gufo.me/dict/ushakov/{urllib.parse.quote(ru)}"
    ok, code, body = _raw_fetch(url)
    path = _save_raw(raw_dir, f"D_gufo_{ru}", "html", body if ok else str(body))
    if not ok:
        return dict(name=name, group=group, url=url, status="❌", text=str(body), raw=path)
    if "Ничего не найдено" in body or "404" in (str(code)):
        return dict(name=name, group=group, url=url, status="❌ нет статьи", text="", raw=path)
    # gufo.me агрегирует несколько словарей; вытащим заголовки словарей + определения
    text = _strip(body, 1600)
    i = text.upper().find(ru.upper())
    if 0 <= i < 800:
        text = text[i:]
    return dict(name=name, group=group, url=url, status="✓", text=text[:1200], raw=path)


# ---------- Оркестрация ----------

DE_SOURCES = [
    src_adelung, src_campe, src_grimm,                # A
    src_dwds, src_pfeifer, src_duden, src_duden_syn, src_wiktionary, src_leipzig,  # A'
    src_goethe, src_wander,                           # A+
    src_bnrs, src_multitran_de, src_pons, src_langenscheidt,  # B
]
RU_SOURCES = [src_brns, src_multitran_ru, src_gufo]   # C, D


def check_word(de_word, ru_candidates=None, raw_root=None):
    ru_candidates = ru_candidates or []
    raw_dir = os.path.join(raw_root, de_word) if raw_root else None
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(fn, de_word, raw_dir) for fn in DE_SOURCES]
        ru_futs = []
        for ru in ru_candidates:
            rd = os.path.join(raw_dir, "ru", ru) if raw_dir else None
            for fn in RU_SOURCES:
                ru_futs.append(ex.submit(fn, ru, rd))
        for f in futs:
            results.append(f.result())
        for f in ru_futs:
            results.append(f.result())
    return results
