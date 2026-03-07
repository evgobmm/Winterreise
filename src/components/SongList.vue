<script setup>
defineProps({
  songs: Array,
  current: Number
})

defineEmits(['select'])
</script>

<template>
  <nav class="song-list">
    <ul>
      <li
        v-for="song in songs"
        :key="song.number"
        :class="{ active: song.number === current, disabled: !song.ready }"
        @click="song.ready && $emit('select', song.number)"
      >
        <span class="song-number">{{ song.number }}.</span>
        <span class="song-title">{{ song.title_de }}</span>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.song-list ul {
  list-style: none;
}

.song-list li {
  padding: 6px 10px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.9rem;
  display: flex;
  gap: 6px;
}

.song-list li:hover:not(.disabled) {
  background: var(--highlight);
}

.song-list li.active {
  background: var(--accent);
  color: #fff;
}

.song-list li.disabled {
  opacity: 0.4;
  cursor: default;
}

.song-number {
  min-width: 22px;
  text-align: right;
  color: var(--text-secondary);
}

.song-list li.active .song-number {
  color: rgba(255, 255, 255, 0.7);
}
</style>
