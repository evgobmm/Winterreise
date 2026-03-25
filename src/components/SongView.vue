<script setup>
import { ref, computed } from 'vue'
import InterlinearLine from './InterlinearLine.vue'
import AnnotationsPanel from './AnnotationsPanel.vue'

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

function collectAnnotations(type) {
  if (!song.value) return []
  const result = []
  let noteIndex = 1
  for (const stanza of song.value.stanzas) {
    for (let l = 0; l < stanza.lines_ru.length; l++) {
      const line = stanza.lines_ru[l]
      for (const ann of (line.annotations || [])) {
        if ((ann.type || 'meaning') === type) {
          const segments = line.segments.slice(ann.segment_range[0], ann.segment_range[1] + 1)
          if (ann.continuation_ranges) {
            for (let c = 0; c < ann.continuation_ranges.length; c++) {
              const nextLine = stanza.lines_ru[l + c + 1]
              if (nextLine) {
                const cr = ann.continuation_ranges[c]
                segments.push(...nextLine.segments.slice(cr[0], cr[1] + 1))
              }
            }
          }
          result.push({
            index: noteIndex++,
            text: ann.text,
            type: ann.type || 'meaning',
            target: ann.target || null,
            segments
          })
        }
      }
    }
  }
  return result
}

const langAnnotations = computed(() => collectAnnotations('lang'))
const meaningAnnotations = computed(() => collectAnnotations('meaning'))

const hoveredAnnKey = ref(null)

function getInheritedAnnotations(stanzaIndex, lineIndex) {
  if (!song.value) return []
  const stanza = song.value.stanzas[stanzaIndex]
  const result = []
  for (let l = 0; l < lineIndex; l++) {
    const lineAnns = stanza.lines_ru[l].annotations || []
    for (let a = 0; a < lineAnns.length; a++) {
      const ann = lineAnns[a]
      const span = ann.line_span || 1
      if (l + span > lineIndex) {
        const isLastSpannedLine = (l + span - 1 === lineIndex)
        const type = ann.type || 'meaning'
        let displayIndex = null
        if (isLastSpannedLine) {
          const offsets = getOffsets(stanzaIndex, l)
          let countBefore = 0
          for (let b = 0; b < a; b++) {
            if ((lineAnns[b].type || 'meaning') === type) countBefore++
          }
          displayIndex = (type === 'lang' ? offsets.lang : offsets.meaning) + countBefore + 1
        }
        const contIndex = lineIndex - l - 1
        const segmentRange = ann.continuation_ranges ? ann.continuation_ranges[contIndex] : null
        result.push({
          key: `${stanzaIndex}-${l}-${a}`,
          type,
          isLastSpannedLine,
          displayIndex,
          text: ann.text,
          segmentRange
        })
      }
    }
  }
  return result
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

function getOffsets(stanzaIndex, lineIndex) {
  if (!song.value) return { lang: 0, meaning: 0 }
  let lang = 0
  let meaning = 0
  for (let s = 0; s < song.value.stanzas.length; s++) {
    const stanza = song.value.stanzas[s]
    for (let l = 0; l < stanza.lines_ru.length; l++) {
      if (s === stanzaIndex && l === lineIndex) return { lang, meaning }
      for (const ann of (stanza.lines_ru[l].annotations || [])) {
        if ((ann.type || 'meaning') === 'lang') lang++
        else meaning++
      }
    }
  }
  return { lang, meaning }
}
</script>

<template>
  <article v-if="song" class="song-view">
    <header class="song-header">
      <div class="col-de">
        <h2>{{ song.title_de }}</h2>
      </div>
      <div class="col-ru">
        <h2 class="title-ru">{{ song.title_ru }}</h2>
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
              :lang-offset="getOffsets(si, li).lang"
              :meaning-offset="getOffsets(si, li).meaning"
              :inherited-annotations="getInheritedAnnotations(si, li)"
              :hovered-ann-key="hoveredAnnKey"
              :ann-key-prefix="`${si}-${li}`"
              @hover-ann="hoveredAnnKey = $event"
            />
          </div>
        </div>
      </div>
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
</style>
