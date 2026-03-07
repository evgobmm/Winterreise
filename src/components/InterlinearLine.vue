<script setup>
import { ref, computed } from 'vue'
import FootnoteMark from './FootnoteMark.vue'

const props = defineProps({
  line: Object,
  noteOffset: Number
})

const hoveredAnn = ref(null)

const segmentInfo = computed(() => {
  return props.line.segments.map((seg, i) => {
    let annLocalIndex = null
    let annGlobalIndex = null
    let annText = null
    let isLast = false
    if (props.line.annotations) {
      for (let a = 0; a < props.line.annotations.length; a++) {
        const ann = props.line.annotations[a]
        if (i >= ann.segment_range[0] && i <= ann.segment_range[1]) {
          annLocalIndex = a
          annGlobalIndex = props.noteOffset + a + 1
          annText = ann.text
          isLast = i === ann.segment_range[1]
          break
        }
      }
    }
    return { seg, annLocalIndex, annGlobalIndex, annText, isLast }
  })
})
</script>

<template>
  <div class="interlinear-line">
    <span
      v-for="(info, i) in segmentInfo"
      :key="i"
      class="segment"
      :class="{
        annotated: info.annLocalIndex !== null,
        highlighted: hoveredAnn !== null && info.annLocalIndex === hoveredAnn
      }"
      @mouseenter="info.annLocalIndex !== null && (hoveredAnn = info.annLocalIndex)"
      @mouseleave="hoveredAnn = null"
    >
      <span class="ru-row">
        <span class="ru-word">{{ info.seg.ru }}</span>
        <FootnoteMark
          v-if="info.isLast"
          :index="info.annGlobalIndex"
        />
      </span>
      <span class="de-gloss">{{ info.seg.de || '\u00A0' }}</span>
      <span
        v-if="info.isLast && hoveredAnn === info.annLocalIndex"
        class="tooltip"
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

.segment.highlighted {
  background: var(--highlight);
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
</style>
