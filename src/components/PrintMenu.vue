<script setup>
import { ref, computed, nextTick, onUnmounted } from 'vue'
import SongView from './SongView.vue'
import songsIndex from '../data/index.json'

const props = defineProps({
  currentSongNumber: { type: Number, required: true },
  showAnnotations: Boolean,
  showLang: Boolean,
  showMeaning: Boolean
})

const emit = defineEmits(['close'])

// Локальные копии настроек: всё, что выбирается в этом меню, живёт только здесь
// и не трогает состояние приложения — ни до печати, ни после закрытия.
const pAnn = ref(props.showAnnotations)
const pMeaning = ref(props.showMeaning)
const pLang = ref(props.showLang)
const selected = ref(new Set([props.currentSongNumber]))

function toggleSong(n) {
  const next = new Set(selected.value)
  if (next.has(n)) next.delete(n)
  else next.add(n)
  selected.value = next
}

function selectAll() {
  selected.value = new Set(songsIndex.map(s => s.number))
}

function clearAll() {
  selected.value = new Set()
}

const selectedSongs = computed(() =>
  songsIndex.filter(s => selected.value.has(s.number))
)

// На время печати рендерим «печатный лист» с выбранными песнями (на экране он
// спрятан за краем); body.printing-songs прячет приложение в @media print.
const printing = ref(false)
const sheetRef = ref(null)

// Полезная высота страницы A4 при полях 14мм (для оценки разбиения на страницы)
const MM = 96 / 25.4
const PAGE_H = (297 - 2 * 14) * MM

// Если песня свешивается на следующую страницу меньше чем на 20% страницы —
// пробуем ступенями ужать кегль пояснений, чтобы убрать «огрызок»;
// не помогло ни на одной ступени — возвращаем нормальный кегль.
function autoFitNotes() {
  const songs = sheetRef.value ? sheetRef.value.querySelectorAll('.print-song') : []
  for (const el of songs) {
    el.removeAttribute('data-compact')
    const pages0 = Math.ceil(el.offsetHeight / PAGE_H)
    const tail0 = el.offsetHeight - (pages0 - 1) * PAGE_H
    if (pages0 <= 1 || tail0 >= 0.2 * PAGE_H) continue
    let applied = 0
    for (let lvl = 1; lvl <= 3; lvl++) {
      el.setAttribute('data-compact', String(lvl))
      if (Math.ceil(el.offsetHeight / PAGE_H) < pages0) {
        applied = lvl
        break
      }
    }
    if (!applied) el.removeAttribute('data-compact')
  }
}

async function doPrint() {
  if (!selectedSongs.value.length) return
  printing.value = true
  document.body.classList.add('printing-songs')
  await nextTick()
  if (document.fonts && document.fonts.ready) await document.fonts.ready
  autoFitNotes()
  window.print()
  document.body.classList.remove('printing-songs')
  printing.value = false
  emit('close')
}

onUnmounted(() => document.body.classList.remove('printing-songs'))
</script>

<template>
  <Teleport to="body">
    <div class="print-backdrop" @click="emit('close')">
      <div class="print-menu" @click.stop>
        <h3 class="print-title">Печать</h3>

        <div class="print-anns">
          <label class="print-check">
            <input type="checkbox" v-model="pAnn" /> Пояснения
          </label>
          <label class="print-check print-meaning" :class="{ disabled: !pAnn }">
            <input type="checkbox" v-model="pMeaning" :disabled="!pAnn" /> Смысл
          </label>
          <label class="print-check print-lang" :class="{ disabled: !pAnn }">
            <input type="checkbox" v-model="pLang" :disabled="!pAnn" /> Язык
          </label>
        </div>

        <div class="print-songs-head">
          <span class="print-songs-label">Песни</span>
          <button class="print-mini" @click="selectAll">Выбрать все</button>
          <button class="print-mini" @click="clearAll">Снять все</button>
        </div>

        <div class="print-song-list">
          <label
            v-for="s in songsIndex"
            :key="s.number"
            class="print-song-item"
          >
            <input
              type="checkbox"
              :checked="selected.has(s.number)"
              @change="toggleSong(s.number)"
            />
            {{ s.number }}. {{ s.title_de }}
          </label>
        </div>

        <div class="print-actions">
          <button class="print-go" :disabled="!selectedSongs.length" @click="doPrint">
            Печать{{ selectedSongs.length > 1 ? ` (${selectedSongs.length})` : '' }}
          </button>
          <button class="print-cancel" @click="emit('close')">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Печатный лист: на экране спрятан за краем (линейка для измерений) -->
    <div v-if="printing" ref="sheetRef" class="print-sheet">
      <div
        v-for="s in selectedSongs"
        :key="s.number"
        class="print-song"
      >
        <SongView
          :song-file="s.file"
          :show-annotations="pAnn"
          :show-lang="pLang"
          :show-meaning="pMeaning"
        />
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.print-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 120;
  display: flex;
  align-items: center;
  justify-content: center;
}

.print-menu {
  width: 520px;
  max-width: calc(100vw - 48px);
  max-height: 84vh;
  overflow-y: auto;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px 22px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  font-family: var(--font-sans);
}

.print-title {
  font-family: var(--font-serif);
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 14px;
}

.print-anns {
  display: flex;
  gap: 18px;
  align-items: center;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}

.print-check {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.95rem;
  color: var(--text-secondary);
  cursor: pointer;
}

.print-check input {
  cursor: pointer;
  accent-color: var(--text-secondary);
}

.print-meaning {
  color: var(--color-meaning);
}

.print-meaning input {
  accent-color: var(--color-meaning);
}

.print-lang {
  color: var(--color-lang);
}

.print-lang input {
  accent-color: var(--color-lang);
}

.print-check.disabled {
  opacity: 0.4;
}

.print-songs-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 14px 0 10px;
}

.print-songs-label {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text);
  margin-right: auto;
}

.print-mini {
  font-family: inherit;
  font-size: 0.82rem;
  color: var(--link);
  background: none;
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 4px 9px;
  cursor: pointer;
}

.print-mini:hover {
  background: var(--highlight);
}

.print-song-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 14px;
  max-height: 38vh;
  overflow-y: auto;
  padding: 2px;
}

.print-song-item {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 0.88rem;
  color: var(--text);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.print-song-item input {
  cursor: pointer;
  accent-color: var(--accent);
  flex-shrink: 0;
}

.print-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

.print-go {
  font-family: inherit;
  font-size: 0.95rem;
  color: #fff;
  background: var(--accent);
  border: none;
  border-radius: 6px;
  padding: 8px 18px;
  cursor: pointer;
}

.print-go:hover:not(:disabled) {
  background: var(--accent-hover);
}

.print-go:disabled {
  opacity: 0.45;
  cursor: default;
}

.print-cancel {
  font-family: inherit;
  font-size: 0.95rem;
  color: var(--text);
  background: none;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 14px;
  cursor: pointer;
}

.print-cancel:hover {
  background: var(--highlight);
}

/* Сам лист (.print-sheet) оформлен в main.css: на экране спрятан за краем
   и служит линейкой для измерений, на печати встаёт в поток */
@media print {
  .print-backdrop {
    display: none;
  }

  .print-song {
    break-after: page;
    page-break-after: always;
  }

  .print-song:last-child {
    break-after: auto;
    page-break-after: auto;
  }
}
</style>
