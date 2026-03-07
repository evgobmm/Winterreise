<script setup>
import FootnoteMark from './FootnoteMark.vue'

const props = defineProps({
  line: Object,
  noteOffset: Number
})

function getAnnotationIndex(segIndex) {
  if (!props.line.annotations) return null
  for (let i = 0; i < props.line.annotations.length; i++) {
    const ann = props.line.annotations[i]
    if (segIndex >= ann.segment_range[0] && segIndex <= ann.segment_range[1]) {
      return props.noteOffset + i + 1
    }
  }
  return null
}

function isLastInAnnotation(segIndex) {
  if (!props.line.annotations) return false
  return props.line.annotations.some(ann => segIndex === ann.segment_range[1])
}
</script>

<template>
  <div class="interlinear-line">
    <span
      v-for="(seg, i) in line.segments"
      :key="i"
      class="segment"
      :class="{ annotated: getAnnotationIndex(i) !== null }"
    >
      <span class="ru-word">{{ seg.ru }}</span>
      <FootnoteMark
        v-if="isLastInAnnotation(i)"
        :index="getAnnotationIndex(i)"
      />
      <span v-if="seg.de" class="de-gloss">{{ seg.de }}</span>
    </span>
  </div>
</template>

<style scoped>
.interlinear-line {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  margin-bottom: 12px;
  align-items: flex-start;
}

.segment {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
}

.segment.annotated {
  background: var(--highlight);
  border-radius: 2px;
  padding: 1px 3px;
  margin: -1px -3px;
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
</style>
