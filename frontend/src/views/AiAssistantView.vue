<template>
  <section class="ai-page">
    <aside class="prompt-panel">
      <span>AI Assistant</span>
      <h1>AI 智能问答</h1>
      <p>输入你想了解的舆情事件，AI 将基于 mock 舆情数据给出摘要、情绪判断和后续建议。</p>

      <div class="suggestions">
        <button v-for="item in suggestions" :key="item" @click="message = item">
          {{ item }}
        </button>
      </div>
    </aside>

    <section class="chat-panel">
      <div class="messages">
        <article class="message ai">
          <strong>舆见 AI</strong>
          <p>你好，我可以帮你总结事件原因、公众态度、传播路径和未来趋势。</p>
        </article>
        <article class="message user">
          <strong>你</strong>
          <p>分析一下某新能源汽车事件的情绪风险。</p>
        </article>
        <article class="message ai">
          <strong>舆见 AI</strong>
          <p>
            当前风险主要来自售后回应不充分与智能驾驶边界争议。建议优先关注官方回应质量、媒体二次传播和负面关键词是否继续上升。
          </p>
        </article>
      </div>

      <div class="composer">
        <input v-model="message" placeholder="请输入你想了解的舆情事件" @keyup.enter="sendMock" />
        <button @click="sendMock">发送</button>
      </div>
    </section>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const message = ref('')
const suggestions = ['总结某新能源汽车事件', '分析今天的正向热点', '找出负面情绪最高的话题']

function sendMock() {
  if (!message.value.trim()) return
  window.alert(`已收到问题：${message.value}。后续可在这里接入大模型接口。`)
  message.value = ''
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
