<script setup>
import { computed } from 'vue'
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
    for (const line of stanza.lines_ru) {
      for (const ann of (line.annotations || [])) {
        if ((ann.type || 'meaning') === type) {
          result.push({
            index: noteIndex++,
            text: ann.text,
            type: ann.type || 'meaning',
            segments: line.segments.slice(ann.segment_range[0], ann.segment_range[1] + 1)
          })
        }
      }
    }
  }
  return result
}

const langAnnotations = computed(() => collectAnnotations('lang'))
const meaningAnnotations = computed(() => collectAnnotations('meaning'))

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
              {{ stanza.lines_de[li] }}
            </p>
          </div>
          <div class="col-ru">
            <InterlinearLine
              :line="lineRu"
              :lang-offset="getOffsets(si, li).lang"
              :meaning-offset="getOffsets(si, li).meaning"
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
