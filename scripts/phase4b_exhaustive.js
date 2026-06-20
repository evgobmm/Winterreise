export const meta = {
  name: 'winterreise-exhaustive',
  description: 'Ф4b ИСЧЕРПЫВАЮЩИЙ: по каждой лемме — все вхождения + ПОЛНАЯ таблица всех словарей; сверка каждого рендера и их согласованности',
  phases: [{ title: 'Пословный ревью', detail: 'чанк лемм на агента, полные таблицы' }],
}

const FINDINGS_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['seg_id', 'lemma', 'song', 'current_ru', 'issue_type', 'severity',
                   'evidence_1820', 'context_note', 'proposal', 'alternatives', 'confidence'],
        properties: {
          seg_id: { type: 'integer' }, lemma: { type: 'string' }, song: { type: 'integer' },
          current_ru: { type: 'string' },
          issue_type: { type: 'string', enum: ['error', 'imprecise', 'lost_meaning', 'compound', 'register', 'inconsistent_render'] },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          evidence_1820: { type: 'string' }, context_note: { type: 'string' },
          proposal: { type: 'string' }, alternatives: { type: 'array', items: { type: 'string' } },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
      },
    },
  },
}

const CONV = `КОНВЕНЦИИ (соблюдать, НЕ считать ошибками):
- Значение берём по 1820-м (Adelung+Campe+Grimm — ПРИОРИТЕТ), не по совр. Adelung-градации значимы.
- РАЗНЫЕ рендеры одной леммы ЧАСТО ЗАКОННЫ: склонение (Herz→сердце/сердца/сердцу), время/вид глагола (gehen→идёт/шёл/идти), синтаксич. роль (so→так/столь/такой), контекст (Eis→лёд/льдом). Это НЕ ошибки. Флагируй рендер ТОЛЬКО если он неверен/неточен по значению 1820-х+контексту в СВОЁМ месте.
- Точность важнее привычности; НЕ добавлять отсутствующих оттенков (уменьшит., ложные архаизмы). Поэтично — только если DE поэтично в 1820-е.
- Компаунд через дефис (прав.45) — если нет однословного RU и важны НЕСКОЛЬКО со-активных смыслов.
- Многие выборы СОЗНАТЕЛЬНЫ (аннотации песни) — НЕ ошибки.`

phase('Пословный ревью')
const NCHUNKS = 89
const WAVE = 4
const all = []
for (let w = 0; w < NCHUNKS; w += WAVE) {
  const ids = []
  for (let k = w; k < Math.min(w + WAVE, NCHUNKS); k++) ids.push(k)
  const res = await parallel(ids.map((ci) => () => {
    const id = String(ci).padStart(3, '0')
    return agent(
`Ты — лексикограф (немецкий 1820-х, Мюллер/Шуберт) и переводчик на русский. Проверь подстрочник ИСЧЕРПЫВАЮЩЕ по чанку лемм.

Прочитай research/review_chunks/chunk_${id}.json — массив объектов {lemma, pos, n_occ, distinct_ru, multi_render, table_file, occurrences:[{song, seg_id, de, ru, line_de}]}.

Для КАЖДОЙ леммы чанка:
1. Прочитай ПОЛНУЮ словарную таблицу по пути table_file (research/tables/<...>.json) — поле sources: все словари (group A=Adelung/Campe/Grimm 1820-е ПРИОРИТЕТ; A'=DWDS/Pfeifer/Duden; B=нем-рус БНРС/PONS/Langenscheidt/Multitran; C=рус-нем; D=RU-толковые). Текст каждого — в s.text.
2. Рассмотри ВСЕ вхождения леммы ВМЕСТЕ (occurrences). Для КАЖДОГО вхождения сверь наш RU со значением 1820-х + контекстом строки (line_de) и цикла.
3. Если лемма multi_render (переведена по-разному) — оцени КАЖДЫЙ рендер: законен ли он (склонение/время/роль/контекст — ОК) или какой-то неточен/ошибочен/непоследователен.
4. Отметь потерю КОНТЕКСТНО-АКТИВНОГО значения (→ возможно компаунд, прав.45) и регистр 1820-х (Adelung gehoben/edel/im gemeinen Leben).

${CONV}

ЖЁСТКАЯ ДИСЦИПЛИНА: флагируй ТОЛЬКО реальную проблему (неверный/неточный смысл для 1820-х+контекста; потеря активного значения; нарушение регистра; НЕОБОСНОВАННЫЙ разнобой рендеров). Полисемия и законное склонение/время ≠ ошибка. Сомневаешься — НЕ флагируй. evidence_1820 ОБЯЗАН быть дословной цитатой из Adelung/Campe/Grimm таблицы. При необходимости сверься с src/data/songs/ (аннотации) и CLAUDE.md (конвенции).

Верни список находок (может быть пустым) по всем леммам чанка. seg_id и song — из occurrences.`,
      { label: `rev:c${id}`, phase: 'Пословный ревью', schema: FINDINGS_SCHEMA }
    )
  }))
  res.filter(Boolean).forEach((r) => { if (r.findings) all.push(...r.findings) })
  log(`Волна ${Math.floor(w / WAVE) + 1}/${Math.ceil(NCHUNKS / WAVE)} (чанки ${ids.join(',')}): всего находок накоплено ${all.length}`)
}
log(`ИСЧЕРПЫВАЮЩИЙ РЕВЬЮ ЗАВЕРШЁН: ${all.length} находок-кандидатов`)
return { count: all.length, findings: all }
