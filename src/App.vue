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

// Выключатель собственных заходов: один раз открыть ?stats=off — этот браузер
// перестаёт учитываться в GoatCounter (штатный флажок skipgc); обратно — ?stats=on.
const statsParam = new URLSearchParams(window.location.search).get('stats')
if (statsParam === 'off') {
  localStorage.setItem('skipgc', 't')
  alert('Ваши заходы из этого браузера исключены из статистики.')
} else if (statsParam === 'on') {
  localStorage.removeItem('skipgc')
  alert('Заходы из этого браузера снова учитываются в статистике.')
}

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
  updateSeoTags(n)
  // GoatCounter считает только загрузку страницы; переключение песни без
  // перезагрузки отправляем как «виртуальный просмотр» — видна статистика по песням
  if (window.goatcounter && window.goatcounter.count && localStorage.getItem('skipgc') !== 't') {
    window.goatcounter.count({
      path: location.pathname + location.search,
      title: document.title
    })
  }
})

// Canonical и description зависят от выбранной песни. Статический canonical
// склеил бы все ?song=N в одну страницу — обновляем из приложения (поисковик
// читает значения после рендера; пользователю не видно). ?song=1 ≡ корню.
function updateSeoTags(n) {
  const base = window.location.origin + window.location.pathname
  const canonical = document.querySelector('link[rel="canonical"]')
  if (canonical) canonical.href = n === 1 ? base : `${base}?song=${n}`
  const desc = document.querySelector('meta[name="description"]')
  const song = songsIndex.find(s => s.number === n)
  // Чистый корень (без ?song) — «обложка» с общим титулом; явно выбранная
  // песня (?song=N, включая N=1) — титул песни, единообразно для всех 24.
  const hasSongParam = new URLSearchParams(window.location.search).has('song')
  if (song && (n !== 1 || hasSongParam)) {
    document.title = `${n}. ${song.title_de} — ${song.title_ru} | Winterreise — Зимний путь`
    if (desc) desc.content = `«${song.title_de}» («${song.title_ru}») — песня ${n} из 24 цикла Шуберта «Зимний путь» (Winterreise): немецкий текст, пословный русский перевод, комментарии к языку и смыслу.`
  } else {
    document.title = 'Winterreise — Зимний путь'
    if (desc) desc.content = 'Все 24 песни цикла Франца Шуберта «Зимний путь» (Winterreise) на стихи Вильгельма Мюллера: немецкий текст, пословный русский перевод, комментарии к языку и смыслу.'
  }
}
updateSeoTags(currentSongNumber.value)
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
    <!-- Мобильная шапка: на десктопе display:none, на раскладку шире 900px не влияет -->
    <header class="mobile-head">
      <div class="mobile-brand">Winterreise · Зимнее путешествие</div>
      <div class="mobile-nav">
        <button
          class="mob-arrow"
          :disabled="currentSongNumber <= 1"
          aria-label="Предыдущая песня"
          @click="currentSongNumber--"
        >‹</button>
        <select
          class="mob-select"
          :value="currentSongNumber"
          aria-label="Выбор песни"
          @change="currentSongNumber = Number($event.target.value)"
        >
          <option v-for="s in songsIndex" :key="s.number" :value="s.number">
            {{ s.number }}. {{ s.title_de }} — {{ s.title_ru }}
          </option>
        </select>
        <button
          class="mob-arrow"
          :disabled="currentSongNumber >= songsIndex.length"
          aria-label="Следующая песня"
          @click="currentSongNumber++"
        >›</button>
      </div>
      <div class="mobile-controls">
        <label class="mob-check">
          <input type="checkbox" v-model="showAnnotations" /> Пояснения
        </label>
        <label class="mob-check mob-meaning" :class="{ disabled: !showAnnotations }">
          <input type="checkbox" v-model="showMeaning" :disabled="!showAnnotations" /> Смысл
        </label>
        <label class="mob-check mob-lang" :class="{ disabled: !showAnnotations }">
          <input type="checkbox" v-model="showLang" :disabled="!showAnnotations" /> Язык
        </label>
        <span class="mob-toggles">
          <ThemeToggle />
          <SnowToggle />
        </span>
      </div>
    </header>
    <aside class="sidebar">
      <div class="sidebar-title">Песни</div>
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
      <div class="masthead">
        <h1 class="masthead-title">Winterreise</h1>
        <div class="masthead-subtitle">Зимнее путешествие</div>
        <div class="credit">
          Музыка Франца Шуберта<br>
          Поэзия Вильгельма Мюллера
        </div>
        <div class="masthead-tagline">Точный семантический подстрочник с&nbsp;пояснениями</div>
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
