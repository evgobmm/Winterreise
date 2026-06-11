<script setup>
import { ref, computed, watch } from 'vue'
import SongList from './components/SongList.vue'
import SongView from './components/SongView.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import PerformancePlayer from './components/PerformancePlayer.vue'
import SnowToggle from './components/SnowToggle.vue'
import SnowOverlay from './components/SnowOverlay.vue'
import { winterEnabled } from './utils/snow.js'
import songsIndex from './data/index.json'

// Deep-link: ?song=N открывает песню N; при переключении URL обновляется
// (replaceState — без засорения истории), остальные параметры (?admin=...) сохраняются.
const songParam = Number(new URLSearchParams(window.location.search).get('song'))
const currentSongNumber = ref(
  songsIndex.some(s => s.number === songParam) ? songParam : 1
)

watch(currentSongNumber, (n) => {
  const url = new URL(window.location.href)
  url.searchParams.set('song', String(n))
  history.replaceState(null, '', url.pathname + url.search + url.hash)
})
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
      <div class="credit">
        Музыка Франца Шуберта<br>
        Поэзия Вильгельма Мюллера
      </div>
      <div class="settings-controls">
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
        <div class="theme-slot">
          <ThemeToggle />
          <SnowToggle />
        </div>
      </div>
      <PerformancePlayer :song-number="currentSongNumber" />
    </aside>
    <SnowOverlay v-if="winterEnabled" />
  </div>
</template>
