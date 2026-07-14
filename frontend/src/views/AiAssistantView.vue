<template>
  <section class="ai-page">
    <aside class="prompt-panel">
      <span>AI Assistant</span>
      <h1>AI 智能问答</h1>
      <p>输入你想了解的舆情事件，AI 将基于真实舆情数据给出摘要、情绪判断和后续建议。</p>

      <div class="suggestions">
        <button v-for="item in suggestions" :key="item" @click="ask(item)">
          {{ item }}
        </button>
      </div>
    </aside>

    <section class="chat-panel">
      <div class="messages" ref="msgBox">
        <article v-for="(msg, i) in messages" :key="i" class="message" :class="msg.role">
          <strong>{{ msg.role === 'assistant' ? '舆见 AI' : '你' }}</strong>
          <p>{{ msg.text }}</p>
        </article>
        <article v-if="loading" class="message ai">
          <strong>舆见 AI</strong>
          <p class="typing">正在分析...</p>
        </article>
      </div>

      <div class="composer">
        <input v-model="message" placeholder="请输入你想了解的舆情事件" @keyup.enter="send" :disabled="loading" />
        <button @click="send" :disabled="loading">{{ loading ? '...' : '发送' }}</button>
      </div>
    </section>
  </section>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { searchSimilarEvents } from '@/api/analysis'
import { request4 } from '@/api/request'

const message = ref('')
const loading = ref(false)
const msgBox = ref(null)
const suggestions = ['总结某新能源汽车事件', '分析今天的正向热点', '找出负面情绪最高的话题']

const messages = ref([
  { role: 'assistant', text: '你好，我可以帮你总结事件原因、公众态度、传播路径和未来趋势。' },
])

async function scrollToBottom() {
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}

async function callAiChat(eventId, question) {
  const payload = await request4.post('/ai/chat', {
    page_type: 'event_detail',
    event_id: eventId || '',
    question,
  })
  if (payload?.code === 200 && payload?.data?.answer) {
    return payload.data.answer
  }
  if (payload?.message) {
    return `AI 服务返回：${payload.message}`
  }
  if (payload?.data?.answer) {
    return payload.data.answer
  }
  return 'AI 暂未返回有效回答，请稍后重试。'
}

async function send() {
  const text = message.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', text })
  message.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    // Step 1: 语义搜索找到最相关的事件
    const searchResults = await searchSimilarEvents(text, 3)
    let answer = ''

    if (searchResults && searchResults.length > 0) {
      const topEvent = searchResults[0]
      // Step 2: 基于匹配事件调用 AI 对话
      answer = await callAiChat(topEvent.event_id, text)
      if (searchResults.length > 1) {
        answer += `\n\n相关事件：「${searchResults.slice(0, 3).map(e => e.event_title).join('」「')}」`
      }
    } else {
      // 无匹配事件，直接问 AI（不带事件上下文）
      answer = await callAiChat('', text)
    }

    messages.value.push({ role: 'assistant', text: answer || '未获取到分析结果，请稍后重试。' })
  } catch {
    messages.value.push({ role: 'assistant', text: 'AI 服务暂不可用，请稍后重试。' })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

function ask(preset) {
  message.value = preset
  send()
}
</script>

<style scoped>
.ai-page {
  display: grid;
  grid-template-columns: minmax(280px, 0.8fr) minmax(0, 1.5fr);
  gap: 24px;
}

.prompt-panel,
.chat-panel {
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 24px 70px rgba(93, 73, 220, 0.11);
  backdrop-filter: blur(20px);
}

.prompt-panel {
  padding: 30px;
}

.prompt-panel span {
  color: #805cff;
  font-weight: 900;
}

h1,
p {
  margin: 0;
}

h1 {
  margin-top: 10px;
  font-size: 42px;
}

.prompt-panel p {
  margin-top: 14px;
  color: #94a3b8;
  line-height: 1.8;
}

.suggestions {
  display: grid;
  gap: 12px;
  margin-top: 28px;
}

.suggestions button {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(128, 92, 255, 0.1);
  color: #5b4dd8;
  cursor: pointer;
  text-align: left;
  font-weight: 850;
  border: 0;
  font: inherit;
}

.chat-panel {
  display: grid;
  min-height: 640px;
  grid-template-rows: 1fr auto;
  padding: 24px;
}

.messages {
  display: grid;
  align-content: start;
  gap: 16px;
  overflow-y: auto;
  max-height: 520px;
}

.message {
  max-width: 78%;
  padding: 18px;
  border-radius: 24px;
}

.message strong {
  display: block;
  margin-bottom: 8px;
}

.message p {
  color: #5f697a;
  line-height: 1.75;
  white-space: pre-wrap;
}

.message.ai {
  background: rgba(128, 92, 255, 0.09);
}

.message.user {
  justify-self: end;
  background: linear-gradient(135deg, #805cff, #6d5dfb);
  color: #fff;
}

.message.user p {
  color: rgba(255, 255, 255, 0.88);
}

.typing {
  opacity: 0.6;
}

.composer {
  display: flex;
  gap: 12px;
  padding: 10px;
  border: 1px solid rgba(128, 92, 255, 0.13);
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.82);
}

.composer input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  padding: 0 12px;
}

.composer button {
  padding: 13px 20px;
  border-radius: 999px;
  background: linear-gradient(135deg, #805cff, #6d5dfb);
  color: #fff;
  cursor: pointer;
  font-weight: 900;
  border: 0;
  font: inherit;
}

.composer button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 860px) {
  .ai-page {
    grid-template-columns: 1fr;
  }
}

/* dark blue technology news theme */
.prompt-panel,
.chat-panel {
  border-color: rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(145deg, rgba(15, 30, 58, 0.84), rgba(8, 20, 38, 0.72)),
    rgba(15, 30, 58, 0.75);
  box-shadow: 0 24px 70px rgba(0, 217, 255, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.prompt-panel span {
  color: #00d9ff;
}

h1,
.message strong {
  color: #ffffff;
}

.prompt-panel p,
.message p {
  color: #94a3b8;
}

.suggestions button,
.message.ai {
  background: rgba(37, 99, 235, 0.16);
  color: #cbd5e1;
  border: 1px solid rgba(56, 189, 248, 0.16);
}

.message.user,
.composer button {
  background: linear-gradient(135deg, #2563eb, #8b5cf6);
}

.composer {
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.08);
}

.composer input {
  color: #ffffff;
}

.composer input::placeholder {
  color: #94a3b8;
}
</style>
