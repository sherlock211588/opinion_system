<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import EventHeader from '@/components/event/EventHeader.vue'
import EventOverview from '@/components/event/EventOverview.vue'
import LifecycleAnalysis from '@/components/event/LifecycleAnalysis.vue'
import PropagationAnalysis from '@/components/event/PropagationAnalysis.vue'
import EmotionAnalysis from '@/components/event/EmotionAnalysis.vue'
import PlatformDistribution from '@/components/event/PlatformDistribution.vue'
import CausalAnalysis from '@/components/event/CausalAnalysis.vue'
import KeywordAnalysis from '@/components/event/KeywordAnalysis.vue'
import RelatedNews from '@/components/event/RelatedNews.vue'
import AIEventAssistant from '@/components/event/AIEventAssistant.vue'
import { eventDetailMock } from '@/mock/eventData'
import { getEventArticles } from '@/api/articles'
import { fetchEventDetailWithFallback } from '@/api/events'
import { addRecentView } from '@/utils/recentViews'

const route = useRoute()
const report = ref({ ...eventDetailMock, id: route.params.id || eventDetailMock.id })

async function loadReport() {
  const eventId = route.params.id || eventDetailMock.id
  const nextReport = await fetchEventDetailWithFallback(eventId)
  const relatedNews = await getEventArticles(eventId)

  report.value = {
    ...nextReport,
    id: eventId,
    relatedNews,
  }
}

watch(
  () => route.params.id,
  () => {
    loadReport()
  },
  { immediate: true },
)

watch(
  report,
  (currentReport) => {
    if (!currentReport?.event?.title) {
      return
    }

    addRecentView({
      id: currentReport.id,
      type: 'report',
      title: currentReport.event.title,
      meta: currentReport.event.category,
      path: route.fullPath,
    })
  },
  { immediate: true },
)
</script>

<template>
  <section class="event-detail-page">
    <EventHeader :event="report.event" />
    <div class="event-layout">
      <main class="event-main">
        <div class="overview-row">
          <EventOverview :overview="report.overview" :event="report.event" />
          <LifecycleAnalysis :data="report.lifecycle" />
        </div>
        <div class="analysis-grid">
          <PropagationAnalysis :data="report.propagation" />
          <div class="analysis-pair">
            <EmotionAnalysis :data="report.sentiment_distribution ?? report.emotion?.sentiment_distribution ?? report.emotion" />
            <PlatformDistribution :data="report.platform_distribution" :propagation="report.propagation" />
          </div>
          <KeywordAnalysis :data="report.keywords" />
          <CausalAnalysis
            :data="{
              transfer_entropy_pairs: report.transfer_entropy_pairs,
              granger_pairs: report.granger_pairs,
              all_lag_pvalues: report.all_lag_pvalues,
            }"
          />
        </div>
        <RelatedNews :data="report.relatedNews" :event-id="report.id" />
      </main>
      <aside class="event-aside"><AIEventAssistant :event-id="report.id" :data="report.assistant" /></aside>
    </div>
  </section>
</template>

<style scoped>
.event-detail-page {
  --card: rgba(11, 31, 68, .72);
  --line: rgba(129, 140, 248, .24);
  --analysis-card-padding: 22px 24px;
  --analysis-card-radius: 20px;
  --analysis-title-height: 28px;
  color: #e8edff;
}

.event-layout {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(300px, 3fr);
  gap: 20px;
  align-items: start;
}

.event-main {
  display: grid;
  min-width: 0;
  gap: 20px;
}

.overview-row,
.analysis-grid,
.analysis-pair {
  display: grid;
  gap: 20px;
  min-width: 0;
  align-items: stretch;
}

.overview-row {
  grid-template-columns: minmax(260px, 4fr) minmax(0, 6fr);
}

.analysis-grid {
  grid-template-columns: 1fr;
}

.analysis-pair {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.event-aside {
  position: sticky;
  top: 112px;
}

.event-main > *,
.overview-row > *,
.analysis-grid > *,
.analysis-pair > * {
  min-width: 0;
  box-sizing: border-box;
}

.overview-row > *,
.analysis-pair > * {
  height: 100%;
}

.event-detail-page :deep(.card),
.event-detail-page :deep(.assistant) {
  min-width: 0;
  box-sizing: border-box;
}

.event-detail-page :deep(.assistant) {
  height: 100%;
}

.event-detail-page :deep(.card) {
  display: grid;
  align-content: start;
  overflow: hidden;
}

.analysis-grid :deep(.card) {
  height: auto;
  padding: var(--analysis-card-padding);
  border: 1px solid var(--line);
  border-radius: var(--analysis-card-radius);
}

.analysis-pair :deep(.card) {
  height: 100%;
}

.event-detail-page :deep(.card > h2),
.event-detail-page :deep(.title),
.event-detail-page :deep(.section-title) {
  min-width: 0;
}

.analysis-grid :deep(.card > h2),
.analysis-grid :deep(.title),
.analysis-grid :deep(.section-title) {
  min-height: var(--analysis-title-height);
  margin: 0;
  align-items: center;
}

.analysis-grid :deep(.card > h2),
.analysis-grid :deep(.title h2),
.analysis-grid :deep(.section-title h2) {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.25;
}

.event-detail-page :deep(.title h2),
.event-detail-page :deep(.title span),
.event-detail-page :deep(.section-title h2),
.event-detail-page :deep(.card > h2),
.event-detail-page :deep(.chart-note),
.event-detail-page :deep(.summary-text),
.event-detail-page :deep(.description-text),
.event-detail-page :deep(.source-note),
.event-detail-page :deep(.relation-card p),
.event-detail-page :deep(.lag-chart p) {
  overflow-wrap: anywhere;
}

.event-detail-page :deep(.content),
.event-detail-page :deep(.keyword-content),
.event-detail-page :deep(.emotion-content),
.event-detail-page :deep(.bars),
.event-detail-page :deep(.relation-row),
.event-detail-page :deep(.lag-chart),
.event-detail-page :deep(.graph-panel),
.event-detail-page :deep(.cloud-panel),
.event-detail-page :deep(.ranking-panel) {
  min-width: 0;
  box-sizing: border-box;
}

.event-detail-page :deep(.content) {
  grid-template-columns: minmax(0, 1fr) minmax(220px, 280px);
  gap: 20px;
  min-height: 0;
}

.analysis-grid :deep(.empty-state) {
  display: grid;
  min-height: 190px;
  margin-top: 16px;
  padding: 20px;
  place-items: center;
  border: 1px dashed rgba(129, 140, 248, .22);
  border-radius: 14px;
  color: #9faec7;
  font-size: 13px;
  line-height: 1.6;
  text-align: center;
}

.analysis-pair :deep(.emotion-card),
.analysis-pair :deep(.card) {
  grid-template-rows: var(--analysis-title-height) minmax(0, 280px) auto;
}

.analysis-pair :deep(.emotion-content),
.analysis-pair :deep(.bars),
.analysis-pair :deep(.empty-state) {
  min-height: 280px;
  height: 280px;
  margin-top: 16px;
}

.analysis-pair :deep(.emotion-content) {
  padding-top: 0;
}

.analysis-pair :deep(.bars) {
  align-content: center;
}

.event-detail-page :deep(.graph-panel) {
  display: grid;
  min-height: 0;
  overflow: hidden;
}

.event-detail-page :deep(.graph-chart) {
  min-height: 280px;
}

.analysis-grid :deep(.content) {
  min-height: 340px;
}

.analysis-grid :deep(.graph-panel),
.analysis-grid :deep(.graph-chart) {
  min-height: 340px;
  height: 340px;
}

.analysis-grid :deep(.keyword-card) {
  min-height: 300px;
}

.analysis-grid :deep(.keyword-content) {
  grid-template-columns: minmax(240px, 38fr) minmax(0, 62fr);
  min-height: 230px;
  margin-top: 14px;
}

.analysis-grid :deep(.ranking-panel span) {
  overflow: visible;
  text-overflow: clip;
  white-space: normal;
  word-break: break-word;
}

.analysis-grid :deep(.word-cloud) {
  height: 220px;
}

.event-detail-page :deep(.word-cloud) {
  width: 100%;
  max-width: 100%;
}

.event-detail-page :deep(.word-cloud span) {
  max-width: 90%;
  overflow-wrap: anywhere;
  white-space: normal;
}

.event-detail-page :deep(.relation-row) {
  grid-auto-flow: row;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  overflow-x: visible;
}

.event-detail-page :deep(.relation-card),
.event-detail-page :deep(.relation-card dl div),
.event-detail-page :deep(.bars > div) {
  min-width: 0;
}

@media (max-width: 1100px) {
  .event-layout {
    grid-template-columns: 1fr;
  }

  .event-aside {
    position: static;
  }
}

@media (max-width: 800px) {
  .overview-row,
  .analysis-pair {
    grid-template-columns: 1fr;
  }

  .event-detail-page :deep(.content),
  .event-detail-page :deep(.keyword-content),
  .event-detail-page :deep(.relation-row) {
    grid-template-columns: 1fr;
  }
}
</style>
