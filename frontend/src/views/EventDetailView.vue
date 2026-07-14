<script setup>
import { computed } from 'vue'
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

const route = useRoute()
// API 预留：const { data } = await axios.get(`/api/event/detail/${route.params.id}`)
const report = computed(() => ({ ...eventDetailMock, id: route.params.id || eventDetailMock.id }))
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
        <div class="analysis-row">
          <PropagationAnalysis :data="report.propagation" />
          <div class="analysis-stack">
            <div class="analysis-pair">
              <EmotionAnalysis :data="report.emotion" />
              <PlatformDistribution :data="report.platforms" />
            </div>
            <CausalAnalysis
            :data="report.causalGraph"
            :event-id="report.id"
          />
          </div>
        </div>
        <KeywordAnalysis :data="report.keywords" />
        <RelatedNews :data="report.relatedNews" />
      </main>
      <aside class="event-aside"><AIEventAssistant :event-id="report.id" :data="report.assistant" /></aside>
    </div>
  </section>
</template>

<style scoped>
.event-detail-page { --card: rgba(11, 31, 68, .72); --line: rgba(129, 140, 248, .24); color: #e8edff; }
.event-layout { display: grid; grid-template-columns: minmax(0, 7fr) minmax(300px, 3fr); gap: 20px; align-items: start; }
.event-main { display: grid; min-width: 0; gap: 18px; }
.overview-row { display: grid; grid-template-columns: minmax(260px, 4fr) minmax(0, 6fr); gap: 18px; }
.analysis-row { display: grid; grid-template-columns: minmax(0, 6fr) minmax(330px, 4fr); gap: 18px; align-items: start; }
.analysis-stack { display: grid; grid-template-rows: auto auto; gap: 18px; align-content: start; }
.analysis-pair { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; align-items: start; }
.event-aside { position: sticky; top: 112px; height: calc(100vh - 146px); }
@media (max-width: 1250px) { .analysis-row { grid-template-columns: 1fr; } }
@media (max-width: 1100px) { .event-layout { grid-template-columns: 1fr; } .event-aside { position: static; height: 560px; } }
@media (max-width: 800px) { .overview-row { grid-template-columns: 1fr; } }
@media (max-width: 680px) { .event-layout, .event-main { gap: 14px; } .analysis-pair { grid-template-columns: 1fr; gap: 14px; } }
</style>
