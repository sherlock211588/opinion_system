<script setup>
import { computed } from 'vue'

const props = defineProps({
  overview: {
    type: Object,
    default: () => ({}),
  },
  event: {
    type: Object,
    default: () => ({}),
  },
})

const fallback = '--'
const people = computed(() => (Array.isArray(props.overview?.people) ? props.overview.people : []))
</script>

<template>
  <section class="card">
    <div class="title"><h2><i>01</i> 事件概览</h2><span>可信度 {{ event?.credibility ?? fallback }}%</span></div>
    <p class="summary">{{ overview?.summary || fallback }}</p>
    <dl>
      <div><dt>发生时间</dt><dd>{{ overview?.time || fallback }}</dd></div>
      <div><dt>涉及地点</dt><dd>{{ overview?.location || fallback }}</dd></div>
      <div><dt>事件起因</dt><dd>{{ overview?.cause || fallback }}</dd></div>
      <div><dt>涉及人物</dt><dd><span v-for="person in people" :key="person">{{ person }}</span><template v-if="!people.length">{{ fallback }}</template></dd></div>
    </dl>
  </section>
</template>

<style scoped>
.card{padding:22px;border:1px solid var(--line);border-radius:20px;background:var(--card);backdrop-filter:blur(18px)}.title{display:flex;justify-content:space-between;align-items:center}.title h2{margin:0;color:#fff;font-size:18px}.title h2 i{padding:4px 6px;border-radius:7px;background:linear-gradient(135deg,#6366f1,#8b5cf6);font-size:10px;font-style:normal}.title>span{color:#22d3ee;font-size:12px}.summary{margin:16px 0;color:#b6c2dc;font-size:13px;line-height:1.8}dl{display:grid;gap:10px;margin:0;padding-top:14px;border-top:1px solid rgba(129,140,248,.12)}dl>div{display:grid;grid-template-columns:70px 1fr;gap:12px}dt{color:#7183a3;font-size:12px}dd{margin:0;color:#c4cee2;font-size:12px;line-height:1.55}dd span{display:inline-block;margin:0 5px 5px 0;padding:3px 8px;border-radius:7px;background:rgba(99,102,241,.1);color:#a5b4fc}
</style>
