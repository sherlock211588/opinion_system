<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
})

const emptyText = '--'
const chartLoading = false
const chartError = false
const hasValue = (value) => value !== undefined && value !== null && value !== ''
const valueOrEmpty = (value) => (hasValue(value) ? value : emptyText)
const toNumber = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}
const eventName = (pair, keys) => {
  for (const key of keys) {
    if (hasValue(pair?.[key])) return pair[key]
  }
  return emptyText
}
const normalizePair = (pair, algorithm) => {
  const lag = pair?.lag_hours ?? pair?.lag ?? pair?.best_lag ?? pair?.lag_time
  return {
    id: `${algorithm}-${eventName(pair, ['source_event', 'cause_event', 'from', 'source', 'event_a'])}-${eventName(pair, ['target_event', 'effect_event', 'to', 'target', 'event_b'])}-${lag}`,
    source: eventName(pair, ['source_event', 'cause_event', 'from', 'source', 'event_a', 'preceding_event']),
    target: eventName(pair, ['target_event', 'effect_event', 'to', 'target', 'event_b', 'affected_event']),
    algorithm,
    pValue: pair?.p_value ?? pair?.pvalue ?? pair?.p,
    teValue: pair?.te_value ?? pair?.transfer_entropy ?? pair?.te,
    lag,
  }
}
const relations = computed(() => [
  ...(Array.isArray(props.data?.granger_pairs) ? props.data.granger_pairs.map((pair) => normalizePair(pair, '格兰杰因果')) : []),
  ...(Array.isArray(props.data?.transfer_entropy_pairs)
    ? props.data.transfer_entropy_pairs.map((pair) => normalizePair(pair, '传递熵因果'))
    : []),
])
const hasRelations = computed(() => relations.value.length > 0)
const plainExplanation = (relation) =>
  `${relation.source}的热度变化通常会在${valueOrEmpty(relation.lag)}小时后影响${relation.target}。`

const lagPValueSource = computed(() => props.data?.all_lag_pvalues)
const lagPoints = computed(() => {
  const source = lagPValueSource.value
  if (!source) return []
  const readValue = (lag) => {
    if (Array.isArray(source)) {
      const item = source.find((entry) => Number(entry?.lag ?? entry?.lag_hours ?? entry?.hour) === lag)
      return item?.p_value ?? item?.pvalue ?? item?.p
    }
    return source[lag] ?? source[String(lag)] ?? source[`lag_${lag}`]
  }
  return [1, 2, 3, 4, 5, 6]
    .map((lag) => ({ lag, value: toNumber(readValue(lag)) }))
    .filter((item) => item.value !== null)
})
const hasLagChart = computed(() => lagPoints.value.length > 1)
const strongestLag = computed(() => {
  if (!lagPoints.value.length) return null
  return lagPoints.value.reduce((best, item) => (item.value < best.value ? item : best), lagPoints.value[0])
})
const lagYRange = computed(() => {
  if (!lagPoints.value.length) return { min: 0, max: 1 }
  const min = Math.min(...lagPoints.value.map((item) => item.value), 0)
  const max = Math.max(...lagPoints.value.map((item) => item.value), 0.05)
  return min === max ? { min: min - 0.01, max: max + 0.01 } : { min, max }
})
const lagX = (lag) => 8 + ((lag - 1) / 5) * 84
const lagY = (value) => {
  const { min, max } = lagYRange.value
  return 82 - ((value - min) / (max - min)) * 64
}
const lagPolyline = computed(() => lagPoints.value.map((point) => `${lagX(point.lag)},${lagY(point.value)}`).join(' '))
</script>

<template>
  <section class="card">
    <div class="title">
      <h2>跨事件因果分析</h2>
      <span>Granger / Transfer Entropy</span>
    </div>

    <div v-if="chartLoading" class="empty-state">图表加载中...</div>
    <div v-else-if="chartError" class="empty-state">图表加载失败，请稍后重试。</div>
    <div v-else-if="!hasRelations && !hasLagChart" class="empty-state">
      <strong>暂无因果分析结果</strong>
      <span>需要跨事件滞后关系后才能生成因果图</span>
      <em>数据状态：待补充</em>
    </div>
    <template v-else>
      <div v-if="hasRelations" class="relation-row">
        <article
          v-for="relation in relations"
          :key="relation.id"
          class="relation-card"
          :class="{ dashed: relation.algorithm === '传递熵因果' }"
        >
          <div class="relation-flow">
            <strong>{{ relation.source }}</strong>
            <i></i>
            <strong>{{ relation.target }}</strong>
          </div>
          <details>
            <summary>查看详细解释</summary>
            <dl>
              <div><dt>算法类型</dt><dd>{{ relation.algorithm }}</dd></div>
              <div><dt>p值</dt><dd>{{ valueOrEmpty(relation.pValue) }}</dd></div>
              <div><dt>TE值</dt><dd>{{ valueOrEmpty(relation.teValue) }}</dd></div>
              <div><dt>滞后时间</dt><dd>{{ valueOrEmpty(relation.lag) }} 小时</dd></div>
            </dl>
          </details>
          <p>{{ plainExplanation(relation) }}</p>
        </article>
      </div>

      <div v-if="hasLagChart" class="lag-chart">
        <div class="chart-head">
          <h3>1-6小时滞后效应</h3>
          <span v-if="strongestLag">最强关联：{{ strongestLag.lag }}小时后</span>
        </div>
        <svg viewBox="0 0 100 92" preserveAspectRatio="none" role="img" aria-label="滞后p值折线图">
          <line v-for="y in [18, 34, 50, 66, 82]" :key="y" x1="8" :y1="y" x2="92" :y2="y" />
          <polyline :points="lagPolyline" />
          <g v-for="point in lagPoints" :key="point.lag" :class="{ strongest: strongestLag && point.lag === strongestLag.lag }">
            <circle :cx="lagX(point.lag)" :cy="lagY(point.value)" r="2.4" />
            <text :x="lagX(point.lag)" y="90">{{ point.lag }}h</text>
            <title>{{ point.lag }}小时滞后，p值：{{ point.value }}</title>
          </g>
        </svg>
        <p v-if="strongestLag">最低p值出现在{{ strongestLag.lag }}小时滞后，说明该时间点的关联最强。</p>
        <p>折线展示不同滞后时间下的统计关联强弱，p值越低通常代表关联越明显。</p>
      </div>
    </template>
  </section>
</template>

<style scoped>
.card { padding: 22px; border: 1px solid var(--line); border-radius: 20px; background: var(--card); backdrop-filter: blur(18px); }
.title { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.title h2 { margin: 0; color: #fff; font-size: 18px; }
.title span { color: #64748b; font-size: 10px; }
.empty-state { display: grid; place-items: center; min-height: 190px; margin-top: 16px; border: 1px dashed rgba(129, 140, 248, .2); border-radius: 14px; color: #9faec7; font-size: 13px; line-height: 1.6; text-align: center; }
.empty-state strong, .empty-state span, .empty-state em { display: block; }
.empty-state strong { color: #c7d2fe; font-size: 14px; font-style: normal; }
.empty-state em { color: #7dd3fc; font-size: 12px; font-style: normal; }
.relation-row { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(240px, 1fr); gap: 14px; margin-top: 16px; overflow-x: auto; padding-bottom: 4px; }
.relation-card { min-width: 0; padding: 13px; border: 1px solid rgba(56, 189, 248, .24); border-radius: 12px; background: rgba(56, 189, 248, .06); }
.relation-card.dashed { border-style: dashed; border-color: rgba(168, 85, 247, .5); background: rgba(168, 85, 247, .07); }
.relation-flow { display: grid; grid-template-columns: minmax(0, 1fr) 42px minmax(0, 1fr); gap: 8px; align-items: center; }
.relation-flow strong { overflow: hidden; color: #dbe5f5; font-size: 12px; text-align: center; text-overflow: ellipsis; white-space: nowrap; }
.relation-flow i { position: relative; height: 2px; border-top: 2px solid #38bdf8; }
.relation-card.dashed .relation-flow i { border-top-style: dashed; border-color: #a78bfa; }
.relation-flow i::after { position: absolute; top: -5px; right: -1px; width: 8px; height: 8px; border-top: 2px solid currentColor; border-right: 2px solid currentColor; color: #38bdf8; transform: rotate(45deg); content: ""; }
.relation-card.dashed .relation-flow i::after { color: #a78bfa; }
.relation-card dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 12px 0 0; }
.relation-card details summary { margin-top: 12px; cursor: pointer; color: #a5b4fc; font-size: 10px; }
.relation-card dt { color: #667895; font-size: 9px; }
.relation-card dd { margin: 2px 0 0; color: #c7d2fe; font-size: 11px; word-break: break-word; }
.relation-card p, .lag-chart p { margin: 12px 0 0; color: #9faec7; font-size: 11px; line-height: 1.5; }
.lag-chart { margin-top: 16px; padding: 13px; border: 1px solid rgba(129, 140, 248, .18); border-radius: 12px; background: rgba(99, 102, 241, .06); }
.chart-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.chart-head h3 { margin: 0; color: #c7d2fe; font-size: 12px; }
.chart-head span { color: #38bdf8; font-size: 11px; }
.lag-chart svg { width: 100%; height: 150px; margin-top: 8px; overflow: visible; }
.lag-chart line { stroke: rgba(148, 163, 184, .12); stroke-width: .5; vector-effect: non-scaling-stroke; }
.lag-chart polyline { fill: none; stroke: #8b5cf6; stroke-width: 2; vector-effect: non-scaling-stroke; filter: drop-shadow(0 0 6px rgba(139, 92, 246, .55)); }
.lag-chart circle { fill: #c7d2fe; stroke: #38bdf8; stroke-width: .8; vector-effect: non-scaling-stroke; }
.lag-chart .strongest circle { fill: #f0abfc; stroke: #fff; filter: drop-shadow(0 0 8px rgba(216, 180, 254, .85)); }
.lag-chart text { fill: #64748b; font-size: 4px; text-anchor: middle; }
@media (max-width: 680px) { .relation-row { grid-auto-flow: row; grid-auto-columns: auto; } .chart-head { align-items: flex-start; flex-direction: column; } }
</style>
