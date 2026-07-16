<script setup>
import { computed, nextTick, ref } from 'vue'
import { request4 } from '@/api/request'

const props = defineProps({
  eventId: { type: String, default: '--' },
  data: { type: Object, default: () => ({}) },
})

const question = ref('')
const messageBox = ref(null)
const loading = ref(false)
const prompts = computed(() => (Array.isArray(props.data?.prompts) ? props.data.prompts : []))
const welcome = computed(() => props.data?.welcome || '你好，我可以协助你理解当前事件。')
const messages = ref([{ id: 1, role: 'assistant', text: welcome.value }])

async function scrollToBottom() {
  await nextTick()
  if (messageBox.value) messageBox.value.scrollTop = messageBox.value.scrollHeight
}

async function send(preset) {
  const text = typeof preset === 'string' ? preset : question.value.trim()
  if (!text || loading.value) return
  messages.value.push({ id: Date.now(), role: 'user', text })
  question.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const payload = await request4.post('/ai/chat', {
      page_type: 'event_detail',
      event_id: props.eventId || '',
      question: text,
    })
    let answer = ''
    if (payload?.code === 200 && payload?.data?.answer) {
      answer = payload.data.answer
    } else if (payload?.message) {
      answer = `AI 服务返回：${payload.message}`
    } else {
      answer = 'AI 暂未返回有效回答，请稍后重试。'
    }
    messages.value.push({ id: Date.now() + 1, role: 'assistant', text: answer })
  } catch {
    messages.value.push({ id: Date.now() + 1, role: 'assistant', text: 'AI 服务暂不可用，请稍后重试。' })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}
</script>

<template>
  <section class="assistant">
    <header><i>AI</i><div><h2>AI 事件助手</h2><p>事件 ID · {{ eventId || '--' }}</p></div><span>● 在线</span></header>
    <div class="suggestions"><small>你可以问我：</small><button v-for="item in prompts" :key="item" @click="send(item)">{{ item }}</button><span v-if="!prompts.length" class="empty-tip">暂无推荐问题</span></div>
    <div ref="messageBox" class="messages"><div v-for="message in messages" :key="message.id" :class="message.role"><i v-if="message.role==='assistant'">AI</i><p>{{ message.text }}</p></div><div v-if="loading" class="assistant"><i>AI</i><p class="typing">•••</p></div></div>
    <form @submit.prevent="send"><textarea v-model="question" rows="2" placeholder="请输入您的问题…" @keydown.enter.exact.prevent="send"></textarea><button type="submit" aria-label="发送" :disabled="loading">↑</button></form>
    <small class="notice">内容由 AI 生成，仅供参考</small>
  </section>
</template>

<style scoped>
.assistant{display:flex;height:100%;box-sizing:border-box;flex-direction:column;padding:20px;border:1px solid rgba(139,92,246,.42);border-radius:22px;background:linear-gradient(150deg,rgba(17,26,69,.9),rgba(7,22,47,.86));backdrop-filter:blur(20px);box-shadow:0 20px 55px rgba(2,6,23,.3)}header{display:flex;align-items:center;gap:10px;padding-bottom:16px;border-bottom:1px solid rgba(129,140,248,.12)}header>i,.messages .assistant i{display:grid;width:34px;height:34px;place-items:center;border-radius:10px;background:linear-gradient(135deg,#6366f1,#a855f7);color:#fff;font-style:normal;font-size:11px;font-weight:800}header h2{margin:0;color:#fff;font-size:17px}header p{margin:4px 0 0;color:#7183a3;font-size:9px}header>span{margin-left:auto;color:#22d3ee;font-size:9px}.suggestions{display:grid;gap:7px;margin:16px 0}.suggestions small,.empty-tip{color:#8999b5;font-size:11px}.suggestions button{padding:9px 11px;border:1px solid rgba(99,102,241,.2);border-radius:10px;background:rgba(99,102,241,.07);color:#aebbd3;text-align:left;cursor:pointer;transition:.2s;font:inherit;font-size:11px}.suggestions button:hover{border-color:#6366f1;color:#e0e7ff}.messages{min-height:140px;flex:1;overflow:auto;padding-right:3px}.messages>div{display:flex;gap:8px;margin-bottom:12px}.messages>div.user{justify-content:flex-end}.messages .assistant{height:auto;padding:0;border:0;background:none;box-shadow:none}.messages .assistant i{flex:0 0 26px;width:26px;height:26px;border-radius:50%;font-size:8px}.messages p{max-width:86%;margin:0;padding:10px 11px;border-radius:11px;background:rgba(99,102,241,.1);color:#bdc9de;font-size:11px;line-height:1.6;white-space:pre-wrap}.messages .user p{background:rgba(168,85,247,.17);color:#e9d5ff}.typing{letter-spacing:3px}form{display:flex;align-items:flex-end;gap:8px;padding:8px;border:1px solid rgba(99,102,241,.32);border-radius:13px;background:rgba(7,22,47,.55)}textarea{min-width:0;flex:1;resize:none;border:0;outline:0;background:transparent;color:#e0e7ff;font:inherit;font-size:11px}form button{flex:0 0 32px;width:32px;height:32px;border:0;border-radius:9px;background:linear-gradient(135deg,#6366f1,#a855f7);color:#fff;cursor:pointer}form button:disabled{opacity:0.5;cursor:not-allowed}.notice{margin-top:9px;color:#526484;text-align:center;font-size:9px}
</style>
