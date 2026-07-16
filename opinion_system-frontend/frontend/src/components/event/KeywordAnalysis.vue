<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartLoading = false
const chartError = false
const keywords = computed(() => (Array.isArray(props.data) ? props.data : []))
const rankedKeywords = computed(() => [...keywords.value].sort((a, b) => (b?.count || 0) - (a?.count || 0)).slice(0, 10))
</script>

<template>
  <section class="card keyword-card">
    <div class="section-title"><span class="accent"></span><h2>关键词分析</h2></div>
    <div v-if="chartLoading" class="empty-state">图表加载中...</div>
    <div v-else-if="chartError" class="empty-state">图表加载失败，请稍后重试。</div>
    <div v-else-if="!keywords.length" class="empty-state">暂无关键词数据。</div>
    <div v-else class="keyword-content">
      <div class="ranking-panel">
        <h3>高频关键词 TOP10</h3>
        <ol>
          <li v-for="(word, index) in rankedKeywords" :key="word?.name || index">
            <b>{{ String(index + 1).padStart(2, '0') }}</b>
            <span>{{ word?.name || '--' }}</span>
            <strong>{{ word?.count ?? '--' }}<small>次</small></strong>
          </li>
        </ol>
      </div>
      <div class="cloud-panel">
        <h3>关键词词云</h3>
        <div class="word-cloud" aria-label="舆情关键词词云">
          <span v-for="(word, index) in keywords" :key="word?.name || index" :title="`${word?.name || '--'}：出现 ${word?.count ?? '--'} 次`" :style="{ left: `${word?.x ?? 50}%`, top: `${word?.y ?? 50}%`, color: word?.color || '#a78bfa', fontSize: `${word?.size ?? 14}px`, transform: `translate(-50%, -50%) rotate(${word?.rotate ?? 0}deg)`, textShadow: `0 0 18px ${word?.color || '#a78bfa'}66` }">{{ word?.name || '--' }}</span>
        </div>
        <p class="chart-note">词云展示当前事件讨论中出现频率较高的关键词。</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card { box-sizing: border-box; height: auto; padding: 22px 24px; border: 1px solid rgba(139, 92, 246, .35); border-radius: 20px; background: linear-gradient(130deg, rgba(15, 30, 70, .68), rgba(48, 18, 70, .38)); box-shadow: 0 0 30px rgba(236, 72, 153, .08); backdrop-filter: blur(20px); }
.section-title { display: flex; align-items: center; gap: 9px; }
.section-title h2 { margin: 0; color: #fff; font-size: 18px; }
.accent { width: 4px; height: 18px; border-radius: 99px; background: linear-gradient(#8b5cf6, #ec4899); }
.keyword-content { display: grid; grid-template-columns: minmax(270px, 35fr) minmax(0, 65fr); gap: 20px; margin-top: 14px; }
.empty-state { display:grid;place-items:center;min-height:180px;margin-top:14px;border:1px dashed rgba(129,140,248,.2);border-radius:14px;color:#7183a3;font-size:13px; }
.ranking-panel { padding-right: 20px; border-right: 1px solid rgba(139, 92, 246, .16); }
h3 { margin: 0 0 9px; color: #aebbd2; font-size: 12px; font-weight: 600; }
.ranking-panel ol { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; margin: 0; padding: 0; list-style: none; }
.ranking-panel li { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto; gap: 7px; align-items: center; padding: 7px 9px; border: 1px solid rgba(139, 92, 246, .13); border-radius: 9px; background: linear-gradient(100deg, rgba(139, 92, 246, .1), rgba(236, 72, 153, .035)); }
.ranking-panel li:hover { border-color: rgba(236, 72, 153, .3); background: linear-gradient(100deg, rgba(139, 92, 246, .16), rgba(236, 72, 153, .08)); }
.ranking-panel b { color: #8b5cf6; font-size: 12px; }
.ranking-panel li:nth-child(-n+3) b { color: #ec4899; }
.ranking-panel span { min-width: 0; overflow: hidden; color: #c7d1e4; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.ranking-panel strong { color: #e9d5ff; font-size: 10px; text-align: right; white-space: nowrap; }
.ranking-panel small { margin-left: 2px; color: #7183a3; font-size: 8px; }
.cloud-panel { min-width: 0; }
.word-cloud { position: relative; height: 184px; overflow: hidden; border: 1px solid rgba(139, 92, 246, .12); border-radius: 14px; background: radial-gradient(circle at 48% 48%, rgba(139, 92, 246, .15), transparent 58%), rgba(5, 11, 36, .2); }
.word-cloud::before { position: absolute; inset: 0; background-image: linear-gradient(rgba(139, 92, 246, .035) 1px, transparent 1px), linear-gradient(90deg, rgba(139, 92, 246, .035) 1px, transparent 1px); background-size: 26px 26px; content: ''; }
.word-cloud span { position: absolute; font-weight: 750; line-height: 1; white-space: nowrap; transition: filter .25s ease; }
.word-cloud span:hover { z-index: 2; filter: brightness(1.25); }
.chart-note { margin: 10px 0 0; color: #9faec7; font-size: 11px; line-height: 1.5; }
@media (max-width: 850px) { .keyword-content { grid-template-columns: 1fr; } .ranking-panel { padding-right: 0; padding-bottom: 16px; border-right: 0; border-bottom: 1px solid rgba(139, 92, 246, .16); } }
@media (max-width: 520px) { .ranking-panel ol { grid-template-columns: 1fr; } .word-cloud { height: 220px; } }
</style>
