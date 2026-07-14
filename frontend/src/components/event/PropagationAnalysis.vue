<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue'
import { GraphChart } from 'echarts/charts'
import {
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import { init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

use([
  GraphChart,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
])

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
})

const chartRef = ref(null)

let chartInstance = null
let resizeObserver = null

const emptyText = '--'
const chartLoading = false
const chartError = false

const MAX_KEY_NODES = 5
const MAX_GRAPH_NODES = 16

const qualityMap = {
  full: '完整',
  basic: '基础',
  minimal: '有限',
  sparse: '稀疏',
}

const roleColors = {
  origin: '#f43f5e',
  source: '#f43f5e',
  initial_source: '#f43f5e',
  media: '#38bdf8',
  news: '#38bdf8',
  creator: '#8b5cf6',
  influencer: '#8b5cf6',
  public: '#22d3ee',
  user: '#22d3ee',
  official: '#34d399',
  government: '#34d399',
  account: '#818cf8',
  unknown: '#818cf8',
}

const roleNames = {
  origin: '初始信息源',
  source: '初始信息源',
  initial_source: '初始信息源',
  media: '媒体节点',
  news: '媒体节点',
  creator: '内容创作者',
  influencer: '影响力账号',
  public: '普通用户',
  user: '普通用户',
  official: '官方账号',
  government: '官方账号',
  account: '传播账号',
  unknown: '传播节点',
}

const hasValue = (value) =>
  value !== undefined &&
  value !== null &&
  value !== ''

const valueOrEmpty = (value) =>
  hasValue(value) ? value : emptyText

const toNumber = (value) => {
  if (!hasValue(value)) return null

  const number = Number(value)

  return Number.isFinite(number)
    ? number
    : null
}

const clamp = (value, min, max) =>
  Math.max(min, Math.min(max, value))

function normalizeId(value) {
  if (!hasValue(value)) return ''

  if (typeof value === 'object') {
    return String(
      value.id ??
        value.node_id ??
        value.account_id ??
        value.name ??
        value.label ??
        '',
    )
  }

  return String(value)
}

function nodeId(node, index = 0) {
  return normalizeId(
    node?.id ??
      node?.node_id ??
      node?.account_id ??
      node?.uid ??
      node?.name ??
      node?.account_name ??
      `node-${index + 1}`,
  )
}

function nodeName(node) {
  return valueOrEmpty(
    node?.account_name ??
      node?.name ??
      node?.label ??
      node?.title ??
      node?.username ??
      node?.id ??
      node?.node_id,
  )
}

function normalizedRole(node) {
  return String(
    node?.role ??
      node?.type ??
      node?.category ??
      node?.node_type ??
      'account',
  )
    .trim()
    .toLowerCase()
}

function roleLabel(node) {
  const explicitLabel =
    node?.role_label ??
    node?.type_label ??
    node?.category_label

  if (hasValue(explicitLabel)) {
    return explicitLabel
  }

  const role = normalizedRole(node)

  return roleNames[role] ?? valueOrEmpty(role)
}

function influenceOf(node) {
  return (
    toNumber(
      node?.influence ??
        node?.influence_score ??
        node?.composite_score ??
        node?.importance ??
        node?.score ??
        node?.pagerank ??
        node?.page_rank,
    ) ?? 0
  )
}

function pagerankOf(node) {
  return (
    toNumber(
      node?.pagerank ??
        node?.page_rank ??
        node?.pageRank,
    ) ?? 0
  )
}

function betweennessOf(node) {
  return (
    toNumber(
      node?.betweenness_centrality ??
        node?.betweenness ??
        node?.centrality,
    ) ?? 0
  )
}

function outDegreeOf(node) {
  return (
    toNumber(
      node?.out_degree_score ??
        node?.out_degree ??
        node?.degree ??
        node?.connections,
    ) ?? 0
  )
}

function isSourceNode(node) {
  if (
    node?.is_initial_source === true ||
    node?.is_source === true ||
    node?.is_origin === true ||
    node?.root === true
  ) {
    return true
  }

  const role = normalizedRole(node)

  return [
    'origin',
    'source',
    'initial_source',
    '初始信息源',
    '首发',
    '源节点',
  ].includes(role)
}

function colorOf(node) {
  return (
    roleColors[normalizedRole(node)] ??
    roleColors.account
  )
}

const graphSource = computed(() => {
  const data = props.data ?? {}

  return (
    data.graph ??
    data.network ??
    data.propagation_graph ??
    data.propagationGraph ??
    {}
  )
})

const rawNodes = computed(() => {
  const data = props.data ?? {}
  const graph = graphSource.value

  const source =
    graph.nodes ??
    graph.data ??
    data.nodes ??
    data.propagation_nodes ??
    data.propagationNodes ??
    data.accounts ??
    []

  return Array.isArray(source)
    ? source
    : []
})

const rawLinks = computed(() => {
  const data = props.data ?? {}
  const graph = graphSource.value

  const source =
    graph.links ??
    graph.edges ??
    data.links ??
    data.edges ??
    data.propagation_links ??
    data.propagation_edges ??
    []

  return Array.isArray(source)
    ? source
    : []
})

const rawCategories = computed(() => {
  const graph = graphSource.value

  const source =
    graph.categories ??
    props.data?.categories ??
    []

  return Array.isArray(source)
    ? source
    : []
})

const normalizedNodes = computed(() => {
  const seen = new Set()

  return rawNodes.value
    .map((node, index) => {
      const id = nodeId(node, index)

      if (!id || seen.has(id)) {
        return null
      }

      seen.add(id)

      return {
        ...node,
        id,
        __id: id,
        __name: nodeName(node),
        __role: normalizedRole(node),
        __influence: influenceOf(node),
        __pagerank: pagerankOf(node),
        __betweenness: betweennessOf(node),
        __outDegree: outDegreeOf(node),
        __source: isSourceNode(node),
      }
    })
    .filter(Boolean)
})

const nodeMap = computed(() => {
  const map = new Map()

  normalizedNodes.value.forEach((node) => {
    map.set(node.__id, node)
    map.set(String(node.__name), node)
  })

  return map
})

const normalizedLinks = computed(() => {
  return rawLinks.value
    .map((link, index) => {
      const sourceId = normalizeId(
        link?.source ??
          link?.from ??
          link?.source_id ??
          link?.sourceId ??
          link?.parent,
      )

      const targetId = normalizeId(
        link?.target ??
          link?.to ??
          link?.target_id ??
          link?.targetId ??
          link?.child,
      )

      const sourceNode =
        nodeMap.value.get(sourceId)

      const targetNode =
        nodeMap.value.get(targetId)

      if (!sourceNode || !targetNode) {
        return null
      }

      return {
        id:
          link?.id ??
          `edge-${index + 1}`,
        source: sourceNode.__id,
        target: targetNode.__id,
        value:
          toNumber(
            link?.value ??
              link?.weight ??
              link?.strength ??
              link?.count,
          ) ?? 1,
        raw: link,
      }
    })
    .filter(Boolean)
})

const connectionStats = computed(() => {
  const stats = new Map()

  normalizedNodes.value.forEach((node) => {
    stats.set(node.__id, {
      inDegree: 0,
      outDegree: 0,
      total: 0,
    })
  })

  normalizedLinks.value.forEach((link) => {
    const source =
      stats.get(link.source)

    const target =
      stats.get(link.target)

    if (source) {
      source.outDegree += 1
      source.total += 1
    }

    if (target) {
      target.inDegree += 1
      target.total += 1
    }
  })

  return stats
})

function autoKeyScore(node) {
  const connections =
    connectionStats.value.get(node.__id)?.total ?? 0

  const sourceBonus =
    node.__source ? 1000 : 0

  return (
    sourceBonus +
    node.__influence * 10 +
    node.__pagerank * 100 +
    node.__betweenness * 50 +
    node.__outDegree * 5 +
    connections * 8
  )
}

const providedKeyNodes = computed(() => {
  const source =
    props.data?.key_nodes ??
    props.data?.keyNodes ??
    props.data?.important_nodes ??
    props.data?.top_nodes ??
    []

  if (!Array.isArray(source)) {
    return []
  }

  return source
    .map((item, index) => {
      if (
        typeof item === 'string' ||
        typeof item === 'number'
      ) {
        const matched =
          nodeMap.value.get(String(item))

        return (
          matched ?? {
            id: String(item),
            __id: String(item),
            __name: String(item),
            __role: 'account',
            __influence: 0,
            __pagerank: 0,
            __betweenness: 0,
            __outDegree: 0,
            __source: false,
          }
        )
      }

      const id = nodeId(item, index)
      const matched =
        nodeMap.value.get(id) ??
        nodeMap.value.get(nodeName(item))

      if (matched) {
        return {
          ...matched,
          ...item,
          __id: matched.__id,
          __name:
            nodeName(item) !== emptyText
              ? nodeName(item)
              : matched.__name,
          __role: normalizedRole({
            ...matched,
            ...item,
          }),
          __influence:
            influenceOf(item) ||
            matched.__influence,
          __pagerank:
            pagerankOf(item) ||
            matched.__pagerank,
          __betweenness:
            betweennessOf(item) ||
            matched.__betweenness,
          __outDegree:
            outDegreeOf(item) ||
            matched.__outDegree,
          __source:
            isSourceNode(item) ||
            matched.__source,
        }
      }

      return {
        ...item,
        id,
        __id: id,
        __name: nodeName(item),
        __role: normalizedRole(item),
        __influence: influenceOf(item),
        __pagerank: pagerankOf(item),
        __betweenness: betweennessOf(item),
        __outDegree: outDegreeOf(item),
        __source: isSourceNode(item),
      }
    })
    .filter((node) => node.__id)
})

const keyNodes = computed(() => {
  const source = providedKeyNodes.value.length
    ? providedKeyNodes.value
    : [...normalizedNodes.value].sort(
        (a, b) =>
          autoKeyScore(b) -
          autoKeyScore(a),
      )

  const seen = new Set()

  return source
    .filter((node) => {
      if (seen.has(node.__id)) {
        return false
      }

      seen.add(node.__id)
      return true
    })
    .slice(0, MAX_KEY_NODES)
})

const keyNodeIds = computed(
  () => new Set(
    keyNodes.value.map(
      (node) => node.__id,
    ),
  ),
)

const visibleGraphNodes = computed(() => {
  if (
    normalizedNodes.value.length <=
    MAX_GRAPH_NODES
  ) {
    return normalizedNodes.value
  }

  const selectedIds =
    new Set(keyNodeIds.value)

  normalizedLinks.value.forEach((link) => {
    if (selectedIds.has(link.source)) {
      selectedIds.add(link.target)
    }

    if (selectedIds.has(link.target)) {
      selectedIds.add(link.source)
    }
  })

  const selected =
    normalizedNodes.value.filter((node) =>
      selectedIds.has(node.__id),
    )

  if (
    selected.length >= MAX_GRAPH_NODES
  ) {
    return selected.slice(
      0,
      MAX_GRAPH_NODES,
    )
  }

  const remaining =
    normalizedNodes.value
      .filter(
        (node) =>
          !selectedIds.has(node.__id),
      )
      .sort(
        (a, b) =>
          autoKeyScore(b) -
          autoKeyScore(a),
      )

  return [
    ...selected,
    ...remaining.slice(
      0,
      MAX_GRAPH_NODES -
        selected.length,
    ),
  ]
})

const visibleNodeIds = computed(
  () => new Set(
    visibleGraphNodes.value.map(
      (node) => node.__id,
    ),
  ),
)

const visibleGraphLinks = computed(() =>
  normalizedLinks.value.filter(
    (link) =>
      visibleNodeIds.value.has(
        link.source,
      ) &&
      visibleNodeIds.value.has(
        link.target,
      ),
  ),
)

const normalizedCategories = computed(() => {
  const names = new Set()

  rawCategories.value.forEach((item) => {
    const name =
      typeof item === 'string'
        ? item
        : item?.name

    if (name) {
      names.add(String(name))
    }
  })

  visibleGraphNodes.value.forEach(
    (node) => {
      names.add(node.__role)
    },
  )

  return Array.from(names).map(
    (name) => ({
      name,
      itemStyle: {
        color:
          roleColors[name] ??
          roleColors.account,
      },
    }),
  )
})

const influenceRange = computed(() => {
  const values =
    visibleGraphNodes.value.map(
      (node) => node.__influence,
    )

  if (!values.length) {
    return {
      min: 0,
      max: 1,
    }
  }

  return {
    min: Math.min(...values),
    max: Math.max(...values),
  }
})

function nodeSize(node) {
  const { min, max } =
    influenceRange.value

  if (max === min) {
    return node.__source ? 48 : 32
  }

  const ratio =
    (node.__influence - min) /
    (max - min)

  const base =
    24 + ratio * 28

  return node.__source
    ? Math.max(base, 48)
    : clamp(base, 24, 52)
}

const chartNodes = computed(() =>
  visibleGraphNodes.value.map((node) => {
    const keyNode =
      keyNodeIds.value.has(node.__id)

    return {
      id: node.__id,
      name: node.__name,
      value: node.__influence,
      category: node.__role,
      symbolSize: nodeSize(node),
      draggable: true,
      raw: node,
      itemStyle: {
        color: colorOf(node),
        borderColor:
          node.__source
            ? '#ffffff'
            : keyNode
              ? '#c4b5fd'
              : 'rgba(255,255,255,.4)',
        borderWidth:
          node.__source
            ? 3
            : keyNode
              ? 2
              : 1,
        shadowBlur:
          node.__source
            ? 24
            : keyNode
              ? 18
              : 10,
        shadowColor:
          node.__source
            ? 'rgba(244,63,94,.8)'
            : 'rgba(99,102,241,.48)',
      },
      label: {
        show:
          node.__source ||
          keyNode,
        color: '#e8edff',
        fontSize: 10,
        fontWeight:
          keyNode ? 700 : 500,
      },
    }
  }),
)

const chartLinks = computed(() =>
  visibleGraphLinks.value.map((link) => ({
    source: link.source,
    target: link.target,
    value: link.value,
    raw: link.raw,
    lineStyle: {
      width: clamp(
        1 + Number(link.value) * 0.3,
        1,
        4,
      ),
    },
  })),
)

const hasPropagationData = computed(
  () => chartNodes.value.length > 0,
)

const nodeCount = computed(
  () => normalizedNodes.value.length,
)

const edgeCount = computed(
  () => normalizedLinks.value.length,
)

const dataQuality = computed(() => {
  const raw =
    props.data?.data_quality ??
    props.data?.dataQuality

  if (
    raw &&
    typeof raw === 'object'
  ) {
    return JSON.stringify(raw)
  }

  const quality =
    String(raw ?? '')
      .trim()
      .toLowerCase()

  return (
    qualityMap[quality] ??
    valueOrEmpty(raw)
  )
})

const summary = computed(() =>
  valueOrEmpty(
    props.data?.propagation_summary ??
      props.data?.summary,
  ),
)

const description = computed(() =>
  valueOrEmpty(
    props.data?.propagation_description ??
      props.data?.description,
  ),
)

const propagationDepth = computed(() =>
  valueOrEmpty(
    props.data?.propagation_depth ??
      props.data?.depth ??
      props.data?.max_depth,
  ),
)

const chartOption = computed(() => ({
  backgroundColor: 'transparent',

  tooltip: {
    trigger: 'item',
    confine: true,
    backgroundColor:
      'rgba(15,23,42,.96)',
    borderColor:
      'rgba(129,140,248,.35)',
    borderWidth: 1,
    padding: 10,
    textStyle: {
      color: '#e8edff',
      fontSize: 12,
    },
    formatter: (params) => {
      if (params.dataType === 'edge') {
        const source =
          nodeMap.value.get(
            params.data.source,
          )

        const target =
          nodeMap.value.get(
            params.data.target,
          )

        return [
          '<strong>传播关系</strong>',
          `${source?.__name ?? params.data.source}`,
          '↓',
          `${target?.__name ?? params.data.target}`,
        ].join('<br/>')
      }

      const node =
        params.data.raw ?? {}

      const stats =
        connectionStats.value.get(
          node.__id,
        )

      return [
        `<strong>${node.__name}</strong>`,
        `角色：${roleLabel(node)}`,
        `影响力：${valueOrEmpty(node.__influence)}`,
        `连接节点：${valueOrEmpty(stats?.total)}`,
        node.__source
          ? '节点属性：初始传播源'
          : '',
      ]
        .filter(Boolean)
        .join('<br/>')
    },
  },

  legend: {
    show:
      normalizedCategories.value.length >
      1,
    bottom: 4,
    left: 'center',
    itemWidth: 10,
    itemHeight: 10,
    textStyle: {
      color: '#94a3b8',
      fontSize: 10,
    },
    formatter: (name) =>
      roleNames[name] ?? name,
  },

  series: [
    {
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      animationDuration: 500,
      animationDurationUpdate: 500,

      data: chartNodes.value,
      links: chartLinks.value,
      categories:
        normalizedCategories.value,

      force: {
        repulsion: 260,
        edgeLength: [70, 150],
        gravity: 0.08,
        friction: 0.55,
        layoutAnimation: true,
      },

      label: {
        show: false,
        position: 'right',
        distance: 6,
        color: '#c7d2fe',
        fontSize: 10,
        overflow: 'truncate',
        width: 90,
      },

      edgeSymbol: [
        'none',
        chartLinks.value.length
          ? 'arrow'
          : 'none',
      ],

      edgeSymbolSize: [0, 7],

      lineStyle: {
        color:
          'rgba(96,165,250,.55)',
        curveness: 0.16,
        opacity: 0.72,
      },

      emphasis: {
        focus: 'adjacency',
        scale: true,
        label: {
          show: true,
          color: '#ffffff',
        },
        lineStyle: {
          width: 3,
          opacity: 1,
        },
      },
    },
  ],
}))

const counterfactualList = computed(() => {
  const source =
    props.data?.counterfactual

  if (Array.isArray(source)) {
    return source
  }

  if (
    source &&
    typeof source === 'object'
  ) {
    return Object.entries(source).map(
      ([key, value]) => ({
        account_name: key,
        ...(value &&
        typeof value === 'object'
          ? value
          : { value }),
      }),
    )
  }

  return []
})

function counterfactualText(node) {
  const match =
    counterfactualList.value.find(
      (item) => {
        const itemName =
          item.account_name ??
          item.name ??
          item.node_name

        const itemId =
          item.node_id ??
          item.id

        return (
          String(itemName ?? '') ===
            String(node.__name ?? '') ||
          String(itemId ?? '') ===
            String(node.__id ?? '')
        )
      },
    )

  const reduction =
    match?.reduction_rate ??
    match?.expected_reduction ??
    match?.scale_reduction ??
    match?.reduced_percent

  if (!hasValue(reduction)) {
    return '该节点被识别为关键传播节点。'
  }

  const value =
    typeof reduction === 'number' &&
    reduction <= 1
      ? `${(
          reduction * 100
        ).toFixed(1)}%`
      : String(reduction).includes('%')
        ? reduction
        : `${reduction}%`

  return `移除该节点后，传播规模预计减少 ${value}。`
}

function renderChart() {
  if (
    !chartRef.value ||
    !hasPropagationData.value
  ) {
    return
  }

  if (!chartInstance) {
    chartInstance = init(
      chartRef.value,
    )
  }

  chartInstance.setOption(
    chartOption.value,
    true,
  )

  nextTick(() => {
    chartInstance?.resize()
  })
}

onMounted(() => {
  renderChart()

  if (chartRef.value) {
    resizeObserver =
      new ResizeObserver(() => {
        chartInstance?.resize()
      })

    resizeObserver.observe(
      chartRef.value,
    )
  }
})

watch(
  chartOption,
  () => {
    renderChart()
  },
  {
    deep: true,
  },
)

watch(
  hasPropagationData,
  (available) => {
    if (available) {
      nextTick(renderChart)
      return
    }

    chartInstance?.dispose()
    chartInstance = null
  },
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<template>
  <section class="card">
    <div class="title">
      <div>
        <h2>传播溯源分析</h2>
        <p>展示事件传播中的核心账号及扩散关系</p>
      </div>

      <span>关键节点传播图</span>
    </div>

    <div
      v-if="chartLoading"
      class="empty-state"
    >
      传播图加载中...
    </div>

    <div
      v-else-if="chartError"
      class="empty-state"
    >
      传播图加载失败，请稍后重试。
    </div>

    <div
      v-else-if="!hasPropagationData"
      class="empty-state"
    >
      <strong>
        当前事件暂无传播节点数据
      </strong>

      <span>
        后端需要提供 nodes
        或 propagation_nodes
      </span>

      <em>数据状态：待补充</em>
    </div>

    <template v-else>
      <div class="summary-row">
        <div>
          <small>节点总数</small>
          <strong>{{ nodeCount }}</strong>
        </div>

        <div>
          <small>传播关系数</small>
          <strong>{{ edgeCount }}</strong>
        </div>

        <div>
          <small>传播深度</small>
          <strong>
            {{ propagationDepth }}
          </strong>
        </div>

        <div>
          <small>数据完整性</small>
          <strong>{{ dataQuality }}</strong>
        </div>
      </div>

      <p
        v-if="summary !== emptyText"
        class="summary-text"
      >
        {{ summary }}
      </p>

      <p
        v-if="description !== emptyText"
        class="description-text"
      >
        {{ description }}
      </p>

      <div class="content">
        <div class="graph-panel">
          <div class="graph-heading">
            <div>
              <strong>传播路径图</strong>
              <span>
                当前显示关键节点及其相关节点
              </span>
            </div>

            <em>
              显示
              {{ visibleGraphNodes.length }}
              /
              {{ nodeCount }}
              个节点
            </em>
          </div>

          <div
            ref="chartRef"
            class="graph-chart"
          ></div>

          <p class="chart-note">
            节点越大表示影响力越高；拖动节点可调整布局，滚轮可缩放传播图。
          </p>
        </div>

        <div class="key-panel">
          <div class="key-title">
            <div>
              <h3>关键传播节点 Top 5</h3>
              <p>
                根据影响力、中心性和连接关系综合筛选
              </p>
            </div>
          </div>

          <div
            v-if="!keyNodes.length"
            class="mini-empty"
          >
            暂无关键节点数据
          </div>

          <ol v-else>
            <li
              v-for="node in keyNodes"
              :key="node.__id"
            >
              <div class="node-head">
                <div class="node-name">
                  <span
                    class="node-dot"
                    :style="{
                      backgroundColor:
                        colorOf(node),
                    }"
                  ></span>

                  <b>{{ node.__name }}</b>
                </div>

                <span>
                  {{ roleLabel(node) }}
                </span>
              </div>

              <div class="node-score">
                <div>
                  <small>影响力</small>
                  <strong>
                    {{
                      valueOrEmpty(
                        node.__influence,
                      )
                    }}
                  </strong>
                </div>

                <div>
                  <small>连接数</small>
                  <strong>
                    {{
                      valueOrEmpty(
                        connectionStats.get(
                          node.__id,
                        )?.total,
                      )
                    }}
                  </strong>
                </div>
              </div>

              <details>
                <summary>
                  查看详细指标
                </summary>

                <dl>
                  <div>
                    <dt>PageRank</dt>
                    <dd>
                      {{
                        valueOrEmpty(
                          node.__pagerank,
                        )
                      }}
                    </dd>
                  </div>

                  <div>
                    <dt>介数中心性</dt>
                    <dd>
                      {{
                        valueOrEmpty(
                          node.__betweenness,
                        )
                      }}
                    </dd>
                  </div>

                  <div>
                    <dt>出度得分</dt>
                    <dd>
                      {{
                        valueOrEmpty(
                          node.__outDegree,
                        )
                      }}
                    </dd>
                  </div>

                  <div>
                    <dt>综合得分</dt>
                    <dd>
                      {{
                        valueOrEmpty(
                          node.composite_score ??
                            node.score ??
                            autoKeyScore(node),
                        )
                      }}
                    </dd>
                  </div>
                </dl>
              </details>

              <p>
                {{ counterfactualText(node) }}
              </p>
            </li>
          </ol>
        </div>
      </div>
    </template>
  </section>
</template>
<style scoped>
.card {
  padding: 22px;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: var(--card);
  color: #e8edff;
  backdrop-filter: blur(18px);
}

.title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.title > div {
  min-width: 0;
}

.title h2 {
  margin: 0;
  color: #fff;
  font-size: 18px;
}

.title p {
  margin: 6px 0 0;
  color: #7183a3;
  font-size: 11px;
  line-height: 1.5;
}

.title > span {
  flex: 0 0 auto;
  padding: 4px 9px;
  border-radius: 99px;
  background: rgba(99, 102, 241, 0.1);
  color: #94a3b8;
  font-size: 10px;
}

.empty-state {
  display: grid;
  place-items: center;
  min-height: 240px;
  margin-top: 16px;
  padding: 24px;
  border: 1px dashed rgba(129, 140, 248, 0.2);
  border-radius: 14px;
  color: #9faec7;
  font-size: 13px;
  text-align: center;
}

.empty-state strong,
.empty-state span,
.empty-state em {
  display: block;
}

.empty-state strong {
  color: #c7d2fe;
  font-size: 14px;
  font-style: normal;
}

.empty-state span {
  margin-top: 7px;
  color: #7183a3;
}

.empty-state em {
  margin-top: 8px;
  color: #7dd3fc;
  font-size: 12px;
  font-style: normal;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.summary-row > div {
  min-width: 0;
  padding: 11px 12px;
  border-radius: 11px;
  background: rgba(99, 102, 241, 0.08);
}

.summary-row small {
  display: block;
  color: #7183a3;
  font-size: 10px;
}

.summary-row strong {
  display: block;
  overflow: hidden;
  margin-top: 5px;
  color: #38bdf8;
  font-size: 19px;
  line-height: 1.2;
  text-overflow: ellipsis;
  word-break: break-word;
}

.summary-text,
.description-text {
  margin: 10px 0 0;
  color: #c7d2fe;
  font-size: 12px;
  line-height: 1.6;
}

.description-text {
  color: #9faec7;
}

.content {
  display: grid;
  grid-template-columns:
    minmax(0, 1fr)
    minmax(250px, 300px);
  gap: 18px;
  min-height: 440px;
  margin-top: 16px;
}

.graph-panel {
  position: relative;
  min-width: 0;
  min-height: 440px;
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.16);
  border-radius: 15px;
  background:
    radial-gradient(
      circle at center,
      rgba(99, 102, 241, 0.13),
      transparent 62%
    ),
    rgba(8, 24, 55, 0.2);
}

.graph-heading {
  position: absolute;
  z-index: 2;
  top: 14px;
  right: 14px;
  left: 14px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  pointer-events: none;
}

.graph-heading > div {
  min-width: 0;
}

.graph-heading strong {
  display: block;
  color: #dbeafe;
  font-size: 12px;
}

.graph-heading span {
  display: block;
  margin-top: 4px;
  color: #7183a3;
  font-size: 10px;
}

.graph-heading em {
  flex: 0 0 auto;
  padding: 4px 8px;
  border-radius: 99px;
  background: rgba(56, 189, 248, 0.09);
  color: #7dd3fc;
  font-size: 10px;
  font-style: normal;
}

.graph-chart {
  width: 100%;
  height: 440px;
}

.chart-note {
  position: absolute;
  right: 14px;
  bottom: 10px;
  left: 14px;
  margin: 0;
  color: #7183a3;
  font-size: 10px;
  line-height: 1.45;
  pointer-events: none;
}

.key-panel {
  min-width: 0;
  padding-left: 17px;
  border-left: 1px solid rgba(129, 140, 248, 0.14);
}

.key-title {
  margin-bottom: 12px;
}

.key-title h3 {
  margin: 0;
  color: #c7d2fe;
  font-size: 13px;
}

.key-title p {
  margin: 5px 0 0;
  color: #7183a3;
  font-size: 10px;
  line-height: 1.45;
}

.key-panel ol {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
  counter-reset: rank;
}

.key-panel li {
  display: grid;
  gap: 9px;
  padding: 11px;
  border: 1px solid rgba(129, 140, 248, 0.1);
  border-radius: 11px;
  background: rgba(99, 102, 241, 0.08);
  counter-increment: rank;
}

.node-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.node-name {
  display: flex;
  min-width: 0;
  gap: 7px;
  align-items: center;
}

.node-name::before {
  flex: 0 0 auto;
  color: #818cf8;
  font-size: 12px;
  font-weight: 700;
  content: counter(rank);
}

.node-dot {
  flex: 0 0 auto;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
}

.node-head b {
  min-width: 0;
  overflow: hidden;
  color: #e0e7ff;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-head > span {
  flex: 0 0 auto;
  padding: 3px 7px;
  border-radius: 99px;
  background: rgba(56, 189, 248, 0.12);
  color: #7dd3fc;
  font-size: 9px;
}

.node-score {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
}

.node-score > div {
  min-width: 0;
  padding: 7px 8px;
  border-radius: 8px;
  background: rgba(15, 30, 70, 0.48);
}

.node-score small {
  display: block;
  color: #667895;
  font-size: 9px;
}

.node-score strong {
  display: block;
  overflow: hidden;
  margin-top: 3px;
  color: #bae6fd;
  font-size: 12px;
  text-overflow: ellipsis;
}

.key-panel details summary {
  cursor: pointer;
  color: #a5b4fc;
  font-size: 10px;
}

.key-panel dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
  margin: 8px 0 0;
}

.key-panel dl div {
  min-width: 0;
}

.key-panel dt {
  color: #667895;
  font-size: 9px;
}

.key-panel dd {
  margin: 2px 0 0;
  color: #c7d2fe;
  font-size: 11px;
  word-break: break-word;
}

.key-panel li > p {
  margin: 0;
  padding: 8px;
  border-radius: 8px;
  background: rgba(15, 30, 70, 0.44);
  color: #9faec7;
  font-size: 10px;
  line-height: 1.5;
}

.mini-empty {
  display: grid;
  place-items: center;
  min-height: 140px;
  border: 1px dashed rgba(129, 140, 248, 0.18);
  border-radius: 10px;
  color: #7183a3;
  font-size: 12px;
}

@media (max-width: 1050px) {
  .summary-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .content {
    grid-template-columns: minmax(0, 1fr) 260px;
  }
}

@media (max-width: 760px) {
  .title {
    flex-direction: column;
  }

  .summary-row {
    grid-template-columns: 1fr;
  }

  .content {
    grid-template-columns: 1fr;
  }

  .key-panel {
    padding: 15px 0 0;
    border-top: 1px solid rgba(129, 140, 248, 0.14);
    border-left: 0;
  }

  .graph-panel,
  .graph-chart {
    min-height: 390px;
    height: 390px;
  }
}
</style>
