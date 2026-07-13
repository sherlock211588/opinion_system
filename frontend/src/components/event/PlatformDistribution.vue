<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: [Array, Object],
    default: null,
  },
  propagation: {
    type: Object,
    default: null,
  },
})

const chartLoading = false
const chartError = false
const hasValue = (value) => value !== undefined && value !== null && value !== ''
const toNumber = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}
const normalizePlatformDistribution = (source) => {
  if (Array.isArray(source)) {
    return source
      .map((item) => ({
        name: item.name ?? item.platform ?? item.source,
        value: toNumber(item.value ?? item.percent ?? item.percentage ?? item.count),
      }))
      .filter((item) => hasValue(item.name) && item.value !== null)
  }
  if (source && typeof source === 'object') {
    return Object.entries(source)
      .map(([name, value]) => ({
        name,
        value: toNumber(typeof value === 'object' ? value.value ?? value.percent ?? value.percentage ?? value.count : value),
      }))
      .filter((item) => hasValue(item.name) && item.value !== null)
  }
  return []
}
const backendItems = computed(() => normalizePlatformDistribution(props.data))
const sourceNodes = computed(() => {
  const nodes = props.propagation?.graph?.nodes
  if (!Array.isArray(nodes)) return []
  const counts = nodes.reduce((result, node) => {
    const source = node.source ?? node.platform_source
    if (!hasValue(source)) return result
    result[source] = (result[source] || 0) + 1
    return result
  }, {})
  return Object.entries(counts).map(([name, value]) => ({ name, value }))
})
const items = computed(() => (backendItems.value.length ? backendItems.value : sourceNodes.value))
const isNodeSourceOverview = computed(() => !backendItems.value.length && sourceNodes.value.length > 0)
const hasData = computed(() => items.value.length > 0)
const total = computed(() => items.value.reduce((sum, item) => sum + item.value, 0))
const displayItems = computed(() => {
  if (!hasData.value) return []
  return items.value.map((item) => {
    const width = total.value ? (item.value / total.value) * 100 : 0
    const display = backendItems.value.length ? `${item.value}%` : `${item.value} 个节点`
    return { ...item, width, display }
  })
})
</script>

<template>
  <section class="card">
    <h2>{{ isNodeSourceOverview ? '传播节点来源概况' : '平台分布' }}</h2>
    <div v-if="chartLoading" class="empty-state">图表加载中...</div>
    <div v-else-if="chartError" class="empty-state">图表加载失败，请稍后重试。</div>
    <div v-else-if="!hasData" class="empty-state">
      <strong>暂无平台来源统计数据</strong>
      <span>需要平台来源字段后才能生成分布图</span>
      <em>数据状态：待补充</em>
    </div>
    <template v-else>
      <div class="bars">
        <div v-for="item in displayItems" :key="item.name" :title="`${item.name}：${item.display}`">
          <div>
            <span>{{ item.name }}</span>
            <strong>{{ item.display }}</strong>
          </div>
          <i><b :style="{ width: item.width + '%' }"></b></i>
        </div>
      </div>
      <p v-if="isNodeSourceOverview" class="source-note">该数据表示传播节点来源，不代表全部新闻平台报道占比。</p>
    </template>
  </section>
</template>

<style scoped>
.card { padding: 22px; border: 1px solid var(--line); border-radius: 20px; background: var(--card); backdrop-filter: blur(18px); }
h2 { margin: 0 0 20px; color: #fff; font-size: 18px; }
.bars { display: grid; gap: 15px; }
.bars div div { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 6px; color: #9baac3; font-size: 12px; }
.bars span { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bars strong { flex: 0 0 auto; color: #c7d2fe; }
.bars i { display: block; height: 7px; border-radius: 99px; background: rgba(99, 102, 241, .12); overflow: hidden; }
.bars b { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #8b5cf6, #22d3ee); box-shadow: 0 0 10px rgba(56, 189, 248, .35); }
.source-note { margin: 14px 0 0; color: #9faec7; font-size: 11px; line-height: 1.5; }
.empty-state { display: grid; place-items: center; min-height: 150px; border: 1px dashed rgba(129, 140, 248, .2); border-radius: 12px; color: #7183a3; font-size: 12px; line-height: 1.6; text-align: center; }
.empty-state strong, .empty-state span, .empty-state em { display: block; }
.empty-state strong { color: #c7d2fe; font-size: 14px; font-style: normal; }
.empty-state em { color: #7dd3fc; font-size: 12px; font-style: normal; }
</style>
