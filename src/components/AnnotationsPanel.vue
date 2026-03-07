<script setup>
defineProps({
  annotations: Array
})

const superscripts = ['', '\u00B9', '\u00B2', '\u00B3', '\u2074', '\u2075', '\u2076', '\u2077', '\u2078', '\u2079']

function toSuperscript(n) {
  if (n < 10) return superscripts[n]
  return String(n).split('').map(d => superscripts[parseInt(d)]).join('')
}
</script>

<template>
  <section class="annotations-panel">
    <h3>Пояснения</h3>
    <div
      v-for="ann in annotations"
      :key="ann.index"
      class="annotation-item"
    >
      <span class="annotation-index">{{ toSuperscript(ann.index) }}</span>
      <span class="annotation-ref">
        {{ ann.segments.map(s => s.ru).join(' ') }}
      </span>
      <span class="annotation-dash"> — </span>
      <span class="annotation-text">{{ ann.text }}</span>
    </div>
  </section>
</template>

<style scoped>
.annotations-panel {
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}

.annotations-panel h3 {
  font-size: 1rem;
  margin-bottom: 16px;
  color: var(--text-secondary);
  font-weight: normal;
}

.annotation-item {
  margin-bottom: 10px;
  font-size: 0.9rem;
  line-height: 1.5;
}

.annotation-index {
  color: var(--accent);
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
}
</style>
