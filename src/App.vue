<script setup>
import { ref, computed } from 'vue'
import SongList from './components/SongList.vue'
import SongView from './components/SongView.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import songsIndex from './data/index.json'

const currentSongNumber = ref(1)
const showAnnotations = ref(true)
const showLang = ref(true)
const showMeaning = ref(true)

const currentSongFile = computed(() => {
  const song = songsIndex.find(s => s.number === currentSongNumber.value)
  return song ? song.file : null
})
</script>

<template>
  <div class="app">
    <aside class="sidebar">
      <h1 class="app-title">Winterreise<br><small>Зимнее путешествие</small></h1>
      <SongList
        :songs="songsIndex"
        :current="currentSongNumber"
        @select="currentSongNumber = $event"
      />
    </aside>
    <main class="content">
      <SongView
        v-if="currentSongFile"
        :song-file="currentSongFile"
        :show-annotations="showAnnotations"
        :show-lang="showLang"
        :show-meaning="showMeaning"
      />
      <p v-else class="placeholder">Выберите песню из списка</p>
    </main>
    <aside class="settings">
      <div class="theme-wrap">
        <ThemeToggle />
      </div>
      <div class="annotations-controls">
        <label class="annotations-checkbox">
          <input type="checkbox" v-model="showAnnotations" />
          Пояснения
        </label>
        <label
          class="annotations-sub meaning-check"
          :class="{ disabled: !showAnnotations }"
        >
          <input type="checkbox" v-model="showMeaning" :disabled="!showAnnotations" />
          Смысл
        </label>
        <label
          class="annotations-sub lang-check"
          :class="{ disabled: !showAnnotations }"
        >
          <input type="checkbox" v-model="showLang" :disabled="!showAnnotations" />
          Язык
        </label>
      </div>
    </aside>
  </div>
</template>
