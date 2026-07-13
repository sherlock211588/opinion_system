<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: [Object, Array],
    default: () => ({}),
  },
})

const palette = {
  positive: '#5eead4',
  neutral: '#a78bfa',
  negative: '#fb923c',
}
const chartLoading = false
const chartError = false
const labels = {
  positive: '正面',
  neutral: '中性',
  negative: '负面',
}
const hasValue = (value) => value !== undefined && value !== null && value !== ''
const toNumber = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}
const rawDistribution = computed(() => {
  if (Array.isArray(props.data)) {
    return Object.fromEntries(props.data.map((item) => [item.key ?? item.type ?? item.label, item.value]))
  }
  return props.data?.sentiment_distribution ?? props.data?.distribution ?? props.data ?? {}
})
const sentimentItems = computed(() => {
  const values = ['positive', 'neutral', 'negative'].map((key) => ({
    key,
    label: labels[key],
    raw: toNumber(rawDistribution.value?.[key]),
    color: palette[key],
  }))
  const presentValues = values.filter((item) => item.raw !== null)
  if (!presentValues.length) return []
  const sum = presentValues.reduce((total, item) => total + item.raw, 0)
  const useRatio = sum > 0 && sum <= 1.01
  const useCount = sum > 100.01
  return values.map((item) => {
    if (item.raw === null) return { ...item, value: 0, display: '--' }
    const percent = useRatio ? item.raw * 100 : useCount && sum ? (item.raw / sum) * 100 : item.raw
    return { ...item, value: percent, display: `${percent.toFixed(1)}%` }
  })
})
const hasSentimentData = computed(() => sentimentItems.value.length > 0)
const chartGradient = computed(() => {
  if (!hasSentimentData.value) return 'conic-gradient(rgba(129,140,248,.16) 0% 100%)'
  let start = 0
  return `conic-gradient(${sentimentItems.value
    .map((item) => {
      const from = start
      start += item.value
      return `${item.color}cc ${from}% ${start}%`
    })
    .join(', ')})`
})
const sampleTotal = computed(() => {
  const total = props.data?.total ?? props.data?.sample_count
  if (hasValue(total)) return Number(total).toLocaleString()
  return '--'
})
</script>

<template>
  <section class="card emotion-card">
    <div class="section-title"><span class="accent"></span><h2>情感分析</h2></div>
    <div v-if="chartLoading" class="empty-state">图表加载中...</div>
    <div v-else-if="chartError" class="empty-state">图表加载失败，请稍后重试。</div>
    <div v-else-if="!hasSentimentData" class="empty-state">
      <strong>暂无情感统计数据</strong>
      <span>需要情感分类结果后才能生成分布图</span>
      <em>数据状态：待补充</em>
    </div>
    <div v-else class="emotion-content">
      <div class="chart-wrap">
        <div class="donut" :style="{ background: chartGradient }">
          <div class="donut-center"><strong>{{ sampleTotal }}</strong><small>分析样本</small></div>
        </div>
      </div>
      <ul class="emotion-list">
        <li v-for="item in sentimentItems" :key="item.key">
          <i :style="{ backgroundColor: item.color, boxShadow: `0 0 8px ${item.color}66` }"></i>
          <span>{{ item.label }}</span>
          <strong>{{ item.display }}</strong>
        </li>
      </ul>
    </div>
    <p v-if="hasSentimentData" class="chart-note">该图展示新闻讨论中正面、中性和负面情绪的占比。</p>
  </section>
</template>

<style scoped>
.card { box-sizing: border-box; height: auto; padding: 24px; border: 1px solid rgba(139, 92, 246, .35); border-radius: 20px; background: rgba(15, 30, 70, .65); box-shadow: 0 0 30px rgba(129, 140, 248, .09); backdrop-filter: blur(20px); }
.section-title { display: flex; align-items: center; gap: 9px; }
.section-title h2 { margin: 0; color: #fff; font-size: 18px; }
.accent { width: 4px; height: 18px; border-radius: 99px; background: linear-gradient(#5eead4, #a78bfa, #fb923c); opacity: .8; }
.emotion-content { display: flex; gap: 16px; align-items: center; min-width: 0; padding-top: 22px; }
.chart-wrap { display: grid; flex: 0 1 46%; min-width: 96px; place-items: center; }
.donut { position: relative; display: grid; width: clamp(96px, 9vw, 124px); aspect-ratio: 1; place-items: center; border-radius: 50%; box-shadow: 0 0 22px rgba(129, 140, 248, .14); }
.donut::after { position: absolute; inset: 23%; border: 1px solid rgba(139, 92, 246, .16); border-radius: 50%; background: linear-gradient(145deg, #0b1638, #17133d); content: ''; }
.donut-center { z-index: 1; display: grid; place-items: center; }
.donut-center strong { color: #f8fafc; font-size: 14px; white-space: nowrap; }
.donut-center small { margin-top: 3px; color: #7384a5; font-size: 8px; white-space: nowrap; }
.emotion-list { display: flex; flex: 1 1 54%; min-width: 0; flex-direction: column; gap: 8px; margin: 0; padding: 0; list-style: none; }
.emotion-list li { display: flex; min-width: 0; align-items: center; gap: 8px; padding: 9px 10px; overflow: hidden; border: 1px solid rgba(139, 92, 246, .11); border-radius: 10px; background: rgba(5, 11, 36, .22); }
.emotion-list i { flex: 0 0 8px; width: 8px; height: 8px; border-radius: 50%; opacity: .82; }
.emotion-list span { min-width: 0; flex: 1; overflow: hidden; color: #aab7cd; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.emotion-list strong { flex: 0 0 auto; color: #e8edf7; font-size: 11px; text-align: right; white-space: nowrap; }
.empty-state { display: grid; place-items: center; min-height: 154px; margin-top: 18px; border: 1px dashed rgba(129, 140, 248, .2); border-radius: 12px; color: #7183a3; font-size: 12px; line-height: 1.6; text-align: center; }
.empty-state strong, .empty-state span, .empty-state em { display: block; }
.empty-state strong { color: #c7d2fe; font-size: 14px; font-style: normal; }
.empty-state em { color: #7dd3fc; font-size: 12px; font-style: normal; }
.chart-note { margin: 12px 0 0; color: #9faec7; font-size: 11px; line-height: 1.5; }
@media (max-width: 460px) { .emotion-content { flex-direction: column; } .emotion-list { width: 100%; } }
</style>
