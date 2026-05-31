import { ref, watch } from 'vue'

// Режим «Зима»: холодная палитра фона + снег/метель.
// Состояние запоминается в localStorage (как тема).
const stored =
  localStorage.getItem('winter') === '1' || localStorage.getItem('snow') === '1'

export const winterEnabled = ref(stored)

function apply(v) {
  document.documentElement.setAttribute('data-season', v ? 'winter' : 'none')
}

// Применяем сразу при загрузке модуля, чтобы палитра встала до отрисовки.
apply(winterEnabled.value)

watch(winterEnabled, (v) => {
  localStorage.setItem('winter', v ? '1' : '0')
  apply(v)
})

export function toggleWinter() {
  winterEnabled.value = !winterEnabled.value
}
