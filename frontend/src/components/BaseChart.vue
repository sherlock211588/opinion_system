<template>
  <div ref="chartRef" class="base-chart"></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { init, use } from 'echarts/core'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
})

const chartRef = ref(null)
let chartInstance
let resizeObserver

function renderChart() {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = init(chartRef.value)
  }

  chartInstance.setOption(props.option, true)
}

onMounted(() => {
  renderChart()
  resizeObserver = new ResizeObserver(() => chartInstance?.resize())
  resizeObserver.observe(chartRef.value)
})

watch(
  () => props.option,
  () => renderChart(),
  { deep: true },
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chartInstance?.dispose()
})
</script>

<style scoped>
.base-chart {
  width: 100%;
  height: 100%;
  min-height: 260px;
}
</style>
