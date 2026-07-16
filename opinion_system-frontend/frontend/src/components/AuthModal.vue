<template>
  <div v-if="loginPrompt.visible" class="modal-mask" @click.self="closeModal">
    <div class="modal-box" role="dialog" aria-modal="true" :aria-label="loginPrompt.title">
      <button class="close-btn" type="button" @click="closeModal">×</button>

      <h2>{{ loginPrompt.title }}</h2>
      <p>{{ loginPrompt.subtitle }}</p>

      <input
        v-model="username"
        placeholder="用户名"
        autocomplete="username"
        @keyup.enter="handleSubmit"
      />

      <input
        v-model="password"
        type="password"
        autocomplete="current-password"
        placeholder="请输入密码"
        @keyup.enter="handleSubmit"
      />

      <p v-if="loginError" class="login-error">{{ loginError }}</p>

      <button
        class="submit-btn ripple-btn"
        type="button"
        :disabled="isSubmitting"
        @click="handleSubmit"
      >
        <span>{{ submitText }}</span>
      </button>

      <div class="switch" @click="changeMode">
        {{ loginPrompt.mode === 'login' ? '没有账号？立即注册' : '已有账号？立即登录' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLoginPromptStore } from '@/stores/loginPrompt'

const router = useRouter()
const authStore = useAuthStore()
const loginPrompt = useLoginPromptStore()

const username = ref('')
const password = ref('')
const loginError = ref('')
const isSubmitting = ref(false)

const submitText = computed(() => {
  if (isSubmitting.value) return '登录中...'
  return loginPrompt.mode === 'login' ? '登录' : '注册'
})

watch(
  () => loginPrompt.visible,
  (visible) => {
    if (visible) {
      loginError.value = ''
      password.value = ''
    }
  },
)

function closeModal() {
  loginPrompt.close()
}

function changeMode() {
  loginPrompt.toggleMode()
  loginError.value = ''
}

async function handleSubmit() {
  const account = username.value.trim()
  const secret = password.value

  loginError.value = ''

  if (!account) {
    loginError.value = 'Please enter your username'
    return
  }

  if (!secret) {
    loginError.value = 'Please enter your password'
    return
  }

  if (isSubmitting.value) {
    return
  }

  isSubmitting.value = true

  try {
    if (loginPrompt.mode === 'register') {
      await authStore.register({
        username: account,
        password: secret,
      })
    } else {
      await authStore.login({
        login_type: 'username',
        account,
        password: secret,
      })
    }

    const target = loginPrompt.redirect || '/home'
    closeModal()
    await router.push(target)
  } catch {
    loginError.value = authStore.error || '登录失败，请检查账号或密码'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.modal-mask {
  position:fixed;
  inset:0;
  z-index:100;
  display:flex;
  align-items:center;
  justify-content:center;
  background:
    radial-gradient(circle at 50% 42%, rgba(37,99,235,.24), transparent 32%),
    rgba(2,6,23,.62);
  backdrop-filter:blur(14px);
}

.modal-box {
  position:relative;
  width:min(400px, calc(100vw - 32px));
  padding:45px;
  border:1px solid rgba(255,255,255,.12);
  border-radius:30px;
  background:
    linear-gradient(145deg, rgba(15,30,58,.84), rgba(8,20,38,.72)),
    rgba(15,30,58,.75);
  box-shadow:0 30px 80px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.08);
  backdrop-filter:blur(25px);
  animation:pop .45s cubic-bezier(.16,1,.3,1);
}

@keyframes pop {
  from {
    opacity:0;
    transform:scale(.7);
  }

  to {
    opacity:1;
    transform:scale(1);
  }
}

.modal-box h2 {
  margin:0;
  color:#fff;
}

.modal-box p {
  color:#94a3b8;
}

.modal-box input {
  width:100%;
  height:48px;
  margin-top:18px;
  padding-left:15px;
  border:1px solid rgba(255,255,255,.12);
  border-radius:12px;
  outline:0;
  background:rgba(255,255,255,.08);
  color:#fff;
}

.modal-box input::placeholder {
  color:#94a3b8;
}

.login-error {
  margin:12px 0 0;
  color:#fca5a5;
  font-size:13px;
}

.submit-btn {
  position:relative;
  z-index:1;
  overflow:hidden;
  isolation:isolate;
  width:100%;
  height:48px;
  margin-top:25px;
  border:0;
  border-radius:35px;
  background:linear-gradient(135deg, #2563eb, #8b5cf6);
  color:white;
  cursor:pointer;
  box-shadow:0 20px 48px rgba(37,99,235,.3);
  transition:.35s;
}

.submit-btn:disabled {
  cursor:not-allowed;
  opacity:.7;
}

.submit-btn span {
  position:relative;
  z-index:3;
}

.submit-btn::before {
  content:"";
  position:absolute;
  width:10px;
  height:10px;
  left:var(--x,50%);
  top:var(--y,50%);
  z-index:0;
  border-radius:50%;
  background:radial-gradient(circle, #00d9ff, #2563eb 48%, #8b5cf6);
  transform:translate(-50%,-50%) scale(0);
  transition:transform .6s cubic-bezier(.16,1,.3,1);
}

.submit-btn:hover::before {
  transform:translate(-50%,-50%) scale(25);
}

.close-btn {
  position:absolute;
  right:20px;
  top:15px;
  border:0;
  background:none;
  color:#38bdf8;
  font-size:28px;
  cursor:pointer;
}

.switch {
  margin-top:25px;
  color:#38bdf8;
  text-align:center;
  cursor:pointer;
}
</style>
