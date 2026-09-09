import { defineStore } from 'pinia'
import api from '../api'

function readUser() {
  try {
    return JSON.parse(localStorage.getItem('ai-news-user') || 'null')
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('ai-news-token'),
    user: readUser(),
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    isAdmin: (state) => Boolean(state.user?.is_admin),
  },
  actions: {
    saveSession(data) {
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('ai-news-token', this.token)
      localStorage.setItem('ai-news-user', JSON.stringify(this.user))
    },
    async login(username, password) {
      const form = new URLSearchParams({ username, password })
      const { data } = await api.post('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      this.saveSession(data)
    },
    async register(payload) {
      await api.post('/auth/register', payload)
      await this.login(payload.username, payload.password)
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('ai-news-token')
      localStorage.removeItem('ai-news-user')
    },
  },
})

