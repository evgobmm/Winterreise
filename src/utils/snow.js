import { ref, watch } from 'vue'

// Общее состояние снегопада (как тема — запоминается в localStorage)
export const snowEnabled = ref(localStorage.getItem('snow') === '1')

watch(snowEnabled, (v) => {
  localStorage.setItem('snow', v ? '1' : '0')
})

export function toggleSnow() {
  snowEnabled.value = !snowEnabled.value
}
