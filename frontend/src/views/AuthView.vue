<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { errorMessage } from '../api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const error = ref('')
const isRegister = computed(() => route.name === 'register')
const form = reactive({ username: '', email: '', full_name: '', password: '' })

watch(() => route.name, () => { error.value = '' })

async function submit() {
  loading.value = true
  error.value = ''
  try {
    if (isRegister.value) await auth.register(form)
    else await auth.login(form.username, form.password)
    router.push(route.query.redirect || '/')
  } catch (err) {
    error.value = errorMessage(err, '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="auth-page">
    <div class="auth-visual">
      <span class="eyebrow">AI NEWSROOM</span>
      <h1>从海量信息中<br />找到值得关注的事</h1>
      <p>收藏重要新闻、同步浏览历史，让每次阅读都成为你的专属情报流。</p>
      <div class="visual-orbit"><span>AI</span><i></i><i></i><i></i></div>
    </div>
    <div class="auth-form-wrap">
      <form class="auth-form" @submit.prevent="submit">
        <span class="eyebrow dark">{{ isRegister ? 'CREATE ACCOUNT' : 'WELCOME BACK' }}</span>
        <h2>{{ isRegister ? '创建阅读账户' : '欢迎回来' }}</h2>
        <p>{{ isRegister ? '第一个注册用户将获得管理员权限。' : '登录后继续你的智能新闻阅读。' }}</p>
        <label><span>用户名{{ isRegister ? '' : '或邮箱' }}</span><input v-model.trim="form.username" required minlength="3" autocomplete="username" placeholder="请输入用户名" /></label>
        <label v-if="isRegister"><span>邮箱</span><input v-model.trim="form.email" required type="email" autocomplete="email" placeholder="name@example.com" /></label>
        <label v-if="isRegister"><span>姓名 <small>选填</small></span><input v-model.trim="form.full_name" autocomplete="name" placeholder="如何称呼你" /></label>
        <label><span>密码</span><input v-model="form.password" required type="password" minlength="8" autocomplete="current-password" placeholder="至少 8 位" /></label>
        <p v-if="error" class="inline-error">{{ error }}</p>
        <button class="button wide submit-button" :disabled="loading">{{ loading ? '请稍候…' : (isRegister ? '注册并进入' : '登录') }}</button>
        <div class="auth-switch">
          {{ isRegister ? '已有账户？' : '还没有账户？' }}
          <RouterLink :to="isRegister ? '/login' : '/register'">{{ isRegister ? '直接登录' : '立即注册' }}</RouterLink>
        </div>
      </form>
    </div>
  </section>
</template>

