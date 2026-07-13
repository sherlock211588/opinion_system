<template>
  <article class="metric-card">
    <div>
      <p>{{ card.label }}</p>
      <strong>{{ displayValue }}{{ card.suffix }}</strong>
    </div>
    <span>{{ card.trend }}</span>
    <small>{{ card.desc }}</small>
  </article>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const props = defineProps({
  card: {
    type: Object,
    required: true,
  },
})

const displayValue = ref(0)

onMounted(() => {
  const duration = 900
  const start = performance.now()
  const target = Number(props.card.value)

  function tick(now) {
    const progress = Math.min((now - start) / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    displayValue.value = Math.round(target * eased)

    if (progress < 1) {
      requestAnimationFrame(tick)
    }
  }

  requestAnimationFrame(tick)
})
</script>

<style scoped>
.metric-card {
  position: relative;
  overflow: hidden;
  min-height: 150px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 22px 60px rgba(93, 73, 220, 0.1);
  backdrop-filter: blur(20px);
  transition:
    transform 0.28s ease,
    box-shadow 0.28s ease;
}

.metric-card::after {
  position: absolute;
  right: -42px;
  bottom: -42px;
  width: 118px;
  height: 118px;
  content: "";
  border-radius: 50%;
  background: radial-gradient(circle, rgba(128, 92, 255, 0.18), transparent 68%);
}

.metric-card:hover {
  box-shadow: 0 28px 70px rgba(93, 73, 220, 0.16);
  transform: translateY(-4px);
}

.metric-card p {
  margin: 0 0 12px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 700;
}

.metric-card strong {
  color: #ffffff;
  font-size: 36px;
  line-height: 1;
}

.metric-card > span {
  display: inline-flex;
  margin-top: 18px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(128, 92, 255, 0.11);
  color: #6d5dfb;
  font-size: 12px;
  font-weight: 800;
}

.metric-card small {
  display: block;
  margin-top: 12px;
  color: #94a3b8;
  font-size: 13px;
}

/* dark blue technology news theme */
.metric-card {
  border-color: rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(145deg, rgba(15, 30, 58, 0.84), rgba(8, 20, 38, 0.72)),
    rgba(15, 30, 58, 0.75);
  box-shadow: 0 22px 60px rgba(0, 217, 255, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.metric-card::after {
  background: radial-gradient(circle, rgba(37, 99, 235, 0.25), transparent 68%);
}

.metric-card:hover {
  box-shadow: 0 28px 70px rgba(37, 99, 235, 0.18);
}

.metric-card p {
  color: #94a3b8;
}

.metric-card strong {
  color: #ffffff;
  text-shadow: 0 0 22px rgba(56, 189, 248, 0.18);
}

.metric-card > span {
  background: rgba(37, 99, 235, 0.18);
  color: #93c5fd;
  border: 1px solid rgba(56, 189, 248, 0.16);
}

.metric-card small {
  color: #94a3b8;
}
</style>
