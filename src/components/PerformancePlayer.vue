<script setup>
import { ref, computed, watch } from 'vue'
import data from '../data/performances.json'

const props = defineProps({
  songNumber: { type: Number, required: true }
})

const performers = data.performers
const expanded = ref(false)

const savedPerformer = localStorage.getItem('performer')
const performer = ref(
  performers.some(p => p.id === savedPerformer) ? savedPerformer : performers[0].id
)
watch(performer, v => localStorage.setItem('performer', v))

const videoId = computed(() => {
  const entry = data.videos[String(props.songNumber)]
  return entry ? entry[performer.value] : null
})

const embedSrc = computed(() =>
  videoId.value
    ? `https://www.youtube-nocookie.com/embed/${videoId.value}?rel=0&modestbranding=1&autoplay=1`
    : ''
)
</script>

<template>
  <div class="performance">
    <button
      class="perf-toggle"
      :class="{ open: expanded }"
      @click="expanded = !expanded"
    >
      <span class="perf-note">♪</span>
      <span class="perf-label">Исполнения</span>
      <span class="perf-caret">{{ expanded ? '▾' : '▸' }}</span>
    </button>

    <div v-if="expanded" class="perf-body">
      <div class="perf-performers">
        <button
          v-for="p in performers"
          :key="p.id"
          class="perf-name"
          :class="{ active: p.id === performer }"
          @click="performer = p.id"
        >{{ p.name }}</button>
      </div>

      <div v-if="videoId" class="perf-frame">
        <iframe
          :key="videoId"
          :src="embedSrc"
          title="Исполнение"
          loading="lazy"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
        ></iframe>
      </div>
      <p v-else class="perf-none">Для этой песни записи нет.</p>

      <a
        v-if="videoId"
        class="perf-yt"
        :href="'https://www.youtube.com/watch?v=' + videoId"
        target="_blank"
        rel="noopener"
      >Открыть на YouTube ↗</a>
    </div>
  </div>
</template>

<style scoped>
.performance {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.perf-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 7px 10px;
  font-family: inherit;
  font-size: 0.9rem;
  color: var(--text);
  background: var(--sidebar-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.perf-toggle:hover {
  background: var(--highlight);
}

.perf-toggle.open {
  border-color: var(--accent);
}

.perf-note {
  color: var(--accent);
}

.perf-label {
  flex: 1;
  text-align: left;
}

.perf-caret {
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.perf-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.perf-performers {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.perf-name {
  padding: 4px 8px;
  font-family: inherit;
  font-size: 0.8rem;
  text-align: left;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.perf-name:hover {
  color: var(--text);
}

.perf-name.active {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.perf-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 6px;
  overflow: hidden;
  background: #000;
}

.perf-frame iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}

.perf-none {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-style: italic;
}

.perf-yt {
  font-size: 0.75rem;
  color: var(--link);
  text-decoration: none;
}

.perf-yt:hover {
  text-decoration: underline;
}

@media print {
  .performance {
    display: none;
  }
}
</style>
