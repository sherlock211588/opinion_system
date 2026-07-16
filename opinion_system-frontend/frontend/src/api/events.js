import { request4 as request } from './request'
import { eventDetailMock } from '@/mock/eventData'
import { hotEvents as mockHotEvents } from '@/data/mockOpinion'
import { newsDetailPreviewArticles } from '@/mock/newsDetailMock'
import {
  normalizeTags,
  toArray,
  toNumber,
  toRatio,
  unwrapPayload,
  valueOrFallback,
} from './helpers'

const sentimentTypeMap = {
  positive: 'positive',
  neutral: 'neutral',
  negative: 'risk',
  risk: 'risk',
}

const sentimentLabelMap = {
  positive: '正面',
  neutral: '中性',
  negative: '负面',
}

function normalizeSentimentDistribution(value = {}) {
  const source =
    value &&
    typeof value === 'object' &&
    !Array.isArray(value)
      ? value
      : {}

  return {
    positive: toRatio(source.positive, 0),
    negative: toRatio(source.negative, 0),
    neutral: toRatio(source.neutral, 0),
  }
}

function parseFiniteNumber(value) {
  if (
    value === undefined ||
    value === null ||
    value === ''
  ) {
    return null
  }

  const number = Number(value)

  return Number.isFinite(number)
    ? number
    : null
}

function parseTimeValue(value) {
  if (
    value === undefined ||
    value === null
  ) {
    return null
  }

  const text = String(value).trim()

  if (!text) {
    return null
  }

  const normalizedText =
    /^\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}/.test(text)
      ? text.replace(/\s+/, 'T')
      : text

  const timestamp =
    new Date(normalizedText).getTime()

  if (!Number.isFinite(timestamp)) {
    return null
  }

  return {
    text,
    timestamp,
  }
}

function normalizeTimeseries(value = []) {
  const merged = new Map()

  toArray(value).forEach((item) => {
    const parsedTime = parseTimeValue(
      item?.time ??
        item?.date ??
        item?.timestamp ??
        item?.publish_time ??
        item?.created_at ??
        item?.updated_at,
    )

    if (!parsedTime) {
      return
    }

    const newsCount = parseFiniteNumber(
      item?.news_count ??
        item?.newsCount ??
        item?.count ??
        item?.article_count ??
        item?.related_count,
    )

    const hotScore = parseFiniteNumber(
      item?.hot_score ??
        item?.hotScore ??
        item?.heat ??
        item?.heat_index ??
        item?.score ??
        item?.value,
    )

    if (
      newsCount === null &&
      hotScore === null
    ) {
      return
    }

    const normalizedItem = {
      time: parsedTime.text,
      timestamp: parsedTime.timestamp,
      news_count: newsCount,
      hot_score: hotScore,
      positive_ratio: toRatio(
        item?.positive_ratio,
        0,
      ),
      negative_ratio: toRatio(
        item?.negative_ratio,
        0,
      ),
      neutral_ratio: toRatio(
        item?.neutral_ratio,
        0,
      ),
    }

    const existing =
      merged.get(parsedTime.timestamp)

    if (!existing) {
      merged.set(
        parsedTime.timestamp,
        normalizedItem,
      )
      return
    }

    merged.set(parsedTime.timestamp, {
      ...existing,
      time:
        normalizedItem.time ||
        existing.time,
      news_count:
        normalizedItem.news_count ??
        existing.news_count,
      hot_score:
        normalizedItem.hot_score ??
        existing.hot_score,
      positive_ratio:
        normalizedItem.positive_ratio,
      negative_ratio:
        normalizedItem.negative_ratio,
      neutral_ratio:
        normalizedItem.neutral_ratio,
    })
  })

  return Array.from(merged.values())
    .sort(
      (a, b) =>
        a.timestamp - b.timestamp,
    )
    .map(({ timestamp, ...item }) => item)
}

export function normalizeThirdEvent(
  item = {},
  index = 0,
) {
  return {
    event_id: valueOrFallback(
      item.event_id ??
        item.id ??
        item.eventId ??
        item.event_code,
      `event-${index + 1}`,
    ),

    event_title: valueOrFallback(
      item.event_title ??
        item.title ??
        item.name,
      '暂无标题',
    ),

    category: valueOrFallback(
      item.category ??
        item.field,
      '暂无分类',
    ),

    hot_score: toNumber(
      item.hot_score ??
        item.heat ??
        item.heat_index ??
        item.score,
      0,
    ),

    news_count: toNumber(
      item.news_count ??
        item.news ??
        item.article_count ??
        item.related_count,
      0,
    ),

    sentiment_distribution:
      normalizeSentimentDistribution(
        item.sentiment_distribution ??
          item.distribution,
      ),

    timeseries: normalizeTimeseries(
      item.timeseries ??
        item.time_series ??
        item.trend,
    ),
  }
}

export function getEvents(params) {
  return request.get('/events', {
    params,
  })
}

export function getEventDetail(eventId) {
  return request.get(
    `/event/${eventId}`,
  )
}

export function getCrossEvent(params) {
  return request.get('/cross-event', {
    params,
  })
}

export function normalizeEventItem(
  item = {},
  index = 0,
) {
  const thirdEvent =
    normalizeThirdEvent(item, index)

  const distribution =
    thirdEvent.sentiment_distribution

  const dominantSentiment =
    Object.entries(distribution)
      .sort(
        (a, b) =>
          b[1] - a[1],
      )[0]?.[0] ?? 'neutral'

  const rawSentimentType =
    String(
      item.sentiment_type ??
        item.sentiment_label ??
        item.sentiment ??
        '',
    ).toLowerCase()

  const sentimentType =
    item.sentimentType ??
    sentimentTypeMap[
      rawSentimentType
    ] ??
    sentimentTypeMap[
      dominantSentiment
    ] ??
    'neutral'

  return {
    raw: item,
    ...thirdEvent,

    id: thirdEvent.event_id,

    rank: String(
      item.rank ??
        index + 1,
    ).padStart(2, '0'),

    title:
      thirdEvent.event_title,

    summary: valueOrFallback(
      item.summary ??
        item.description ??
        item.intro,
      '暂无摘要',
    ),

    heat:
      thirdEvent.hot_score,

    source: valueOrFallback(
      item.source ??
        item.platform ??
        item.sources,
      '暂无来源',
    ),

    time: valueOrFallback(
      item.time ??
        item.publish_time ??
        item.created_at ??
        item.updated_at ??
        thirdEvent.timeseries[0]?.time,
      '暂无时间',
    ),

    sentiment: valueOrFallback(
      item.sentiment ??
        item.sentiment_label ??
        item.status ??
        sentimentLabelMap[
          dominantSentiment
        ],
      '暂无情感',
    ),

    sentimentType,

    tags: normalizeTags(
      item.tags ??
        item.keywords ??
        item.categories ??
        thirdEvent.category,
    ),

    stage: valueOrFallback(
      item.stage ??
        item.current_stage,
      '暂无阶段',
    ),

    sentimentRate: Number(
      (
        toRatio(
          item.sentiment_rate ??
            item.sentimentRate ??
            item.positive_rate ??
            distribution[
              dominantSentiment
            ],
          0,
        ) * 100
      ).toFixed(1),
    ),

    news:
      thirdEvent.news_count,
  }
}

export function normalizeEventsPayload(
  payload,
) {
  const data =
    unwrapPayload(payload)

  const list =
    Array.isArray(data)
      ? data
      : data?.events ??
        data?.items ??
        data?.list ??
        data?.records ??
        []

  return toArray(list).map(
    normalizeEventItem,
  )
}

export async function fetchEventsWithFallback(
  params,
) {
  try {
    const payload =
      await getEvents(params)

    const events =
      normalizeEventsPayload(payload)

    return events.length
      ? events
      : mockHotEvents.map(
          normalizeEventItem,
        )
  } catch (error) {
    console.warn(
      '事件列表接口不可用，使用本地模拟数据。',
      error,
    )

    return mockHotEvents.map(
      normalizeEventItem,
    )
  }
}

function buildLifecycleFromThirdEvent(
  thirdEvent,
) {
  const timeseries =
    toArray(
      thirdEvent?.timeseries,
    )

  const heatPoints =
    timeseries
      .filter((item) =>
        Number.isFinite(
          item.hot_score,
        ),
      )
      .map((item) => ({
        label: item.time,
        time: item.time,
        value: item.hot_score,
      }))

  const newsPoints =
    timeseries
      .filter((item) =>
        Number.isFinite(
          item.news_count,
        ),
      )
      .map((item) => ({
        label: item.time,
        time: item.time,
        value: item.news_count,
      }))

  return {
    points: heatPoints,
    heat_trend: heatPoints,
    news_trend: newsPoints,
    labels: heatPoints.map(
      (item) => item.time,
    ),
    heat:
      thirdEvent.hot_score,
    current_heat_index:
      thirdEvent.hot_score,
    current_avg_count:
      thirdEvent.news_count,
  }
}

function normalizePropagation(
  value = {},
) {
  const source =
    value &&
    typeof value === 'object' &&
    !Array.isArray(value)
      ? value
      : {}

  const graphSource =
    source.graph ??
    source.network ??
    source.propagation_graph ??
    source.propagationGraph ??
    {}

  const rawNodes =
    graphSource.nodes ??
    graphSource.data ??
    source.nodes ??
    source.propagation_nodes ??
    source.propagationNodes ??
    source.accounts ??
    []

  const rawLinks =
    graphSource.links ??
    graphSource.edges ??
    source.links ??
    source.edges ??
    source.propagation_links ??
    source.propagation_edges ??
    []

  const rawCategories =
    graphSource.categories ??
    source.categories ??
    []

  const nodes =
    toArray(rawNodes)
      .map((node, index) => {
        const id =
          valueOrFallback(
            node?.id ??
              node?.node_id ??
              node?.account_id ??
              node?.uid ??
              node?.name ??
              node?.account_name,
            `node-${index + 1}`,
          )

        return {
          ...node,

          id: String(id),

          name: valueOrFallback(
            node?.name ??
              node?.account_name ??
              node?.label ??
              node?.title ??
              node?.username,
            String(id),
          ),

          account_name:
            valueOrFallback(
              node?.account_name ??
                node?.name ??
                node?.label ??
                node?.username,
              String(id),
            ),

          role: valueOrFallback(
            node?.role ??
              node?.type ??
              node?.category ??
              node?.node_type,
            'account',
          ),

          influence: toNumber(
            node?.influence ??
              node?.influence_score ??
              node?.composite_score ??
              node?.importance ??
              node?.score ??
              node?.pagerank ??
              node?.page_rank,
            0,
          ),

          pagerank: toNumber(
            node?.pagerank ??
              node?.page_rank ??
              node?.pageRank,
            0,
          ),

          betweenness_centrality:
            toNumber(
              node?.betweenness_centrality ??
                node?.betweenness ??
                node?.centrality,
              0,
            ),

          out_degree_score:
            toNumber(
              node?.out_degree_score ??
                node?.out_degree ??
                node?.degree ??
                node?.connections,
              0,
            ),

          is_initial_source:
            node?.is_initial_source ===
              true ||
            node?.is_source === true ||
            node?.is_origin === true ||
            node?.root === true,
        }
      })
      .filter((node) => node.id)

  const nodeIds =
    new Set(
      nodes.map((node) =>
        String(node.id),
      ),
    )

  const nodeNameToId =
    new Map()

  nodes.forEach((node) => {
    nodeNameToId.set(
      String(node.id),
      String(node.id),
    )

    nodeNameToId.set(
      String(node.name),
      String(node.id),
    )

    nodeNameToId.set(
      String(node.account_name),
      String(node.id),
    )
  })

  function resolveNodeId(value) {
    let target = value

    if (
      target &&
      typeof target === 'object'
    ) {
      target =
        target.id ??
        target.node_id ??
        target.account_id ??
        target.name ??
        target.label
    }

    if (
      target === undefined ||
      target === null ||
      target === ''
    ) {
      return null
    }

    const text =
      String(target)

    if (nodeIds.has(text)) {
      return text
    }

    return (
      nodeNameToId.get(text) ??
      null
    )
  }

  const links =
    toArray(rawLinks)
      .map((link, index) => {
        const sourceId =
          resolveNodeId(
            link?.source ??
              link?.from ??
              link?.source_id ??
              link?.sourceId ??
              link?.parent,
          )

        const targetId =
          resolveNodeId(
            link?.target ??
              link?.to ??
              link?.target_id ??
              link?.targetId ??
              link?.child,
          )

        if (
          !sourceId ||
          !targetId ||
          sourceId === targetId
        ) {
          return null
        }

        return {
          ...link,

          id: valueOrFallback(
            link?.id,
            `edge-${index + 1}`,
          ),

          source: sourceId,
          target: targetId,

          value: toNumber(
            link?.value ??
              link?.weight ??
              link?.strength ??
              link?.count,
            1,
          ),

          weight: toNumber(
            link?.weight ??
              link?.value ??
              link?.strength ??
              link?.count,
            1,
          ),
        }
      })
      .filter(Boolean)

  const keyNodeSource =
    source.key_nodes ??
    source.keyNodes ??
    source.important_nodes ??
    source.top_nodes ??
    []

  const keyNodes =
    toArray(keyNodeSource)
      .map((item) => {
        if (
          typeof item === 'string' ||
          typeof item === 'number'
        ) {
          const id =
            resolveNodeId(item)

          return nodes.find(
            (node) =>
              String(node.id) ===
              String(id),
          )
        }

        const id =
          resolveNodeId(
            item?.id ??
              item?.node_id ??
              item?.account_id ??
              item?.name ??
              item?.account_name,
          )

        const matched =
          nodes.find(
            (node) =>
              String(node.id) ===
              String(id),
          )

        return matched
          ? {
              ...matched,
              ...item,
              id: matched.id,
            }
          : item
      })
      .filter(Boolean)
      .slice(0, 5)

  return {
    ...source,

    graph: {
      ...graphSource,
      nodes,
      links,
      edges: links,
      categories:
        toArray(rawCategories),
    },

    nodes,
    links,
    edges: links,
    key_nodes: keyNodes,

    propagation_depth:
      valueOrFallback(
        source.propagation_depth ??
          source.depth ??
          source.max_depth,
        '--',
      ),

    propagation_summary:
      valueOrFallback(
        source.propagation_summary ??
          source.summary,
        '',
      ),

    propagation_description:
      valueOrFallback(
        source.propagation_description ??
          source.description,
        '',
      ),

    data_quality:
      source.data_quality ??
      source.dataQuality ??
      (
        nodes.length &&
        links.length
          ? 'full'
          : nodes.length
            ? 'sparse'
            : 'minimal'
      ),
  }
}
export function mergeEventDetailWithMock(
  payload,
  eventId,
) {
  const data =
    unwrapPayload(payload)

  const source =
    data &&
    typeof data === 'object' &&
    !Array.isArray(data)
      ? data
      : {}

  const eventSource =
    source.event ??
    source.event_info ??
    source

  const normalizedItem =
    normalizeEventItem(
      eventSource,
      0,
    )

  const thirdEvent =
    normalizeThirdEvent(
      eventSource,
      0,
    )

  const lifecycleFromThird =
    buildLifecycleFromThirdEvent(
      thirdEvent,
    )

  const lifecycleSource =
    source.lifecycle ??
    source.lifecycle_analysis ??
    {}

  const propagationSource =
    source.propagation ??
    source.propagation_analysis ??
    source.propagationAnalysis ??
    source.network ??
    {}

  const normalizedPropagation =
    normalizePropagation(
      propagationSource,
    )

  const hasRealPropagation =
    normalizedPropagation.graph.nodes
      .length > 0

  return {
    ...eventDetailMock,
    ...source,
    ...thirdEvent,

    id:
      eventId ??
      thirdEvent.event_id ??
      eventDetailMock.id,

    event: {
      ...eventDetailMock.event,
      ...(source.event ?? {}),

      title:
        normalizedItem.title,

      source:
        normalizedItem.source,

      time:
        normalizedItem.time,

      category:
        thirdEvent.category,

      heat:
        normalizedItem.heat ||
        eventDetailMock.event.heat,

      stage:
        normalizedItem.stage ||
        eventDetailMock.event.stage,

      riskLevel:
        valueOrFallback(
          eventSource.riskLevel ??
            eventSource.risk_level,
          eventDetailMock.event
            .riskLevel,
        ),

      credibility:
        toNumber(
          eventSource.credibility ??
            eventSource.credibility_score,
          eventDetailMock.event
            .credibility,
        ),
    },

    overview: {
      ...eventDetailMock.overview,
      ...(source.overview ?? {}),

      summary:
        valueOrFallback(
          source.overview?.summary ??
            source.summary,
          normalizedItem.title,
        ),
    },

    lifecycle: {
      ...eventDetailMock.lifecycle,
      ...lifecycleFromThird,
      ...lifecycleSource,

      points:
        lifecycleSource.points ??
        lifecycleFromThird.points,

      heat_trend:
        lifecycleSource.heat_trend ??
        lifecycleSource.heatTrend ??
        lifecycleFromThird.heat_trend,

      news_trend:
        lifecycleSource.news_trend ??
        lifecycleSource.newsTrend ??
        lifecycleFromThird.news_trend,

      labels:
        lifecycleSource.labels ??
        lifecycleFromThird.labels,
    },

    propagation:
      hasRealPropagation
        ? {
            ...eventDetailMock.propagation,
            ...normalizedPropagation,
          }
        : {
            ...eventDetailMock.propagation,
            ...normalizedPropagation,

            graph: {
              nodes: [],
              links: [],
              edges: [],
              categories: [],
            },

            nodes: [],
            links: [],
            edges: [],
            key_nodes: [],
          },

    relatedNews:
      source.relatedNews ??
      source.related_news ??
      eventDetailMock.relatedNews,

    sentiment_distribution:
      thirdEvent.sentiment_distribution,

    assistant: {
      ...eventDetailMock.assistant,
      ...(source.assistant ?? {}),
    },
  }
}

export async function fetchEventDetailWithFallback(
  eventId,
) {
  try {
    const payload =
      await getEventDetail(eventId)

    return mergeEventDetailWithMock(
      payload,
      eventId,
    )
  } catch (error) {
    console.warn(
      '事件详情接口不可用，使用本地模拟数据。',
      error,
    )

    return {
      ...eventDetailMock,
      id:
        eventId ||
        eventDetailMock.id,
    }
  }
}

export function getMockEventArticles(
  eventId,
) {
  const filtered =
    newsDetailPreviewArticles.filter(
      (item) =>
        String(
          item.event_id ??
            item.eventId,
        ) === String(eventId),
    )

  return Promise.resolve(
    filtered.length
      ? filtered
      : newsDetailPreviewArticles,
  )
}