#!/usr/bin/env python3
"""Механическая валидация всех песен: структура данных, диапазоны, типографика.

Запуск: python3 scripts/validate_all.py            — все песни
        python3 scripts/validate_all.py 07 19      — только указанные номера

Коды: E = ошибка (чинить), W = предупреждение (посмотреть глазами).
"""
import json, glob, re, sys, os

SONGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'songs')
INDEX = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'index.json')

SEG_KEYS = {'ru', 'de', 'variant_ru', 'variant_de'}
ANN_KEYS = {'type', 'segment_range', 'text', 'line_span', 'continuation_ranges', 'target'}
YO_RE = re.compile(r'\bеще\b|задает|осознается|передает|\bидет\b|найдет|\bчетко\b'
                   r'|твердой|замерзш|\bсвое\b|изможденн|истощенн|потрясенн|удрученн|огорченн|\b(?:во|в|о|об|обо|на|при)\s+(?:всем|нем)\b')
findings = []


def add(sev, song, loc, code, msg):
    findings.append((sev, song, loc, code, msg))


def is_pair(x):
    return isinstance(x, list) and len(x) == 2 and all(isinstance(v, int) for v in x)


def norm_ranges(sr):
    """segment_range -> список пар [[s,e],...] или None, если форма кривая."""
    if is_pair(sr):
        return [sr]
    if isinstance(sr, list) and sr and all(is_pair(p) for p in sr):
        return sr
    return None


def check_text_typography(song, loc, text, kind):
    """kind: 'ru' (сегмент) или 'ann' (аннотация)."""
    if re.search(r'"[А-Яа-яёЁ]|[А-Яа-яёЁ]"', text):
        add('E', song, loc, 'ascii-quote', f'ASCII-кавычка у кириллицы: {text[:60]!r}')
    if YO_RE.search(text):
        add('E', song, loc, 'yo', f'возможна е вместо ё: «{YO_RE.search(text).group(0)}» в {text[:60]!r}')
    if '–' in text:
        add('W', song, loc, 'endash', f'короткое тире (en dash): {text[:60]!r}')
    if re.search(r'[а-яё] - [а-яё]', text):
        add('E', song, loc, 'hyphen-dash', f'дефис вместо тире между словами: {text[:60]!r}')
    if '…' in text:
        add('W', song, loc, 'ellipsis-char', f'символ … вместо трёх точек: {text[:60]!r}')
    if '  ' in text:
        add('E', song, loc, 'dblspace', f'двойной пробел: {text[:60]!r}')
    if re.search(r'[а-яё] [,;:]', text) or re.search(r'[а-яё] \.(?!\.)', text):
        add('E', song, loc, 'space-punct', f'пробел перед знаком: {text[:60]!r}')
    if kind == 'ann':
        if '\n\n' in text:
            add('E', song, loc, 'nn', 'двойной \\n в аннотации (нужен одиночный)')
        # немецкое в ёлочках (стиль: немецкое без кавычек) — только чисто латинское содержимое
        for m in re.finditer(r'«([^»]+)»', text):
            inner = m.group(1)
            if re.search(r'[A-Za-zÄÖÜäöüß]', inner) and not re.search(r'[А-Яа-яёЁ]', inner):
                add('W', song, loc, 'de-in-quotes', f'немецкое в ёлочках: «{inner[:40]}»')


def check_song(path):
    song = os.path.basename(path)
    try:
        d = json.load(open(path, encoding='utf-8'))
    except Exception as e:
        add('E', song, '-', 'json', f'не парсится: {e}')
        return None

    m = re.match(r'(\d+)', song)
    if m and d.get('number') != int(m.group(1)):
        add('E', song, '-', 'number', f'number={d.get("number")} не совпадает с именем файла')

    # плоский список строк всей песни (line_span может пересекать строфы)
    flat = []  # (stanza_i, line_i, lines_de_str, segments, annotations)
    for si, st in enumerate(d.get('stanzas', [])):
        lde, lru = st.get('lines_de', []), st.get('lines_ru', [])
        if len(lde) != len(lru):
            add('E', song, f'stz{si}', 'line-count', f'lines_de={len(lde)} != lines_ru={len(lru)}')
        for li in range(min(len(lde), len(lru))):
            flat.append((si, li, lde[li], lru[li].get('segments', []), lru[li].get('annotations', [])))

    markers = {}  # (flat_idx, seg_idx) -> [описания аннотаций]

    for fi, (si, li, lde, segs, anns) in enumerate(flat):
        loc = f'stz{si}L{li}'
        # --- сегменты ---
        for gi, s in enumerate(segs):
            extra = set(s) - SEG_KEYS
            if extra:
                add('W', song, f'{loc}[{gi}]', 'seg-keys', f'неизвестные ключи {extra}')
            ru, de = s.get('ru', ''), s.get('de', '')
            if not ru:
                add('E', song, f'{loc}[{gi}]', 'empty-ru', 'пустой ru (запрещено правилом 18)')
            if re.search(r'[,!?;:]', de) or re.search(r'(?<!\.)\.(?!\.)', de):
                add('E', song, f'{loc}[{gi}]', 'punct-in-de', f'пунктуация в de: {de!r}')
            if ('variant_de' in s) != ('variant_ru' in s):
                add('W', song, f'{loc}[{gi}]', 'variant-pair', f'variant_de/variant_ru не парой: {s}')
            check_text_typography(song, f'{loc}[{gi}]', ru, 'ru')
        # прописная в начале строки (правило 58)
        if segs:
            first = segs[0].get('ru', '')
            mm = re.search(r'[А-Яа-яёЁA-Za-z]', first)
            if mm and mm.group(0).islower():
                add('E', song, loc, 'lowercase-start', f'строка начинается со строчной: {first!r}')
        # --- аннотации ---
        for ai, a in enumerate(anns):
            aloc = f'{loc}/ann{ai}'
            extra = set(a) - ANN_KEYS
            if extra:
                add('W', song, aloc, 'ann-keys', f'неизвестные ключи {extra}')
            if a.get('type') not in ('lang', 'meaning'):
                add('E', song, aloc, 'ann-type', f'type={a.get("type")!r}')
            if not a.get('text', '').strip():
                add('E', song, aloc, 'ann-empty', 'пустой текст')
            check_text_typography(song, aloc, a.get('text', ''), 'ann')

            pairs = norm_ranges(a.get('segment_range'))
            if pairs is None:
                add('E', song, aloc, 'range-form', f'кривая форма segment_range: {a.get("segment_range")}')
                continue
            for s_, e_ in pairs:
                if not (0 <= s_ <= e_ < len(segs)):
                    add('E', song, aloc, 'range-bounds',
                        f'segment_range [{s_},{e_}] вне сегментов 0..{len(segs)-1}')
            span = a.get('line_span', 1)
            cont = a.get('continuation_ranges')
            marker_pos = (fi, pairs[-1][1])  # по умолчанию — конец последней пары якорной строки
            if span == 1 and cont:
                add('E', song, aloc, 'cont-nospan', 'continuation_ranges при line_span=1')
            if span > 1:
                if cont is not None and len(cont) != span - 1:
                    add('E', song, aloc, 'cont-len',
                        f'line_span={span}, а continuation_ranges: {len(cont)} (нужно {span-1})')
                if fi + span - 1 >= len(flat):
                    add('E', song, aloc, 'span-bounds', f'line_span={span} выходит за конец песни')
                last_fi = min(fi + span - 1, len(flat) - 1)
                if cont is None:
                    marker_pos = (last_fi, len(flat[last_fi][3]) - 1)
                if cont:
                    if cont[-1] == [-1, -1]:
                        add('E', song, aloc, 'marker-lost',
                            'последний continuation=[-1,-1] — сноска не отрисуется')
                    for k, cr in enumerate(cont):
                        tgt = fi + 1 + k
                        if tgt >= len(flat):
                            break
                        cpairs = norm_ranges(cr) if cr != [-1, -1] else 'skip'
                        if cr == [-1, -1]:
                            continue
                        if cpairs is None:
                            add('E', song, aloc, 'cont-form', f'кривой continuation_range[{k}]: {cr}')
                            continue
                        tsegs = flat[tgt][3]
                        for s_, e_ in cpairs:
                            if not (0 <= s_ <= e_ < len(tsegs)):
                                add('E', song, aloc, 'cont-bounds',
                                    f'continuation[{k}] [{s_},{e_}] вне сегментов строки '
                                    f'stz{flat[tgt][0]}L{flat[tgt][1]} (0..{len(tsegs)-1})')
                        marker_pos = (tgt, cpairs[-1][1])
            slot = 'variant' if a.get('target') == 'variant' else 'main'
            markers.setdefault((marker_pos, slot), []).append(f'{a.get("type")}@{aloc}')

    # коллизии сносок: два маркера на одном сегменте (правило: сноска на сегменте одна)
    for ((tfi, gi), slot), lst in markers.items():
        if len(lst) > 1 and tfi < len(flat):
            si, li = flat[tfi][0], flat[tfi][1]
            add('W', song, f'stz{si}L{li}[{gi}]', 'marker-collision',
                f'{len(lst)} сноски на одном сегменте: {lst} (спанящая вытесняет локальную — проверить глазами)')

    # title_annotations
    for ti, a in enumerate(d.get('title_annotations', [])):
        if 'segment_range' in a:
            add('E', song, f'title/ann{ti}', 'title-range', 'segment_range в title_annotation')
        check_text_typography(song, f'title/ann{ti}', a.get('text', ''), 'ann')
    return d


def main():
    only = set(sys.argv[1:])
    files = sorted(glob.glob(os.path.join(SONGS_DIR, '*.json')))
    if only:
        files = [f for f in files if re.match(r'(\d+)', os.path.basename(f)).group(1) in only]
    data = {}
    for f in files:
        d = check_song(f)
        if d:
            data[os.path.basename(f)] = d
    # сверка с index.json
    try:
        idx = json.load(open(INDEX, encoding='utf-8'))
        entries = idx if isinstance(idx, list) else idx.get('songs', [])
        by_num = {e.get('number'): e for e in entries}
        for name, d in data.items():
            e = by_num.get(d.get('number'))
            if not e:
                add('E', 'index.json', '-', 'idx-missing', f'нет записи для №{d.get("number")}')
                continue
            for k in ('title_de', 'title_ru'):
                if k in e and e[k] != d.get(k):
                    add('E', 'index.json', f'№{d["number"]}', 'idx-title',
                        f'{k}: index={e[k]!r} != файл={d.get(k)!r}')
    except Exception as ex:
        add('W', 'index.json', '-', 'idx', f'не сверить: {ex}')

    findings.sort(key=lambda x: (x[0] != 'E', x[1], x[2]))
    ne = sum(1 for f_ in findings if f_[0] == 'E')
    nw = len(findings) - ne
    for sev, song, loc, code, msg in findings:
        print(f'{sev} [{song} {loc}] {code}: {msg}')
    print(f'\nИтого: {ne} ошибок, {nw} предупреждений; песен проверено: {len(data)}')
    return 1 if ne else 0


if __name__ == '__main__':
    sys.exit(main())
