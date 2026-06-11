<script setup>
defineProps({
  index: Number,
  type: String
})

</script>

<template>
  <sup class="footnote-mark" :class="'mark-' + type" :title="'Сноска ' + index">{{ index }}</sup>
</template>

<style scoped>
.footnote-mark {
  cursor: pointer;
  /* Обычные цифры в sup вместо юникод-суперскриптов (⁰⁴⁵… нет во многих
     шрифтах — браузер брал их из запасного, и «10» прыгало по вертикали) */
  font-size: 0.68em;
  line-height: 0;
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
