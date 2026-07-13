import axios from 'axios'

const TOKEN_KEY = 'opinion_access_token'
const USER_KEY = 'opinion_current_user'

const request = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 15000,
})

request.interceptors.request.use(
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

let redirectingToLogin = false

request.interceptors.response.use(
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

export default request
