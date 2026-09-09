<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import api, { errorMessage } from '../api'
import NewsCard from '../components/NewsCard.vue'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const rows = ref([])
const mode = computed(() => route.meta.mode)
const title = computed(() => mode.value === 'favorites' ? '我的收藏' : '浏览历史')
const subtitle = computed(() => mode.value === 'favorites' ? '随时回看你标记的重要新闻' : '沿着时间线找回最近读过的内容')

function formatMeta(row) {
  if (mode.value === 'favorites') return `收藏于 ${new Date(row.created_at).toLocaleString('zh-CN')}`
  return `最近浏览 ${new Date(row.viewed_at).toLocaleString('zh-CN')} · 共 ${row.view_count} 次`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/news/${mode.value}`)
    rows.value = data
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    loading.value = false
  }
}

watch(() => route.meta.mode, load)
onMounted(load)
</script>

<template>
  <section class="shell collection-page">
    <div class="page-title"><span class="eyebrow dark">PERSONAL NEWSROOM</span><h1>{{ title }}</h1><p>{{ subtitle }}</p></div>
    <div v-if="loading" class="state-block"><div class="loader"></div><p>正在整理内容…</p></div>
    <div v-else-if="error" class="state-block error-state"><strong>加载失败</strong><p>{{ error }}</p></div>
    <div v-else-if="!rows.length" class="state-block"><strong>这里还是空的</strong><p>去新闻广场读几篇感兴趣的内容吧。</p><RouterLink class="button" to="/">浏览新闻</RouterLink></div>
    <div v-else class="news-grid"><NewsCard v-for="row in rows" :key="row.news.id" :news="row.news" :meta="formatMeta(row)" /></div>
  </section>
</template>

