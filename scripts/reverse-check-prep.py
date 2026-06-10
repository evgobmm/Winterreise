#!/usr/bin/env python3
"""
Этап 0 полного RU→DE-прохода (обратная сверка, правило 21).

Запуск из корня репозитория:
    python3 scripts/reverse-check-prep.py            # все песни
    python3 scripts/reverse-check-prep.py 01 02 20   # только указанные

Что делает: построчно печатает DE-оригинал и наш RU (склейка сегментов),
помечая ⚑ строки повышенного риска — там, где обратный перевод чаще всего
вскрывает расхождения: модальные глаголы (+лицо), вопросы, частицы
(doch/denn/nun/wohl/ja/schon/gar/je), вопросительные wie/was.

ДАЛЬШЕ (в чате, НЕ автоматически):
  Этап 1 — триаж: каждую строку (сначала ⚑) RU → DeepL → DE′, сравнить с DE.
  Этап 2 — разбор КАЖДОГО расхождения: намеренная буквальность/конвенция
           (оставить) или реальная ошибка смысла/грамматики/падежа/фокуса
           (во флаг). Верификация: Adelung/Grimm/DWDS/Duden (для 1820-х —
           НЕ DeepL) + grep по циклу + scripts/word-check.py. Обратно-сверить
           предлагаемую правку.
  Этап 3 — таблица по расхождениям: DE | RU | DeepL | вердикт | предложение.
  Ничего не менять и не пушить без явного слова по каждому пункту (правило 7).
"""
import json
import glob
import os
import re
import sys

RISK = re.compile(
    r'\b(soll\w*|will|willst|wollt\w*|wollen|kann\w*|könnt\w*|muss\w*|mag|magst'
    r'|möcht\w*|darf|wird|werde|hätt\w*|wär\w*)\b'
    r'|\?'
    r'|\b(doch|denn|nun|wohl|ja|schon|mal|gar|je|wie|was)\b',
    re.I,
)

songs_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'songs')
files = sorted(glob.glob(os.path.join(songs_dir, '*.json')))

only = set(sys.argv[1:])  # напр. «01 20»; пусто — все
total_lines = total_flag = 0

for f in files:
    num = os.path.basename(f)[:2]
    if only and num not in only:
        continue
    d = json.load(open(f, encoding='utf-8'))
    print(f'\n###### П{num}: {d["title_de"]} — {d["title_ru"]} ######')
    song_flag = 0
    for si, st in enumerate(d['stanzas']):
        for li, de in enumerate(st['lines_de']):
            ru = ' '.join(s['ru'] for s in st['lines_ru'][li]['segments'])
            flagged = bool(RISK.search(de))
            total_lines += 1
            song_flag += flagged
            total_flag += flagged
            mark = ' ⚑' if flagged else ''
            print(f'{si + 1}.{li + 1}{mark}')
            print(f'  DE: {de}')
            print(f'  RU: {ru}')
    print(f'  — строк: {sum(len(st["lines_de"]) for st in d["stanzas"])}, из них ⚑: {song_flag}')

print(f'\n====== ИТОГО: строк {total_lines}, повышенного риска (⚑) {total_flag} ======')
