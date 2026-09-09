<script setup>
import { onMounted, reactive, ref } from 'vue'
import api, { errorMessage } from '../api'
import NewsCard from '../components/NewsCard.vue'

const loading = ref(true)
const error = ref('')
const data = reactive({ items: [], total: 0, page: 1, pages: 1 })
const stats = reactive({ news_count: 0, category_count: 0, total_views: 0, user_count: 0 })
const categories = ref([])
const filters = reactive({ keyword: '', category: '', sort: 'latest', page: 1, page_size: 12 })

async function loadNews() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get('/news', { params: { ...filters, keyword: filters.keyword || undefined, category: filters.category || undefined } })
    Object.assign(data, response.data)
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    loading.value = false
  }
}

function search() {
  filters.page = 1
  loadNews()
}

function selectCategory(category) {
  filters.category = category
  search()
}

function goPage(page) {
  if (page < 1 || page > data.pages) return
  filters.page = page
  loadNews()
  window.scrollTo({ top: 420, behavior: 'smooth' })
}

onMounted(async () => {
  const [statsResult, categoriesResult] = await Promise.allSettled([
    api.get('/news/stats'), api.get('/news/categories'),
  ])
  if (statsResult.status === 'fulfilled') Object.assign(stats, statsResult.value.data)
  if (categoriesResult.status === 'fulfilled') categories.value = categoriesResult.value.data
  await loadNews()
})
</script>

<template>
  <section class="hero">
    <div class="shell hero-grid">
      <div class="hero-copy">
        <span class="eyebrow">SINA NEWS · AI BRIEFING</span>
        <h1>看见正在发生的事<br /><i>读懂新闻背后的重点</i></h1>
        <p>持续采集新浪新闻，由 AI 提炼核心信息，让每一次阅读都更清晰、更高效。</p>
        <form class="hero-search" @submit.prevent="search">
          <span>⌕</span>
          <input v-model.trim="filters.keyword" placeholder="搜索标题或正文关键词" />
          <button type="submit">搜索新闻</button>
        </form>
      </div>
      <div class="hero-panel">
        <div class="signal"><span></span>实时数据流</div>
        <div class="stat-main"><strong>{{ stats.news_count }}</strong><small>已收录新闻</small></div>
        <div class="stat-row">
          <div><strong>{{ stats.category_count }}</strong><span>内容分类</span></div>
          <div><strong>{{ stats.total_views }}</strong><span>累计阅读</span></div>
          <div><strong>{{ stats.user_count }}</strong><span>注册读者</span></div>
        </div>
        <div class="pulse-lines"><i></i><i></i><i></i><i></i><i></i><i></i></div>
      </div>
    </div>
  </section>

  <section class="shell content-section">
    <div class="section-heading">
      <div><span class="eyebrow dark">LATEST INTELLIGENCE</span><h2>新闻情报流</h2></div>
      <div class="sort-tabs">
        <button :class="{ active: filters.sort === 'latest' }" @click="filters.sort = 'latest'; search()">最新发布</button>
        <button :class="{ active: filters.sort === 'hot' }" @click="filters.sort = 'hot'; search()">热门阅读</button>
      </div>
    </div>
    <div class="category-row">
      <button :class="{ active: !filters.category }" @click="selectCategory('')">全部</button>
      <button v-for="category in categories" :key="category" :class="{ active: filters.category === category }" @click="selectCategory(category)">{{ category }}</button>
    </div>

    <div v-if="loading" class="state-block"><div class="loader"></div><p>正在汇集新闻流…</p></div>
    <div v-else-if="error" class="state-block error-state"><strong>加载失败</strong><p>{{ error }}</p><button class="button" @click="loadNews">重新加载</button></div>
    <div v-else-if="!data.items.length" class="state-block"><strong>暂无匹配新闻</strong><p>管理员可以在采集管理页立即运行新浪新闻爬虫。</p></div>
    <div v-else class="news-grid">
      <NewsCard v-for="item in data.items" :key="item.id" :news="item" />
    </div>

    <div v-if="data.pages > 1" class="pagination">
      <button :disabled="data.page <= 1" @click="goPage(data.page - 1)">上一页</button>
      <span>第 <b>{{ data.page }}</b> / {{ data.pages }} 页 · 共 {{ data.total }} 条</span>
      <button :disabled="data.page >= data.pages" @click="goPage(data.page + 1)">下一页</button>
    </div>
  </section>
</template>

