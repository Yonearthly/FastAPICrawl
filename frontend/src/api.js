import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 70000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ai-news-token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('ai-news-token')
      localStorage.removeItem('ai-news-user')
    }
    return Promise.reject(error)
  },
)

export function errorMessage(error, fallback = '请求失败，请稍后重试') {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join('；')
  return detail || fallback
}

export default api

