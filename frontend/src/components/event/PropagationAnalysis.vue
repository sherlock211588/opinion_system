<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { GraphChart } from 'echarts/charts'
import { LegendComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

use([GraphChart, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  data: {
    type: Object,
    default: null,
  },
})

const chartRef = ref(null)
let chartInstance
let resizeObserver

const emptyText = '--'
const chartLoading = false
const chartError = false
const qualityMap = {
  full: '完整',
  basic: '基础',
  minimal: '有限',
  sparse: '稀疏',
}
const roleColors = {
  origin: '#f472b6',
  source: '#f472b6',
  media: '#38bdf8',
  creator: '#8b5cf6',
  public: '#22d3ee',
  official: '#34d399',
  account: '#818cf8',
}

const hasValue = (value) => value !== undefined && value !== null && value !== ''
const valueOrEmpty = (value) => (hasValue(value) ? value : emptyText)
const toNumber = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}
const graph = computed(() => props.data?.graph || null)
const graphNodes = computed(() => (Array.isArray(graph.value?.nodes) ? graph.value.nodes : []))
const graphLinks = computed(() => (Array.isArray(graph.value?.links) ? graph.value.links : []))
const graphCategories = computed(() => (Array.isArray(graph.value?.categories) ? graph.value.categories : []))
const hasPropagationData = computed(() => Boolean(props.data && graphNodes.value.length && graphLinks.value.length))
const nodeCount = computed(() => graphNodes.value.length)
const dataQuality = computed(() => {
  const quality = String(props.data?.data_quality ?? '').toLowerCase()
  return qualityMap[quality] || valueOrEmpty(props.data?.data_quality)
})
const roleLabel = (node) => valueOrEmpty(node?.role_label ?? node?.role ?? node?.category ?? node?.type)
const nodeName = (node) => valueOrEmpty(node?.account_name ?? node?.name ?? node?.label ?? node?.id)
const influenceOf = (node) =>
  toNumber(node?.influence ?? node?.influence_score ?? node?.composite_score ?? node?.score ?? node?.pagerank) ?? 1
const isSourceNode = (node) =>
  node?.is_initial_source === true ||
  node?.is_source === true ||
  node?.is_origin === true ||
  ['origin', 'source', '初始信息源', '首发'].includes(String(node?.role ?? node?.type ?? '').toLowerCase())
const categoryName = (node) => String(node?.category ?? node?.role ?? node?.type ?? 'account')
const colorOf = (node) => roleColors[String(node?.role ?? node?.type ?? node?.category ?? 'account').toLowerCase()] || '#818cf8'
const normalizedCategories = computed(() => {
  const names = new Set(graphCategories.value.map((item) => (typeof item === 'string' ? item : item?.name)).filter(Boolean))
  graphNodes.value.forEach((node) => names.add(categoryName(node)))
  return [...names].map((name) => ({ name }))
})
const chartNodes = computed(() =>
  graphNodes.value.map((node) => {
    const influence = influenceOf(node)
    const source = isSourceNode(node)
    return {
      id: String(node.id ?? node.name),
      name: nodeName(node),
      value: influence,
      category: categoryName(node),
      symbolSize: Math.max(18, Math.min(58, 18 + influence * 0.35)),
      itemStyle: {
        color: colorOf(node),
        borderColor: source ? '#fff' : 'rgba(255,255,255,.35)',
        borderWidth: source ? 3 : 1,
        shadowBlur: source ? 24 : 12,
        shadowColor: source ? 'rgba(244,114,182,.75)' : 'rgba(56,189,248,.28)',
      },
      label: {
        show: source,
        color: '#fff',
        fontSize: 11,
      },
      raw: node,
    }
  }),
)
const chartLinks = computed(() =>
  graphLinks.value.map((link) => ({
    source: String(link.source),
    target: String(link.target),
    value: link.value ?? link.weight ?? 1,
    lineStyle: {
      width: Math.max(1, Math.min(4, Number(link.weight ?? link.value ?? 1))),
    },
  })),
)
const chartOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item',
    confine: true,
    backgroundColor: 'rgba(15, 23, 42, .94)',
    borderColor: 'rgba(129, 140, 248, .3)',
    textStyle: { color: '#e8edff', fontSize: 12 },
    formatter: (params) => {
      if (params.dataType === 'edge') {
        return `传播关系<br/>${params.data.source} → ${params.data.target}`
      }
      const node = params.data.raw || {}
      return [
        `${nodeName(node)}${isSourceNode(node) ? '（初始信息源）' : ''}`,
        `角色：${roleLabel(node)}`,
        `影响力：${valueOrEmpty(influenceOf(node))}`,
      ].join('<br/>')
    },
  },
  legend: {
    show: normalizedCategories.value.length > 1,
    bottom: 0,
    textStyle: { color: '#94a3b8', fontSize: 10 },
  },
  series: [
    {
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      data: chartNodes.value,
      links: chartLinks.value,
      categories: normalizedCategories.value,
      force: {
        repulsion: 150,
        edgeLength: [55, 130],
        gravity: 0.08,
      },
      label: {
        show: true,
        position: 'right',
        color: '#c7d2fe',
        fontSize: 10,
      },
      lineStyle: {
        color: 'rgba(56, 189, 248, .5)',
        curveness: 0.18,
        opacity: 0.72,
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 3 },
      },
    },
  ],
}))
const keyNodes = computed(() => (Array.isArray(props.data?.key_nodes) ? props.data.key_nodes : []))
const counterfactualList = computed(() => {
  const source = props.data?.counterfactual
  if (Array.isArray(source)) return source
  if (source && typeof source === 'object') return Object.entries(source).map(([key, value]) => ({ account_name: key, ...value }))
  return []
})
const counterfactualText = (node) => {
  const match = counterfactualList.value.find((item) => {
    const name = item.account_name ?? item.name ?? item.node_name ?? item.id
    const id = item.node_id ?? item.id
    return name === (node.account_name ?? node.name) || id === node.id
  })
  const reduction = match?.reduction_rate ?? match?.expected_reduction ?? match?.scale_reduction ?? match?.reduced_percent
  return hasValue(reduction) ? `移除该账号后，传播规模预计减少 ${reduction}。` : '暂无反事实影响评估。'
}
const summary = computed(() => valueOrEmpty(props.data?.propagation_summary))
const description = computed(() => valueOrEmpty(props.data?.propagation_description))

function renderChart() {
  if (!chartRef.value || !hasPropagationData.value) return
  if (!chartInstance) chartInstance = init(chartRef.value)
  chartInstance.setOption(chartOption.value, true)
}

onMounted(() => {
  renderChart()
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => chartInstance?.resize())
    resizeObserver.observe(chartRef.value)
  }
})

watch(chartOption, () => renderChart(), { deep: true })
watch(hasPropagationData, (available) => {
  if (available) {
    renderChart()
  } else {
    chartInstance?.dispose()
    chartInstance = null
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chartInstance?.dispose()
})
</script>

<template>
  <section class="card">
    <div class="title">
      <h2>传播溯源分析</h2>
      <span>力导向传播链路</span>
    </div>

    <div v-if="chartLoading" class="empty-state">传播图加载中...</div>
    <div v-else-if="chartError" class="empty-state">传播图加载失败，请稍后重试。</div>
    <div v-else-if="!hasPropagationData" class="empty-state">
      <strong>当前事件暂无完整传播链路数据</strong>
      <span>需要传播节点关系后才能生成拓扑图</span>
      <em>数据状态：待补充</em>
    </div>
    <template v-else>
      <div class="summary-row">
        <div>
          <small>节点总数</small>
          <strong>{{ nodeCount }}</strong>
        </div>
        <div>
          <small>传播深度</small>
          <strong>{{ valueOrEmpty(data.propagation_depth) }}</strong>
        </div>
        <div>
          <small>数据完整性</small>
          <strong>{{ dataQuality }}</strong>
        </div>
      </div>

      <p class="summary-text">{{ summary }}</p>
      <p class="description-text">{{ description }}</p>

      <div class="content">
        <div class="graph-panel">
          <div ref="chartRef" class="graph-chart"></div>
          <p class="chart-note">该图展示传播节点之间的扩散关系，节点越大表示影响力越高。</p>
        </div>

        <div class="key-panel">
          <h3>关键传播节点</h3>
          <div v-if="!keyNodes.length" class="mini-empty">暂无关键节点数据</div>
          <ol v-else>
            <li v-for="node in keyNodes" :key="node.id || node.account_name || node.name">
              <div class="node-head">
                <b>{{ node.account_name || node.name || node.label || emptyText }}</b>
                <span>{{ roleLabel(node) }}</span>
              </div>
              <details>
                <summary>查看详细解释</summary>
                <dl>
                  <div><dt>PageRank</dt><dd>{{ valueOrEmpty(node.pagerank ?? node.page_rank) }}</dd></div>
                  <div><dt>介数中心性</dt><dd>{{ valueOrEmpty(node.betweenness_centrality ?? node.betweenness) }}</dd></div>
                  <div><dt>出度得分</dt><dd>{{ valueOrEmpty(node.out_degree_score ?? node.out_degree) }}</dd></div>
                  <div><dt>综合得分</dt><dd>{{ valueOrEmpty(node.composite_score ?? node.score) }}</dd></div>
                </dl>
              </details>
              <p>{{ counterfactualText(node) }}</p>
            </li>
          </ol>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.card { padding: 22px; border: 1px solid var(--line); border-radius: 20px; background: var(--card); color: #e8edff; backdrop-filter: blur(18px); }
.title { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.title h2 { margin: 0; color: #fff; font-size: 18px; }
.title span { color: #64748b; font-size: 10px; }
.empty-state { display: grid; place-items: center; min-height: 200px; margin-top: 16px; border: 1px dashed rgba(129, 140, 248, .2); border-radius: 14px; color: #9faec7; font-size: 13px; text-align: center; }
.empty-state strong, .empty-state span, .empty-state em { display: block; }
.empty-state strong { color: #c7d2fe; font-size: 14px; font-style: normal; }
.empty-state em { color: #7dd3fc; font-size: 12px; font-style: normal; }
.summary-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 16px; }
.summary-row > div { padding: 10px 12px; border-radius: 10px; background: rgba(99, 102, 241, .07); }
.summary-row small { display: block; color: #7183a3; font-size: 10px; }
.summary-row strong { display: block; margin-top: 5px; color: #38bdf8; font-size: 19px; line-height: 1.15; word-break: break-word; }
.summary-text, .description-text { margin: 10px 0 0; color: #c7d2fe; font-size: 12px; line-height: 1.55; }
.description-text { color: #9faec7; }
.content { display: grid; grid-template-columns: minmax(0, 1fr) 280px; gap: 18px; min-height: 330px; margin-top: 16px; }
.graph-panel { min-width: 0; min-height: 330px; border: 1px solid rgba(99, 102, 241, .12); border-radius: 15px; background: radial-gradient(circle at center, rgba(99, 102, 241, .09), transparent 65%); }
.graph-chart { width: 100%; height: 100%; min-height: 330px; }
.chart-note { margin: -34px 14px 12px; color: #7183a3; font-size: 10px; line-height: 1.45; pointer-events: none; }
.key-panel { padding-left: 17px; border-left: 1px solid rgba(129, 140, 248, .12); }
.key-panel h3 { margin: 0 0 12px; color: #c7d2fe; font-size: 12px; }
.key-panel ol { display: grid; gap: 9px; margin: 0; padding: 0; list-style: none; counter-reset: rank; }
.key-panel li { display: grid; gap: 8px; padding: 10px; border-radius: 10px; background: rgba(99, 102, 241, .07); counter-increment: rank; }
.node-head { display: flex; justify-content: space-between; gap: 8px; align-items: center; }
.node-head b { min-width: 0; overflow: hidden; color: #e0e7ff; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.node-head b::before { margin-right: 7px; color: #818cf8; content: counter(rank); }
.node-head span { flex: 0 0 auto; padding: 3px 7px; border-radius: 99px; background: rgba(56, 189, 248, .12); color: #7dd3fc; font-size: 10px; }
.key-panel dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; margin: 0; }
.key-panel details summary { margin-bottom: 7px; cursor: pointer; color: #a5b4fc; font-size: 10px; }
.key-panel dl div { min-width: 0; }
.key-panel dt { color: #667895; font-size: 9px; }
.key-panel dd { margin: 2px 0 0; color: #c7d2fe; font-size: 11px; word-break: break-word; }
.key-panel p { margin: 0; padding: 8px; border-radius: 8px; background: rgba(15, 30, 70, .42); color: #9faec7; font-size: 10px; line-height: 1.45; }
.mini-empty { display: grid; place-items: center; min-height: 110px; border: 1px dashed rgba(129, 140, 248, .18); border-radius: 10px; color: #7183a3; font-size: 12px; }
@media (max-width: 760px) {
  .summary-row { grid-template-columns: 1fr; }
  .content { grid-template-columns: 1fr; }
  .key-panel { padding: 14px 0 0; border-top: 1px solid rgba(129, 140, 248, .12); border-left: 0; }
}
</style>
