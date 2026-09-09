<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()
const mobileOpen = ref(false)
const displayName = computed(() => auth.user?.full_name || auth.user?.username || '访客')

function logout() {
  auth.logout()
  mobileOpen.value = false
  router.push('/')
}
</script>

<template>
  <header class="topbar">
    <div class="shell nav-shell">
      <RouterLink to="/" class="brand" @click="mobileOpen = false">
        <span class="brand-mark">AI</span>
        <span><strong>掘金头条</strong><small>NEWS INTELLIGENCE</small></span>
      </RouterLink>
      <button class="menu-button" aria-label="展开菜单" @click="mobileOpen = !mobileOpen">☰</button>
      <nav :class="['main-nav', { open: mobileOpen }]">
        <RouterLink to="/" @click="mobileOpen = false">新闻广场</RouterLink>
        <RouterLink v-if="auth.isLoggedIn" to="/favorites" @click="mobileOpen = false">我的收藏</RouterLink>
        <RouterLink v-if="auth.isLoggedIn" to="/history" @click="mobileOpen = false">浏览历史</RouterLink>
        <RouterLink v-if="auth.isAdmin" to="/admin" @click="mobileOpen = false">采集管理</RouterLink>
      </nav>
      <div class="account-actions">
        <template v-if="auth.isLoggedIn">
          <span class="user-chip"><i></i>{{ displayName }}</span>
          <button class="text-button" @click="logout">退出</button>
        </template>
        <template v-else>
          <RouterLink class="text-button" to="/login">登录</RouterLink>
          <RouterLink class="button compact" to="/register">注册</RouterLink>
        </template>
      </div>
    </div>
  </header>

  <main>
    <RouterView />
  </main>

  <footer class="footer">
    <div class="shell footer-inner">
      <div>
        <strong>AI掘金头条</strong>
        <p>新浪新闻增量采集 · 智能摘要 · 个性化阅读</p>
      </div>
      <a href="/docs" target="_blank">API 文档 ↗</a>
    </div>
  </footer>
</template>

