<script setup>
import { ref } from 'vue'

const emit = defineEmits(['close'])

const ADDRESS = 'evgobmm@gmail.com'
const message = ref('')
const copied = ref(false)

// Письмо уходит через почтовый клиент посетителя (mailto) — сайт ничего
// не собирает и не хранит, сообщения приходят обычной почтой автору.
function send() {
  const subject = encodeURIComponent('Winterreise — отзыв')
  const body = encodeURIComponent(message.value)
  window.location.href = `mailto:${ADDRESS}?subject=${subject}&body=${body}`
}

async function copyAddress() {
  try {
    await navigator.clipboard.writeText(ADDRESS)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (e) {
    /* буфер недоступен — адрес виден текстом, можно выделить вручную */
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fb-backdrop" @click="emit('close')">
      <div class="fb-menu" @click.stop>
        <h3 class="fb-title">Письмо автору</h3>

        <p class="fb-text">
          Вы можете написать мне о найденных ошибках, неточностях, предложить
          улучшения или просто оставить отзыв.
        </p>
        <p class="fb-sign">Евгений Обухов</p>

        <textarea
          v-model="message"
          class="fb-area"
          rows="6"
          placeholder="Текст письма…"
        ></textarea>

        <div class="fb-actions">
          <button class="fb-send" :disabled="!message.trim()" @click="send">
            Отправить письмом
          </button>
          <button class="fb-cancel" @click="emit('close')">Отмена</button>
        </div>

        <p class="fb-fallback">
          Кнопка откроет вашу почтовую программу. Если это неудобно — напишите
          напрямую: <span class="fb-address">{{ ADDRESS }}</span>
          <button class="fb-copy" @click="copyAddress">{{ copied ? 'скопировано' : 'скопировать' }}</button>
        </p>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.fb-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 120;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.fb-menu {
  width: 480px;
  max-width: calc(100vw - 32px);
  max-height: 86vh;
  overflow-y: auto;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px 22px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  font-family: var(--font-sans);
}

.fb-title {
  font-family: var(--font-serif);
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.fb-text {
  font-family: var(--font-serif);
  font-size: 0.98rem;
  line-height: 1.55;
  color: var(--text);
}

.fb-sign {
  font-family: var(--font-serif);
  font-style: italic;
  text-align: right;
  color: var(--text-secondary);
  margin: 6px 0 14px;
}

.fb-area {
  width: 100%;
  resize: vertical;
  min-height: 110px;
  padding: 10px 12px;
  font-family: var(--font-serif);
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
}

.fb-area:focus {
  outline: none;
  border-color: var(--accent);
}

.fb-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 14px;
}

.fb-send {
  font-family: inherit;
  font-size: 0.95rem;
  color: #fff;
  background: var(--accent);
  border: none;
  border-radius: 6px;
  padding: 8px 18px;
  cursor: pointer;
}

.fb-send:hover:not(:disabled) {
  background: var(--accent-hover);
}

.fb-send:disabled {
  opacity: 0.45;
  cursor: default;
}

.fb-cancel {
  font-family: inherit;
  font-size: 0.95rem;
  color: var(--text);
  background: none;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 14px;
  cursor: pointer;
}

.fb-cancel:hover {
  background: var(--highlight);
}

.fb-fallback {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--text-secondary);
}

.fb-address {
  color: var(--link);
  user-select: all;
}

.fb-copy {
  margin-left: 6px;
  font-family: inherit;
  font-size: 0.78rem;
  color: var(--link);
  background: none;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 7px;
  cursor: pointer;
}

.fb-copy:hover {
  background: var(--highlight);
}

@media print {
  .fb-backdrop {
    display: none;
  }
}
</style>
