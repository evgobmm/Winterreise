<script setup>
import { ref, watch, computed } from 'vue'
import InterlinearLine from './InterlinearLine.vue'
import AnnotationsPanel from './AnnotationsPanel.vue'

const songModules = import.meta.glob('../data/songs/*.json', { eager: true })

const props = defineProps({
  songFile: String
})

const song = computed(() => {
  if (!props.songFile) return null
  const key = `../data/songs/${props.songFile}`
  const mod = songModules[key]
  return mod ? mod.default : null
})

const allAnnotations = computed(() => {
  if (!song.value) return []
  const result = []
  let noteIndex = 1
  for (const stanza of song.value.stanzas) {
    for (const line of stanza.lines_ru) {
      for (const ann of (line.annotations || [])) {
        result.push({
          index: noteIndex++,
          text: ann.text,
          segments: line.segments.slice(ann.segment_range[0], ann.segment_range[1] + 1)
        })
      }
    }
  }
  return result
})

function getNoteOffset(stanzaIndex, lineIndex) {
  if (!song.value) return 0
  let count = 0
  for (let s = 0; s < song.value.stanzas.length; s++) {
    const stanza = song.value.stanzas[s]
    for (let l = 0; l < stanza.lines_ru.length; l++) {
      if (s === stanzaIndex && l === lineIndex) return count
      count += (stanza.lines_ru[l].annotations || []).length
    }
  }
  return count
}
</script>

<template>
  <article v-if="song" class="song-view">
    <header class="song-header">
      <h2>{{ song.title_de }}</h2>
      <p class="song-title-ru">{{ song.title_ru }}</p>
    </header>

    <div class="song-body">
      <div
        v-for="(stanza, si) in song.stanzas"
        :key="si"
        class="stanza"
      >
        <div class="stanza-columns">
          <div class="col-de">
            <p v-for="(line, li) in stanza.lines_de" :key="li" class="line-de">
              {{ line }}
            </p>
          </div>
          <div class="col-ru">
            <InterlinearLine
              v-for="(line, li) in stanza.lines_ru"
              :key="li"
              :line="line"
              :note-offset="getNoteOffset(si, li)"
            />
          </div>
        </div>
      </div>
    </div>

    <AnnotationsPanel
      v-if="allAnnotations.length"
      :annotations="allAnnotations"
    />
  </article>
</template>

<style scoped>
.song-header {
  margin-bottom: 32px;
}

.song-header h2 {
  font-size: 1.5rem;
  font-style: italic;
}

.song-title-ru {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin-top: 4px;
}

.stanza {
  margin-bottom: 28px;
}

.stanza-columns {
  display: flex;
  gap: 40px;
}

.col-de {
  flex: 1;
  min-width: 0;
}

.col-ru {
  flex: 1;
  min-width: 0;
}

.line-de {
  font-style: italic;
  color: var(--text);
  margin-bottom: 4px;
  line-height: 1.5;
}
</style>
