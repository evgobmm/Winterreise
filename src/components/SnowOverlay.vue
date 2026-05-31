<script setup>
// Падающий снег: каждый «хлопок» — внешний span (вертикальное падение)
// с вложенным span (независимое покачивание по горизонтали).
// Всё на transform → GPU, плавно и дёшево.
const COUNT = 60

const rand = (min, max) => min + Math.random() * (max - min)

const flakes = Array.from({ length: COUNT }, (_, id) => {
  const fallDuration = rand(9, 18)
  const swayDuration = rand(2.5, 5)
  return {
    id,
    left: rand(0, 100),
    size: rand(2, 6),
    opacity: rand(0.35, 0.85),
    blur: Math.random() < 0.45 ? rand(0.4, 1.1) : 0,
    fallDuration,
    fallDelay: -rand(0, fallDuration),
    drift: rand(6, 28),
    swayDuration,
    swayDelay: -rand(0, swayDuration)
  }
})
</script>

<template>
  <div class="snow" aria-hidden="true">
    <span
      v-for="f in flakes"
      :key="f.id"
      class="flake"
      :style="{
        left: f.left + 'vw',
        animationDuration: f.fallDuration + 's',
        animationDelay: f.fallDelay + 's'
      }"
    >
      <span
        class="flake-dot"
        :style="{
          width: f.size + 'px',
          height: f.size + 'px',
          opacity: f.opacity,
          filter: f.blur ? `blur(${f.blur}px)` : 'none',
          animationDuration: f.swayDuration + 's',
          animationDelay: f.swayDelay + 's',
          '--drift': f.drift + 'px'
        }"
      ></span>
    </span>
  </div>
</template>

<style scoped>
.snow {
  position: fixed;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 9999;
}

.flake {
  position: absolute;
  top: 0;
  display: block;
  animation-name: snow-fall;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
  will-change: transform;
}

.flake-dot {
  display: block;
  border-radius: 50%;
  background: var(--snow);
  animation-name: snow-sway;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  animation-direction: alternate;
  will-change: transform;
}

@keyframes snow-fall {
  from { transform: translateY(-10vh); }
  to { transform: translateY(110vh); }
}

@keyframes snow-sway {
  from { transform: translateX(calc(var(--drift) * -1)); }
  to { transform: translateX(var(--drift)); }
}

@media print {
  .snow {
    display: none;
  }
}
</style>
