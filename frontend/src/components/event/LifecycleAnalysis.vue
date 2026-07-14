<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
})

const emptyValue = '--'
const chartLoading = false
const chartError = false
const stages = [
  { key: 'latent', label: '潜伏期' },
  { key: 'growth', label: '成长期' },
  { key: 'peak', label: '高潮期' },
  { key: 'decline', label: '衰退期' },
]
const stageAlias = {
  latent: 'latent',
  incubation: 'latent',
  potential: 'latent',
  '潜伏期': 'latent',
  '潜伏': 'latent',
  growth: 'growth',
  growing: 'growth',
  development: 'growth',
  '成长期': 'growth',
  '成长': 'growth',
  peak: 'peak',
  climax: 'peak',
  high: 'peak',
  '高潮期': 'peak',
  '高潮': 'peak',
  decline: 'decline',
  decay: 'decline',
  recession: 'decline',
  fading: 'decline',
  '衰退期': 'decline',
  '衰退': 'decline',
}

const hasValue = (value) => value !== undefined && value !== null && value !== ''
const valueOrEmpty = (value) => (hasValue(value) ? value : emptyValue)
const normalizeStageKey = (stage) => stageAlias[String(stage ?? '').trim().toLowerCase()] || null
const toNumber = (value) => {
  if (value === undefined || value === null || value === '') return null
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

const parseTimestamp = (value) => {
  if (value === undefined || value === null) return null
  const text = String(value).trim()
  if (!text) return null

  const normalizedText = /^\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}/.test(text)
    ? text.replace(/\s+/, 'T')
    : text
  const timestamp = new Date(normalizedText).getTime()
  return Number.isFinite(timestamp) ? timestamp : null
}

const formatFullTime = (value) => {
  const timestamp = parseTimestamp(value)
  if (timestamp === null) return valueOrEmpty(value)

  const date = new Date(timestamp)
  const pad = (number) => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const normalizePoint = (point, index) => {
  if (typeof point === 'number') {
    return {
      value: Number.isFinite(point) ? point : null,
      label: `${index + 1}`,
      timestamp: null,
    }
  }

  const label = point?.label ?? point?.time ?? point?.date ?? point?.timestamp ?? point?.publish_time ?? ''
  return {
    value: toNumber(
      point?.value ??
        point?.heat ??
        point?.hot_score ??
        point?.count ??
        point?.news_count ??
        point?.predicted_count ??
        point?.y,
    ),
    label: String(label ?? '').trim(),
    timestamp: parseTimestamp(label),
  }
}

const normalizeSeries = (values) => {
  if (!Array.isArray(values)) return []

  const merged = new Map()
  const unparsed = []

  values.forEach((point, index) => {
    const normalized = normalizePoint(point, index)
    if (normalized.value === null) return

    if (normalized.timestamp !== null) {
      merged.set(normalized.timestamp, normalized)
    } else {
      unparsed.push({ ...normalized, fallbackIndex: index })
    }
  })

  const parsed = Array.from(merged.values()).sort((a, b) => a.timestamp - b.timestamp)
  return [...parsed, ...unparsed.sort((a, b) => a.fallbackIndex - b.fallbackIndex)]
}

const currentStageKey = computed(() => normalizeStageKey(props.data?.current_stage ?? props.data?.stage))
const currentStageLabel = computed(() => {
  const stage = stages.find((item) => item.key === currentStageKey.value)
  return stage?.label || valueOrEmpty(props.data?.current_stage ?? props.data?.stage)
})
const warningLevelMap = {
  none: '状态正常',
  yellow: '需要关注',
  orange: '存在爆发风险',
  red: '高风险预警',
}
const dataQualityMap = {
  full: '完整',
  basic: '基础',
  minimal: '有限',
  sparse: '稀疏',
}
const earlyWarning = computed(() => props.data?.critical_early_warning || {})
const warningLevel = computed(() => String(earlyWarning.value?.level ?? earlyWarning.value?.status ?? 'none').toLowerCase())
const warningStatus = computed(() => warningLevelMap[warningLevel.value] || valueOrEmpty(earlyWarning.value?.level ?? earlyWarning.value?.status))
const warningReason = computed(() => valueOrEmpty(earlyWarning.value?.reason ?? earlyWarning.value?.cause))
const warningMessage = computed(() => valueOrEmpty(earlyWarning.value?.message))
const varianceRatio = computed(() => valueOrEmpty(earlyWarning.value?.variance_ratio))
const ar1Coefficient = computed(() => valueOrEmpty(earlyWarning.value?.ar1_coefficient))
const resurgence = computed(() => props.data?.resurgence || {})
const isResurgence = computed(() => resurgence.value?.is_resurgence === true)
const resurgenceInfo = computed(() => {
  const peak = resurgence.value?.peak ?? resurgence.value?.related_peak ?? resurgence.value?.peak_info
  const valley = resurgence.value?.valley ?? resurgence.value?.related_valley ?? resurgence.value?.valley_info
  const peakText = hasValue(peak) ? `峰值：${typeof peak === 'object' ? valueOrEmpty(peak.value ?? peak.count ?? peak.time ?? peak.label) : peak}` : '峰值：--'
  const valleyText = hasValue(valley) ? `谷值：${typeof valley === 'object' ? valueOrEmpty(valley.value ?? valley.count ?? valley.time ?? valley.label) : valley}` : '谷值：--'
  return `${peakText}，${valleyText}`
})
const diurnalCycle = computed(() => props.data?.diurnal_cycle || {})
const hasDiurnalCycle = computed(() => {
  const value = diurnalCycle.value?.has_cycle ?? diurnalCycle.value?.detected ?? diurnalCycle.value?.is_diurnal_cycle
  return value === true
})
const dataQuality = computed(() => {
  const quality = String(props.data?.data_quality ?? '').toLowerCase()
  return dataQualityMap[quality] || valueOrEmpty(props.data?.data_quality)
})
const trendDirection = computed(() => {
  const direction = String(props.data?.trend_direction ?? props.data?.trendDirection ?? '').trim().toLowerCase()
  if (['up', 'rise', 'rising', 'increase', '上升', '上涨'].includes(direction)) return '↑'
  if (['down', 'fall', 'falling', 'decrease', '下降', '下跌'].includes(direction)) return '↓'
  if (['flat', 'stable', 'steady', 'neutral', '持平', '平稳'].includes(direction)) return '→'
  return emptyValue
})
const metrics = computed(() => [
  { label: '当前阶段', value: currentStageLabel.value },
  { label: '热度指数', value: valueOrEmpty(props.data?.current_heat_index ?? props.data?.heat) },
  { label: '趋势方向', value: trendDirection.value },
  { label: '当前平均声量', value: valueOrEmpty(props.data?.current_avg_count) },
])
const radarDimensions = [
  { key: 'volume', label: '报道量', description: '反映事件被报道、转载和提及的规模。' },
  { key: 'sentiment_volatility', label: '情感分歧', description: '反映公众态度是否分化，数值越高代表争议越明显。' },
  { key: 'platform_spread', label: '平台扩散', description: '反映事件在不同平台之间扩散的广度。' },
  { key: 'engagement', label: '互动热度', description: '反映评论、转发、点赞等互动活跃程度。' },
]
const compositeBreakdown = computed(() => props.data?.composite_index_breakdown || null)
const radarItems = computed(() =>
  radarDimensions.map((dimension, index) => {
    const source = compositeBreakdown.value?.[dimension.key]
    const rawValue = typeof source === 'object' ? source?.value ?? source?.score ?? source?.count : source
    const value = toNumber(rawValue)
    const normalized = value === null ? null : Math.max(0, Math.min(value <= 1 ? value * 100 : value, 100))
    return { ...dimension, index, value, normalized }
  }),
)
const hasRadarData = computed(() => radarItems.value.every((item) => item.normalized !== null))
const radarPoint = (index, value = 100, radius = 34) => {
  const angle = -Math.PI / 2 + (index * Math.PI * 2) / radarDimensions.length
  const distance = (value / 100) * radius
  return {
    x: 50 + Math.cos(angle) * distance,
    y: 50 + Math.sin(angle) * distance,
  }
}
const radarPolygon = computed(() =>
  hasRadarData.value
    ? radarItems.value
        .map((item) => {
          const point = radarPoint(item.index, item.normalized)
          return `${point.x},${point.y}`
        })
        .join(' ')
    : '',
)
const radarTooltip = (item) => `${item.label}：${item.description}\n当前值：${valueOrEmpty(item.value)}`

const actualSeries = computed(() => normalizeSeries(props.data?.points ?? props.data?.heat_trend ?? props.data?.series))
const predictionRaw = computed(() => props.data?.predicted_next_24h)
const predictionItems = computed(() => {
  const source = Array.isArray(predictionRaw.value)
    ? predictionRaw.value
    : predictionRaw.value?.points ?? predictionRaw.value?.values ?? predictionRaw.value?.trend
  return Array.isArray(source) ? source : []
})
const predictedSeries = computed(() => {
  return predictionItems.value
    .map((point, index) => ({
      value: toNumber(point?.predicted_count ?? point?.value ?? point?.heat ?? point?.count ?? point?.y),
      label: point?.prediction_time ?? point?.time ?? point?.date ?? point?.label ?? `${index + 1}`,
      lower: toNumber(point?.lower_bound),
      upper: toNumber(point?.upper_bound),
      description: point?.turning_point_description ?? point?.description ?? point?.note ?? '',
    }))
    .filter((item) => item.value !== null)
})
const confidenceUpper = computed(() => {
  const inline = predictedSeries.value
    .map((point) => ({ value: point.upper, label: point.label }))
    .filter((point) => point.value !== null)
  return inline.length ? inline : normalizeSeries(predictionRaw.value?.upper ?? predictionRaw.value?.confidence_upper)
})
const confidenceLower = computed(() => {
  const inline = predictedSeries.value
    .map((point) => ({ value: point.lower, label: point.label }))
    .filter((point) => point.value !== null)
  return inline.length ? inline : normalizeSeries(predictionRaw.value?.lower ?? predictionRaw.value?.confidence_lower)
})
const allValues = computed(() => [
  ...actualSeries.value.map((item) => item.value),
  ...predictedSeries.value.map((item) => item.value),
  ...confidenceUpper.value.map((item) => item.value),
  ...confidenceLower.value.map((item) => item.value),
])
const valueRange = computed(() => {
  if (!allValues.value.length) return { min: 0, max: 100 }
  const min = Math.min(...allValues.value, 0)
  const max = Math.max(...allValues.value, 100)
  return min === max ? { min: min - 1, max: max + 1 } : { min, max }
})
const xStep = computed(() => {
  const total = actualSeries.value.length + predictedSeries.value.length
  return total > 1 ? 100 / (total - 1) : 0
})
const yOf = (value) => {
  const { min, max } = valueRange.value
  return 94 - ((value - min) / (max - min)) * 82
}
const xOf = (index) => {
  const total = actualSeries.value.length + predictedSeries.value.length
  if (total <= 1) return 50
  return index * xStep.value
}
const coords = (series, offset = 0) =>
  series.map((point, index) => `${xOf(index + offset)},${yOf(point.value)}`).join(' ')
const areaPath = (series, offset = 0) => {
  if (series.length < 2) return ''
  const points = series.map((point, index) => `${xOf(index + offset)},${yOf(point.value)}`)
  return `M ${xOf(offset)},94 L ${points.join(' L ')} L ${xOf(offset + series.length - 1)},94 Z`
}
const confidencePath = computed(() => {
  if (!confidenceUpper.value.length || !confidenceLower.value.length) return ''
  const offset = Math.max(actualSeries.value.length - 1, 0)
  const upper = confidenceUpper.value.map((point, index) => `${xOf(index + offset)},${yOf(point.value)}`)
  const lower = confidenceLower.value
    .map((point, index) => `${xOf(index + offset)},${yOf(point.value)}`)
    .reverse()
  return `M ${upper.join(' L ')} L ${lower.join(' L ')} Z`
})
const turningPoints = computed(() =>
  Array.isArray(props.data?.turning_points)
    ? props.data.turning_points
        .map((point) => {
          const matchedIndex = predictedSeries.value.findIndex(
            (item) => item.label && item.label === (point?.prediction_time ?? point?.time ?? point?.date ?? point?.label),
          )
          const index = toNumber(point?.index) ?? (matchedIndex >= 0 ? matchedIndex + Math.max(actualSeries.value.length - 1, 0) : null)
          const value = toNumber(point?.value ?? point?.heat ?? point?.count ?? point?.predicted_count)
          return index === null || value === null ? null : { ...point, index, value }
        })
        .filter(Boolean)
    : [],
)
const labels = computed(() => {
  const source = actualSeries.value
  if (!source.length) return []

  const maxLabels = 5
  if (source.length <= maxLabels) {
    return source.map((item) => item.label || emptyValue)
  }

  const indexes = new Set([0, source.length - 1])
  const step = (source.length - 1) / (maxLabels - 1)
  for (let index = 1; index < maxLabels - 1; index += 1) {
    indexes.add(Math.round(index * step))
  }

  return Array.from(indexes)
    .sort((a, b) => a - b)
    .map((index) => source[index]?.label || emptyValue)
})
const chartDataState = computed(() => {
  if (actualSeries.value.length === 0) return 'empty'
  if (actualSeries.value.length === 1) return 'single'
  return 'line'
})
const hasChartData = computed(() => chartDataState.value !== 'empty')
const hasPredictionData = computed(() => predictedSeries.value.length > 0)
const actualTooltipText = (point) =>
  [`时间：${formatFullTime(point.label)}`, `热度：${valueOrEmpty(point.value)}`].join('\n')
const tooltipText = (point) => {
  const range =
    point.lower !== null && point.upper !== null
      ? `${point.lower} - ${point.upper}`
      : emptyValue
  const turningPoint = turningPoints.value.find((item) => item.index === point.index || item.label === point.label)
  return [
    `预测时间：${valueOrEmpty(point.label)}`,
    `预测数量：${valueOrEmpty(point.value)}`,
    `上下波动范围：${range}`,
    `拐点说明：${valueOrEmpty(turningPoint?.description ?? turningPoint?.label ?? point.description)}`,
  ].join('\n')
}
</script>

<template>
  <section class="card">
    <div class="title">
      <h2><i>02</i> 舆情生命周期分析</h2>
      <div class="title-tags">
        <span class="stage-tag">{{ currentStageLabel }}</span>
        <span class="warning-tag" :class="`warning-${warningLevel}`">{{ warningStatus }}</span>
      </div>
    </div>

    <div class="analysis-body">
      <div class="chart-panel">
        <div v-if="chartLoading" class="empty-chart">图表加载中...</div>
        <div v-else-if="chartError" class="empty-chart">图表加载失败，请稍后重试。</div>
        <svg v-else-if="hasChartData" viewBox="0 0 100 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="lifecycleLine" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0%" stop-color="#38bdf8" />
              <stop offset="55%" stop-color="#6366f1" />
              <stop offset="100%" stop-color="#a855f7" />
            </linearGradient>
            <linearGradient id="lifecycleArea" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#8b5cf6" stop-opacity=".34" />
              <stop offset="100%" stop-color="#38bdf8" stop-opacity=".03" />
            </linearGradient>
            <filter id="pointGlow" x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="1.6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <line v-for="y in [20, 40, 60, 80]" :key="y" x1="0" :y1="y" x2="100" :y2="y" />
          <path v-if="chartDataState === 'line'" class="area" :d="areaPath(actualSeries)" />
          <path v-if="confidencePath" class="confidence" :d="confidencePath" />
          <polyline v-if="chartDataState === 'line'" class="actual-line" :points="coords(actualSeries)" />
          <polyline
            v-if="predictedSeries.length"
            class="predict-line"
            :points="coords(predictedSeries, Math.max(actualSeries.length - 1, 0))"
          />
          <circle
            v-for="(point, index) in predictedSeries"
            :key="`predict-${index}`"
            class="predict-point"
            :cx="xOf(index + Math.max(actualSeries.length - 1, 0))"
            :cy="yOf(point.value)"
            r="1.9"
          >
            <title>{{ tooltipText({ ...point, index: index + Math.max(actualSeries.length - 1, 0) }) }}</title>
          </circle>
          <circle
            v-for="(point, index) in actualSeries"
            :key="`actual-${point.timestamp ?? point.label}-${index}`"
            class="data-point"
            :class="{ 'single-data-point': chartDataState === 'single' }"
            :cx="xOf(index)"
            :cy="yOf(point.value)"
            :r="chartDataState === 'single' ? 3.2 : 1.8"
          >
            <title>{{ actualTooltipText(point) }}</title>
          </circle>
          <g v-for="point in turningPoints" :key="`${point.index}-${point.value}`" class="turning-point">
            <circle :cx="xOf(point.index)" :cy="yOf(point.value)" r="2.4" />
            <text :x="xOf(point.index)" :y="Math.max(yOf(point.value) - 6, 8)">
              {{ point.label || '拐点' }}
            </text>
            <title>{{ valueOrEmpty(point.description ?? point.label) }}</title>
          </g>
        </svg>
        <div v-else class="empty-chart">暂无生命周期数据</div>
        <div v-if="chartDataState === 'single'" class="single-point-note">数据不足，暂无法形成趋势</div>
        <div v-if="!hasPredictionData" class="empty-prediction">暂无预测数据</div>
        <p v-else class="prediction-note">阴影区域代表预测可能波动的范围，范围越宽，不确定性越高。</p>
        <div class="labels">
          <span v-for="label in labels" :key="label">{{ label }}</span>
        </div>
      </div>

      <div class="metric-panel">
        <div v-for="metric in metrics" :key="metric.label" class="metric-item">
          <small>{{ metric.label }}</small>
          <strong>{{ metric.value }}</strong>
        </div>
      </div>
    </div>

    <div class="composite-radar">
      <div class="radar-heading">
        <div>
          <span>四维综合热度</span>
          <p>该图展示事件热度由哪些因素共同构成。</p>
        </div>
      </div>

      <div v-if="chartLoading" class="radar-empty">图表加载中...</div>
      <div v-else-if="chartError" class="radar-empty">图表加载失败，请稍后重试。</div>
      <div v-else-if="hasRadarData" class="radar-body">
        <svg viewBox="0 0 100 100" role="img" aria-label="四维综合热度雷达图">
          <defs>
            <linearGradient id="compositeRadarFill" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stop-color="#38bdf8" stop-opacity=".34" />
              <stop offset="100%" stop-color="#8b5cf6" stop-opacity=".42" />
            </linearGradient>
            <linearGradient id="compositeRadarLine" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stop-color="#38bdf8" />
              <stop offset="100%" stop-color="#a855f7" />
            </linearGradient>
          </defs>
          <polygon
            v-for="level in [25, 50, 75, 100]"
            :key="level"
            class="radar-ring"
            :points="radarDimensions.map((_, index) => `${radarPoint(index, level).x},${radarPoint(index, level).y}`).join(' ')"
          />
          <line
            v-for="(dimension, index) in radarDimensions"
            :key="dimension.key"
            class="radar-axis"
            x1="50"
            y1="50"
            :x2="radarPoint(index).x"
            :y2="radarPoint(index).y"
          />
          <polygon class="radar-shape" :points="radarPolygon" />
          <g v-for="item in radarItems" :key="item.key" class="radar-point">
            <circle :cx="radarPoint(item.index, item.normalized).x" :cy="radarPoint(item.index, item.normalized).y" r="2.2">
              <title>{{ radarTooltip(item) }}</title>
            </circle>
            <text
              :x="radarPoint(item.index, 112).x"
              :y="radarPoint(item.index, 112).y"
              :text-anchor="item.index === 1 ? 'start' : item.index === 3 ? 'end' : 'middle'"
              :dominant-baseline="item.index === 0 ? 'text-after-edge' : item.index === 2 ? 'text-before-edge' : 'middle'"
            >
              {{ item.label }}
              <title>{{ radarTooltip(item) }}</title>
            </text>
          </g>
        </svg>
        <div class="radar-values">
          <span v-for="item in radarItems" :key="item.key" :title="radarTooltip(item)">
            {{ item.label }} {{ item.value }}
          </span>
        </div>
      </div>
      <div v-else class="radar-empty">暂无数据</div>
    </div>

    <details class="advanced-details">
      <summary>查看详细解释</summary>
      <div class="aux-status">
      <div class="aux-card warning-detail">
        <div class="aux-heading">
          <span>预警说明</span>
          <strong :class="`warning-text-${warningLevel}`">{{ warningStatus }}</strong>
        </div>
        <p>预警原因：{{ warningReason }}</p>
        <div class="aux-grid">
          <span>波动放大程度：{{ varianceRatio }}</span>
          <span>持续升温倾向：{{ ar1Coefficient }}</span>
        </div>
        <p>系统提示：{{ warningMessage }}</p>
      </div>

      <div class="aux-card">
        <div class="aux-heading">
          <span>辅助判断</span>
          <strong v-if="isResurgence" class="resurgence-tag">二次爆发</strong>
          <strong v-else>--</strong>
        </div>
        <p v-if="isResurgence">事件出现二次升温迹象，{{ resurgenceInfo }}。</p>
        <p v-else>暂未发现明显二次爆发迹象。</p>
        <p v-if="hasDiurnalCycle">系统已排除凌晨自然流量下降的影响。</p>
        <p v-else>暂未识别到需要单独修正的昼夜周期影响。</p>
      </div>

      <div class="aux-card quality-card">
        <small>数据质量</small>
        <strong>{{ dataQuality }}</strong>
        <p>数据越完整，阶段判断和趋势预测越可靠。</p>
      </div>
      </div>
    </details>

    <div class="stage-progress" aria-label="生命周期进度">
      <div
        v-for="(stage, index) in stages"
        :key="stage.key"
        class="stage-item"
        :class="{ active: stage.key === currentStageKey }"
      >
        <span class="stage-node">{{ index + 1 }}</span>
        <strong>{{ stage.label }}</strong>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card { height: auto; padding: 22px; border: 1px solid rgba(129, 140, 248, .34); border-radius: 20px; background: linear-gradient(135deg, rgba(15, 30, 70, .68), rgba(49, 46, 129, .22)); box-shadow: 0 0 30px rgba(99, 102, 241, .09); color: #e8edff; backdrop-filter: blur(20px); }
.title { display: flex; justify-content: space-between; gap: 14px; align-items: center; }
.title h2 { margin: 0; color: #fff; font-size: 18px; }
.title h2 i { padding: 4px 6px; border-radius: 7px; background: linear-gradient(135deg, #6366f1, #8b5cf6); font-size: 10px; font-style: normal; }
.title-tags { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.title-tags span { padding: 5px 11px; border-radius: 99px; font-size: 12px; white-space: nowrap; }
.stage-tag { background: linear-gradient(135deg, rgba(56, 189, 248, .24), rgba(139, 92, 246, .28)); color: #e0e7ff; box-shadow: 0 0 14px rgba(99, 102, 241, .18); }
.warning-tag { background: rgba(168, 85, 247, .15); color: #d8b4fe; }
.warning-none { background: rgba(34, 197, 94, .13); color: #86efac; }
.warning-yellow { background: rgba(234, 179, 8, .14); color: #fde68a; }
.warning-orange { background: rgba(249, 115, 22, .15); color: #fdba74; }
.warning-red { background: rgba(244, 63, 94, .16); color: #fda4af; }
.analysis-body { display: grid; grid-template-columns: minmax(0, 7fr) minmax(150px, 3fr); gap: 14px; margin-top: 18px; align-items: stretch; }
.chart-panel { min-width: 0; }
.chart-panel svg { width: 100%; height: 190px; overflow: visible; }
.chart-panel line { stroke: rgba(148, 163, 184, .12); stroke-width: .5; }
.area { fill: url(#lifecycleArea); }
.confidence { fill: rgba(56, 189, 248, .1); stroke: rgba(56, 189, 248, .2); stroke-width: .4; }
.actual-line { fill: none; stroke: url(#lifecycleLine); stroke-width: 2.3; vector-effect: non-scaling-stroke; filter: drop-shadow(0 0 6px rgba(99, 102, 241, .85)); }
.predict-line { fill: none; stroke: #38bdf8; stroke-dasharray: 4 3; stroke-width: 1.8; vector-effect: non-scaling-stroke; filter: drop-shadow(0 0 5px rgba(56, 189, 248, .55)); }
.data-point { fill: #e0f2fe; stroke: #8b5cf6; stroke-width: .8; vector-effect: non-scaling-stroke; filter: url(#pointGlow); }
.single-data-point { fill: #fff; stroke: #38bdf8; stroke-width: 1.2; }
.predict-point { fill: #bae6fd; stroke: #38bdf8; stroke-width: .8; vector-effect: non-scaling-stroke; filter: url(#pointGlow); }
.turning-point circle { fill: #f0abfc; stroke: #fff; stroke-width: .6; vector-effect: non-scaling-stroke; filter: drop-shadow(0 0 6px rgba(216, 180, 254, .85)); }
.turning-point text { fill: #d8b4fe; font-size: 3px; text-anchor: middle; paint-order: stroke; stroke: rgba(15, 23, 42, .75); stroke-width: .8; }
.labels { display: flex; justify-content: space-between; gap: 8px; min-height: 14px; color: #64748b; font-size: 10px; }
.empty-chart { display: grid; place-items: center; height: 190px; border: 1px dashed rgba(129, 140, 248, .2); border-radius: 12px; color: #7183a3; }
.single-point-note { margin-top: 8px; color: #facc15; font-size: 11px; }
.empty-prediction { margin-top: 8px; color: #7183a3; font-size: 11px; }
.prediction-note { margin: 8px 0 0; color: #9faec7; font-size: 11px; line-height: 1.5; }
.metric-panel { display: grid; grid-template-rows: repeat(4, 1fr); gap: 10px; }
.metric-item { display: flex; min-width: 0; padding: 10px 12px; border-radius: 10px; background: rgba(99, 102, 241, .07); flex-direction: column; justify-content: center; }
.metric-item small { color: #7183a3; font-size: 10px; }
.metric-item strong { margin-top: 5px; color: #38bdf8; font-size: 18px; line-height: 1.2; word-break: break-word; }
.composite-radar { margin-top: 16px; padding: 14px; border: 1px solid rgba(129, 140, 248, .18); border-radius: 12px; background: rgba(15, 30, 70, .28); }
.radar-heading { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.radar-heading span { color: #e0e7ff; font-size: 13px; font-weight: 700; }
.radar-heading p { margin: 5px 0 0; color: #9faec7; font-size: 11px; line-height: 1.5; }
.radar-body { display: grid; grid-template-columns: minmax(180px, 240px) minmax(0, 1fr); gap: 14px; margin-top: 10px; align-items: center; }
.radar-body svg { width: 100%; height: 190px; overflow: visible; }
.radar-ring { fill: none; stroke: rgba(129, 140, 248, .18); stroke-width: .55; vector-effect: non-scaling-stroke; }
.radar-axis { stroke: rgba(148, 163, 184, .16); stroke-width: .55; vector-effect: non-scaling-stroke; }
.radar-shape { fill: url(#compositeRadarFill); stroke: url(#compositeRadarLine); stroke-width: 1.8; vector-effect: non-scaling-stroke; filter: drop-shadow(0 0 8px rgba(99, 102, 241, .5)); }
.radar-point circle { fill: #e0f2fe; stroke: #8b5cf6; stroke-width: .8; vector-effect: non-scaling-stroke; filter: drop-shadow(0 0 5px rgba(56, 189, 248, .75)); }
.radar-point text { fill: #c7d2fe; font-size: 4px; paint-order: stroke; stroke: rgba(15, 23, 42, .65); stroke-width: .8; }
.radar-values { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.radar-values span { min-width: 0; padding: 8px 10px; border-radius: 9px; background: rgba(99, 102, 241, .08); color: #c7d2fe; font-size: 11px; line-height: 1.35; }
.radar-empty { display: grid; place-items: center; min-height: 110px; margin-top: 10px; border: 1px dashed rgba(129, 140, 248, .2); border-radius: 10px; color: #7183a3; font-size: 12px; }
.aux-status { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1.2fr) minmax(130px, .8fr); gap: 10px; margin-top: 16px; }
.aux-card { min-width: 0; padding: 12px; border: 1px solid rgba(129, 140, 248, .18); border-radius: 12px; background: rgba(99, 102, 241, .06); }
.aux-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px; }
.aux-heading span, .quality-card small { color: #7183a3; font-size: 10px; }
.aux-heading strong { color: #c7d2fe; font-size: 13px; white-space: nowrap; }
.warning-text-none { color: #86efac; }
.warning-text-yellow { color: #fde68a; }
.warning-text-orange { color: #fdba74; }
.warning-text-red { color: #fda4af; }
.aux-card p { margin: 6px 0 0; color: #9faec7; font-size: 11px; line-height: 1.5; }
.aux-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 8px; }
.aux-grid span { padding: 7px 8px; border-radius: 8px; background: rgba(15, 30, 70, .5); color: #c7d2fe; font-size: 11px; line-height: 1.35; }
.resurgence-tag { padding: 3px 8px; border-radius: 99px; background: linear-gradient(135deg, rgba(56, 189, 248, .24), rgba(168, 85, 247, .28)); color: #e0e7ff; box-shadow: 0 0 14px rgba(99, 102, 241, .16); }
.quality-card { display: flex; flex-direction: column; justify-content: center; }
.quality-card strong { margin-top: 5px; color: #38bdf8; font-size: 20px; line-height: 1.2; }
.advanced-details { margin-top: 16px; }
.advanced-details summary { cursor: pointer; color: #c7d2fe; font-size: 12px; }
.stage-progress { position: relative; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 18px; }
.stage-progress::before { content: ""; position: absolute; top: 15px; left: 10%; right: 10%; height: 2px; background: linear-gradient(90deg, rgba(56, 189, 248, .28), rgba(139, 92, 246, .36)); }
.stage-item { position: relative; z-index: 1; display: grid; justify-items: center; gap: 7px; min-width: 0; color: #7183a3; text-align: center; }
.stage-node { display: grid; place-items: center; width: 32px; height: 32px; border: 1px solid rgba(129, 140, 248, .34); border-radius: 50%; background: #10204a; color: #94a3b8; font-size: 12px; box-shadow: inset 0 0 0 6px rgba(15, 30, 70, .95); }
.stage-item strong { overflow: hidden; width: 100%; color: #9faec7; font-size: 12px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.stage-item.active .stage-node { border-color: transparent; background: linear-gradient(135deg, #38bdf8, #6366f1 52%, #a855f7); color: #fff; box-shadow: 0 0 20px rgba(99, 102, 241, .52); }
.stage-item.active strong { color: #fff; }
@media (max-width: 720px) {
  .title { align-items: flex-start; flex-direction: column; }
  .title-tags { justify-content: flex-start; }
  .analysis-body { grid-template-columns: 1fr; }
  .metric-panel { grid-template-columns: repeat(2, minmax(0, 1fr)); grid-template-rows: auto; }
  .radar-body { grid-template-columns: 1fr; }
  .aux-status { grid-template-columns: 1fr; }
  .stage-progress { gap: 6px; }
  .stage-item strong { font-size: 11px; }
}
</style>