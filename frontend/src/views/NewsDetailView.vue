<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { errorMessage } from '../api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const news = ref(null)
const loading = ref(true)
const actionLoading = ref(false)
const error = ref('')
const paragraphs = computed(() => news.value?.content?.split(/\n+/).filter(Boolean) || [])

function formatDate(value) {
  return value ? new Intl.DateTimeFormat('zh-CN', { dateStyle: 'long', timeStyle: 'short' }).format(new Date(value)) : '时间未知'
}

async function load() {
  try {
    const { data } = await api.get(`/news/${route.params.id}`)
    news.value = data
  } catch (err) {
    error.value = errorMessage(err, '新闻不存在或已下线')
  } finally {
    loading.value = false
  }
}

async function toggleFavorite() {
  if (!auth.isLoggedIn) return router.push({ name: 'login', query: { redirect: route.fullPath } })
  actionLoading.value = true
  try {
    if (news.value.is_favorite) await api.delete(`/news/${news.value.id}/favorite`)
    else await api.post(`/news/${news.value.id}/favorite`)
    news.value.is_favorite = !news.value.is_favorite
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    actionLoading.value = false
  }
}

async function generateSummary() {
  if (!auth.isLoggedIn) return router.push({ name: 'login', query: { redirect: route.fullPath } })
  actionLoading.value = true
  error.value = ''
  try {
    const { data } = await api.post(`/news/${news.value.id}/ai-summary`)
    news.value = data
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    actionLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="detail-wrap shell">
    <div v-if="loading" class="state-block"><div class="loader"></div><p>正在打开新闻…</p></div>
    <div v-else-if="!news" class="state-block error-state"><strong>无法打开这篇新闻</strong><p>{{ error }}</p><RouterLink class="button" to="/">返回首页</RouterLink></div>
    <template v-else>
      <button class="back-link" @click="router.back()">← 返回新闻流</button>
      <article class="article-layout">
        <div class="article-main">
          <div class="article-kicker"><span>{{ news.category }}</span><i></i>{{ news.source_name }}</div>
          <h1>{{ news.title }}</h1>
          <div class="article-meta">
            <span>{{ formatDate(news.published_at || news.crawled_at) }}</span>
            <span>{{ news.source_author || '新浪新闻' }}</span>
            <span>{{ news.click_count }} 次阅读</span>
          </div>
          <div v-if="news.image_url" class="article-image"><img :src="news.image_url" :alt="news.title" /></div>
          <div v-if="news.ai_summary" class="ai-brief">
            <div><span>AI</span><strong>智能摘要</strong><small>由大语言模型提炼</small></div>
            <p>{{ news.ai_summary }}</p>
          </div>
          <div class="article-content">
            <p v-for="(paragraph, index) in paragraphs" :key="index">{{ paragraph }}</p>
          </div>
          <p class="source-note">本文内容采集自新浪新闻，版权归原作者及原媒体所有。</p>
        </div>
        <aside class="article-sidebar">
          <div class="action-card">
            <span class="eyebrow dark">READING TOOLS</span>
            <h3>阅读助手</h3>
            <button class="button wide" :disabled="actionLoading" @click="generateSummary">✦ {{ news.ai_summary ? '重新生成摘要' : '生成 AI 摘要' }}</button>
            <button class="outline-button wide" :disabled="actionLoading" @click="toggleFavorite">{{ news.is_favorite ? '★ 已收藏' : '☆ 收藏文章' }}</button>
            <a class="outline-button wide" :href="news.source_url" target="_blank" rel="noopener">查看新浪原文 ↗</a>
            <p v-if="error" class="inline-error">{{ error }}</p>
          </div>
          <div class="sidebar-note"><i></i><p>登录后浏览记录会自动保存，并用于生成更贴合兴趣的推荐。</p></div>
        </aside>
      </article>
    </template>
  </section>
</template>

