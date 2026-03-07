<script setup>
defineProps({
  index: Number,
  type: String
})

const superscripts = ['', '\u00B9', '\u00B2', '\u00B3', '\u2074', '\u2075', '\u2076', '\u2077', '\u2078', '\u2079']

function toSuperscript(n) {
  if (n < 10) return superscripts[n]
  return String(n).split('').map(d => superscripts[parseInt(d)]).join('')
}
</script>

<template>
  <sup class="footnote-mark" :class="'mark-' + type" :title="'Сноска ' + index">{{ toSuperscript(index) }}</sup>
</template>

<style scoped>
.footnote-mark {
  cursor: pointer;
  font-size: 0.8rem;
  margin-left: 2px;
  font-style: normal;
}

.mark-lang {
  color: var(--color-lang);
}

.mark-meaning {
  color: var(--color-meaning);
}

.footnote-mark:hover {
  text-decoration: underline;
}
</style>
