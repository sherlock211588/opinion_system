import axios from 'axios'

const TOKEN_KEY = 'opinion_access_token'
const USER_KEY = 'opinion_current_user'

let redirectingToLogin = false

function createAuthInterceptors(instance) {
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem(TOKEN_KEY)

      if (token) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${token}`
      }

      return config
    },
    (error) => Promise.reject(error),
  )

  instance.interceptors.response.use(
    (response) => response.data,
    (error) => {
      if (error?.response?.status === 401) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)

        window.dispatchEvent(new CustomEvent('opinion-auth-expired'))

        const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`
        const isLoginPage = window.location.pathname === '/login'

        if (!isLoginPage && !redirectingToLogin) {
          redirectingToLogin = true
          window.location.replace(`/login?redirect=${encodeURIComponent(currentPath)}`)
        }
      }

      return Promise.reject(error)
    },
  )

  return instance
}

function createApiClient(baseURL) {
  const instance = axios.create({
    baseURL,
    timeout: 15000,
  })

  return createAuthInterceptors(instance)
}

// 3号后端 — 事件分析 / 语义搜索 / 历史筛选
export const request3 = createApiClient('http://localhost:8000/api')

// 4号后端 — 事件看板 / 传播分析 / 虚假检测 / AI问答 / 用户认证
export const request4 = createApiClient('http://localhost:8002/api')

// 默认导出 4号（向后兼容，现有 API 模块无需大改）
export default request4
