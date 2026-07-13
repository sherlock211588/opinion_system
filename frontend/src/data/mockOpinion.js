export const overviewCards = [
  {
    label: '今日热点数量',
    value: 128,
    suffix: '个',
    trend: '+18%',
    desc: '较昨日新增 23 个事件',
  },
  {
    label: '当前热度指数',
    value: 8560,
    suffix: '',
    trend: '+12.6%',
    desc: '全网讨论持续升温',
  },
  {
    label: '整体情感趋势',
    value: 72,
    suffix: '%',
    trend: '偏正向',
    desc: '正向与中立观点占主导',
  },
  {
    label: '数据来源数量',
    value: 36,
    suffix: '类',
    trend: '+5',
    desc: '新闻、社交与内容平台',
  },
]

export const hotEvents = [
  {
    id: 'ev',
    title: '某新能源汽车事件',
    summary: '围绕智能驾驶、售后沟通与品牌回应的讨论持续发酵。',
    heat: 9820,
    source: '微博 / 新闻 / 小红书',
    time: '12 分钟前',
    sentiment: '争议上升',
    sentimentType: 'risk',
    tags: ['新能源', '智能驾驶', '品牌回应'],
  },
  {
    id: 'city',
    title: '城市文旅活动带动周末消费',
    summary: '本地生活、短视频和攻略社区形成传播合力。',
    heat: 8754,
    source: '抖音 / 今日头条',
    time: '28 分钟前',
    sentiment: '正向增强',
    sentimentType: 'positive',
    tags: ['文旅', '消费', '城市品牌'],
  },
  {
    id: 'ai-phone',
    title: 'AI 手机新品发布引发功能讨论',
    summary: '用户关注端侧模型能力、隐私保护和续航表现。',
    heat: 7938,
    source: '科技媒体 / 社区',
    time: '43 分钟前',
    sentiment: '中性观察',
    sentimentType: 'neutral',
    tags: ['AI硬件', '隐私', '体验'],
  },
  {
    id: 'edu',
    title: '高校毕业季就业服务话题升温',
    summary: '政策解读、岗位质量和城市吸引力成为讨论焦点。',
    heat: 7216,
    source: '新闻 / 问答社区',
    time: '1 小时前',
    sentiment: '关注提升',
    sentimentType: 'neutral',
    tags: ['就业', '高校', '政策'],
  },
]

export const trendData = {
  hours: ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'],
  values: [3200, 4600, 5200, 6800, 7400, 8560, 9100],
}

export const sentimentData = [
  { value: 42, name: '正面' },
  { value: 36, name: '中立' },
  { value: 22, name: '负面' },
]

export const keywords = [
  'AI总结',
  '新能源',
  '售后回应',
  '用户体验',
  '智能驾驶',
  '情绪变化',
  '媒体报道',
  '事件进展',
  '品牌信任',
  '公开说明',
]

export const detailEvent = {
  id: 'ev',
  title: '某新能源汽车事件',
  intro:
    '该事件从用户体验反馈开始，经社交平台扩散后被科技媒体与财经媒体跟进，公众讨论集中在智能驾驶边界、售后响应效率与品牌沟通方式。',
  time: '2026-07-09 09:30',
  range: '微博、小红书、今日头条、科技媒体与本地社区',
  impact: '影响范围覆盖 12 个核心平台，相关讨论约 18.6 万条',
  causes: ['产品体验反馈被集中转发', '售后沟通信息不对称', '媒体二次报道扩大影响'],
  attitudes: ['用户希望获得清晰解释', '中立群体关注事实进展', '品牌支持者期待正式回应'],
  forecast: ['未来 24 小时仍将保持较高关注', '若官方回应充分，负面占比有望下降', '技术边界与用户教育会继续成为讨论点'],
}

export const eventHeatTrend = {
  hours: ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
  values: [800, 1600, 3400, 5200, 6300, 7600, 8900, 9820],
}

export const eventSentiment = [
  { value: 28, name: '正面' },
  { value: 34, name: '中立' },
  { value: 38, name: '负面' },
]

export const wordCloudItems = [
  { word: '智能驾驶', size: 'large' },
  { word: '售后回应', size: 'medium' },
  { word: '用户体验', size: 'large' },
  { word: '安全边界', size: 'medium' },
  { word: '品牌信任', size: 'small' },
  { word: '媒体报道', size: 'small' },
  { word: '公开说明', size: 'medium' },
  { word: '技术争议', size: 'small' },
]

export const communityPosts = [
  {
    author: '林夏',
    title: '如何判断一次热点是不是会持续发酵？',
    content: '我通常会看跨平台传播速度、核心关键词变化和情绪拐点，单一平台热度不一定代表真正扩散。',
    likes: 286,
    replies: 34,
  },
  {
    author: 'Data Rae',
    title: 'AI 总结适合放在事件详情页哪个位置？',
    content: '建议放在趋势和情感之后，用户先看到证据，再看到总结，会更容易建立信任。',
    likes: 198,
    replies: 21,
  },
  {
    author: '南风',
    title: '今天文旅话题的正向情绪很明显',
    content: '短视频平台的体验分享贡献了大量正向内容，新闻端则负责放大活动信息。',
    likes: 143,
    replies: 16,
  },
]
