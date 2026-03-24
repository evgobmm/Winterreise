<script setup>
import { computed } from 'vue'
import FootnoteMark from './FootnoteMark.vue'

const props = defineProps({
  line: Object,
  langOffset: Number,
  meaningOffset: Number,
  inheritedAnnotations: { type: Array, default: () => [] },
  hoveredAnnKey: { type: String, default: null },
  annKeyPrefix: String
})

const emit = defineEmits(['hoverAnn'])

const segmentInfo = computed(() => {
  return props.line.segments.map((seg, i) => {
    const annKeys = []
    let primaryKey = null
    let primaryType = null
    let primaryLocalIndex = null
    let footnote = null

    if (props.line.annotations) {
      for (let a = 0; a < props.line.annotations.length; a++) {
        const ann = props.line.annotations[a]
        if (i >= ann.segment_range[0] && i <= ann.segment_range[1]) {
          const key = `${props.annKeyPrefix}-${a}`
          const type = ann.type || 'meaning'
          annKeys.push({ key, type })

          if (primaryKey === null) {
            primaryKey = key
            primaryType = type
            primaryLocalIndex = a
          }

          const isLastOfThis = i === ann.segment_range[1] && !(ann.line_span && ann.line_span > 1)
          if (isLastOfThis) {
            let displayIndex
            if (type === 'lang') {
              displayIndex = props.langOffset + countBefore('lang', a) + 1
            } else {
              displayIndex = props.meaningOffset + countBefore('meaning', a) + 1
            }
            footnote = { key, type, displayIndex, text: ann.text }
          }
        }
      }
    }

    for (const inh of props.inheritedAnnotations) {
      const inRange = !inh.segmentRange || (i >= inh.segmentRange[0] && i <= inh.segmentRange[1])
      if (inRange) {
        annKeys.push({ key: inh.key, type: inh.type })
        if (primaryKey === null) {
          primaryKey = inh.key
          primaryType = inh.type
        }
        if (inh.isLastSpannedLine) {
          const lastSeg = inh.segmentRange ? inh.segmentRange[1] : props.line.segments.length - 1
          if (i === lastSeg) {
            footnote = { key: inh.key, type: inh.type, displayIndex: inh.displayIndex, text: inh.text }
          }
        }
      }
    }

    return { seg, annKeys, primaryKey, primaryType, footnote }
  })
})

function countBefore(type, localIndex) {
  let count = 0
  for (let a = 0; a < localIndex; a++) {
    if ((props.line.annotations[a].type || 'meaning') === type) count++
  }
  return count
}
</script>

<template>
  <div class="interlinear-line">
    <span
      v-for="(info, i) in segmentInfo"
      :key="i"
      class="segment"
      :class="{
        annotated: info.annKeys.length > 0,
        'highlighted-lang': info.annKeys.some(a => a.key === hoveredAnnKey && a.type === 'lang'),
        'highlighted-meaning': info.annKeys.some(a => a.key === hoveredAnnKey && a.type === 'meaning')
      }"
      @mouseenter="emit('hoverAnn', info.footnote ? info.footnote.key : info.primaryKey)"
      @mouseleave="emit('hoverAnn', null)"
    >
      <span class="ru-row">
        <span v-if="info.seg.variant_ru" class="variant-ru">{{ info.seg.variant_ru }}</span>
        <span class="ru-word">{{ info.seg.ru || '\u00A0' }}</span>
        <FootnoteMark
          v-if="info.footnote"
          :index="info.footnote.displayIndex"
          :type="info.footnote.type"
        />
      </span>
      <span class="de-row">
        <span v-if="info.seg.variant_de" class="variant-de">{{ info.seg.variant_de }}</span>
        <span class="de-gloss">{{ info.seg.de || '\u00A0' }}</span>
      </span>
      <span
        v-if="info.footnote && hoveredAnnKey === info.footnote.key"
        class="tooltip"
        :class="'tooltip-' + info.footnote.type"
      >
        {{ info.footnote.text }}
      </span>
    </span>
  </div>
</template>

<style scoped>
.interlinear-line {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 16px;
  margin-bottom: 8px;
  align-items: flex-start;
}

.segment {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
}

.ru-row {
  display: inline-flex;
  align-items: baseline;
  position: relative;
}

.de-row {
  position: relative;
}

.segment.annotated {
  border-radius: 2px;
  padding: 1px 3px;
  margin: -1px -3px;
  cursor: pointer;
  transition: background 0.15s;
}

.segment.highlighted-lang {
  background: var(--highlight-lang);
}

.segment.highlighted-meaning {
  background: var(--highlight-meaning);
}

.ru-word {
  font-size: 1rem;
  color: var(--text);
}

.variant-ru {
  position: absolute;
  bottom: 100%;
  left: 0;
  font-size: 1rem;
  color: var(--text);
  white-space: nowrap;
}

.variant-de {
  font-size: 0.75rem;
  color: var(--de-text);
  font-style: italic;
  white-space: nowrap;
}

.de-gloss {
  font-size: 0.75rem;
  color: var(--de-text);
  font-style: italic;
  white-space: nowrap;
}

.tooltip {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 6px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.85rem;
  line-height: 1.4;
  color: var(--text);
  width: 300px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  pointer-events: none;
}

.tooltip-lang {
  border-left: 3px solid var(--color-lang);
}

.tooltip-meaning {
  border-left: 3px solid var(--color-meaning);
}
</style>
