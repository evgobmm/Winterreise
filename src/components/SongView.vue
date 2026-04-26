<script setup>
import { ref, computed, nextTick } from 'vue'
import InterlinearLine from './InterlinearLine.vue'
import AnnotationsPanel from './AnnotationsPanel.vue'
import FootnoteMark from './FootnoteMark.vue'

const songModules = import.meta.glob('../data/songs/*.json', { eager: true })

const props = defineProps({
  songFile: String,
  showAnnotations: Boolean,
  showLang: Boolean,
  showMeaning: Boolean
})

const song = computed(() => {
  if (!props.songFile) return null
  const key = `../data/songs/${props.songFile}`
  const mod = songModules[key]
  return mod ? mod.default : null
})

// Build a global map: "stanzaIdx-lineIdx-annIdx" -> display number, sorted by footnote position
const annNumberMap = computed(() => {
  if (!song.value) return new Map()
  const byType = { lang: [], meaning: [] }
  const titleAnns = song.value.title_annotations || []
  for (let a = 0; a < titleAnns.length; a++) {
    const type = titleAnns[a].type || 'meaning'
    byType[type].push({ key: `title-${a}`, footS: -1, footL: 0, footSeg: a })
  }
  const stanzas = song.value.stanzas
  for (let s = 0; s < stanzas.length; s++) {
    const stanza = stanzas[s]
    for (let l = 0; l < stanza.lines_ru.length; l++) {
      for (let a = 0; a < (stanza.lines_ru[l].annotations || []).length; a++) {
        const ann = stanza.lines_ru[l].annotations[a]
        const type = ann.type || 'meaning'
        const span = ann.line_span || 1
        let footS = s, footL = l + span - 1
        while (footS < stanzas.length && footL >= stanzas[footS].lines_ru.length) {
          footL -= stanzas[footS].lines_ru.length
          footS++
        }
        let footSeg = ann.segment_range[1]
        if (span > 1) {
          if (ann.continuation_ranges && ann.continuation_ranges.length > 0) {
            let lastRange = null
            for (let ci = ann.continuation_ranges.length - 1; ci >= 0; ci--) {
              if (ann.continuation_ranges[ci] !== null) { lastRange = ann.continuation_ranges[ci]; break }
            }
            footSeg = lastRange ? lastRange[1] : ann.segment_range[1]
          } else {
            const footStanza = stanzas[footS]
            if (footStanza && footStanza.lines_ru[footL]) {
              footSeg = footStanza.lines_ru[footL].segments.length - 1
            }
          }
        }
        byType[type].push({ key: `${s}-${l}-${a}`, footS, footL, footSeg })
      }
    }
  }
  const result = new Map()
  for (const type of ['lang', 'meaning']) {
    byType[type].sort((a, b) => a.footS !== b.footS ? a.footS - b.footS : a.footL !== b.footL ? a.footL - b.footL : a.footSeg - b.footSeg)
    byType[type].forEach((item, i) => { result.set(item.key, i + 1) })
  }
  return result
})

function collectAnnotations(type) {
  if (!song.value) return []
  const items = []
  const titleAnns = song.value.title_annotations || []
  for (let a = 0; a < titleAnns.length; a++) {
    const ann = titleAnns[a]
    if ((ann.type || 'meaning') === type) {
      const displayNum = annNumberMap.value.get(`title-${a}`) || 0
      items.push({
        text: ann.text,
        type: ann.type || 'meaning',
        target: null,
        segments: [{ ru: song.value.title_ru, de: song.value.title_de }],
        displayNum
      })
    }
  }
  const stanzas = song.value.stanzas
  for (let s = 0; s < stanzas.length; s++) {
    const stanza = stanzas[s]
    for (let l = 0; l < stanza.lines_ru.length; l++) {
      const line = stanza.lines_ru[l]
      for (let a = 0; a < (line.annotations || []).length; a++) {
        const ann = line.annotations[a]
        if ((ann.type || 'meaning') === type) {
          const segments = line.segments.slice(ann.segment_range[0], ann.segment_range[1] + 1)
          if (ann.continuation_ranges) {
            for (let c = 0; c < ann.continuation_ranges.length; c++) {
              const cr = ann.continuation_ranges[c]
              if (cr === null) continue
              let tS = s, tL = l + c + 1
              while (tS < stanzas.length && tL >= stanzas[tS].lines_ru.length) {
                tL -= stanzas[tS].lines_ru.length
                tS++
              }
              const nextLine = tS < stanzas.length ? stanzas[tS].lines_ru[tL] : null
              if (nextLine) {
                segments.push(...nextLine.segments.slice(cr[0], cr[1] + 1))
              }
            }
          }
          const displayNum = annNumberMap.value.get(`${s}-${l}-${a}`) || 0
          items.push({
            text: ann.text,
            type: ann.type || 'meaning',
            target: ann.target || null,
            segments,
            displayNum
          })
        }
      }
    }
  }
  items.sort((a, b) => a.displayNum - b.displayNum)
  return items.map(item => ({ ...item, index: item.displayNum }))
}

const langAnnotations = computed(() => collectAnnotations('lang'))
const meaningAnnotations = computed(() => collectAnnotations('meaning'))

const hoveredAnnKey = ref(null)
const hoveredY = ref(16)
const tooltipRef = ref(null)
const tooltipReady = ref(false)
let lastKey = null

const annDataByKey = computed(() => {
  const map = new Map()
  if (!song.value) return map
  const titleAnns = song.value.title_annotations || []
  for (let a = 0; a < titleAnns.length; a++) {
    const ann = titleAnns[a]
    map.set(`title-${a}`, { text: ann.text, type: ann.type || 'meaning' })
  }
  const stanzas = song.value.stanzas
  for (let s = 0; s < stanzas.length; s++) {
    const stanza = stanzas[s]
    for (let l = 0; l < stanza.lines_ru.length; l++) {
      const anns = stanza.lines_ru[l].annotations || []
      for (let a = 0; a < anns.length; a++) {
        const ann = anns[a]
        map.set(`${s}-${l}-${a}`, { text: ann.text, type: ann.type || 'meaning' })
      }
    }
  }
  return map
})

const TOOLTIP_MARGIN = 16

function handleHover(payload) {
  if (!payload) {
    hoveredAnnKey.value = null
    tooltipReady.value = false
    lastKey = null
    return
  }
  hoveredAnnKey.value = payload.key
  if (payload.key === lastKey) return
  lastKey = payload.key
  hoveredY.value = Math.max(TOOLTIP_MARGIN, payload.y)
  tooltipReady.value = false
  nextTick(() => {
    if (!tooltipRef.value) return
    const h = tooltipRef.value.offsetHeight
    const vh = window.innerHeight
    if (h > vh - TOOLTIP_MARGIN * 2) {
      hoveredY.value = TOOLTIP_MARGIN
    } else {
      const maxTop = vh - h - TOOLTIP_MARGIN
      hoveredY.value = Math.max(TOOLTIP_MARGIN, Math.min(payload.y, maxTop))
    }
    tooltipReady.value = true
  })
}

const hoveredTooltip = computed(() => {
  if (!hoveredAnnKey.value) return null
  const data = annDataByKey.value.get(hoveredAnnKey.value)
  if (!data) return null
  if (!props.showAnnotations) return null
  if (data.type === 'lang' && !props.showLang) return null
  if (data.type === 'meaning' && !props.showMeaning) return null
  return data
})

function getInheritedAnnotations(stanzaIndex, lineIndex) {
  if (!song.value) return []
  const result = []

  const stanzas = song.value.stanzas

  // Check all stanzas at or before current; for each anchor, compute distance to current line.
  for (let prevS = 0; prevS <= stanzaIndex; prevS++) {
    const prevStanza = stanzas[prevS]
    const prevLineCount = prevStanza.lines_ru.length
    const lineLimit = (prevS === stanzaIndex) ? lineIndex : prevLineCount
    for (let l = 0; l < lineLimit; l++) {
      const lineAnns = prevStanza.lines_ru[l].annotations || []
      for (let a = 0; a < lineAnns.length; a++) {
        const ann = lineAnns[a]
        const span = ann.line_span || 1

        // Distance from anchor (prevS, l) to current line (stanzaIndex, lineIndex), 0-indexed.
        let distance
        if (prevS === stanzaIndex) {
          distance = lineIndex - l
        } else {
          distance = prevLineCount - l
          for (let ts = prevS + 1; ts < stanzaIndex; ts++) {
            distance += stanzas[ts].lines_ru.length
          }
          distance += lineIndex
        }

        if (distance >= 1 && distance < span) {
          const isLastSpannedLine = (distance === span - 1)
          const type = ann.type || 'meaning'
          let displayIndex = null
          if (isLastSpannedLine) {
            displayIndex = annNumberMap.value.get(`${prevS}-${l}-${a}`) || 0
          }
          const contIndex = distance - 1
          const segmentRange = ann.continuation_ranges ? ann.continuation_ranges[contIndex] : null
          if (ann.continuation_ranges && segmentRange === null) continue
          result.push({
            key: `${prevS}-${l}-${a}`,
            type,
            isLastSpannedLine,
            displayIndex,
            text: ann.text,
            segmentRange
          })
        }
      }
    }
  }

  return result
}

const titleFootnotes = computed(() => {
  if (!song.value) return []
  const titleAnns = song.value.title_annotations || []
  return titleAnns.map((ann, a) => {
    const type = ann.type || 'meaning'
    return {
      key: `title-${a}`,
      type,
      displayIndex: annNumberMap.value.get(`title-${a}`) || 0,
      visible: props.showAnnotations && (type === 'lang' ? props.showLang : props.showMeaning)
    }
  })
})

function onTitleHover(key, event) {
  handleHover({ key, y: event.currentTarget.getBoundingClientRect().top })
}

function getLineDeParts(stanza, lineIndex) {
  const line = stanza.lines_ru[lineIndex]
  const lineDe = stanza.lines_de[lineIndex]
  if (!line || !lineDe) return null
  const variantSeg = line.segments.find(s => s.variant_de)
  if (!variantSeg) return null
  const mainWord = variantSeg.de
  const idx = lineDe.indexOf(mainWord)
  if (idx === -1) return null
  return {
    before: lineDe.substring(0, idx),
    main: mainWord,
    variant: variantSeg.variant_de,
    after: lineDe.substring(idx + mainWord.length)
  }
}
</script>

<template>
  <article v-if="song" class="song-view">
    <header class="song-header">
      <div class="col-de">
        <h2
          :class="{
            'title-highlighted-lang': titleFootnotes.some(fn => fn.visible && fn.key === hoveredAnnKey && fn.type === 'lang'),
            'title-highlighted-meaning': titleFootnotes.some(fn => fn.visible && fn.key === hoveredAnnKey && fn.type === 'meaning')
          }"
        >{{ song.title_de }}</h2>
      </div>
      <div class="col-ru">
        <h2
          class="title-ru"
          :class="{
            'title-highlighted-lang': titleFootnotes.some(fn => fn.visible && fn.key === hoveredAnnKey && fn.type === 'lang'),
            'title-highlighted-meaning': titleFootnotes.some(fn => fn.visible && fn.key === hoveredAnnKey && fn.type === 'meaning')
          }"
          @mouseenter="titleFootnotes.find(fn => fn.visible) ? onTitleHover(titleFootnotes.find(fn => fn.visible).key, $event) : null"
          @mouseleave="handleHover(null)"
        >{{ song.title_ru }}<FootnoteMark
          v-for="fn in titleFootnotes.filter(f => f.visible)"
          :key="fn.key"
          :index="fn.displayIndex"
          :type="fn.type"
        /></h2>
      </div>
    </header>

    <div class="song-body">
      <div
        v-for="(stanza, si) in song.stanzas"
        :key="si"
        class="stanza"
      >
        <div
          v-for="(lineRu, li) in stanza.lines_ru"
          :key="li"
          class="line-pair"
        >
          <div class="col-de">
            <p v-if="stanza.lines_de[li]" class="line-de">
              <template v-if="getLineDeParts(stanza, li)">
                {{ getLineDeParts(stanza, li).before }}<span class="de-variant-stack"><span class="de-variant-word">{{ getLineDeParts(stanza, li).variant }}</span><span>{{ getLineDeParts(stanza, li).main }}</span></span>{{ getLineDeParts(stanza, li).after }}
              </template>
              <template v-else>
                {{ stanza.lines_de[li] }}
              </template>
            </p>
          </div>
          <div class="col-ru">
            <InterlinearLine
              :line="lineRu"
              :ann-number-map="annNumberMap"
              :ann-key-prefix="`${si}-${li}`"
              :inherited-annotations="getInheritedAnnotations(si, li)"
              :hovered-ann-key="hoveredAnnKey"
              :show-annotations="showAnnotations"
              :show-lang="showLang"
              :show-meaning="showMeaning"
              @hover-ann="handleHover"
            />
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="hoveredTooltip"
      :key="hoveredAnnKey"
      ref="tooltipRef"
      class="hover-tooltip"
      :class="[
        'hover-tooltip-' + hoveredTooltip.type,
        { 'is-ready': tooltipReady }
      ]"
      :style="{ top: hoveredY + 'px' }"
    >
      {{ hoveredTooltip.text }}
    </div>

    <div
      v-if="showAnnotations && (langAnnotations.length || meaningAnnotations.length)"
      class="annotations-columns"
    >
      <AnnotationsPanel
        v-if="showMeaning && meaningAnnotations.length"
        :annotations="meaningAnnotations"
        type="meaning"
        title="Смысл"
      />
      <AnnotationsPanel
        v-if="showLang && langAnnotations.length"
        :annotations="langAnnotations"
        type="lang"
        title="Язык"
      />
    </div>
  </article>
</template>

<style scoped>
.song-header {
  display: flex;
  gap: 40px;
  margin-bottom: 32px;
}

.song-header h2 {
  font-size: 1.5rem;
  font-style: italic;
}

.title-ru {
  font-weight: normal;
  color: var(--text-secondary);
}

.title-highlighted-lang {
  background: var(--highlight-lang);
  border-radius: 2px;
  padding: 0 4px;
  margin: 0 -4px;
}

.title-highlighted-meaning {
  background: var(--highlight-meaning);
  border-radius: 2px;
  padding: 0 4px;
  margin: 0 -4px;
}

.stanza {
  margin-bottom: 28px;
}

.line-pair {
  display: flex;
  gap: 40px;
  align-items: flex-start;
  margin-bottom: 8px;
}

.col-de {
  flex: 0 0 340px;
  display: flex;
  align-items: flex-start;
}

.col-ru {
  flex: 1;
  min-width: 0;
}

.line-de {
  font-style: italic;
  color: var(--text);
  line-height: 1.5;
}

.de-variant-stack {
  position: relative;
  display: inline;
}

.de-variant-word {
  position: absolute;
  bottom: 100%;
  left: 0;
  white-space: nowrap;
}

.annotations-columns {
  display: flex;
  gap: 40px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}

.annotations-columns > * {
  flex: 1;
  min-width: 0;
}

.hover-tooltip {
  position: fixed;
  left: calc(260px + 900px + 16px);
  width: 300px;
  max-width: calc(100vw - 260px - 900px - 32px);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.85rem;
  line-height: 1.4;
  color: var(--text);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  pointer-events: none;
  white-space: pre-wrap;
  opacity: 0;
  transition: opacity 0.08s;
}

.hover-tooltip.is-ready {
  opacity: 1;
}

.hover-tooltip-lang {
  border-left: 3px solid var(--color-lang);
}

.hover-tooltip-meaning {
  border-left: 3px solid var(--color-meaning);
}

@media print {
  .hover-tooltip {
    display: none;
  }
}
</style>
