<script setup>
defineProps({
  news: { type: Object, required: true },
  meta: { type: String, default: '' },
})

function formatDate(value) {
  if (!value) return '时间未知'
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <article class="news-card">
    <RouterLink :to="`/news/${news.id}`" class="card-media" :class="{ placeholder: !news.image_url }">
      <img v-if="news.image_url" :src="news.image_url" :alt="news.title" loading="lazy" />
      <span v-else>NEWS<br />WIRE</span>
      <em>{{ news.category }}</em>
    </RouterLink>
    <div class="card-body">
      <div class="card-meta">
        <span>{{ formatDate(news.published_at || news.crawled_at) }}</span>
        <span>{{ news.click_count }} 次阅读</span>
      </div>
      <RouterLink :to="`/news/${news.id}`" class="card-title">{{ news.title }}</RouterLink>
      <p>{{ news.ai_summary || news.description || news.content.slice(0, 90) }}</p>
      <div class="card-footer">
        <span>{{ meta || news.source_author || news.source_name }}</span>
        <RouterLink :to="`/news/${news.id}`">阅读全文 <b>→</b></RouterLink>
      </div>
    </div>
  </article>
</template>

