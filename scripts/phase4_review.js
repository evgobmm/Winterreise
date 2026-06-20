export const meta = {
  name: 'winterreise-review',
  description: 'Ф4: ревью перевода 24 песен на словарной базе 1820-х → находки → состязательная верификация (волнами против rate-limit)',
  phases: [
    { title: 'Находки', detail: 'по песне: сверка RU vs словарь 1820-х' },
    { title: 'Верификация', detail: 'скептик опровергает каждую находку' },
  ],
}

const FINDINGS_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['seg_id', 'form', 'lemma', 'current_ru', 'issue_type', 'severity',
                   'evidence_1820', 'context_note', 'proposal', 'alternatives',
                   'deliberate_annotation', 'confidence'],
        properties: {
          seg_id: { type: 'integer' }, form: { type: 'string' }, lemma: { type: 'string' },
          current_ru: { type: 'string' },
          issue_type: { type: 'string', enum: ['error', 'imprecise', 'lost_meaning', 'compound', 'register', 'convention_conflict'] },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          evidence_1820: { type: 'string' }, context_note: { type: 'string' },
          proposal: { type: 'string' }, alternatives: { type: 'array', items: { type: 'string' } },
          deliberate_annotation: { type: 'boolean' },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['upheld', 'reason', 'refined_proposal'],
  properties: {
    upheld: { type: 'boolean' }, reason: { type: 'string' }, refined_proposal: { type: 'string' },
  },
}

const CONV = `КОНВЕНЦИИ ПРОЕКТА (соблюдать, НЕ считать ошибками):
- Точность важнее привычности/красоты; НЕ добавлять отсутствующих оттенков (уменьшит., ложные архаизмы, аспект). Поэтично — только если DE поэтично в 1820-е (Adelung gehoben/edel/dichterisch, Grimm poetisch).
- Значение берём по 1820-м (Adelung+Campe+Grimm — ПРИОРИТЕТ), не по современному. Adelung-градации значимы (erster Grad der Unlust, im gemeinen Leben, mit Widerwillen, edler).
- Одно DE через цикл — один RU (rauschen→шуметь, still→«тих-», starr→«застыв-», bald→скоро); близкие в одной песне — разные RU.
- Компаунд через дефис (прав.45) — когда нет однословного RU и важны НЕСКОЛЬКО со-активных смыслов (Traum→сон-мечта, elend→жалок-несчастен-обездолен).
- Многие выборы СОЗНАТЕЛЬНЫ и объяснены в аннотациях песни — НЕ ошибки.`

function stage1(song) {
  const id = String(song).padStart(2, '0')
  return agent(
`Ты — лексикограф и переводчик, эксперт по немецкому языку начала XIX века (Мюллер/Шуберт «Winterreise») и русскому. Найди в подстрочнике песни ${song} места, где наш русский перевод НЕ САМЫЙ ТОЧНЫЙ, ошибочен, ТЕРЯЕТ важное значение (возможно, не одно), или где лучше КОМПАУНД через дефис.

ИСТОЧНИКИ:
1. research/dossiers/song_${id}.json — ПЕРВИЧНЫЙ. Поле segments: наш RU ↔ DE по строкам + content_words (форма→лемма). Поле evidence: словарные цитаты по лемме (adelung_1820, campe_1820, grimm — ПРИОРИТЕТ значения 1820-х; bnrs_de_ru/langenscheidt/multitran_de_ru — RU-кандидаты).
2. research/tables/<лемма>.json — ПОЛНАЯ таблица (dwds, pfeifer-этимология, duden, ru-толковые и пр.) — читай по запросу для конкретного слова, если нужно глубже.
3. src/data/songs/${id}-*.json — аннотации (сознательные выборы; ставь deliberate_annotation=true).
4. CLAUDE.md — конвенции (прав. 28/45/29, частицы) — сверяйся по необходимости.

${CONV}

МЕТОД (для КАЖДОГО контентного DE-слова каждого сегмента): сопоставь наш RU со ЗНАЧЕНИЕМ 1820-х (adelung/campe/grimm) + контекст строки и цикла. Точен — пропусти. Неточен/теряет смысл — находка.

ЖЁСТКАЯ ДИСЦИПЛИНА (против ложных срабатываний):
- Флагируй ТОЛЬКО при реальной проблеме: (а) неверный смысл для 1820-х+контекста; (б) есть конкретно ТОЧНЕЕ; (в) теряется КОНТЕКСТНО-АКТИВНОЕ второе значение (→компаунд); (г) не передан регистр 1820-х; (д) нарушена сквозная конвенция.
- НЕ флагируй из-за того, что есть другие переводы или слово многозначно. Полисемия ≠ ошибка. Сомневаешься — НЕ флагируй.
- evidence_1820 ОБЯЗАН быть дословной цитатой из adelung_1820/campe_1820/grimm досье. Нет словарной опоры — нет находки.
- Уважай аннотированные выборы.

Верни список находок (может быть пустым). seg_id — из досье.`,
    { label: `find:П${id}`, phase: 'Находки', schema: FINDINGS_SCHEMA }
  )
}

function stage2(song, f) {
  const id = String(song).padStart(2, '0')
  return agent(
`Ты — придирчивый скептик-лексикограф (немецкий 1820-х + русский). Перед тобой ПРЕДПОЛАГАЕМАЯ находка о переводе песни ${song}. Твоя задача — ОПРОВЕРГНУТЬ её: показать, что текущий перевод защитим. Отклоняй (upheld=false), если есть хоть одно разумное обоснование текущего выбора.

Находка: слово ${f.form} (лемма ${f.lemma}), наш перевод «${f.current_ru}»; тип ${f.issue_type}; заявлено: ${f.context_note}; предложение «${f.proposal}» (альт.: ${(f.alternatives || []).join(', ')}); цитата-обоснование: ${f.evidence_1820}

Проверь по research/dossiers/song_${id}.json (evidence — словарные цитаты; segments — контекст), при нужде research/tables/${f.lemma}.json (полная таблица) и src/data/songs/${id}-*.json (аннотации), CLAUDE.md (конвенции):
1. Значение 1820-х (Adelung/Campe/Grimm) РАЗДЕЛЯЕТ заявленную проблему или ПОДДЕРЖИВАЕТ текущий RU?
2. Контекст: «потерянное» значение реально активно здесь или лишь теоретически?
3. Это сознательная конвенция/аннотация (тогда защитим)?
4. Предложение действительно ТОЧНЕЕ, или лишь иное?
${CONV}
По умолчанию upheld=false, если текущий перевод разумно защитим. upheld=true — ТОЛЬКО при явной, обоснованной цитатой проблеме. Если upheld — дай refined_proposal.`,
    { label: `verify:П${id}:${f.form}`, phase: 'Верификация', schema: VERDICT_SCHEMA }
  )
}

const SONGS = Array.from({ length: 24 }, (_, i) => i + 1)
const WAVE = 4
const all = []
for (let w = 0; w < SONGS.length; w += WAVE) {
  phase('Находки')
  const wave = SONGS.slice(w, w + WAVE)
  const s1 = await parallel(wave.map((song) => () => stage1(song)))
  const pairs = []
  s1.forEach((res, idx) => {
    const song = wave[idx]
    if (res && res.findings) res.findings.forEach((f) => pairs.push({ song, f }))
  })
  phase('Верификация')
  const verified = await parallel(pairs.map(({ song, f }) => () =>
    stage2(song, f).then((v) => ({ song, ...f, verdict: v }))
  ))
  all.push(...verified.filter(Boolean))
  log(`Волна ${Math.floor(w / WAVE) + 1}/${Math.ceil(SONGS.length / WAVE)} (песни ${wave.join(',')}): кандидатов ${pairs.length}, проверено ${verified.filter(Boolean).length}`)
}

const upheld = all.filter((f) => f.verdict && f.verdict.upheld)
log(`ИТОГО кандидатов: ${all.length}; подтверждено скептиком: ${upheld.length}`)
return { total_candidates: all.length, upheld_count: upheld.length, all }
