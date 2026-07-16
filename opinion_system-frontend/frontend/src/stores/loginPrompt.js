import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const useLoginPromptStore = defineStore('loginPrompt', () => {
  const visible = ref(false)
  const mode = ref('login')
  const redirect = ref('')
  const message = ref('')

  const title = computed(() =>
    mode.value === 'login' ? '欢迎回来' : '创建账号',
  )

  const subtitle = computed(() => {
    if (message.value) return message.value

    return mode.value === 'login'
      ? '登录以继续'
      : '注册账号，开始使用舆见'
  })

  function openLogin(options = {}) {
    mode.value = 'login'
    visible.value = true
    redirect.value = options.redirect || ''
    message.value = options.message || ''
  }

  function openRegister(options = {}) {
    mode.value = 'register'
    visible.value = true
    redirect.value = options.redirect || ''
    message.value = options.message || ''
  }

  function close() {
    visible.value = false
    message.value = ''
  }

  function toggleMode() {
    mode.value = mode.value === 'login' ? 'register' : 'login'
    message.value = ''
  }

  return {
    visible,
    mode,
    redirect,
    message,
    title,
    subtitle,
    openLogin,
    openRegister,
    close,
    toggleMode,
  }
})
