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
    let annKey = null
    let annType = null
    let annDisplayIndex = null
    let annText = null
    let isLast = false
    let annLocalIndex = null

    if (props.line.annotations) {
      for (let a = 0; a < props.line.annotations.length; a++) {
        const ann = props.line.annotations[a]
        if (i >= ann.segment_range[0] && i <= ann.segment_range[1]) {
          annLocalIndex = a
          annKey = `${props.annKeyPrefix}-${a}`
          annType = ann.type || 'meaning'
          annText = ann.text
          isLast = i === ann.segment_range[1]
          break
        }
      }
    }

    if (annKey === null && props.inheritedAnnotations.length > 0) {
      const inh = props.inheritedAnnotations[0]
      annKey = inh.key
      annType = inh.type
    }

    if (isLast && annLocalIndex !== null) {
      if (annType === 'lang') {
        annDisplayIndex = props.langOffset + countBefore('lang', annLocalIndex) + 1
      } else if (annType === 'meaning') {
        annDisplayIndex = props.meaningOffset + countBefore('meaning', annLocalIndex) + 1
      }
    }

    return { seg, annKey, annType, annDisplayIndex, annText, isLast }
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
        annotated: info.annKey !== null,
        'highlighted-lang': hoveredAnnKey !== null && info.annKey === hoveredAnnKey && info.annType === 'lang',
        'highlighted-meaning': hoveredAnnKey !== null && info.annKey === hoveredAnnKey && info.annType === 'meaning'
      }"
      @mouseenter="info.annKey !== null && emit('hoverAnn', info.annKey)"
      @mouseleave="emit('hoverAnn', null)"
    >
      <span class="ru-row">
        <span class="ru-word">{{ info.seg.ru }}</span>
        <FootnoteMark
          v-if="info.isLast"
          :index="info.annDisplayIndex"
          :type="info.annType"
        />
      </span>
      <span class="de-gloss">{{ info.seg.de || '\u00A0' }}</span>
      <span
        v-if="info.isLast && hoveredAnnKey === info.annKey"
        class="tooltip"
        :class="'tooltip-' + info.annType"
      >
        {{ info.annText }}
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
