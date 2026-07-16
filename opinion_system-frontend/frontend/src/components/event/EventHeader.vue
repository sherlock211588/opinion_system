<script setup>
import { computed } from 'vue'

const props = defineProps({
  event: {
    type: Object,
    default: () => ({}),
  },
})

const fallback = '--'
const eventTime = computed(() => props.event?.time || fallback)
const eventCode = computed(() => {
  const rawTime = props.event?.time
  return rawTime ? `EVENT_${String(rawTime).slice(0, 10).replaceAll('-', '')}` : 'EVENT_--'
})
</script>

<template>
  <header class="header">
    <div class="heading">
      <span class="eyebrow">EVENT INTELLIGENCE REPORT</span>
      <h1>{{ event?.title || fallback }} <i>热</i></h1>
      <div class="meta">
        <span>事件编号：{{ eventCode }}</span>
        <span>{{ event?.source || fallback }}</span>
        <time>发生时间：{{ eventTime }}</time>
        <span class="tag">{{ event?.category || fallback }}</span>
      </div>
    </div>
    <div class="metrics">
      <div><small>当前阶段</small><strong class="purple">{{ event?.stage || '高潮期' }}</strong><span>{{ event?.stageNote || '预计持续 1–2 天' }}</span></div>
      <div><small>热度指数</small><strong>{{ event?.heat ?? fallback }}</strong><span>{{ event?.heatTrend || '较昨日 ↑ 12' }}</span></div>
      <div><small>风险等级</small><strong class="orange">{{ event?.riskLevel || fallback }}</strong><span>{{ event?.riskNote || '波动较大，需重点关注' }}</span></div>
      <div><small>信息可信度</small><strong class="cyan">{{ event?.credibility ?? fallback }}%</strong><span>{{ event?.credibilityTrend || '较昨日 ↑ 5%' }}</span></div>
    </div>
  </header>
</template>

<style scoped>
.header{margin-bottom:20px}.heading,.metrics{border:1px solid rgba(129,140,248,.25);background:linear-gradient(115deg,rgba(11,31,68,.86),rgba(17,26,69,.72));backdrop-filter:blur(18px);box-shadow:0 20px 60px rgba(2,6,23,.2)}.heading{padding:24px 28px;border-radius:22px 22px 0 0}.eyebrow{color:#38bdf8;font-size:11px;font-weight:800;letter-spacing:.14em}.header h1{margin:8px 0 12px;color:#fff;font-size:clamp(23px,2.3vw,34px);line-height:1.35}.header h1 i{display:inline-grid;width:24px;height:24px;place-items:center;border-radius:8px;background:rgba(168,85,247,.16);color:#d8b4fe;font-size:12px;font-style:normal;vertical-align:middle}.meta{display:flex;gap:14px;align-items:center;flex-wrap:wrap;color:#94a3b8;font-size:12px}.tag{padding:4px 10px;border-radius:99px;background:rgba(99,102,241,.16);color:#a5b4fc}.metrics{display:grid;grid-template-columns:repeat(4,1fr);border-top:0;border-radius:0 0 22px 22px}.metrics div{display:grid;gap:6px;padding:17px 24px;border-right:1px solid rgba(129,140,248,.13)}.metrics div:last-child{border:0}.metrics small,.metrics span{color:#7486a7;font-size:11px}.metrics strong{color:#38bdf8;font-size:25px}.metrics .purple{color:#c084fc}.metrics .orange{color:#a855f7}.metrics .cyan{color:#22d3ee}@media(max-width:760px){.metrics{grid-template-columns:repeat(2,1fr)}.metrics div:nth-child(2){border-right:0}.metrics div:nth-child(-n+2){border-bottom:1px solid rgba(129,140,248,.13)}}@media(max-width:500px){.heading{padding:20px}.metrics{grid-template-columns:1fr}.metrics div{border-right:0;border-bottom:1px solid rgba(129,140,248,.13)!important}}
</style>
