#!/usr/bin/env node
/**
 * Генерация статических HTML-страниц песен + sitemap.xml (после vite build).
 *
 * Зачем: сайт — SPA, краулеры получают пустой <div id="app">. Эти страницы —
 * полный подстрочник + комментарии как обычный HTML, индексируемый Google и
 * Яндексом без исполнения JS (рендеринг JS у Яндекса — бета, не гарантирован).
 *
 * Выход: dist/songs/<slug>/index.html (24 шт.) и dist/sitemap.xml.
 * Источник данных: src/data/index.json + src/data/songs/*.json (только чтение).
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const dist = join(root, 'dist')
const SITE = 'https://evgobmm.github.io/Winterreise/'

if (!existsSync(dist)) {
  console.error('dist/ не найден — сначала vite build')
  process.exit(1)
}

const index = JSON.parse(readFileSync(join(root, 'src/data/index.json'), 'utf8'))

// Экранирование + *курсив* → <em> (та же логика, что src/utils/renderText.js) + \n → <br>
const esc = (s) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const rich = (s) => esc(s).replace(/\*([^*]+)\*/g, '<em>$1</em>').replace(/\n/g, '<br>')

const ruLine = (line) => line.segments.map((s) => s.ru).join(' ').replace(/\s+/g, ' ').trim()

const annLabel = (line, range) =>
  line.segments
    .slice(range[0], range[1] + 1)
    .map((s) => s.ru)
    .join(' ')
    .replace(/\s+/g, ' ')
    .replace(/[.,;:!?]+$/, '')
    .trim()

const TYPE_NAME = { lang: 'о языке', meaning: 'о смысле' }

const CSS = `
  body{font-family:Georgia,'Times New Roman',serif;background:#faf8f5;color:#2c2c2c;line-height:1.6;max-width:680px;margin:0 auto;padding:24px 16px 48px}
  a{color:#5a3a1a}
  header a{text-decoration:none;font-size:.95rem;color:#6b6b6b}
  h1{font-size:1.5rem;margin:18px 0 4px}
  .open-app{margin:4px 0 26px}
  .open-app a{color:#8b4513}
  .stanza{margin:0 0 24px}
  .line{margin:0 0 10px}
  .de{font-style:italic}
  .ru{display:block}
  section.notes,section.about{margin-top:30px;border-top:1px solid #d4d0c8;padding-top:16px}
  h2{font-size:1.1rem;margin:0 0 8px}
  dt{font-weight:bold;margin-top:14px}
  dd{margin:2px 0 0}
  .ann-type{font-size:.8rem;color:#6b6b6b;text-transform:lowercase;letter-spacing:.03em}
  nav.songs{display:flex;justify-content:space-between;gap:12px;margin-top:34px;font-size:.95rem}
  footer{margin-top:36px;font-size:.85rem;color:#6b6b6b;border-top:1px solid #d4d0c8;padding-top:12px}
`

function songHtml(meta, song, prev, next) {
  const n = meta.number
  const slug = meta.file.replace(/\.json$/, '')
  const url = `${SITE}songs/${slug}/`
  const title = `${n}. ${meta.title_de} — ${meta.title_ru} | Winterreise: подстрочный перевод`
  const desc = `«${meta.title_de}» («${meta.title_ru}») — песня ${n} из 24 цикла Шуберта «Зимний путь» (Winterreise): немецкий текст с пословным русским переводом и комментариями к языку и смыслу.`

  const about = (song.title_annotations || [])
    .map((a) => `<p>${rich(a.text)}</p>`)
    .join('\n')

  const stanzas = song.stanzas
    .map((st) => {
      const lines = st.lines_de
        .map((de, i) => {
          const ru = st.lines_ru[i] ? ruLine(st.lines_ru[i]) : ''
          return `<p class="line"><span class="de" lang="de">${esc(de)}</span><span class="ru">${esc(ru)}</span></p>`
        })
        .join('\n')
      return `<div class="stanza">\n${lines}\n</div>`
    })
    .join('\n')

  const notes = []
  for (const st of song.stanzas) {
    for (const line of st.lines_ru) {
      for (const a of line.annotations || []) {
        const label = a.segment_range ? annLabel(line, a.segment_range) : ''
        notes.push(
          `<dt>${esc(label)} <span class="ann-type">(${TYPE_NAME[a.type] || a.type})</span></dt>\n<dd>${rich(a.text)}</dd>`
        )
      }
    }
  }

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CreativeWork',
    name: `«${meta.title_de}» — «${meta.title_ru}»: подстрочный перевод`,
    url,
    inLanguage: ['de', 'ru'],
    isPartOf: { '@type': 'WebSite', name: 'Winterreise — Зимний путь: подстрочный перевод', url: SITE },
    about: {
      '@type': 'MusicComposition',
      name: `${meta.title_de} (Winterreise, D 911, № ${n})`,
      composer: { '@type': 'Person', name: 'Franz Schubert' },
      lyricist: { '@type': 'Person', name: 'Wilhelm Müller' },
    },
    author: { '@type': 'Person', name: 'Евгений Обухов' },
    license: 'https://creativecommons.org/publicdomain/zero/1.0/',
  }

  return `<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<link rel="canonical" href="${url}">
<meta property="og:type" content="article">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${url}">
<meta property="og:locale" content="ru_RU">
<link rel="icon" type="image/svg+xml" href="/Winterreise/favicon.svg">
<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>
<style>${CSS}</style>
</head>
<body>
<header><a href="../../">Winterreise — Зимний путь · подстрочный перевод цикла Шуберта</a></header>
<main>
<h1>${n}. ${esc(meta.title_de)} — ${esc(meta.title_ru)}</h1>
<p class="open-app"><a href="../../?song=${n}">Открыть в интерактивной версии →</a></p>
${about ? `<section class="about">\n<h2>О песне</h2>\n${about}\n</section>` : ''}
${stanzas}
${notes.length ? `<section class="notes">\n<h2>Комментарии</h2>\n<dl>\n${notes.join('\n')}\n</dl>\n</section>` : ''}
<nav class="songs">
<span>${prev ? `<a href="../${prev.file.replace(/\.json$/, '')}/">← ${prev.number}. ${esc(prev.title_de)}</a>` : ''}</span>
<span>${next ? `<a href="../${next.file.replace(/\.json$/, '')}/">${next.number}. ${esc(next.title_de)} →</a>` : ''}</span>
</nav>
</main>
<footer>Подстрочный перевод и комментарии — Евгений Обухов · CC0 (общественное достояние) · <a href="https://github.com/evgobmm/Winterreise">данные и исходники</a></footer>
</body>
</html>
`
}

const urls = [SITE]
for (let i = 0; i < index.length; i++) {
  const meta = index[i]
  const song = JSON.parse(readFileSync(join(root, 'src/data/songs', meta.file), 'utf8'))
  const slug = meta.file.replace(/\.json$/, '')
  const dir = join(dist, 'songs', slug)
  mkdirSync(dir, { recursive: true })
  writeFileSync(join(dir, 'index.html'), songHtml(meta, song, index[i - 1], index[i + 1]))
  urls.push(`${SITE}songs/${slug}/`)
}

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map((u) => `  <url><loc>${u}</loc></url>`).join('\n')}
</urlset>
`
writeFileSync(join(dist, 'sitemap.xml'), sitemap)

console.log(`Сгенерировано: ${index.length} страниц песен + sitemap.xml (${urls.length} URL)`)
