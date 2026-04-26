<script setup>
defineProps({
  annotations: Array,
  type: String,
  title: String
})

const superscripts = ['', '\u00B9', '\u00B2', '\u00B3', '\u2074', '\u2075', '\u2076', '\u2077', '\u2078', '\u2079']
const digitMap = ['\u2070', '\u00B9', '\u00B2', '\u00B3', '\u2074', '\u2075', '\u2076', '\u2077', '\u2078', '\u2079']

function toSuperscript(n) {
  if (n < 10) return superscripts[n]
  return String(n).split('').map(d => digitMap[parseInt(d)]).join('')
}
</script>

<template>
  <section class="annotations-panel">
    <h3 :class="'panel-title-' + type">{{ title }}</h3>
    <div
      v-for="ann in annotations"
      :key="ann.index"
      class="annotation-item"
    >
      <span class="annotation-index" :class="'index-' + type">{{ toSuperscript(ann.index) }}</span>
      <span class="annotation-ref">
        {{ ann.segments.map(s => ann.target === 'variant' ? (s.variant_ru || s.ru) : s.ru).join(' ') }}
      </span>
      <span class="annotation-dash"> — </span>
      <span class="annotation-text">{{ ann.text }}</span>
    </div>
  </section>
</template>

<style scoped>
.annotations-panel h3 {
  font-size: 1rem;
  margin-bottom: 16px;
  font-weight: normal;
}

.panel-title-lang {
  color: var(--color-lang);
}

.panel-title-meaning {
  color: var(--color-meaning);
}

.annotation-item {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 10px;
  font-size: 0.9rem;
  line-height: 1.5;
}

.index-lang {
  color: var(--color-lang);
  margin-right: 4px;
}

.index-meaning {
  color: var(--color-meaning);
  margin-right: 4px;
}

.annotation-ref {
  font-style: italic;
  color: var(--text);
}

.annotation-dash {
  color: var(--text-secondary);
}

.annotation-text {
  color: var(--text-secondary);
  white-space: pre-line;
  flex: 1;
  min-width: 0;
}
</style>
