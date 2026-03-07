<script setup>
import { ref, computed } from 'vue'
import SongList from './components/SongList.vue'
import SongView from './components/SongView.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import songsIndex from './data/index.json'

const currentSongNumber = ref(2)
const showAnnotations = ref(true)

const currentSongFile = computed(() => {
  const song = songsIndex.find(s => s.number === currentSongNumber.value)
  return song ? song.file : null
})
</script>

<template>
  <div class="app">
    <aside class="sidebar">
      <h1 class="app-title">Winterreise<br><small>Зимний путь</small></h1>
      <SongList
        :songs="songsIndex"
        :current="currentSongNumber"
        @select="currentSongNumber = $event"
      />
    </aside>
    <main class="content">
      <div class="toolbar">
        <label class="annotations-checkbox">
          <input type="checkbox" v-model="showAnnotations" />
          Пояснения
        </label>
        <ThemeToggle />
      </div>
      <SongView
        v-if="currentSongFile"
        :song-file="currentSongFile"
        :show-annotations="showAnnotations"
      />
      <p v-else class="placeholder">Выберите песню из списка</p>
    </main>
  </div>
</template>
