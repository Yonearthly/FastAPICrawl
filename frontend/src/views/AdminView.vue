<script setup>
import { onMounted, reactive, ref } from 'vue'
import api, { errorMessage } from '../api'

const runs = ref([])
const scheduler = reactive({ enabled: false, running: false, interval_minutes: 0, next_run_at: null })
const loading = ref(true)
const running = ref(false)
const message = ref('')
const error = ref('')

function formatDate(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '—'
}

async function load() {
  try {
    const [runResult, schedulerResult] = await Promise.all([api.get('/crawler/runs'), api.get('/crawler/scheduler')])
    runs.value = runResult.data
    Object.assign(scheduler, schedulerResult.data)
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    loading.value = false
  }
}

async function trigger() {
  running.value = true
  error.value = ''
  message.value = '正在访问新浪新闻并筛选未抓取链接，请稍候…'
  try {
    const { data } = await api.post('/crawler/run')
    message.value = `采集完成：发现 ${data.discovered_count} 条，新增 ${data.new_count} 条，跳过 ${data.skipped_count} 条，失败 ${data.failed_count} 条。`
    await load()
  } catch (err) {
    error.value = errorMessage(err, '采集任务执行失败')
    message.value = ''
  } finally {
    running.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="shell admin-page">
    <div class="page-title admin-title"><div><span class="eyebrow dark">INGESTION CONTROL</span><h1>新浪新闻采集管理</h1><p>查看定时器状态、手动触发增量抓取并审计每次运行结果。</p></div><button class="button" :disabled="running" @click="trigger">{{ running ? '采集中…' : '▶ 立即采集' }}</button></div>
    <p v-if="message" class="status-message">{{ message }}</p>
    <p v-if="error" class="inline-error">{{ error }}</p>
    <div class="admin-metrics">
      <div><span>调度器</span><strong :class="scheduler.running ? 'ok' : 'muted'">{{ scheduler.running ? '运行中' : '未运行' }}</strong></div>
      <div><span>定时采集</span><strong>{{ scheduler.enabled ? '已启用' : '已停用' }}</strong></div>
      <div><span>执行间隔</span><strong>{{ scheduler.interval_minutes }} 分钟</strong></div>
      <div><span>下次执行</span><strong>{{ formatDate(scheduler.next_run_at) }}</strong></div>
    </div>
    <div class="runs-panel">
      <div class="panel-heading"><h2>运行记录</h2><span>URL 指纹预检 + 数据库唯一索引</span></div>
      <div v-if="loading" class="state-block compact-state"><div class="loader"></div></div>
      <div v-else class="table-scroll">
        <table>
          <thead><tr><th>开始时间</th><th>触发方式</th><th>状态</th><th>发现</th><th>新增</th><th>跳过</th><th>失败</th><th>耗时</th></tr></thead>
          <tbody>
            <tr v-for="run in runs" :key="run.id">
              <td>{{ formatDate(run.started_at) }}</td><td>{{ run.trigger === 'manual' ? '手动' : '定时' }}</td>
              <td><span :class="['status-pill', run.status]">{{ run.status }}</span></td><td>{{ run.discovered_count }}</td><td>{{ run.new_count }}</td><td>{{ run.skipped_count }}</td><td>{{ run.failed_count }}</td>
              <td>{{ run.finished_at ? `${Math.max(0, Math.round((new Date(run.finished_at) - new Date(run.started_at)) / 1000))} 秒` : '运行中' }}</td>
            </tr>
            <tr v-if="!runs.length"><td colspan="8" class="empty-cell">还没有运行记录，点击“立即采集”开始。</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

