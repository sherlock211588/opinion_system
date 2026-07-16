<template>
  <div class="app-shell">
    <div class="shell-background" aria-hidden="true"></div>
    <GlobalHeader @open-assistant="assistantOpen = true" />

    <main class="page-content">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>

    <Transition name="assistant">
      <div v-if="assistantOpen" class="assistant-mask" @click.self="assistantOpen = false">
        <aside class="assistant-panel" role="dialog" aria-modal="true" aria-label="AI 助手">
          <header>
            <div><span>AI</span><strong>舆见 AI 助手</strong></div>
            <button type="button" aria-label="关闭 AI 助手" @click="assistantOpen = false">×</button>
          </header>

          <div ref="msgBox" class="assistant-messages">
            <div v-if="!messages.length" class="assistant-welcome">
              <i>✦</i>
              <h2>有什么可以帮你？</h2>
              <p>我可以协助分析热点事件、舆情趋势与风险信息。</p>
            </div>
            <div v-for="(m, i) in messages" :key="i" class="assistant-msg" :class="m.role">
              <strong>{{ m.role === 'assistant' ? 'AI' : '你' }}</strong>
              <p>{{ m.text }}</p>
            </div>
            <div v-if="msgLoading" class="assistant-msg assistant"><strong>AI</strong><p class="typing">•••</p></div>
          </div>

          <form @submit.prevent="sendMsg">
            <input v-model="msgInput" placeholder="输入你想了解的问题…" aria-label="向 AI 助手提问" @keyup.enter="sendMsg" :disabled="msgLoading" />
            <button type="submit" :disabled="msgLoading">{{ msgLoading ? '...' : '发送' }}</button>
          </form>
        </aside>
      </div>
    </Transition>

    <AuthModal />
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import GlobalHeader from '@/components/Header.vue'
import AuthModal from '@/components/AuthModal.vue'
import { searchSimilarEvents } from '@/api/analysis'
import { request4 } from '@/api/request'

const assistantOpen = ref(false)
const msgInput = ref('')
const msgLoading = ref(false)
const messages = ref([])
const msgBox = ref(null)

async function scrollMsgs() {
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}

async function callAiChat(eventId, question) {
  const payload = await request4.post('/ai/chat', {
    page_type: 'event_detail',
    event_id: eventId || '',
    question,
  })
  if (payload?.code === 200 && payload?.data?.answer) return payload.data.answer
  if (payload?.message) return 'AI 服务返回：' + payload.message
  return 'AI 暂未返回有效回答，请稍后重试。'
}

async function sendMsg() {
  const text = msgInput.value.trim()
  if (!text || msgLoading.value) return
  messages.value.push({ role: 'user', text })
  msgInput.value = ''
  msgLoading.value = true
  await scrollMsgs()
  try {
    const results = await searchSimilarEvents(text, 3)
    let answer
    if (results && results.length > 0 && results[0].similarity > 0.05) {
      answer = await callAiChat(results[0].event_id, text)
    } else {
      answer = await callAiChat('', text)
    }
    messages.value.push({ role: 'assistant', text: answer || '未获取到分析结果。' })
  } catch (e) {
    console.error('AI助手错误:', e)
    messages.value.push({ role: 'assistant', text: 'AI 服务暂不可用: ' + (e?.message || e?.response?.status || String(e)) })
  } finally {
    msgLoading.value = false
    await scrollMsgs()
  }
}

function openAssistant() {
  assistantOpen.value = true
}
</script>

<style scoped>
.app-shell { position:relative;min-height:100vh;background:#071326;color:#e2e8f0;font-family:Inter,"PingFang SC","Microsoft YaHei",sans-serif }.shell-background { position:fixed;inset:0;pointer-events:none;background:radial-gradient(circle at 16% 12%,rgba(37,99,235,.31),transparent 30%),radial-gradient(circle at 84% 18%,rgba(139,92,246,.25),transparent 32%),radial-gradient(circle at 50% 90%,rgba(0,217,255,.1),transparent 32%),linear-gradient(135deg,#081426 0%,#0f1e3a 52%,#081426 100%) }.shell-background::after { position:absolute;inset:0;background-image:linear-gradient(rgba(56,189,248,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(56,189,248,.06) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to bottom,rgba(0,0,0,.72),transparent 82%);content:"" }.page-content { position:relative;z-index:1;padding:34px clamp(28px,5vw,72px) 60px }
.assistant-mask { position:fixed;inset:0;z-index:80;display:flex;justify-content:flex-end;background:rgba(2,6,23,.55);backdrop-filter:blur(5px) }.assistant-panel { display:flex;width:min(430px,100%);height:100%;box-sizing:border-box;flex-direction:column;padding:24px;border-left:1px solid rgba(139,92,246,.3);background:linear-gradient(155deg,rgba(15,30,68,.98),rgba(6,18,39,.99));box-shadow:-25px 0 70px rgba(2,6,23,.45) }.assistant-panel header { display:flex;align-items:center;justify-content:space-between;padding-bottom:20px;border-bottom:1px solid rgba(129,140,248,.15) }.assistant-panel header div { display:flex;align-items:center;gap:10px }.assistant-panel header span { display:grid;width:34px;height:34px;place-items:center;border-radius:10px;background:linear-gradient(135deg,#2563eb,#a855f7);font-size:11px;font-weight:900 }.assistant-panel header strong { color:#fff }.assistant-panel header button { border:0;background:none;color:#8292af;font-size:28px;cursor:pointer }.assistant-welcome { margin:auto;text-align:center }.assistant-welcome i { display:grid;width:58px;height:58px;margin:0 auto 16px;place-items:center;border-radius:18px;background:rgba(139,92,246,.15);color:#c4b5fd;font-size:25px;font-style:normal }.assistant-welcome h2 { margin:0;color:#fff;font-size:22px }.assistant-welcome p { color:#8292af;font-size:13px;line-height:1.7 }.assistant-panel form { display:flex;gap:8px;padding:8px;border:1px solid rgba(129,140,248,.25);border-radius:14px;background:rgba(7,20,45,.72) }.assistant-panel input { min-width:0;flex:1;border:0;outline:0;background:none;color:#fff;padding:0 8px }.assistant-panel form button { padding:10px 14px;border:0;border-radius:9px;background:linear-gradient(135deg,#2563eb,#8b5cf6);color:#fff;cursor:pointer }.assistant-panel form button:disabled{opacity:.5;cursor:not-allowed}
.assistant-messages{flex:1;overflow:auto;margin:16px 0;padding-right:4px}
.assistant-msg{margin-bottom:12px;max-width:90%}.assistant-msg.assistant{align-self:flex-start}.assistant-msg.user{align-self:flex-end;margin-left:auto}.assistant-msg strong{display:block;margin-bottom:4px;color:#7183a3;font-size:10px}.assistant-msg.user strong{text-align:right}.assistant-msg p{margin:0;padding:10px 12px;border-radius:12px;color:#cbd5e1;font-size:12px;line-height:1.6;white-space:pre-wrap}.assistant-msg.assistant p{background:rgba(37,99,235,.14)}.assistant-msg.user p{background:rgba(168,85,247,.2);color:#e9d5ff}
.typing{letter-spacing:3px;opacity:.6}.page-enter-active,.page-leave-active{transition:opacity .22s,transform .22s}.page-enter-from,.page-leave-to{opacity:0;transform:translateY(8px)}.assistant-enter-active,.assistant-leave-active{transition:opacity .25s}.assistant-enter-active .assistant-panel,.assistant-leave-active .assistant-panel{transition:transform .3s}.assistant-enter-from,.assistant-leave-to{opacity:0}.assistant-enter-from .assistant-panel,.assistant-leave-to .assistant-panel{transform:translateX(100%)}
@media(max-width:680px){.page-content{padding:22px 16px 40px}}
</style>
